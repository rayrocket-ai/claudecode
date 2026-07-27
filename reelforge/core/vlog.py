"""Compose a long-form episode.

A different job from reels, and the difference is not just aspect ratio.

A reel *extracts* — find the one best moment and throw the other fifty-nine
minutes away. A vlog *tightens* — keep the whole thing, remove what drags,
and give it a shape. Almost every rule inverts. Cuts are rarer and gentler.
Length is not a constraint to hit but an outcome. Nothing is thrown away
without a reason, because the viewer chose this video and expects the content.

Reuses the composer's span arithmetic and cut rules; what differs is what gets
kept, and the structure laid on top: a cold open, chapters, b-roll slots.
"""

from __future__ import annotations

from .analyze import Signals
from .compose import (
    build_captions, internal_cuts, merge_spans, snap_to_words, subtract,
    to_segments,
)
from .edl import (
    EDL, Audio, BRollSlot, Chapter, Framing, Segment, Target, Transition,
)
from .playbook import Playbook
from .transcribe import Transcript

# A cold open is a moment lifted from later and played first. It works because
# the first fifteen seconds decide whether a YouTube viewer stays, and the
# strongest thing you said is rarely the first thing you said.
COLD_OPEN_MAX = 12.0
COLD_OPEN_MIN = 3.0


class Episode:
    """What the producer agent returns for a long-form edit."""

    def __init__(self, payload: dict):
        self.cold_open: tuple[float, float] | None = None
        raw = payload.get("cold_open")
        if raw and raw.get("end", 0) > raw.get("start", 0):
            self.cold_open = (float(raw["start"]), float(raw["end"]))

        self.body: tuple[float, float] | None = None
        body = payload.get("body")
        if body and body.get("end", 0) > body.get("start", 0):
            self.body = (float(body["start"]), float(body["end"]))

        self.drop = [
            (float(d["start"]), float(d["end"]), d.get("reason", "tangent"))
            for d in payload.get("drop", [])
            if float(d.get("end", 0)) > float(d.get("start", 0))
        ]
        self.chapters = [
            (float(c["at"]), str(c["title"]).strip())
            for c in payload.get("chapters", [])
            if str(c.get("title", "")).strip()
        ]
        self.broll = [
            (float(b["start"]), float(b.get("dur", 4.0)), b.get("prompt", ""))
            for b in payload.get("broll", [])
        ]
        self.title = payload.get("title", "")
        self.description = payload.get("description", "")
        self.tags = list(payload.get("tags", []))


def _map_to_output(edl: EDL, src_t: float) -> float | None:
    """Output time for a source timestamp, or None if it was cut."""
    for seg in edl.segments:
        if seg.src_in <= src_t <= seg.src_out:
            return edl.output_time(seg.id, src_t)
    return None


def _nearest_output(edl: EDL, src_t: float) -> float:
    """Output time for a source timestamp, snapped to the nearest surviving cut.

    A chapter boundary the producer placed inside a removed tangent still has
    to land somewhere. Snapping to the start of the next surviving segment is
    right: a chapter should open on content, and the alternative -- dropping it
    -- silently reduces the count below YouTube's minimum of three and makes
    every other chapter vanish too.
    """
    exact = _map_to_output(edl, src_t)
    if exact is not None:
        return exact
    elapsed = 0.0
    for seg in edl.segments:
        if seg.src_in > src_t:
            return round(elapsed, 3)
        elapsed += seg.out_duration
    return round(max(0.0, elapsed - 0.1), 3)


def _dedupe_chapters(chapters: list[Chapter], duration: float,
                     min_gap: float = 10.0) -> list[Chapter]:
    """Enforce YouTube's spacing by merging, never by dropping silently.

    Two chapter marks that collapse onto the same moment after cutting are one
    chapter. Keeping the first preserves the section's opening; keeping the
    later one would start it mid-thought.
    """
    ordered = sorted(chapters, key=lambda c: c.at)
    kept: list[Chapter] = []
    for chapter in ordered:
        if kept and chapter.at - kept[-1].at < min_gap:
            continue
        if duration - chapter.at < min_gap:
            break                                # too close to the end to render
        kept.append(chapter)

    # All or nothing. Once cutting has collapsed the list below YouTube's
    # minimum of three, the survivors are not a shorter chapter list -- they
    # are a list YouTube will refuse to render while reporting nothing. Better
    # to return none and say why than to ship one chapter and a permanent
    # validation error.
    if len(kept) < 3:
        return []

    kept[0] = Chapter(0.0, kept[0].title)        # YouTube requires 0:00
    return kept


def compose_episode(episode: Episode, source: str, transcript: Transcript,
                    signals: Signals, target: Target, book: Playbook) -> EDL:
    """Compose a long-form edit."""
    body_window = episode.body or (0.0, transcript.duration)
    body_window = snap_to_words(body_window, transcript, book)

    from .highlights import Clip, Drop
    proxy = Clip(body_window[0], body_window[1],
                 drop=[Drop(s, e, r) for s, e, r in episode.drop])

    cuts = internal_cuts(proxy, transcript, book, body_window)
    kept = subtract(body_window, cuts)
    body_segments = to_segments(kept, book)

    segments: list[Segment] = []
    transitions: list[Transition] = []
    cold_open_out = 0.0

    if episode.cold_open:
        start, end = snap_to_words(episode.cold_open, transcript, book)
        length = min(max(end - start, 0.0), COLD_OPEN_MAX)
        if length >= COLD_OPEN_MIN:
            segments.append(Segment("cold", round(start, 3),
                                    round(start + length, 3),
                                    why="cold open, lifted from later"))
            cold_open_out = length
            # A hard cut from the cold open into the intro reads as an error;
            # a short dissolve reads as a title card boundary.
            transitions.append(Transition(at=round(length, 3), type="dissolve",
                                          dur=0.4))

    for index, seg in enumerate(body_segments, start=1):
        segments.append(Segment(f"s{index}", seg.src_in, seg.src_out,
                                speed=seg.speed, why=seg.why))

    edl = EDL(
        source=source,
        target=target,
        segments=segments,
        transitions=transitions,
        audio=Audio(fade_ms=book.fade_ms),
        notes=episode.description,
    )
    if not segments:
        return edl

    # Long-form does not want reel framing. A 16:9 source going to 16:9 needs
    # no crop, and constant push-ins over twenty minutes are exhausting -- the
    # move that makes a reel feel alive makes an episode feel restless.
    edl.framing = [Framing(seg=s.id, focus=signals.focus_at((s.src_in + s.src_out) / 2),
                           mode="static") for s in segments]

    edl.captions = build_captions(edl, transcript, book)
    # Burned-in captions are wrong for YouTube: it has its own caption UI, the
    # viewer may want them off, and burned text cannot be translated. The words
    # are kept so a sidecar .srt can be written instead.
    edl.captions.enabled = False

    chapters = [Chapter(_nearest_output(edl, at), title)
                for at, title in episode.chapters]
    edl.chapters = _dedupe_chapters(chapters, edl.duration)

    edl.broll = []
    for start, dur, prompt in episode.broll:
        at = _map_to_output(edl, start)
        if at is None:
            continue                             # the moment was cut
        edl.broll.append(BRollSlot(
            start=round(at, 3),
            dur=round(min(dur, max(0.0, edl.duration - at)), 3),
            prompt=prompt,
        ))

    return edl
