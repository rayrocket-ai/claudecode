"""Learn a style from reference videos.

``memory/style-profile.md`` is for the things that are not numbers. This is
for the things that are: how fast the cuts come, how tight the pauses are,
where the captions sit, how hot the mix runs, how long the whole thing is. A
reference video *has* those numbers, and measuring them beats asking someone
to describe an edit they admire in words -- nobody says "median shot 1.4s,
pauses held to 180ms", but that is what they mean by "snappy".

Every number here is a measurement, and every suggestion is derived from one
with the reasoning attached. Nothing is inferred from vibes.

Two rules carried over from the feedback engine:

**One reference is a data point, not a style.** Suggestions are computed over
the *median* of every reference studied so far, so the first reference sets a
direction and the third settles it. Applying to the playbook is explicit
(``--apply``) because a playbook that swings on one video never converges.

**Provenance travels with the rule.** A value written by ``--apply`` carries
the reference names it came from, in the same ``provenance.json`` the
feedback engine uses, so a rule you later disagree with can be traced to the
video that caused it and removed.

What is *not* measured, and said so rather than guessed: emoji density,
b-roll, transitions, music genre, and any caption *style* beyond position.
Those are the editor agent's job with the reference's frames in front of it.
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from . import media
from .analyze import parse_energy
from .playbook import Playbook, load, render

#: Hard cuts: the existing analysis threshold. Soft events: low enough to fire
#: on punch-ins, reframes and jump cuts that a hard threshold treats as the
#: same shot. The gap between the two counts is the reference's *reframing*
#: cadence, which is the closest measurable proxy for "how many zooms".
HARD_CUT = 0.40
SOFT_CUT = 0.15
#: A soft event this close to a hard cut is the same cut seen twice.
CUT_MERGE_WINDOW = 0.25

#: Frame sampling for the caption band. One frame a second at 540px is enough
#: to see text edges and cheap enough to run on a phone-length reference.
SAMPLE_EVERY = 1.0
SAMPLE_WIDTH = 540
#: Caption band height as a fraction of the frame, and how much stronger than
#: the rest of the frame its edge density must be to count as text.
BAND_FRACTION = 0.08
BAND_CONTRAST = 1.8
#: How much the band's edge profile must move between consecutive sampled
#: frames for it to be captions rather than a static graphic. Profiles are
#: normalised to a mean of 1, so this is a fraction of the frame's own edge
#: level; identical frames differ by exactly zero, compressed video by a
#: few hundredths, changing words by far more.
STATIC_CHANGE = 0.05
#: Letterbox borders and UI chrome live in the outer few percent; a burned-in
#: caption never does.
BAND_MARGIN = 0.03

_NAME_CLEAN = re.compile(r"[^a-z0-9]+")


@dataclass
class Reading:
    """Everything measured from one reference, plus what derives from it."""

    name: str
    source: str
    measured_at: str
    duration: float
    width: int
    height: int
    fps: float
    cuts: list[float] = field(default_factory=list)
    soft_cuts: list[float] = field(default_factory=list)
    silences: list[tuple[float, float]] = field(default_factory=list)
    energy: list[float] = field(default_factory=list)
    loudness_lufs: float | None = None
    loudness_range: float | None = None
    caption_presence: float = 0.0
    caption_position: float | None = None

    # -- derived ---------------------------------------------------------
    @property
    def shot_lengths(self) -> list[float]:
        bounds = [0.0, *self.cuts, self.duration]
        return [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0]

    @property
    def median_shot(self) -> float:
        lengths = self.shot_lengths
        return statistics.median(lengths) if lengths else self.duration

    @property
    def cuts_per_minute(self) -> float:
        return 60.0 * len(self.cuts) / self.duration if self.duration else 0.0

    @property
    def soft_per_minute(self) -> float:
        return 60.0 * len(self.soft_cuts) / self.duration if self.duration else 0.0

    @property
    def silence_fraction(self) -> float:
        if not self.duration:
            return 0.0
        return min(1.0, sum(e - s for s, e in self.silences) / self.duration)

    @property
    def median_pause(self) -> float | None:
        gaps = [e - s for s, e in self.silences]
        return statistics.median(gaps) if gaps else None

    @property
    def energy_dynamics(self) -> float:
        """Coefficient of variation of the energy curve.

        A flat curve is a monologue at one level; a spiky one is emphasis,
        reactions and cuts landing on beats. It is the number that separates
        "edited" from "recorded".
        """
        if len(self.energy) < 2:
            return 0.0
        mean = statistics.fmean(self.energy)
        return statistics.pstdev(self.energy) / mean if mean > 0 else 0.0

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Reading":
        raw = json.loads(text)
        raw["silences"] = [tuple(pair) for pair in raw.get("silences", [])]
        return cls(**raw)


# --------------------------------------------------------------------------
# measurement
# --------------------------------------------------------------------------

def clean_name(source: Path, name: str | None = None) -> str:
    base = name or source.stem
    return _NAME_CLEAN.sub("-", base.lower()).strip("-") or "reference"


def _merge_soft(hard: list[float], soft: list[float]) -> list[float]:
    """Soft events that are not just a hard cut seen at a lower threshold."""
    return [
        t for t in soft
        if not any(abs(t - h) <= CUT_MERGE_WINDOW for h in hard)
    ]


def row_edge_profile(image) -> np.ndarray:
    """Per-row horizontal-edge density, normalised to the frame's own mean.

    Text is the densest horizontal-edge structure a frame ever has -- every
    glyph is a run of vertical strokes -- so a band of rows that is much
    edgier than the rest of the frame is where the captions are. Normalising
    by the frame's own mean makes a dark talking-head shot and a bright
    exterior comparable.
    """
    grey = np.asarray(image.convert("L"), dtype=np.float32)
    if grey.shape[1] < 2:
        return np.zeros(grey.shape[0], dtype=np.float32)
    dx = np.abs(np.diff(grey, axis=1))
    rows = dx.mean(axis=1)
    mean = float(rows.mean())
    if mean <= 1e-6:
        return np.zeros_like(rows)
    return rows / mean


def caption_band(profiles: list[np.ndarray]) -> tuple[float, float | None]:
    """Find the caption band across sampled frames.

    Returns ``(presence, position)``: the fraction of frames in which the band
    reads as text, and the band's vertical centre as 0..1 -- or ``None`` when
    no band is convincing.

    The band is chosen from the *average* profile over all frames, because a
    burned-in caption sits in the same place in every frame it appears in
    while everything else in the picture moves. That recurrence is the whole
    signal: a single edgy row in one frame is a fence; the same edgy rows in
    forty frames are subtitles.
    """
    if not profiles:
        return 0.0, None
    height = profiles[0].shape[0]
    stack = np.stack([p for p in profiles if p.shape[0] == height])
    if stack.size == 0:
        return 0.0, None

    band = max(3, int(height * BAND_FRACTION))
    margin = int(height * BAND_MARGIN)
    mean_profile = stack.mean(axis=0)

    window = np.convolve(mean_profile, np.ones(band) / band, mode="valid")
    lo, hi = margin, max(margin + 1, len(window) - margin)
    if hi <= lo:
        return 0.0, None
    start = lo + int(np.argmax(window[lo:hi]))
    centre = (start + band / 2) / height

    band_rows = stack[:, start:start + band]
    per_frame = band_rows.mean(axis=1)
    present = per_frame >= BAND_CONTRAST
    presence = float(present.mean())
    if presence == 0:
        return 0.0, None

    # Recurrence alone is not enough: a poster with big lettering behind the
    # speaker recurs at the same rows in every frame too. What separates
    # captions from set dressing is that captions *change* -- the words are
    # different a second later, so the band's edge profile moves. A band
    # whose profile is the same in every captioned frame is furniture.
    if stack.shape[0] >= 2:
        change = np.abs(np.diff(band_rows, axis=0)).mean(axis=1)
        if float(np.median(change)) < STATIC_CHANGE:
            return 0.0, None
    return presence, centre


def measure(src: Path, workdir: Path, *, name: str | None = None,
            when: str = "") -> Reading:
    """Measure one reference video. Everything here is an ffmpeg pass."""
    src = Path(src)
    info = media.probe(src)
    reading = Reading(
        name=clean_name(src, name),
        source=str(src),
        measured_at=when,
        duration=float(info.duration),
        width=int(info.width),
        height=int(info.height),
        fps=float(getattr(info, "fps", 30.0) or 30.0),
    )

    hard = media.parse_scenes(
        media.run_capturing_stderr(media.scene_cmd(src, threshold=HARD_CUT)))
    soft = media.parse_scenes(
        media.run_capturing_stderr(media.scene_cmd(src, threshold=SOFT_CUT)))
    reading.cuts = hard
    reading.soft_cuts = _merge_soft(hard, soft)

    reading.silences = media.parse_silence(
        media.run_capturing_stderr(media.silence_cmd(src)))
    reading.energy = parse_energy(
        media.run_capturing_stderr(media.loudness_curve_cmd(src)))
    reading.loudness_lufs, reading.loudness_range = media.parse_loudness(
        media.run_capturing_stderr(media.loudness_cmd(src)))

    frames_dir = Path(workdir) / f"frames-{reading.name}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    media.run(media.filmstrip_cmd(
        src, frames_dir / "f%05d.jpg", every_seconds=SAMPLE_EVERY, width=SAMPLE_WIDTH))
    from PIL import Image

    profiles = []
    for frame in sorted(frames_dir.glob("f*.jpg")):
        with Image.open(frame) as image:
            profiles.append(row_edge_profile(image))
    reading.caption_presence, reading.caption_position = caption_band(profiles)
    return reading


# --------------------------------------------------------------------------
# from measurements to playbook values
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Suggestion:
    field: str
    value: float | bool | str
    reason: str


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _median(values: list[float]) -> float:
    return statistics.median(values)


def suggest(readings: list[Reading]) -> list[Suggestion]:
    """Playbook values implied by the references, medians across all of them.

    Each mapping is a judgement, stated in its reason. The *direction* of each
    is what matters and what the tests pin down: a snappier reference must
    yield tighter pauses and shorter minimum shots, never the reverse.
    """
    if not readings:
        return []
    names = ", ".join(r.name for r in readings)
    out: list[Suggestion] = []

    median_shot = _median([r.median_shot for r in readings])
    # A shot shorter than ~40% of the reference's typical shot would read as
    # faster than the style, not as the style.
    out.append(Suggestion(
        "min_shot", round(_clamp(0.4 * median_shot, 0.4, 1.0), 2),
        f"reference median shot {median_shot:.2f}s ({names})"))

    soft = _median([r.soft_per_minute for r in readings])
    if soft >= 0.5:
        gap = _clamp(60.0 / soft, 1.5, 6.0)
        reason = f"reference reframes {soft:.1f}/min ({names})"
    else:
        gap = 6.0
        reason = f"reference almost never reframes ({names})"
    out.append(Suggestion("min_punch_gap", round(gap, 1), reason))

    pauses = [r.median_pause for r in readings if r.median_pause is not None]
    if pauses:
        pause = _median(pauses)
        out.append(Suggestion(
            "keep_pause", round(_clamp(0.6 * pause, 0.10, 0.35), 2),
            f"reference median pause {pause:.2f}s ({names})"))
        out.append(Suggestion(
            "min_gap_to_cut", round(_clamp(1.2 * pause, 0.35, 0.90), 2),
            f"pauses under this are the reference's own rhythm ({names})"))

    presence = _median([r.caption_presence for r in readings])
    captioned = presence >= 0.5
    out.append(Suggestion(
        "captions_enabled", captioned,
        f"text band present in {presence:.0%} of sampled frames ({names})"))
    positions = [r.caption_position for r in readings
                 if r.caption_position is not None and r.caption_presence >= 0.5]
    if captioned and positions:
        out.append(Suggestion(
            "caption_position", round(_median(positions), 2),
            f"reference caption band centre ({names})"))

    duration = _median([r.duration for r in readings])
    max_s = _clamp(round(1.15 * duration), 15, 180)
    min_s = _clamp(round(0.6 * duration), 8, max_s - 5)
    out.append(Suggestion("max_seconds", float(max_s),
                          f"reference runs {duration:.0f}s ({names})"))
    out.append(Suggestion("min_seconds", float(min_s),
                          f"reference runs {duration:.0f}s ({names})"))

    lufs = [r.loudness_lufs for r in readings if r.loudness_lufs is not None]
    if lufs:
        out.append(Suggestion(
            "loudness", float(_clamp(round(_median(lufs)), -20, -12)),
            f"reference integrated loudness {_median(lufs):.1f} LUFS ({names})"))
    return out


# --------------------------------------------------------------------------
# persistence and reporting
# --------------------------------------------------------------------------

def references_dir(memory: Path) -> Path:
    return Path(memory) / "references"


def save(reading: Reading, memory: Path) -> Path:
    folder = references_dir(memory)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{reading.name}.json"
    path.write_text(reading.to_json(), encoding="utf-8")
    return path


def load_all(memory: Path) -> list[Reading]:
    folder = references_dir(memory)
    if not folder.exists():
        return []
    readings = []
    for path in sorted(folder.glob("*.json")):
        try:
            readings.append(Reading.from_json(path.read_text(encoding="utf-8")))
        except (ValueError, TypeError, KeyError):
            # One corrupt file must not hide every other reference.
            continue
    return readings


def apply(suggestions: list[Suggestion], memory: Path, *, when: str) -> Playbook:
    """Write suggestions into the playbook with provenance, like feedback does."""
    memory = Path(memory)
    memory.mkdir(parents=True, exist_ok=True)
    book = load(memory / "playbook.md")

    provenance_path = memory / "provenance.json"
    provenance: dict[str, str] = {}
    if provenance_path.exists():
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        except ValueError:
            provenance = {}

    for s in suggestions:
        if not hasattr(book, s.field):
            continue
        setattr(book, s.field, s.value)
        provenance[s.field] = f"learned {when} from reference: {s.reason}"

    (memory / "playbook.md").write_text(render(book, provenance=provenance),
                                        encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return book


def render_report(reading: Reading, suggestions: list[Suggestion],
                  *, total_references: int) -> str:
    """A human-readable account of what was measured and what it implies."""
    pause = reading.median_pause
    lines = [
        f"# Reference study: {reading.name}",
        "",
        f"Source: `{reading.source}`",
        f"Measured: {reading.measured_at or 'now'}",
        "",
        "## What was measured",
        "",
        f"- Length: {reading.duration:.1f}s, "
        f"{reading.width}x{reading.height} "
        f"({'vertical' if reading.is_vertical else 'horizontal'}), {reading.fps:g}fps",
        f"- Hard cuts: {len(reading.cuts)} ({reading.cuts_per_minute:.1f}/min), "
        f"median shot {reading.median_shot:.2f}s",
        f"- Reframes / soft cuts: {len(reading.soft_cuts)} "
        f"({reading.soft_per_minute:.1f}/min) -- the zoom and jump-cut cadence",
        f"- Silence: {reading.silence_fraction:.0%} of runtime"
        + (f", median pause {pause:.2f}s" if pause is not None else ", no pauses found"),
        f"- Energy dynamics: {reading.energy_dynamics:.2f} "
        "(0 = one flat level, higher = emphasis and beats)",
        f"- Loudness: "
        + (f"{reading.loudness_lufs:.1f} LUFS, range {reading.loudness_range or 0:.1f} LU"
           if reading.loudness_lufs is not None else "not measured"),
        f"- Captions: text band in {reading.caption_presence:.0%} of sampled frames"
        + (f", centred at {reading.caption_position:.0%} of frame height"
           if reading.caption_position is not None else ""),
        "",
        "## What it implies for the playbook",
        "",
        f"Computed over {total_references} reference"
        f"{'s' if total_references != 1 else ''} studied so far."
        + (" One reference is a direction, not a style -- study two more "
           "before applying." if total_references < 3 else ""),
        "",
    ]
    for s in suggestions:
        lines.append(f"- `{s.field}: {s.value}`  -- {s.reason}")
    lines += [
        "",
        "## Not measured (on purpose)",
        "",
        "Emoji density, b-roll, transitions, music, and caption *style* beyond",
        "position. Those need eyes on the frames -- hand the reference to the",
        "editor agent alongside this report.",
        "",
    ]
    return "\n".join(lines)
