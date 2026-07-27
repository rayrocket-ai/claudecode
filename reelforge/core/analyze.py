"""Cheap deterministic signals, computed once and cached.

Nothing here calls a language model. These are the measurements the brain reads
*instead of* watching the video: where the silences are, where the picture cuts,
where the energy peaks, and where the subject's face sits in frame.

Face positions matter more than they sound. Reframing 16:9 to 9:16 throws away
44% of the width, and the difference between a reel that looks shot vertically
and one that looks cropped is entirely whether that window follows the speaker.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import media
from .cache import Cache


@dataclass
class Signals:
    duration: float
    silence: list[tuple[float, float]] = field(default_factory=list)
    scenes: list[float] = field(default_factory=list)
    energy: list[float] = field(default_factory=list)      # per-second, 0..1
    focus: list[tuple[float, float, float]] = field(default_factory=list)
    filmstrip: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Signals":
        return cls(
            duration=d["duration"],
            silence=[tuple(s) for s in d.get("silence", [])],
            scenes=list(d.get("scenes", [])),
            energy=list(d.get("energy", [])),
            focus=[tuple(f) for f in d.get("focus", [])],
            filmstrip=list(d.get("filmstrip", [])),
        )

    def energy_at(self, t: float) -> float:
        i = int(t)
        return self.energy[i] if 0 <= i < len(self.energy) else 0.0

    def focus_at(self, t: float) -> tuple[float, float]:
        """Normalised subject centre at time ``t``, defaulting to frame centre.

        Falling back to centre rather than to the previous known position is
        deliberate: when detection fails the safest crop is the middle, and
        holding a stale position is how a reframe ends up locked on an empty
        chair.
        """
        best = (0.5, 0.5)
        for start, x, y in self.focus:
            if start > t:
                break
            best = (x, y)
        return best


# --------------------------------------------------------------------------
# energy
# --------------------------------------------------------------------------

_RMS_LINE = re.compile(r"RMS_level=(-?\d+(?:\.\d+)?|-?inf)")


def parse_energy(stderr: str, *, floor_db: float = -60.0) -> list[float]:
    """Per-window RMS in dB, normalised to 0..1.

    Digital silence reports ``-inf``, which is not a number any downstream
    arithmetic survives -- it is clamped to the floor rather than propagated.
    """
    values: list[float] = []
    for match in _RMS_LINE.finditer(stderr):
        raw = match.group(1)
        db = floor_db if raw.lstrip("-") == "inf" else float(raw)
        db = max(floor_db, min(0.0, db))
        values.append(round((db - floor_db) / -floor_db, 4))
    return values


def peaks(energy: list[float], *, above: float = 1.25, min_gap: int = 3) -> list[int]:
    """Seconds where energy jumps well above the local average.

    Emphasis, laughter and audience reaction all show up here. It is a weak
    signal alone -- it is useful because it *agrees* with the transcript and the
    scene cuts, and three weak signals agreeing is a strong one.
    """
    if not energy:
        return []
    mean = sum(energy) / len(energy)
    if mean <= 0:
        return []
    found, last = [], -min_gap
    for i, value in enumerate(energy):
        if value >= mean * above and i - last >= min_gap:
            found.append(i)
            last = i
    return found


# --------------------------------------------------------------------------
# subject tracking
# --------------------------------------------------------------------------

def smooth_focus(
    raw: list[tuple[float, float, float]], *, max_step: float = 0.06
) -> list[tuple[float, float, float]]:
    """Rate-limit focus movement so a reframe reads as a camera move.

    Per-frame face detection jitters by a few percent every frame, and a crop
    that follows it exactly looks like handheld footage shot during an
    earthquake. Clamping per-step movement produces the slow, intentional
    drift a human operator would make.
    """
    if not raw:
        return []
    out = [raw[0]]
    for t, x, y in raw[1:]:
        _, px, py = out[-1]
        dx, dy = x - px, y - py
        dist = math.hypot(dx, dy)
        if dist > max_step:
            scale = max_step / dist
            x, y = px + dx * scale, py + dy * scale
        out.append((t, round(x, 4), round(y, 4)))
    return out


def detect_focus(frames: list[Path], *, every_seconds: float) -> list[tuple[float, float, float]]:
    """Normalised face centre per sampled frame.

    Uses OpenCV's Haar cascade rather than a neural detector: it is bundled,
    needs no model download, and runs in milliseconds on CPU. It misses profile
    views, which is exactly why the result is smoothed and defaults to centre
    rather than being trusted frame by frame.
    """
    try:
        import cv2
    except ImportError:
        return []

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    raw: list[tuple[float, float, float]] = []
    for index, frame_path in enumerate(sorted(frames)):
        image = cv2.imread(str(frame_path))
        if image is None:
            continue
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5)
        if len(faces) == 0:
            continue
        # Largest face wins: in a two-shot the nearer speaker is the subject.
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        raw.append((
            round(index * every_seconds, 3),
            round((x + w / 2) / width, 4),
            # Bias upward: framing on the eyeline rather than the chin is the
            # difference between a portrait and a headless torso.
            round((y + h * 0.4) / height, 4),
        ))
    return smooth_focus(raw)


# --------------------------------------------------------------------------
# orchestration
# --------------------------------------------------------------------------

def analyze(src: Path, cache: Cache, key: str, *, every_seconds: float = 5.0) -> Signals:
    """Compute (or load) all deterministic signals for a source."""
    cached = cache.read_json(key, "signals.json")
    if cached:
        return Signals.from_dict(cached)

    info = media.probe(src)
    frames_dir = cache.dir_for(key) / "frames"
    frames_dir.mkdir(exist_ok=True)

    media.run(media.filmstrip_cmd(src, frames_dir / "f-%05d.jpg",
                                  every_seconds=every_seconds))
    frames = sorted(frames_dir.glob("f-*.jpg"))

    signals = Signals(
        duration=info.duration,
        silence=media.parse_silence(
            media.run_capturing_stderr(media.silence_cmd(src))
        ) if info.has_audio else [],
        scenes=media.parse_scenes(
            media.run_capturing_stderr(media.scene_cmd(src))
        ),
        energy=parse_energy(
            media.run_capturing_stderr(media.loudness_curve_cmd(src))
        ) if info.has_audio else [],
        focus=detect_focus(frames, every_seconds=every_seconds),
        filmstrip=[str(p.relative_to(cache.root)) for p in frames],
    )
    cache.write_json(key, "signals.json", signals.as_dict())
    return signals
