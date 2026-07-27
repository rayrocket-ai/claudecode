"""Turn a chosen clip into a concrete EDL.

This is where craft lives. The brain decided *what* is worth keeping; this
decides *how* it gets cut -- where cuts land relative to word boundaries, how
much breath survives a removed pause, when a push-in is one push-in too many,
how many emoji stop being punctuation and become wallpaper.

None of those numbers are hardcoded. They come from :class:`Playbook`, which is
read from ``memory/playbook.md``, which is what `/reel-feedback` rewrites. Move
a rule from here into a prompt and the system stops being able to learn it.

Everything in this module is pure: clip + transcript + signals + playbook in,
EDL out. That is what lets the editorial logic be tested against golden files
with no ffmpeg, no model, and no video.
"""

from __future__ import annotations

from .analyze import Signals
from .edl import (
    EDL, Audio, CaptionWord, Captions, Framing, Overlay, Segment, Target,
)
from .highlights import Clip
from .playbook import Playbook
from .transcribe import Transcript, Word

# Emoji chosen by what is actually being said. A keyword map is crude next to
# asking a model, but it is deterministic, inspectable, and free -- and being
# wrong here is cheap, whereas an unexplainable choice is not.
EMOJI_CUES: list[tuple[frozenset[str], str]] = [
    (frozenset({"money", "revenue", "profit", "paid", "price", "cost", "dollars"}), "\U0001F4B0"),
    (frozenset({"fast", "faster", "quick", "instantly", "speed", "rapid"}), "⚡"),
    (frozenset({"grow", "growth", "scale", "up", "increase", "doubled", "tripled"}), "\U0001F4C8"),
    (frozenset({"idea", "realise", "realize", "insight", "learned", "discovered"}), "\U0001F4A1"),
    (frozenset({"warning", "careful", "mistake", "wrong", "fail", "failed", "avoid"}), "⚠️"),
    (frozenset({"love", "favourite", "favorite", "best", "amazing", "incredible"}), "\U0001F525"),
    (frozenset({"think", "question", "why", "how", "wondering", "curious"}), "\U0001F914"),
    (frozenset({"launch", "shipped", "ship", "built", "release", "started"}), "\U0001F680"),
]
DEFAULT_EMOJI = "\U0001F525"


# --------------------------------------------------------------------------
# span arithmetic
# --------------------------------------------------------------------------

Span = tuple[float, float]


def merge_spans(spans: list[Span], *, gap: float = 0.0) -> list[Span]:
    ordered = sorted(s for s in spans if s[1] > s[0])
    if not ordered:
        return []
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]


def subtract(window: Span, cuts: list[Span]) -> list[Span]:
    """What remains of ``window`` after removing ``cuts``."""
    kept: list[Span] = []
    cursor = window[0]
    for start, end in merge_spans(cuts):
        if end <= window[0] or start >= window[1]:
            continue
        start, end = max(start, window[0]), min(end, window[1])
        if start > cursor:
            kept.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < window[1]:
        kept.append((cursor, window[1]))
    return kept


def snap_to_words(window: Span, transcript: Transcript, book: Playbook) -> Span:
    """Move clip boundaries onto word edges, with breath either side.

    A cut placed mid-word is the single most obvious sign a video was machine
    edited -- more obvious than a jump cut, because the ear catches a severed
    consonant instantly. The padding matters just as much: flush to the
    syllable clips the attack going in and feels truncated coming out.
    """
    inside = [w for w in transcript.words if w.end > window[0] and w.start < window[1]]
    if not inside:
        return window
    return (max(0.0, inside[0].start - book.lead_in), inside[-1].end + book.lead_out)


# --------------------------------------------------------------------------
# what gets cut from inside a clip
# --------------------------------------------------------------------------

def internal_cuts(clip: Clip, transcript: Transcript, book: Playbook,
                  window: Span) -> list[Span]:
    """Spans to remove from within the clip: the brain's, plus filler and air."""
    cuts: list[Span] = [(d.start, d.end) for d in clip.drop]

    for word in transcript.words:
        if word.start < window[0] or word.end > window[1]:
            continue
        if word.is_hard_filler:
            cuts.append((word.start - 0.02, word.end + 0.02))

    inside = [w for w in transcript.words if w.start >= window[0] and w.end <= window[1]]
    for prev, nxt in zip(inside, inside[1:]):
        gap = nxt.start - prev.end
        if gap >= book.min_gap_to_cut:
            # Remove the middle of the silence and leave `keep_pause` of it,
            # split either side of the cut, so the rhythm survives the
            # tightening. The half-pause on each side is what the cut is
            # padded with -- take it all and the delivery machine-guns.
            slack = book.keep_pause / 2
            cuts.append((prev.end + slack, nxt.start - slack))

    return merge_spans(cuts, gap=0.08)


def to_segments(kept: list[Span], book: Playbook) -> list[Segment]:
    """Kept spans to segments, discarding anything too short to read.

    A sliver left between two cuts flashes, so it has to go. It is *dropped*,
    never folded into its neighbour: extending the previous segment to cover a
    sliver would also swallow the cut that created it, silently reinstating the
    filler or flubbed take the edit had just removed. Dropping it simply widens
    the surrounding cut, which is what was wanted anyway.
    """
    segments: list[Segment] = []
    for start, end in kept:
        if end - start < book.min_shot:
            continue
        segments.append(Segment(f"s{len(segments) + 1}", round(start, 3),
                                round(end, 3), why="kept"))
    return segments


