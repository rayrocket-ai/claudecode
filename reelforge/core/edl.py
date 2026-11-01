"""The Edit Decision List -- the contract everything else agrees on.

The EDL is the product; the MP4 is a build artifact. The brain writes one, the
renderer reads one, QC repairs one, and `/reel-feedback` learns by diffing what
was proposed against what survived. Nothing downstream of here ever re-derives
an editorial decision -- if it is not in the EDL, it does not happen.

Times are always **source** seconds in :class:`Segment`, and **output** seconds
everywhere else. That distinction is the single easiest thing to get wrong here,
so :meth:`EDL.output_time` is the only sanctioned way to convert.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

SCHEMA_VERSION = 1

Aspect = Literal["9:16", "16:9", "1:1", "4:5"]
Ease = Literal["linear", "outCubic", "inOutCubic"]


@dataclass
class Target:
    platform: str = "reels"
    aspect: Aspect = "9:16"
    fps: int = 30
    width: int = 1080
    max_dur: float | None = 59.0
    loudness: float = -16.0          # LUFS; -16 short-form, -14 YouTube

    @property
    def height(self) -> int:
        w, h = (int(n) for n in self.aspect.split(":"))
        # Force even: h264 chroma subsampling rejects odd dimensions, and the
        # error ffmpeg gives for it is famously unhelpful.
        return int(round(self.width * h / w / 2)) * 2


@dataclass
class Segment:
    """A span of the source that survives into the output."""
    id: str
    src_in: float
    src_out: float
    speed: float = 1.0
    why: str = ""                    # why the brain kept it -- read by feedback

    @property
    def src_duration(self) -> float:
        return max(0.0, self.src_out - self.src_in)

    @property
    def out_duration(self) -> float:
        return self.src_duration / max(0.01, self.speed)


@dataclass
class Framing:
    """How the crop window moves during one segment."""
    seg: str
    focus: tuple[float, float] = (0.5, 0.5)   # normalised subject centre
    mode: Literal["static", "punch"] = "static"
    zoom_from: float = 1.0
    zoom_to: float = 1.0
    ease: Ease = "outCubic"


@dataclass
class CaptionWord:
    text: str
    start: float                     # output seconds
    end: float
    break_before: bool = False
    """Force a new caption card here.

    Set on the first word after every cut. Without it a card can straddle a
    cut -- the last word of one segment and the first of the next land close
    together in *output* time, so nothing else in the grouping rules notices
    that a cut happened. On screen it reads as a mistake and joins two
    unrelated sentences."""


@dataclass
class Captions:
    style: str = "karaoke-bold"
    words: list[CaptionWord] = field(default_factory=list)
    enabled: bool = True
    position: float | None = None
    """Where the bottom of the caption block sits, 0..1 of frame height.

    ``None`` means the style's default. Set from the playbook's learned
    ``caption_position`` -- without this field, "the captions sat too low"
    moved a number in the playbook that no renderer ever read."""


@dataclass
class Overlay:
    type: Literal["emoji", "remotion", "hyperframes", "image"]
    at: float                        # output seconds
    dur: float = 0.8
    glyph: str = ""                  # emoji only
    anchor: Literal["tl", "tr", "bl", "br", "c"] = "tr"
    anim: Literal["pop", "fade", "none"] = "pop"
    comp: str = ""                   # remotion/hyperframes composition name
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class Transition:
    at: float                        # output seconds, at a segment boundary
    type: Literal["cut", "fade", "whip", "dissolve"] = "cut"
    dur: float = 0.0


@dataclass
class Chapter:
    """A YouTube chapter marker, in output seconds.

    YouTube only renders chapters when the first one starts at 0:00 and there
    are at least three, each ten seconds or longer. Those are its rules, not
    ours, and :func:`validate` enforces them -- a description with almost-valid
    chapters silently shows none at all, which is worse than having omitted
    them.
    """
    at: float
    title: str


@dataclass
class BRollSlot:
    """A span where the picture wants covering, with what it is about.

    Marked, not filled. An editor cutting a vlog knows where the talking head
    gets boring long before they know what to put there, and separating those
    two decisions means the edit is reviewable before any asset is generated
    or licensed.
    """
    start: float                     # output seconds
    dur: float
    prompt: str = ""
    source: str = ""                 # filled in once an asset is chosen


@dataclass
class SoundEffect:
    """One effect, placed in output seconds.

    ``at`` is where the effect should be *heard landing*, not where its file
    starts. The renderer shifts playback earlier by the catalogue's ``lead`` so
    a whoosh covers the cut it belongs to instead of arriving just after it --
    getting this wrong is the difference between "produced" and "someone added
    sound effects".
    """
    at: float
    name: str                        # a key in render.sfx.CATALOGUE
    gain_db: float = -6.0
    why: str = ""


@dataclass
class Audio:
    music: str | None = None
    music_gain_db: float = -18.0
    duck: bool = True
    fade_ms: int = 20                # at every cut -- this is what kills pops
    #: Compression applied to the music whenever speech is present. Defaults
    #: chosen to be felt and not heard: enough that words stay in front, slow
    #: enough on release that the bed does not pump between sentences.
    duck_threshold: float = 0.045
    duck_ratio: float = 9.0
    duck_attack_ms: float = 15.0
    duck_release_ms: float = 420.0


@dataclass
class TopClip:
    """One visual in the top panel of a split-screen layout, in output seconds.

    Three kinds, taken from the two reference formats the layout copies:

    - ``image`` -- a screenshot, diagram or photo, with an optional pan/zoom
      from ``pan_from`` to ``pan_to`` (each ``(cx, cy, zoom)``, centre in
      0..1). One big diagram panned across while the speaker walks through
      it is the explainer format.
    - ``video`` -- a screen recording or b-roll clip, muted, cover-fitted.
    - ``prompt`` -- the showcase format: a chat box types ``text`` in, then
      ``result`` (an image or video) appears beside it. ``label`` is the pill
      at the seam -- "WRITE THIS" while typing, "TO GET THIS." on the reveal.
    """
    at: float
    dur: float
    kind: Literal["image", "video", "prompt"] = "image"
    asset: str = ""
    pan_from: tuple[float, float, float] = (0.5, 0.5, 1.0)
    pan_to: tuple[float, float, float] = (0.5, 0.5, 1.0)
    text: str = ""
    result: str = ""
    label: str = ""
    result_label: str = ""
    """Seam pill once the result is showing; defaults to "TO GET THIS." for
    prompts. ``label`` defaults to "WRITE THIS" while the text types."""
    reveal: float = 0.5
    """Fraction of ``dur`` after which a prompt's result appears."""


