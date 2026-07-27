"""Everything that ships alongside the video.

Subtitles, chapter text, and thumbnail candidates. None of it touches the
picture, all of it decides whether the video gets watched.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .edl import EDL, CaptionWord
from .render.ass import STYLES, group_words


def _srt_ts(seconds: float) -> str:
    """SRT wants ``HH:MM:SS,mmm`` -- a comma, not a point."""
    seconds = max(0.0, seconds)
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt(edl: EDL, style_name: str = "clean") -> str:
    """A sidecar subtitle file.

    Long-form gets a sidecar rather than burned-in text: YouTube has its own
    caption UI, the viewer may want them off, and burned pixels cannot be
    auto-translated into any other language.
    """
    words = edl.captions.words
    if not words:
        return ""
    style = STYLES.get(style_name, STYLES["clean"])
    lines = []
    for index, group in enumerate(group_words(words, style, edl.target), start=1):
        lines.append(str(index))
        lines.append(f"{_srt_ts(group[0].start)} --> {_srt_ts(group[-1].end)}")
        lines.append(" ".join(w.text for w in group))
        lines.append("")
    return "\n".join(lines)


def chapter_text(edl: EDL) -> str:
    """Chapter lines for a YouTube description.

    Returns empty when the chapters would not render. YouTube's failure mode is
    silence -- almost-valid chapters produce none at all, with no warning -- so
    publishing a broken list is strictly worse than publishing none.
    """
    from .edl import _chapter_problems

    if _chapter_problems(edl.chapters, edl.duration):
        return ""
    return "\n".join(f"{_stamp(c.at)} {c.title}"
                     for c in sorted(edl.chapters, key=lambda c: c.at))


def _stamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def description(edl: EDL, *, summary: str = "", tags: list[str] | None = None) -> str:
    parts = [summary.strip() or edl.notes.strip()]
    chapters = chapter_text(edl)
    if chapters:
        parts.append("Chapters:\n" + chapters)
    if tags:
        parts.append(" ".join(f"#{t.lstrip('#')}" for t in tags[:15]))
    return "\n\n".join(p for p in parts if p)


# --------------------------------------------------------------------------
# thumbnails
# --------------------------------------------------------------------------

@dataclass
class ThumbCandidate:
    path: Path
    at: float
    score: float
    reasons: list[str]


def score_frame(image) -> tuple[float, list[str]]:
    """Score one frame's suitability as a thumbnail.

    Three signals, in the order they matter:

    **Sharpness.** A motion-blurred frame is unusable no matter what is in it,
    and blur is what most mid-sentence frames are. Laplacian variance is the
    standard cheap measure.

    **A face, large and looking out.** Thumbnails with a visible face
    outperform ones without, consistently enough that it is the first thing a
    human picks for.

    **Contrast.** The thumbnail competes in a grid of other thumbnails at about
    thirty percent of this size. Flat frames disappear there.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        return 0.0, ["opencv unavailable"]

    reasons: list[str] = []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]

    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # ~100 is the conventional blur threshold; 400 is comfortably crisp.
    sharp_score = min(1.0, sharpness / 400.0)
    if sharp_score < 0.25:
        reasons.append("soft or motion-blurred")

    contrast = float(gray.std()) / 64.0
    contrast_score = min(1.0, contrast)
    if contrast_score < 0.4:
        reasons.append("low contrast, will vanish in a grid")

    face_score = 0.0
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5)
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        coverage = (w * h) / float(width * height)
        # Peaks around 12% of frame area: big enough to read at grid size,
        # not so big it is a nostril.
        face_score = max(0.0, 1.0 - abs(math.log(max(coverage, 1e-4) / 0.12)) / 2.5)
        reasons.append(f"face at {coverage * 100:.0f}% of frame")
    else:
        reasons.append("no face detected")

    score = 0.40 * sharp_score + 0.40 * face_score + 0.20 * contrast_score
    return round(score, 4), reasons


def thumbnail_candidates(frames: list[Path], *, every_seconds: float,
                         top: int = 5) -> list[ThumbCandidate]:
    """Rank sampled frames as thumbnail options."""
    try:
        import cv2
    except ImportError:
        return []

    scored: list[ThumbCandidate] = []
    for index, path in enumerate(sorted(frames)):
        image = cv2.imread(str(path))
        if image is None:
            continue
        score, reasons = score_frame(image)
        scored.append(ThumbCandidate(path, round(index * every_seconds, 2),
                                     score, reasons))

    scored.sort(key=lambda c: c.score, reverse=True)

    # Spread the picks out. The five best frames of a talking head are usually
    # five consecutive frames of the same expression, which is one option
    # presented five times.
    spread: list[ThumbCandidate] = []
    for candidate in scored:
        if any(abs(candidate.at - c.at) < every_seconds * 3 for c in spread):
            continue
        spread.append(candidate)
        if len(spread) >= top:
            break
    return spread
