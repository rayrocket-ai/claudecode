"""Tests for the composer -- where editorial craft is enforced.

These are the highest-value tests in the project. Everything here is a decision
you would notice in the finished video and could not see in the code.
"""

import pytest

from reelforge.core.analyze import Signals
from reelforge.core.compose import (
    build_overlays, compose, internal_cuts, merge_spans, pick_emoji,
    snap_to_words, subtract, to_segments, trim_to_length,
)
from reelforge.core.edl import Segment, Target
from reelforge.core.highlights import Clip, Drop
from reelforge.core.playbook import Playbook
from reelforge.core.transcribe import Transcript, Word

TARGET = Target(aspect="9:16", width=1080, fps=30, max_dur=59.0)
BOOK = Playbook()


def speech(*specs) -> Transcript:
    return Transcript([Word(t, s, e) for t, s, e in specs], "en", 120.0, "test")


def steady(count=30, *, start=0.0, dur=0.35, gap=0.05, word="word") -> Transcript:
    words, t = [], start
    for i in range(count):
        words.append(Word(f"{word}{i}", round(t, 3), round(t + dur, 3)))
        t += dur + gap
    return Transcript(words, "en", t, "test")


# --------------------------------------------------------------------------
# span arithmetic
# --------------------------------------------------------------------------

def test_subtract_splits_a_window():
    assert subtract((0.0, 10.0), [(3.0, 4.0)]) == [(0.0, 3.0), (4.0, 10.0)]


def test_subtract_handles_cuts_at_the_edges():
    assert subtract((0.0, 10.0), [(0.0, 2.0)]) == [(2.0, 10.0)]
    assert subtract((0.0, 10.0), [(8.0, 10.0)]) == [(0.0, 8.0)]


def test_subtract_ignores_cuts_outside_the_window():
    assert subtract((5.0, 10.0), [(0.0, 1.0), (20.0, 21.0)]) == [(5.0, 10.0)]


def test_subtract_of_everything_leaves_nothing():
    assert subtract((0.0, 10.0), [(0.0, 10.0)]) == []


def test_merge_joins_touching_spans():
    assert merge_spans([(0.0, 1.0), (1.0, 2.0)]) == [(0.0, 2.0)]


def test_merge_respects_a_gap_tolerance():
    assert merge_spans([(0.0, 1.0), (1.05, 2.0)], gap=0.1) == [(0.0, 2.0)]
    assert len(merge_spans([(0.0, 1.0), (1.05, 2.0)], gap=0.0)) == 2


# --------------------------------------------------------------------------
# word-boundary snapping -- the most audible failure in machine editing
# --------------------------------------------------------------------------

def test_boundaries_snap_to_whole_words():
    t = speech(("hello", 1.0, 1.4), ("there", 1.5, 2.0), ("friend", 2.1, 2.6))
    start, end = snap_to_words((1.2, 2.3), t, BOOK)
    assert start == pytest.approx(1.0 - BOOK.lead_in)
    assert end == pytest.approx(2.6 + BOOK.lead_out)


def test_breath_is_left_at_both_ends():
    """Flush to the syllable clips the consonant attack and sounds truncated."""
    t = speech(("word", 5.0, 5.5))
    start, end = snap_to_words((5.0, 5.5), t, BOOK)
    assert start < 5.0 and end > 5.5


def test_lead_in_never_goes_negative():
    t = speech(("word", 0.02, 0.5))
    assert snap_to_words((0.0, 0.5), t, BOOK)[0] == 0.0


def test_silent_window_is_left_alone():
    assert snap_to_words((10.0, 20.0), speech(("a", 1.0, 1.4)), BOOK) == (10.0, 20.0)


# --------------------------------------------------------------------------
# internal cuts
# --------------------------------------------------------------------------

def test_filler_words_are_cut():
    t = speech(("we", 0.0, 0.3), ("um", 0.4, 0.8), ("shipped", 0.9, 1.4))
    cuts = internal_cuts(Clip(0.0, 1.5), t, BOOK, (0.0, 1.5))
    assert any(c[0] <= 0.4 and c[1] >= 0.8 for c in cuts)


