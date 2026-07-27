"""Quality control: inspect a render, repair the EDL, render again.

This is the difference between "an agent cut my video" and "this is
publishable". Everything upstream makes decisions that are individually
reasonable and occasionally combine badly -- a cut that lands mid-syllable, a
caption sitting under the platform's share tray, two shots spliced so similarly
that the join reads as a glitch rather than an edit.

Two principles:

**Repairs go into the EDL, never into the pixels.** Fixing a render would leave
the EDL lying about what was made. Fixing the EDL and re-rendering keeps the one
guarantee the whole system rests on -- that the output is a pure function of
``(source, EDL)``.

**Detection is separated from measurement.** Anything that needs ffmpeg returns
raw numbers; the judgment about those numbers is a pure function. That keeps the
editorial thresholds -- which is where the arguments are -- testable without
rendering anything.
"""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import media
from .edl import EDL, Segment
from .playbook import Playbook
from .render.ass import STYLES, safe_area
from .transcribe import Transcript

# A cut this close to a word boundary is inside the word. Whisper's boundaries
# are good to a few tens of milliseconds, so anything tighter would flag noise.
MIDWORD_TOLERANCE = 0.06

# A jump cut sits in a *band* of structural difference, not at either extreme.
# Below the floor the frames are effectively identical and the join is
# invisible; above the ceiling it is a genuine change of shot and reads as
# intentional. Between them is the same shot spliced to itself with the subject
# displaced -- which is what cutting filler out of a locked-off camera makes,
# and what the eye reads as a dropped frame.
JUMP_MIN_DIFFERENCE = 0.012
JUMP_MAX_DIFFERENCE = 0.090

# Sample-to-sample jump at a splice, as a fraction of full scale. Above this it
# is audible as a click.
POP_THRESHOLD = 0.25

LOUDNESS_TOLERANCE = 1.5     # LUFS


@dataclass
class Finding:
    check: str
    detail: str
    severity: str = "warn"           # "fail" blocks, "warn" is advisory
    at: float | None = None          # output seconds
    repairable: bool = False

    def __str__(self) -> str:
        where = f" at {self.at:.2f}s" if self.at is not None else ""
        return f"[{self.severity}] {self.check}{where}: {self.detail}"


@dataclass
class QCResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "fail"]

    @property
    def repairable(self) -> list[Finding]:
        return [f for f in self.findings if f.repairable]

    @property
    def clean(self) -> bool:
        return not self.failures


# --------------------------------------------------------------------------
# static checks -- pure, no render required
# --------------------------------------------------------------------------

def check_midword_cuts(edl: EDL, transcript: Transcript) -> list[Finding]:
    """Cuts landing inside a word.

    The most audible failure in machine editing -- more obvious than any visual
    jump, because the ear catches a severed consonant instantly.
    """
    findings = []
    for seg in edl.segments:
        for boundary, label in ((seg.src_in, "in"), (seg.src_out, "out")):
            for word in transcript.words:
                inside = word.start + MIDWORD_TOLERANCE < boundary < word.end - MIDWORD_TOLERANCE
                if inside:
                    findings.append(Finding(
                        check="midword-cut",
                        detail=f"{seg.id} {label} cuts through {word.text!r} "
                               f"({word.start:.2f}-{word.end:.2f})",
                        severity="fail",
                        at=boundary,
                        repairable=True,
                    ))
                    break
    return findings


def check_caption_safe_area(edl: EDL) -> list[Finding]:
    """Captions inside the zone platform UI covers.

    Text there is not small, it is invisible -- hidden behind the caption,
    username and share tray that every vertical platform overlays.
    """
    if not edl.captions.enabled or not edl.captions.words:
        return []
    style = STYLES.get(edl.captions.style, STYLES["karaoke-bold"])
    top, bottom = safe_area(edl.target)
    y = style.position * edl.target.height
    if y > bottom:
        return [Finding(
            check="caption-safe-area",
            detail=f"captions sit at {y:.0f}px, below the {bottom:.0f}px safe "
                   "line -- platform UI will cover them",
            severity="fail", repairable=True,
        )]
    if y < top:
        return [Finding(
            check="caption-safe-area",
            detail=f"captions sit at {y:.0f}px, above the {top:.0f}px safe line",
            severity="fail", repairable=True,
        )]
    return []