@dataclass
class Layout:
    """How the frame is divided.

    ``full`` is the classic reel: the speaker fills the frame. ``split`` puts
    a visual panel on top and the speaker underneath, cropped to the lower
    region around their face, with captions on the seam -- the layout both
    reference reels use, because it lets the viewer see the thing being
    talked about *and* the person talking, all the time.
    """
    kind: Literal["full", "split"] = "full"
    ratio: float = 0.5
    """Share of the frame height given to the top panel."""
    top: list[TopClip] = field(default_factory=list)
    background: str = "#141416"


@dataclass
class EndCard:
    """A "Comment KEYWORD" call to action over the last seconds of the edit.

    The speaker keeps talking inside a phone-shaped frame while the keyword
    sits above them -- the comment-to-DM lead magnet both references end on.
    ``outro`` seconds at the very end fade to the handle and an Instagram
    mark.
    """
    keyword: str
    at: float
    dur: float
    subtitle: str = ""
    handle: str = ""
    outro: float = 0.0
    accent: str = "#FF6B2C"


@dataclass
class EDL:
    source: str
    target: Target = field(default_factory=Target)
    segments: list[Segment] = field(default_factory=list)
    framing: list[Framing] = field(default_factory=list)
    captions: Captions = field(default_factory=Captions)
    overlays: list[Overlay] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)
    audio: Audio = field(default_factory=Audio)
    sfx: list[SoundEffect] = field(default_factory=list)
    chapters: list[Chapter] = field(default_factory=list)
    broll: list[BRollSlot] = field(default_factory=list)
    layout: Layout = field(default_factory=Layout)
    end_card: EndCard | None = None
    version: int = SCHEMA_VERSION
    notes: str = ""

    # -- derived -----------------------------------------------------------

    @property
    def duration(self) -> float:
        return round(sum(s.out_duration for s in self.segments), 3)

    def framing_for(self, seg_id: str) -> Framing:
        for f in self.framing:
            if f.seg == seg_id:
                return f
        return Framing(seg=seg_id)

    def output_time(self, seg_id: str, src_t: float) -> float:
        """Convert a source timestamp inside a segment to output time.

        The only sanctioned source-to-output conversion. Everything that places
        a caption or an overlay goes through here, because doing the arithmetic
        by hand is how captions end up drifting a few frames per cut.
        """
        elapsed = 0.0
        for seg in self.segments:
            if seg.id == seg_id:
                offset = min(max(src_t - seg.src_in, 0.0), seg.src_duration)
                return round(elapsed + offset / max(0.01, seg.speed), 3)
            elapsed += seg.out_duration
        raise KeyError(f"no segment {seg_id!r}")

    # -- serialisation -----------------------------------------------------

    def as_dict(self) -> dict:
        data = asdict(self)
        data["target"]["height"] = self.target.height
        data["duration"] = self.duration
        return data

    def save(self, path: Path) -> Path:
        path.write_text(json.dumps(self.as_dict(), indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "EDL":
        return cls.from_dict(json.loads(Path(path).read_text()))

    @classmethod
    def from_dict(cls, d: dict) -> "EDL":
        version = d.get("version", SCHEMA_VERSION)
        if version > SCHEMA_VERSION:
            raise ValueError(
                f"EDL schema v{version} is newer than this build (v{SCHEMA_VERSION}). "
                "Update ReelForge rather than rendering it with stale rules."
            )
        target_fields = {k: v for k, v in d.get("target", {}).items() if k != "height"}
        caps = d.get("captions", {})
        return cls(
            source=d["source"],
            target=Target(**target_fields),
            segments=[Segment(**s) for s in d.get("segments", [])],
            framing=[Framing(**{**f, "focus": tuple(f.get("focus", (0.5, 0.5)))})
                     for f in d.get("framing", [])],
            captions=Captions(
                style=caps.get("style", "karaoke-bold"),
                enabled=caps.get("enabled", True),
                words=[CaptionWord(**w) for w in caps.get("words", [])],
                position=caps.get("position"),
            ),
            overlays=[Overlay(**o) for o in d.get("overlays", [])],
            transitions=[Transition(**t) for t in d.get("transitions", [])],
            audio=Audio(**d.get("audio", {})),
            sfx=[SoundEffect(**x) for x in d.get("sfx", [])],
            chapters=[Chapter(**c) for c in d.get("chapters", [])],
            broll=[BRollSlot(**b) for b in d.get("broll", [])],
            layout=_layout_from(d.get("layout")),
            end_card=EndCard(**d["end_card"]) if d.get("end_card") else None,
            version=version,
            notes=d.get("notes", ""),
        )


def _layout_from(raw: dict | None) -> Layout:
    if not raw:
        return Layout()
    top = []
    for clip in raw.get("top", []):
        clip = dict(clip)
        for key in ("pan_from", "pan_to"):
            if key in clip:
                clip[key] = tuple(clip[key])
        top.append(TopClip(**clip))
    return Layout(kind=raw.get("kind", "full"), ratio=raw.get("ratio", 0.5), top=top,
                  background=raw.get("background", "#141416"))


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

class EDLError(ValueError):
    pass


def validate(edl: EDL, *, source_duration: float | None = None) -> list[str]:
    """Return a list of problems. Empty means renderable.

    Deliberately returns problems rather than raising on the first one: QC
    repairs EDLs, and a repair loop that only ever sees one fault at a time
    takes several passes to converge on what could have been fixed in one.
    """
    problems: list[str] = []

    if not edl.segments:
        problems.append("no segments: nothing to render")

    seen: set[str] = set()
    for seg in edl.segments:
        if seg.id in seen:
            problems.append(f"duplicate segment id {seg.id!r}")
        seen.add(seg.id)

        if seg.src_out <= seg.src_in:
            problems.append(
                f"{seg.id}: src_out ({seg.src_out}) must be after src_in ({seg.src_in})"
            )
        if seg.src_in < 0:
            problems.append(f"{seg.id}: negative src_in {seg.src_in}")
        if source_duration is not None and seg.src_out > source_duration + 0.05:
            problems.append(
                f"{seg.id}: src_out {seg.src_out} runs past the source "
                f"({source_duration:.2f}s)"
            )
        if not 0.25 <= seg.speed <= 4.0:
            problems.append(f"{seg.id}: speed {seg.speed} outside 0.25-4.0")
        # Below about a third of a second a shot registers as a glitch rather
        # than as an edit -- the viewer sees a flash, not a cut.
        if seg.out_duration < 0.3:
            problems.append(
                f"{seg.id}: {seg.out_duration:.2f}s is too short to read as a shot"
            )

    for f in edl.framing:
        if f.seg not in seen:
            problems.append(f"framing references unknown segment {f.seg!r}")
        if not (0.0 <= f.focus[0] <= 1.0 and 0.0 <= f.focus[1] <= 1.0):
            problems.append(f"{f.seg}: focus {f.focus} outside the frame")
        if not (0.5 <= f.zoom_from <= 3.0 and 0.5 <= f.zoom_to <= 3.0):
            problems.append(f"{f.seg}: zoom outside 0.5-3.0")

    duration = edl.duration
    if edl.target.max_dur and duration > edl.target.max_dur:
        problems.append(
            f"{duration:.1f}s exceeds the {edl.target.max_dur:.0f}s "
            f"{edl.target.platform} limit"
        )

    for word in edl.captions.words:
        if word.end > duration + 0.05:
            problems.append(f"caption {word.text!r} at {word.start} runs past the edit")
            break
    for ov in edl.overlays:
        if ov.at > duration:
            problems.append(f"overlay at {ov.at}s is past the end of the edit")
            break

    for cue in edl.sfx:
        if cue.at > duration + 0.05:
            problems.append(f"sound effect {cue.name!r} at {cue.at}s is past the end")
            break
        if cue.gain_db > 0:
            # Effects are normalised to a fixed peak, so a positive gain is
            # asking for clipping rather than for emphasis.
            problems.append(
                f"sound effect {cue.name!r} gain {cue.gain_db}dB is above unity"
            )
            break

    for slot in edl.broll:
        if slot.start + slot.dur > duration + 0.05:
            problems.append(
                f"b-roll slot at {slot.start}s runs {slot.start + slot.dur - duration:.1f}s "
                "past the end of the edit"
            )
            break

    if edl.layout.kind == "split":
        if not 0.3 <= edl.layout.ratio <= 0.7:
            problems.append(f"split ratio {edl.layout.ratio} outside 0.3-0.7")
        for clip in edl.layout.top:
            if clip.at + clip.dur > duration + 0.05:
                problems.append(f"top-panel {clip.kind} at {clip.at}s runs past the end")
                break
            if clip.kind == "prompt" and not clip.text:
                problems.append(f"prompt panel at {clip.at}s has no text to type")
                break
    if edl.end_card is not None:
        card = edl.end_card
        if card.at + card.dur > duration + 0.05:
            problems.append(f"end card at {card.at}s runs past the end of the edit")
        if not card.keyword.strip():
            problems.append("end card has no keyword to comment")

    problems += _chapter_problems(edl.chapters, duration)
    return problems


# YouTube's own rules for rendering chapters at all. Almost-valid chapters show
# nothing, with no error and no indication anywhere that they were rejected --
# so these are hard failures here rather than warnings.
YT_MIN_CHAPTERS = 3
YT_MIN_CHAPTER_SECONDS = 10.0


def _chapter_problems(chapters: list[Chapter], duration: float) -> list[str]:
    if not chapters:
        return []

    problems: list[str] = []
    ordered = sorted(chapters, key=lambda c: c.at)

    if ordered[0].at > 0.001:
        problems.append(
            f"chapters must start at 0:00 (first is at {ordered[0].at:.1f}s) "
            "or YouTube renders none of them"
        )
    if len(ordered) < YT_MIN_CHAPTERS:
        problems.append(
            f"{len(ordered)} chapter(s): YouTube needs at least {YT_MIN_CHAPTERS}"
        )
    for a, b in zip(ordered, ordered[1:]):
        if b.at - a.at < YT_MIN_CHAPTER_SECONDS:
            problems.append(
                f"chapter {b.title!r} is only {b.at - a.at:.1f}s after the "
                f"previous one; YouTube requires {YT_MIN_CHAPTER_SECONDS:.0f}s"
            )
            break
    if duration and duration - ordered[-1].at < YT_MIN_CHAPTER_SECONDS:
        problems.append(
            f"last chapter {ordered[-1].title!r} leaves under "
            f"{YT_MIN_CHAPTER_SECONDS:.0f}s of video after it"
        )
    if any(not c.title.strip() for c in ordered):
        problems.append("a chapter has no title")

    return problems