def test_soft_filler_survives():
    """'like' and 'so' are as often real speech; only the brain may cut them."""
    t = speech(("I", 0.0, 0.3), ("like", 0.4, 0.8), ("this", 0.9, 1.4))
    assert internal_cuts(Clip(0.0, 1.5), t, BOOK, (0.0, 1.5)) == []


def test_long_pauses_are_tightened_not_erased():
    """A pause cut to zero machine-guns the delivery."""
    t = speech(("before", 0.0, 0.5), ("after", 3.0, 3.5))
    cuts = internal_cuts(Clip(0.0, 4.0), t, BOOK, (0.0, 4.0))
    removed = sum(e - s for s, e in cuts)
    assert (3.0 - 0.5) - removed == pytest.approx(BOOK.keep_pause, abs=0.01)


def test_short_pauses_are_left_alone():
    assert internal_cuts(Clip(0.0, 5.0), steady(6), BOOK, (0.0, 5.0)) == []


def test_brain_drops_are_honoured():
    clip = Clip(0.0, 10.0, drop=[Drop(4.0, 6.0, "repeat")])
    cuts = internal_cuts(clip, steady(30), BOOK, (0.0, 10.0))
    assert any(s <= 4.0 and e >= 6.0 for s, e in cuts)


# --------------------------------------------------------------------------
# segments
# --------------------------------------------------------------------------

def test_slivers_are_dropped_not_absorbed():
    """Folding a sliver into its neighbour would extend that segment across
    the cut that created the sliver, silently reinstating the filler or flubbed
    take the edit had just removed."""
    segments = to_segments([(0.0, 5.0), (5.1, 5.3), (6.0, 10.0)], BOOK)
    assert len(segments) == 2
    assert segments[0].src_out == pytest.approx(5.0)
    assert segments[1].src_in == pytest.approx(6.0)


def test_a_leading_sliver_is_dropped():
    assert to_segments([(0.0, 0.2), (1.0, 5.0)], BOOK) == [
        Segment("s1", 1.0, 5.0, why="kept")
    ]


def test_a_cut_word_cannot_reappear_via_sliver_handling():
    """Regression: a filler cut followed closely by a dead-air cut leaves a
    0.09s sliver between them, and absorbing it put the filler back."""
    t = speech(("word", 8.0, 8.4), ("uh", 10.0, 10.28), ("next", 14.0, 14.4))
    clip = Clip(8.0, 15.0)
    cuts = internal_cuts(clip, t, BOOK, (8.0, 15.0))
    segments = to_segments(subtract((8.0, 15.0), cuts), BOOK)
    assert not any(s.src_in <= 10.1 <= s.src_out for s in segments)


def test_segment_ids_are_sequential():
    segments = to_segments([(0.0, 3.0), (4.0, 7.0), (8.0, 11.0)], BOOK)
    assert [s.id for s in segments] == ["s1", "s2", "s3"]


# --------------------------------------------------------------------------
# length
# --------------------------------------------------------------------------

def test_trimming_takes_from_the_end_not_the_start():
    """The opening earns the view; the tail is what can be lost."""
    segments = [Segment("s1", 0, 30), Segment("s2", 40, 70)]
    trimmed = trim_to_length(segments, 45.0)
    assert trimmed[0].src_in == 0
    assert trimmed[-1].out_duration == pytest.approx(15.0)


def test_a_trim_that_would_leave_a_stub_drops_the_segment():
    segments = [Segment("s1", 0, 58), Segment("s2", 60, 70)]
    trimmed = trim_to_length(segments, 58.5)
    assert len(trimmed) == 1


def test_no_trim_needed_is_a_passthrough():
    segments = [Segment("s1", 0, 10)]
    assert trim_to_length(segments, 59.0) == segments


# --------------------------------------------------------------------------
# framing
# --------------------------------------------------------------------------

