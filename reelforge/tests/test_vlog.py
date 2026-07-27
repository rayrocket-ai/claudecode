"""Tests for long-form composition and its metadata."""

import pytest

from reelforge.core.analyze import Signals
from reelforge.core.edl import Chapter, Target, validate
from reelforge.core.metadata import chapter_text, description, srt
from reelforge.core.playbook import Playbook
from reelforge.core.transcribe import Transcript, Word
from reelforge.core.vlog import Episode, compose_episode

TARGET = Target(platform="youtube", aspect="16:9", width=1920, fps=30,
                max_dur=None, loudness=-14.0)
BOOK = Playbook()


def talk(minutes=3.0) -> Transcript:
    """Continuous speech at a natural cadence."""
    words, t = [], 0.0
    i = 0
    while t < minutes * 60:
        words.append(Word(f"word{i}", round(t, 3), round(t + 0.32, 3)))
        t += 0.40
        i += 1
    return Transcript(words, "en", t, "test")


def episode(**kw) -> Episode:
    payload = {"body": {"start": 0.0, "end": 180.0}}
    payload.update(kw)
    return Episode(payload)


# --------------------------------------------------------------------------
# the shape of a long-form edit
# --------------------------------------------------------------------------

def test_the_whole_body_is_kept():
    """A vlog tightens; it does not extract. The viewer chose this video."""
    edl = compose_episode(episode(), "/a.mp4", talk(), Signals(duration=180),
                          TARGET, BOOK)
    assert edl.duration > 170


def test_no_length_cap_is_applied():
    assert TARGET.max_dur is None
    edl = compose_episode(episode(), "/a.mp4", talk(), Signals(duration=180),
                          TARGET, BOOK)
    assert validate(edl, source_duration=180.0) == []


def test_long_form_does_not_punch_in():
    """The move that makes a reel feel alive makes an episode feel restless."""
    edl = compose_episode(episode(), "/a.mp4", talk(), Signals(duration=180),
                          TARGET, BOOK)
    assert all(f.mode == "static" for f in edl.framing)


def test_captions_are_kept_but_not_burned():
    """YouTube has its own caption UI, and burned pixels cannot be translated."""
    edl = compose_episode(episode(), "/a.mp4", talk(), Signals(duration=180),
                          TARGET, BOOK)
    assert edl.captions.enabled is False
    assert edl.captions.words


# --------------------------------------------------------------------------
# cold open
# --------------------------------------------------------------------------

