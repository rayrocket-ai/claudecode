"""Tests for transcript-derived editorial signals.

No model is loaded -- these are pure functions over word lists, which is where
the editorial logic lives and therefore where it can go wrong.
"""

import pytest

from reelforge.core.transcribe import (
    Transcript, Word, dead_air, filler_spans, repeated_takes,
)


def build(*pairs, start=0.0, gap=0.05, dur=0.3) -> Transcript:
    """Build a transcript from bare words at a regular cadence."""
    words, t = [], start
    for item in pairs:
        if isinstance(item, tuple):
            text, t = item
            words.append(Word(text, t, t + dur))
        else:
            words.append(Word(item, t, t + dur))
        t = words[-1].end + gap
    return Transcript(words=words, language="en", duration=t, model="test")


# --------------------------------------------------------------------------
# filler
# --------------------------------------------------------------------------

def test_hard_fillers_are_cut():
    t = build("so", "um", "we", "uh", "shipped")
    assert len(filler_spans(t)) == 2


def test_soft_fillers_are_left_to_the_brain():
    """'like' and 'so' are real speech as often as they are filler."""
    t = build("I", "like", "this", "so", "much")
    assert filler_spans(t) == []


def test_filler_spans_are_padded_outward():
    """Whisper clips leading consonants; a tight cut leaves an audible stub."""
    t = build("um")
    (start, end), = filler_spans(t, pad=0.02)
    assert start == pytest.approx(0.0)          # clamped, never negative
    assert end == pytest.approx(0.32)


def test_punctuation_and_case_do_not_hide_filler():
    t = Transcript([Word("Um,", 0.0, 0.3), Word("UH!", 0.4, 0.7)], "en", 1.0, "test")
    assert len(filler_spans(t)) == 2


# --------------------------------------------------------------------------
# dead air
# --------------------------------------------------------------------------

def test_dead_air_found_between_distant_words():
    t = Transcript([Word("a", 0.0, 0.5), Word("b", 3.0, 3.5)], "en", 4.0, "test")
    (start, end), = dead_air(t, min_gap=0.6, keep=0.25)
    assert start == pytest.approx(0.625)
    assert end == pytest.approx(2.875)


def test_dead_air_leaves_a_beat_for_breath():
    """A pause cut to zero sounds machine-gunned; keep must survive the cut."""
    t = Transcript([Word("a", 0.0, 1.0), Word("b", 3.0, 3.5)], "en", 4.0, "test")
    (start, end), = dead_air(t, min_gap=0.6, keep=0.4)
    remaining = (3.0 - 1.0) - (end - start)
    assert remaining == pytest.approx(0.4)


def test_short_pauses_are_kept():
    t = build("normal", "conversational", "pace")
    assert dead_air(t, min_gap=0.6) == []


def test_dead_air_on_empty_transcript():
    assert dead_air(Transcript([], "en", 0.0, "test")) == []


# --------------------------------------------------------------------------
# repeated takes -- "cut the repeats"
# --------------------------------------------------------------------------

def test_restarted_sentence_drops_the_first_attempt():
    t = build("the", "point", "is", "that", "the", "point", "is", "that", "we", "won")
    spans = repeated_takes(t, min_words=4, similarity=0.8)
    assert len(spans) == 1
    # The *earlier* attempt is the one cut -- the retake is the better read.
    assert spans[0][0] == pytest.approx(t.words[0].start)
    assert spans[0][1] == pytest.approx(t.words[3].end)


def test_distinct_speech_is_not_flagged():
    t = build("we", "shipped", "the", "thing", "and", "it", "worked", "well", "today", "here")
    assert repeated_takes(t, min_words=4) == []


def test_short_echo_below_threshold_is_ignored():
    """Two repeated words is emphasis, not a flubbed take."""
    t = build("no", "no", "we", "are", "not", "doing", "that", "again", "ok", "fine")
    assert repeated_takes(t, min_words=4) == []


def test_repeats_needs_no_special_case_for_short_input():
    assert repeated_takes(build("a", "b")) == []


# --------------------------------------------------------------------------
# the brain's input format
# --------------------------------------------------------------------------

def test_timestamped_lines_are_compact():
    """Word-level JSON is ~40x this. The brain gets the compact form."""
    t = build("one", "two", "three", "four")
    out = t.as_timestamped_lines(window=8.0)
    assert out == "[00:00] one two three four"


def test_timestamped_lines_break_on_window():
    t = Transcript(
        [Word("a", 0.0, 0.2), Word("b", 9.0, 9.2), Word("c", 9.4, 9.6)],
        "en", 10.0, "test",
    )
    assert t.as_timestamped_lines(window=8.0).splitlines() == ["[00:00] a", "[00:09] b c"]


def test_timestamps_include_hours_only_when_needed():
    t = Transcript([Word("x", 3700.0, 3700.5)], "en", 3701.0, "test")
    assert t.as_timestamped_lines().startswith("[1:01:40]")


def test_transcript_survives_a_json_roundtrip():
    t = build("hello", "world")
    assert Transcript.from_dict(t.as_dict()).words[1].text == "world"