def trim_to_length(segments: list[Segment], max_seconds: float) -> list[Segment]:
    """Drop from the end until the edit fits the platform limit.

    From the end deliberately. The opening is what earns the view, so when
    something has to go it is the tail -- and a clip trimmed to a hard stop
    still works, whereas one missing its hook does not.
    """
    if max_seconds <= 0:
        return segments
    kept, total = [], 0.0
    for seg in segments:
        if total + seg.out_duration <= max_seconds:
            kept.append(seg)
            total += seg.out_duration
            continue
        remaining = max_seconds - total
        if remaining >= 1.0:
            kept.append(Segment(seg.id, seg.src_in, round(seg.src_in + remaining, 3),
                                speed=seg.speed, why=seg.why + " (trimmed to fit)"))
        break
    return kept


# --------------------------------------------------------------------------
# framing, captions, overlays
# --------------------------------------------------------------------------

def build_framing(segments: list[Segment], clip: Clip, signals: Signals,
                  book: Playbook) -> list[Framing]:
    """Focus and zoom per segment."""
    framing: list[Framing] = []
    last_punch = -1e9
    elapsed = 0.0

    for index, seg in enumerate(segments):
        focus = signals.focus_at((seg.src_in + seg.src_out) / 2)

        punch = False
        if index == 0 and book.hook_punch:
            punch = True                       # open on motion
        elif any(seg.src_in <= beat <= seg.src_out for beat in clip.emphasis):
            # Cadence is enforced in *output* time: two punches three seconds
            # apart in the source may be adjacent once the gap between them is
            # cut out.
            if elapsed - last_punch >= book.min_punch_gap:
                punch = True

        if punch:
            last_punch = elapsed
            framing.append(Framing(
                seg=seg.id, focus=focus, mode="punch",
                zoom_from=1.0, zoom_to=book.punch_zoom, ease="outCubic",
            ))
        else:
            framing.append(Framing(seg=seg.id, focus=focus, mode="static"))

        elapsed += seg.out_duration
    return framing


def build_captions(edl: EDL, transcript: Transcript, book: Playbook) -> Captions:
    """Map surviving words onto the output timeline."""
    if not book.captions_enabled:
        return Captions(enabled=False)

    words: list[CaptionWord] = []
    for index, seg in enumerate(edl.segments):
        first_in_segment = True
        for word in transcript.words:
            if word.start < seg.src_in or word.end > seg.src_out:
                continue
            if word.is_hard_filler:
                continue
            words.append(CaptionWord(
                text=word.text,
                start=edl.output_time(seg.id, word.start),
                end=edl.output_time(seg.id, word.end),
                # A cut is a sentence boundary as far as captions are
                # concerned, even when the words either side of it end up
                # adjacent in output time.
                break_before=first_in_segment and index > 0,
            ))
            first_in_segment = False
    return Captions(style=book.caption_style, words=words, enabled=True)


def pick_emoji(words: list[Word]) -> str:
    """Choose an emoji from what is being said around a beat."""
    spoken = {w.normalized for w in words}
    for cues, glyph in EMOJI_CUES:
        if spoken & cues:
            return glyph
    return DEFAULT_EMOJI


def build_overlays(edl: EDL, clip: Clip, transcript: Transcript,
                   book: Playbook) -> list[Overlay]:
    """Place emoji at emphasis beats, under a density ceiling."""
    if book.emoji_per_minute <= 0:
        return []

    budget = int(edl.duration / 60 * book.emoji_per_minute)
    if budget < 1:
        # Even a very short reel gets one, or the ceiling silently means "none"
        # for everything under ten seconds.
        budget = 1 if edl.duration >= 4.0 else 0

    overlays: list[Overlay] = []
    last_at = -1e9
    anchors = ("tr", "tl")

    for beat in sorted(clip.emphasis):
        if len(overlays) >= budget:
            break
        seg = next((s for s in edl.segments if s.src_in <= beat <= s.src_out), None)
        if seg is None:
            continue                            # the beat was cut out
        at = edl.output_time(seg.id, beat)
        if at - last_at < book.emoji_min_gap:
            continue
        if at > edl.duration - 0.6:
            continue                            # would be cut off by the end
        nearby = [w for w in transcript.words if beat - 1.5 <= w.start <= beat + 1.5]
        overlays.append(Overlay(
            type="emoji", at=round(at, 3), dur=0.9,
            glyph=pick_emoji(nearby),
            anchor=anchors[len(overlays) % len(anchors)],
            anim="pop",
        ))
        last_at = at
    return overlays


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def compose(clip: Clip, source: str, transcript: Transcript, signals: Signals,
            target: Target, book: Playbook) -> EDL:
    """Compose one clip into a renderable EDL."""
    window = snap_to_words((clip.start, clip.end), transcript, book)
    cuts = internal_cuts(clip, transcript, book, window)
    kept = subtract(window, cuts)
    segments = to_segments(kept, book)

    if target.max_dur:
        segments = trim_to_length(segments, target.max_dur)

    edl = EDL(
        source=source,
        target=target,
        segments=segments,
        audio=Audio(fade_ms=book.fade_ms),
        notes=clip.why,
    )
    if not segments:
        return edl

    edl.framing = build_framing(segments, clip, signals, book)
    edl.captions = build_captions(edl, transcript, book)
    edl.overlays = build_overlays(edl, clip, transcript, book)
    return edl