def check_orphan_ending(edl: EDL) -> list[Finding]:
    """A single word left alone on the final caption card.

    It flashes up as the clip ends and reads as a rendering fault rather than
    an edit. Almost always means the clip ended one word past its real end.
    """
    words = edl.captions.words
    if not edl.captions.enabled or len(words) < 2:
        return []
    last, previous = words[-1], words[-2]
    if last.break_before or last.start - previous.end > 0.7:
        if last.end - last.start < 0.45:
            return [Finding(
                check="orphan-ending",
                detail=f"the clip ends on {last.text!r} alone on a card",
                severity="warn", at=last.start, repairable=True,
            )]
    return []


def check_length(edl: EDL, book: Playbook) -> list[Finding]:
    findings = []
    if edl.target.max_dur and edl.duration > edl.target.max_dur:
        findings.append(Finding(
            check="over-length",
            detail=f"{edl.duration:.1f}s exceeds the "
                   f"{edl.target.max_dur:.0f}s {edl.target.platform} limit",
            severity="fail", repairable=True,
        ))
    if edl.target.platform == "reels" and edl.duration < book.min_seconds:
        findings.append(Finding(
            check="under-length",
            detail=f"{edl.duration:.1f}s is below the {book.min_seconds:.0f}s "
                   "floor for short-form",
            severity="warn",
        ))
    return findings


def check_shot_rhythm(edl: EDL, book: Playbook) -> list[Finding]:
    """Shots too short to register, and zoom cadence.

    Both are about the same thing: an edit that changes faster than the viewer
    can absorb reads as broken rather than energetic.
    """
    findings = []
    elapsed = 0.0
    last_punch = -1e9
    for seg in edl.segments:
        if seg.out_duration < book.min_shot:
            findings.append(Finding(
                check="flash-shot",
                detail=f"{seg.id} is {seg.out_duration:.2f}s, under the "
                       f"{book.min_shot:.2f}s floor",
                severity="fail", at=elapsed, repairable=True,
            ))
        framing = edl.framing_for(seg.id)
        if framing.mode == "punch":
            if elapsed - last_punch < book.min_punch_gap:
                findings.append(Finding(
                    check="punch-cadence",
                    detail=f"{seg.id} pushes in {elapsed - last_punch:.1f}s after "
                           f"the previous push (minimum {book.min_punch_gap:.1f}s)",
                    severity="warn", at=elapsed, repairable=True,
                ))
            last_punch = elapsed
        elapsed += seg.out_duration
    return findings


def static_checks(edl: EDL, transcript: Transcript | None,
                  book: Playbook) -> list[Finding]:
    """Everything checkable without rendering a frame."""
    findings: list[Finding] = []
    if transcript is not None:
        findings += check_midword_cuts(edl, transcript)
    findings += check_caption_safe_area(edl)
    findings += check_orphan_ending(edl)
    findings += check_length(edl, book)
    findings += check_shot_rhythm(edl, book)
    return findings


# --------------------------------------------------------------------------
# measurement -- needs ffmpeg; judgment stays pure
# --------------------------------------------------------------------------

def measure_loudness(path: Path) -> float | None:
    """Integrated loudness in LUFS, or None if it cannot be measured."""
    stderr = media.run_capturing_stderr([
        "ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
        "-af", "ebur128=framelog=quiet", "-f", "null", "-",
    ])
    marker = "I:"
    for line in reversed(stderr.splitlines()):
        if marker in line and "LUFS" in line:
            try:
                return float(line.split(marker)[1].split("LUFS")[0].strip())
            except (IndexError, ValueError):
                continue
    return None


def judge_loudness(measured: float | None, target: float) -> list[Finding]:
    if measured is None:
        return []
    drift = measured - target
    if abs(drift) <= LOUDNESS_TOLERANCE:
        return []
    return [Finding(
        check="loudness",
        detail=f"{measured:.1f} LUFS against a {target:.1f} target "
               f"({drift:+.1f})",
        # Platforms re-normalise anyway, so this is a quality note rather than
        # something that stops the video being posted.
        severity="warn", repairable=True,
    )]