def test_the_hook_opens_on_a_push():
    edl = compose(Clip(0.0, 12.0), "/a.mp4", steady(30), Signals(duration=60),
                  TARGET, BOOK)
    assert edl.framing[0].mode == "punch"


def test_hook_punch_can_be_switched_off():
    book = Playbook(hook_punch=False)
    edl = compose(Clip(0.0, 12.0), "/a.mp4", steady(30), Signals(duration=60),
                  TARGET, book)
    assert edl.framing[0].mode == "static"


def test_punch_cadence_is_measured_in_output_time():
    """Two beats three seconds apart in the source can be adjacent once the
    gap between them has been cut out."""
    book = Playbook(hook_punch=False, min_punch_gap=5.0)
    clip = Clip(0.0, 12.0, emphasis=[2.0, 3.0, 4.0])
    edl = compose(clip, "/a.mp4", steady(30), Signals(duration=60), TARGET, book)
    assert sum(1 for f in edl.framing if f.mode == "punch") <= 1


def test_framing_follows_the_detected_subject():
    signals = Signals(duration=60, focus=[(0.0, 0.3, 0.4)])
    edl = compose(Clip(0.0, 12.0), "/a.mp4", steady(30), signals, TARGET, BOOK)
    assert edl.framing[0].focus == (0.3, 0.4)


def test_every_segment_gets_framing():
    clip = Clip(0.0, 12.0, drop=[Drop(4.0, 5.0, "repeat")])
    edl = compose(clip, "/a.mp4", steady(30), Signals(duration=60), TARGET, BOOK)
    assert {f.seg for f in edl.framing} == {s.id for s in edl.segments}


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------

def test_captions_are_in_output_time_not_source_time():
    """This is where a few frames of drift per cut would creep in."""
    clip = Clip(0.0, 12.0, drop=[Drop(2.0, 5.0, "tangent")])
    edl = compose(clip, "/a.mp4", steady(30), Signals(duration=60), TARGET, BOOK)
    assert edl.captions.words
    assert max(w.end for w in edl.captions.words) <= edl.duration + 0.05


def test_cut_words_do_not_appear_in_captions():
    t = speech(("keep", 0.0, 0.4), ("gone", 5.0, 5.4), ("keep2", 9.0, 9.4))
    clip = Clip(0.0, 10.0, drop=[Drop(4.8, 5.6, "tangent")])
    edl = compose(clip, "/a.mp4", t, Signals(duration=60), TARGET, BOOK)
    assert "gone" not in [w.text for w in edl.captions.words]


def test_filler_is_never_captioned():
    t = speech(("we", 0.0, 0.3), ("um", 0.4, 0.8), ("shipped", 0.9, 1.4))
    edl = compose(Clip(0.0, 2.0), "/a.mp4", t, Signals(duration=60), TARGET, BOOK)
    assert "um" not in [w.text for w in edl.captions.words]


def test_captions_can_be_disabled():
    book = Playbook(captions_enabled=False)
    edl = compose(Clip(0.0, 12.0), "/a.mp4", steady(30), Signals(duration=60),
                  TARGET, book)
    assert edl.captions.enabled is False


# --------------------------------------------------------------------------
# emoji
# --------------------------------------------------------------------------

def test_emoji_are_chosen_from_what_is_being_said():
    assert pick_emoji([Word("revenue", 0, 1)]) == "\U0001F4B0"
    assert pick_emoji([Word("shipped", 0, 1)]) == "\U0001F680"
    assert pick_emoji([Word("nondescript", 0, 1)]) == "\U0001F525"


def test_emoji_density_is_capped():
    """Past the ceiling they stop being punctuation and become wallpaper."""
    book = Playbook(emoji_per_minute=2.0, emoji_min_gap=0.1, hook_punch=False)
    clip = Clip(0.0, 30.0, emphasis=[float(i) for i in range(1, 25)])
    edl = compose(clip, "/a.mp4", steady(90), Signals(duration=60), TARGET, book)
    assert len(edl.overlays) <= 2