def test_cold_open_is_lifted_to_the_front():
    edl = compose_episode(
        episode(cold_open={"start": 100.0, "end": 108.0}),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.segments[0].id == "cold"
    assert edl.segments[0].src_in >= 99.0
    assert edl.segments[1].src_in < 5.0


def test_cold_open_is_capped():
    edl = compose_episode(
        episode(cold_open={"start": 100.0, "end": 160.0}),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.segments[0].out_duration <= 12.0


def test_a_too_short_cold_open_is_skipped():
    edl = compose_episode(
        episode(cold_open={"start": 100.0, "end": 101.0}),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.segments[0].id != "cold"


def test_cold_open_gets_a_dissolve_not_a_hard_cut():
    """A hard cut from a cold open into the intro reads as an error."""
    edl = compose_episode(
        episode(cold_open={"start": 100.0, "end": 108.0}),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.transitions and edl.transitions[0].type == "dissolve"


# --------------------------------------------------------------------------
# chapters -- YouTube's rules are unforgiving and silent
# --------------------------------------------------------------------------

def test_chapters_are_mapped_into_output_time():
    edl = compose_episode(
        episode(drop=[{"start": 20.0, "end": 50.0, "reason": "tangent"}],
                chapters=[{"at": 0.0, "title": "Intro"},
                          {"at": 60.0, "title": "Middle"},
                          {"at": 120.0, "title": "End"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    middle = next(c for c in edl.chapters if c.title == "Middle")
    assert middle.at < 60.0          # the 30s tangent came out before it


def test_first_chapter_is_forced_to_zero():
    """YouTube renders no chapters at all unless one starts at 0:00."""
    edl = compose_episode(
        episode(chapters=[{"at": 12.0, "title": "Intro"},
                          {"at": 60.0, "title": "Middle"},
                          {"at": 120.0, "title": "End"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.chapters[0].at == 0.0


def test_chapters_that_collapse_together_are_merged():
    """Two marks either side of a removed tangent become one chapter."""
    edl = compose_episode(
        episode(drop=[{"start": 60.0, "end": 115.0, "reason": "tangent"}],
                chapters=[{"at": 0.0, "title": "Intro"},
                          {"at": 58.0, "title": "Before"},
                          {"at": 118.0, "title": "After"},
                          {"at": 160.0, "title": "End"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert all(b.at - a.at >= 10.0 for a, b in zip(edl.chapters, edl.chapters[1:]))


def test_a_chapter_inside_a_cut_snaps_forward_rather_than_vanishing():
    """Dropping it would push the count below three and hide them all."""
    edl = compose_episode(
        episode(drop=[{"start": 55.0, "end": 70.0, "reason": "tangent"}],
                chapters=[{"at": 0.0, "title": "Intro"},
                          {"at": 60.0, "title": "Inside the cut"},
                          {"at": 120.0, "title": "End"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert any(c.title == "Inside the cut" for c in edl.chapters)


def test_untitled_chapters_are_discarded_at_parse_time():
    ep = episode(chapters=[{"at": 0.0, "title": "  "}, {"at": 30.0, "title": "Real"}])
    assert [t for _, t in ep.chapters] == ["Real"]


def test_composed_chapters_pass_validation():
    edl = compose_episode(
        episode(chapters=[{"at": 0.0, "title": "Intro"},
                          {"at": 60.0, "title": "Middle"},
                          {"at": 120.0, "title": "End"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert validate(edl, source_duration=180.0) == []


def test_validation_catches_youtube_chapter_rules():
    from reelforge.core.edl import EDL, Segment
    edl = EDL(source="/a.mp4", segments=[Segment("s1", 0, 120)],
              chapters=[Chapter(5.0, "Late start"), Chapter(60.0, "Two only")])
    problems = validate(edl)
    assert any("0:00" in p for p in problems)
    assert any("at least 3" in p for p in problems)


# --------------------------------------------------------------------------
# b-roll
# --------------------------------------------------------------------------

def test_broll_slots_are_marked_in_output_time():
    edl = compose_episode(
        episode(drop=[{"start": 10.0, "end": 40.0, "reason": "tangent"}],
                broll=[{"start": 60.0, "dur": 4.0, "prompt": "city timelapse"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.broll[0].start < 60.0
    assert edl.broll[0].prompt == "city timelapse"


def test_broll_in_a_removed_span_is_dropped():
    edl = compose_episode(
        episode(drop=[{"start": 50.0, "end": 80.0, "reason": "tangent"}],
                broll=[{"start": 60.0, "dur": 4.0, "prompt": "gone"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.broll == []


def test_broll_cannot_run_past_the_end():
    edl = compose_episode(
        episode(broll=[{"start": 178.0, "dur": 30.0, "prompt": "outro"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert validate(edl, source_duration=180.0) == []


# --------------------------------------------------------------------------
# metadata
# --------------------------------------------------------------------------

def test_srt_uses_commas_for_milliseconds():
    edl = compose_episode(episode(), "/a.mp4", talk(0.5), Signals(duration=30),
                          TARGET, BOOK)
    out = srt(edl)
    assert "-->" in out
    assert "," in out.splitlines()[1]
    assert "." not in out.splitlines()[1]


def test_srt_is_empty_without_captions():
    from reelforge.core.edl import EDL, Segment
    assert srt(EDL(source="/a.mp4", segments=[Segment("s1", 0, 10)])) == ""


def test_chapter_text_is_empty_when_youtube_would_reject_it():
    """Publishing a broken list is worse than publishing none -- YouTube shows
    nothing and says nothing."""
    from reelforge.core.edl import EDL, Segment
    edl = EDL(source="/a.mp4", segments=[Segment("s1", 0, 120)],
              chapters=[Chapter(0.0, "One"), Chapter(60.0, "Two")])
    assert chapter_text(edl) == ""


def test_chapter_text_formats_valid_chapters():
    from reelforge.core.edl import EDL, Segment
    edl = EDL(source="/a.mp4", segments=[Segment("s1", 0, 300)],
              chapters=[Chapter(0.0, "Intro"), Chapter(65.0, "Middle"),
                        Chapter(200.0, "End")])
    assert chapter_text(edl).splitlines() == ["0:00 Intro", "1:05 Middle", "3:20 End"]


def test_description_assembles_summary_chapters_and_tags():
    from reelforge.core.edl import EDL, Segment
    edl = EDL(source="/a.mp4", segments=[Segment("s1", 0, 300)],
              chapters=[Chapter(0.0, "Intro"), Chapter(65.0, "Middle"),
                        Chapter(200.0, "End")])
    out = description(edl, summary="How we shipped it.", tags=["startup", "#build"])
    assert out.startswith("How we shipped it.")
    assert "0:00 Intro" in out
    assert "#startup #build" in out


def test_chapters_are_all_or_nothing():
    """Survivors of a collapse are not a shorter list -- they are a list
    YouTube refuses to render while reporting nothing."""
    edl = compose_episode(
        episode(drop=[{"start": 20.0, "end": 170.0, "reason": "tangent"}],
                chapters=[{"at": 0.0, "title": "One"},
                          {"at": 60.0, "title": "Two"},
                          {"at": 120.0, "title": "Three"}]),
        "/a.mp4", talk(), Signals(duration=180), TARGET, BOOK)
    assert edl.chapters == []
    assert validate(edl, source_duration=180.0) == []


def test_a_short_edit_gets_no_chapters_rather_than_broken_ones():
    edl = compose_episode(
        Episode({"body": {"start": 0.0, "end": 25.0},
                 "chapters": [{"at": 0.0, "title": "A"},
                              {"at": 8.0, "title": "B"},
                              {"at": 16.0, "title": "C"}]}),
        "/a.mp4", talk(0.5), Signals(duration=30), TARGET, BOOK)
    assert edl.chapters == []