def sample_frames_at(path: Path, times: list[float], dest: Path) -> dict[float, Path]:
    """Extract one frame at each given output time."""
    dest.mkdir(parents=True, exist_ok=True)
    out: dict[float, Path] = {}
    for index, t in enumerate(times):
        frame = dest / f"qc-{index:04d}.png"
        try:
            media.run([
                "ffmpeg", "-hide_banner", "-nostdin", "-y",
                "-ss", f"{max(0.0, t):.3f}", "-i", str(path),
                "-frames:v", "1", str(frame),
            ])
        except media.FFmpegError:
            continue
        if frame.exists():
            out[t] = frame
    return out


def frame_difference(a: Path, b: Path) -> float | None:
    """Structural difference between two frames, 0..1.

    Deliberately *not* a colour histogram. A histogram ignores where things are,
    so for a talking head -- same person, same room, same lighting -- it barely
    moves across any cut. Measured on a real render, histogram correlation was
    above 0.97 for both a genuine shot change and two adjacent frames of the
    same shot, which would flag every cut in every reel and therefore tell you
    nothing.

    Downsampling to a small grayscale thumbnail and taking the mean absolute
    difference keeps composition, which is what actually changes at a cut.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    ia, ib = cv2.imread(str(a), cv2.IMREAD_GRAYSCALE), cv2.imread(str(b), cv2.IMREAD_GRAYSCALE)
    if ia is None or ib is None:
        return None
    size = (64, 64)
    ta = cv2.resize(ia, size, interpolation=cv2.INTER_AREA).astype("float32") / 255.0
    tb = cv2.resize(ib, size, interpolation=cv2.INTER_AREA).astype("float32") / 255.0
    return float(np.mean(np.abs(ta - tb)))


def judge_jump_cut(difference: float | None, at: float) -> list[Finding]:
    """A jump cut lives in a narrow band of difference, not at either extreme.

    Three cases, and only the middle one is a fault:

    - **Near zero** -- the frames are effectively identical, so the join is
      invisible. Fine.
    - **Large** -- a genuine change of shot or framing. Reads as an intentional
      cut. Fine.
    - **Small but visible** -- the same shot spliced to itself with the subject
      slightly displaced. This is exactly what removing a filler word from a
      locked-off camera produces, and the eye reads it as a dropped frame
      rather than an edit.

    Flagging by similarity alone gets this wrong at both ends: it passes the
    ugly middle case whenever lighting shifts, and fails every clean cut in any
    video shot in one room.
    """
    if difference is None:
        return []
    if JUMP_MIN_DIFFERENCE <= difference <= JUMP_MAX_DIFFERENCE:
        return [Finding(
            check="jump-cut",
            detail=f"frames either side differ by {difference:.3f} -- same "
                   "framing, subject displaced; the join will read as a skip",
            severity="warn", at=at, repairable=True,
        )]
    return []


def measure_pop(path: Path, at: float, window: float = 0.05) -> float | None:
    """Largest sample-to-sample jump near ``at``, as a fraction of full scale.

    A splice at an arbitrary sample value leaves a step discontinuity in the
    waveform. It reproduces as a click, it is completely inaudible in a
    waveform view, and it is the single most common thing that makes an
    otherwise good cut sound amateur.
    """
    try:
        import numpy as np
    except ImportError:
        return None

    proc = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
        "-ss", f"{max(0.0, at - window):.3f}",
        "-t", f"{window * 2:.3f}",
        "-i", str(path),
        "-f", "s16le", "-ac", "1", "-ar", "48000", "-",
    ], capture_output=True, check=False)

    if proc.returncode != 0 or len(proc.stdout) < 4:
        return None
    samples = np.frombuffer(proc.stdout, dtype="<i2").astype("float32") / 32768.0
    if samples.size < 2:
        return None
    return float(np.max(np.abs(np.diff(samples))))


def judge_pop(delta: float | None, at: float) -> list[Finding]:
    if delta is None or delta < POP_THRESHOLD:
        return []
    return [Finding(
        check="audio-pop",
        detail=f"sample discontinuity of {delta:.2f} at the splice -- audible click",
        severity="fail", at=at, repairable=True,
    )]


def cut_times(edl: EDL) -> list[float]:
    """Output times of every internal cut."""
    times, elapsed = [], 0.0
    for seg in edl.segments[:-1]:
        elapsed += seg.out_duration
        times.append(round(elapsed, 3))
    return times


def render_checks(edl: EDL, rendered: Path, workdir: Path) -> list[Finding]:
    """Everything that requires looking at, and listening to, the output."""
    findings: list[Finding] = []

    findings += judge_loudness(measure_loudness(rendered), edl.target.loudness)

    cuts = cut_times(edl)
    if not cuts:
        return findings

    for at in cuts:
        findings += judge_pop(measure_pop(rendered, at), at)

    # One frame either side of each cut, far enough out to miss the boundary
    # frame itself but close enough to still be the same moment.
    wanted: list[float] = []
    for at in cuts:
        wanted += [max(0.0, at - 0.10), min(edl.duration - 0.05, at + 0.10)]
    frames = sample_frames_at(rendered, wanted, workdir / "qcframes")

    covered = {round(t.at, 2) for t in edl.transitions
               if t.type != "cut" and t.dur > 0}

    for at in cuts:
        # A join already carrying a dissolve has been dealt with. The frames
        # either side still differ -- the dip mitigates the join, it does not
        # change the content -- so re-measuring would re-raise the same finding
        # forever and make the repair look ineffective.
        if round(at, 2) in covered:
            continue
        before, after = frames.get(max(0.0, at - 0.10)), frames.get(min(edl.duration - 0.05, at + 0.10))
        if before and after:
            findings += judge_jump_cut(frame_difference(before, after), at)

    return findings


# --------------------------------------------------------------------------
# repair
# --------------------------------------------------------------------------

def repair(edl: EDL, findings: list[Finding], transcript: Transcript | None,
           book: Playbook) -> tuple[EDL, list[str]]:
    """Apply what can be fixed. Returns the new EDL and a log of changes."""
    from .compose import to_segments
    from .edl import Transition

    changes: list[str] = []
    kinds = {f.check for f in findings if f.repairable}

    if "midword-cut" in kinds and transcript is not None:
        moved = 0
        for index, seg in enumerate(edl.segments):
            new_in = _snap_out_of_word(seg.src_in, transcript, prefer="before")
            new_out = _snap_out_of_word(seg.src_out, transcript, prefer="after")
            if abs(new_in - seg.src_in) > 1e-3 or abs(new_out - seg.src_out) > 1e-3:
                edl.segments[index] = Segment(seg.id, round(new_in, 3),
                                              round(new_out, 3),
                                              speed=seg.speed, why=seg.why)
                moved += 1
        if moved:
            changes.append(f"snapped {moved} segment boundary(s) out of words")

    if "caption-safe-area" in kinds:
        # Styles are frozen, so a corrected position is registered as a new
        # named style rather than mutating a shared one -- otherwise fixing one
        # reel would silently move captions in every other render.
        from dataclasses import replace
        style = STYLES.get(edl.captions.style, STYLES["karaoke-bold"])
        top, bottom = safe_area(edl.target)
        wanted = min(max(style.position, top / edl.target.height + 0.02),
                     bottom / edl.target.height - 0.02)
        name = f"{style.name}-qc"
        STYLES[name] = replace(style, name=name, position=wanted)
        edl.captions.style = name
        changes.append(f"moved captions to {wanted:.2f} of frame height")

    if "audio-pop" in kinds:
        # The fade is what removes the step discontinuity at a splice. Longer
        # is safe: even 60ms is well under what reads as a fade rather than a
        # cut, and the click is worse than any softness.
        before = edl.audio.fade_ms
        edl.audio.fade_ms = min(60, max(before * 2, before + 15))
        changes.append(f"lengthened cut fades {before}ms -> {edl.audio.fade_ms}ms")

    if "jump-cut" in kinds:
        for finding in findings:
            if finding.check == "jump-cut" and finding.at is not None:
                if not any(abs(t.at - finding.at) < 0.01 for t in edl.transitions):
                    edl.transitions.append(
                        Transition(at=finding.at, type="dissolve", dur=0.16))
                    changes.append(f"added a 0.16s dissolve at {finding.at:.2f}s")

    if "flash-shot" in kinds:
        before = len(edl.segments)
        kept = to_segments([(s.src_in, s.src_out) for s in edl.segments], book)
        if kept:
            edl.segments = kept
            edl.framing = [f for f in edl.framing
                           if f.seg in {s.id for s in kept}]
            if before != len(kept):
                changes.append(f"dropped {before - len(kept)} flash shot(s)")

    if "punch-cadence" in kinds:
        elapsed, last_punch, relaxed = 0.0, -1e9, 0
        for seg in edl.segments:
            framing = edl.framing_for(seg.id)
            if framing.mode == "punch":
                if elapsed - last_punch < book.min_punch_gap:
                    framing.mode = "static"
                    framing.zoom_from = framing.zoom_to = 1.0
                    relaxed += 1
                else:
                    last_punch = elapsed
            elapsed += seg.out_duration
        if relaxed:
            changes.append(f"removed {relaxed} crowded push-in(s)")

    if "over-length" in kinds and edl.target.max_dur:
        from .compose import trim_to_length
        before = edl.duration
        edl.segments = trim_to_length(edl.segments, edl.target.max_dur)
        changes.append(f"trimmed {before:.1f}s -> {edl.duration:.1f}s")

    if "orphan-ending" in kinds and edl.captions.words:
        dropped = edl.captions.words.pop()
        changes.append(f"dropped the orphaned final word {dropped.text!r}")

    return edl, changes


def _snap_out_of_word(t: float, transcript: Transcript, *, prefer: str) -> float:
    """Move a boundary out of any word it currently falls inside.

    ``prefer='before'`` moves to the word's start (an in-point should not clip
    the attack), ``'after'`` to its end (an out-point should let the word
    finish). Moving the other way would cut the word in half from the other
    side, which is the same fault.
    """
    for word in transcript.words:
        if word.start + MIDWORD_TOLERANCE < t < word.end - MIDWORD_TOLERANCE:
            return word.start if prefer == "before" else word.end
    return t


# --------------------------------------------------------------------------
# the loop
# --------------------------------------------------------------------------

@dataclass
class QCRun:
    edl: EDL
    output: Path
    passes: int
    findings: list[Finding]
    changes: list[str]
    clean: bool


def render_with_qc(edl: EDL, dst: Path, profile, *, transcript=None,
                   book: Playbook | None = None, draft: bool = False,
                   max_passes: int = 3, workdir: Path | None = None) -> QCRun:
    """Render, inspect, repair, re-render -- up to ``max_passes`` times.

    Static checks run before the first render, because catching a mid-word cut
    from the EDL costs nothing and catching it from the output costs a full
    encode. Only the faults that genuinely need pixels or samples -- pops, jump
    cuts, loudness -- wait for a render.

    The loop stops early when a pass changes nothing. A repair that does not
    move the needle will not move it on the next attempt either, and burning
    two more encodes to discover that is exactly the kind of waste an
    unattended server should not be doing.
    """
    import tempfile

    from .render import ffmpeg_renderer

    book = book or Playbook()
    temp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="reelforge-qc-"))
    temp.mkdir(parents=True, exist_ok=True)

    all_changes: list[str] = []
    findings: list[Finding] = []
    output = dst

    for attempt in range(1, max_passes + 1):
        findings = static_checks(edl, transcript, book)
        if findings:
            edl, changes = repair(edl, findings, transcript, book)
            all_changes += changes
            if changes and attempt < max_passes:
                continue                     # re-check before spending an encode

        result = ffmpeg_renderer.render(edl, dst, profile, draft=draft,
                                        workdir=temp / f"pass{attempt}")
        output = result.output

        findings = static_checks(edl, transcript, book) + \
            render_checks(edl, output, temp / f"pass{attempt}")

        if not [f for f in findings if f.repairable]:
            return QCRun(edl, output, attempt, findings, all_changes,
                         clean=not [f for f in findings if f.severity == "fail"])

        if attempt == max_passes:
            break

        edl, changes = repair(edl, findings, transcript, book)
        if not changes:
            break                            # nothing moved; stop burning encodes
        all_changes += changes

    return QCRun(edl, output, max_passes, findings, all_changes,
                 clean=not [f for f in findings if f.severity == "fail"])