def test_emoji_respect_a_minimum_gap():
    book = Playbook(emoji_per_minute=60.0, emoji_min_gap=3.0, hook_punch=False)
    clip = Clip(0.0, 20.0, emphasis=[1.0, 1.2, 1.4, 10.0])
    edl = compose(clip, "/a.mp4", steady(60), Signals(duration=60), TARGET, book)
    times = [o.at for o in edl.overlays]
    assert all(b - a >= 3.0 for a, b in zip(times, times[1:]))


def test_a_short_reel_still_gets_one_emoji():
    """A per-minute ceiling silently means 'none' for anything under 10s."""
    clip = Clip(0.0, 8.0, emphasis=[3.0])
    edl = compose(clip, "/a.mp4", steady(20), Signals(duration=60), TARGET, BOOK)
    assert len(edl.overlays) == 1


def test_emoji_are_disabled_by_a_zero_ceiling():
    book = Playbook(emoji_per_minute=0.0)
    clip = Clip(0.0, 20.0, emphasis=[5.0])
    assert compose(clip, "/a.mp4", steady(60), Signals(duration=60), TARGET, book).overlays == []


def test_beats_that_were_cut_out_get_no_emoji():
    clip = Clip(0.0, 20.0, emphasis=[6.0], drop=[Drop(5.0, 8.0, "tangent")])
    edl = compose(clip, "/a.mp4", steady(60), Signals(duration=60), TARGET, BOOK)
    assert edl.overlays == []


def test_no_emoji_lands_on_the_final_frames():
    clip = Clip(0.0, 10.0, emphasis=[9.9])
    edl = compose(clip, "/a.mp4", steady(30), Signals(duration=60), TARGET, BOOK)
    assert all(o.at <= edl.duration - 0.6 for o in edl.overlays)


# --------------------------------------------------------------------------
# end to end
# --------------------------------------------------------------------------

def test_composed_edl_validates():
    from reelforge.core.edl import validate
    t = speech(("we", 0.0, 0.4), ("um", 0.5, 0.9), ("shipped", 1.0, 1.6),
               ("it", 1.7, 2.0), ("yesterday", 2.1, 2.9), ("finally", 12.0, 12.8))
    clip = Clip(0.0, 13.0, emphasis=[2.5], scores={"hook": 8})
    edl = compose(clip, "/a.mp4", t, Signals(duration=60), TARGET, BOOK)
    assert validate(edl, source_duration=60.0) == []


def test_a_clip_that_is_entirely_filler_yields_nothing_rather_than_crashing():
    t = speech(("um", 0.0, 0.4), ("uh", 0.5, 0.9))
    edl = compose(Clip(0.0, 1.0), "/a.mp4", t, Signals(duration=60), TARGET, BOOK)
    assert edl.segments == []
    assert edl.captions.words == []


def test_caption_cards_never_straddle_a_cut():
    """The last word before a cut and the first after it land adjacent in
    output time, so nothing else in the grouping rules notices the cut. On
    screen a card spanning it reads as a mistake and joins two sentences."""
    t = speech(("wrong", 1.0, 1.4), ("um", 1.6, 1.9), ("we", 2.2, 2.5),
               ("shipped", 2.6, 3.1))
    edl = compose(Clip(0.5, 4.0), "/a.mp4", t, Signals(duration=60), TARGET, BOOK)
    assert len(edl.segments) == 2
    breaks = [w.text for w in edl.captions.words if w.break_before]
    assert breaks == ["we"]


def test_the_first_word_never_forces_a_break():
    edl = compose(Clip(0.0, 12.0), "/a.mp4", steady(30), Signals(duration=60),
                  TARGET, BOOK)
    assert edl.captions.words[0].break_before is False


def test_lead_out_cannot_run_past_the_end_of_the_source():
    """Asking ffmpeg for frames past the end yields a frozen final frame
    rather than an error, so it is invisible until someone watches the tail."""
    t = Transcript([Word("last", 9.6, 9.95)], "en", 10.0, "test")
    assert snap_to_words((9.0, 10.0), t, BOOK)[1] <= 10.0
