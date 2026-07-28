"""Tests for the learning loop.

The most important behaviour in the project and the easiest to get subtly
wrong: a system that over-learns swings wildly on one offhand remark, and one
that under-learns looks like it is ignoring you.
"""

import json

import pytest

from reelforge.core import feedback as fb
from reelforge.core.playbook import Playbook, load


def note(aspect, direction, **kw) -> fb.Note:
    return fb.Note(aspect=aspect, direction=direction, **kw)


# --------------------------------------------------------------------------
# the vocabulary
# --------------------------------------------------------------------------

def test_every_adjustment_targets_a_real_playbook_field():
    """A typo here would silently learn nothing at all."""
    book = Playbook()
    for adjustment in fb.ADJUSTMENTS.values():
        assert hasattr(book, adjustment.field), adjustment.field


def test_every_aspect_has_opposing_directions():
    """A correction you can only make in one direction cannot be walked back."""
    for aspect in fb.ASPECTS:
        assert len(fb.directions_for(aspect)) >= 2, aspect


def test_opposing_adjustments_push_opposite_ways():
    for aspect in fb.ASPECTS:
        deltas = [fb.ADJUSTMENTS[(aspect, d)].delta
                  for d in fb.directions_for(aspect)]
        assert any(d > 0 for d in deltas) and any(d < 0 for d in deltas), aspect


def test_an_unknown_correction_is_rejected_with_the_vocabulary():
    with pytest.raises(fb.UnknownCorrection, match="captions/"):
        fb.validate_note("captions", "too-purple")


# --------------------------------------------------------------------------
# the promotion threshold
# --------------------------------------------------------------------------

def test_one_complaint_changes_nothing():
    """A single reaction to one clip is a mood, not taste."""
    book, promotions = fb.promote([note("captions", "too-low")], Playbook())
    assert promotions == []
    assert book.caption_position == Playbook().caption_position


def test_the_same_complaint_twice_becomes_a_rule():
    book, promotions = fb.promote(
        [note("captions", "too-low"), note("captions", "too-low")], Playbook())
    assert len(promotions) == 1
    assert book.caption_position < Playbook().caption_position


def test_two_different_complaints_do_not_combine_into_one():
    book, promotions = fb.promote(
        [note("captions", "too-low"), note("zooms", "too-many")], Playbook())
    assert promotions == []


def test_pending_shows_what_it_is_waiting_on():
    """Otherwise a single correction looks like it was ignored."""
    assert fb.pending([note("emoji", "too-many")]) == {"emoji:too-many": 1}


def test_pending_excludes_what_has_already_been_promoted():
    notes = [note("emoji", "too-many")] * 2
    assert fb.pending(notes) == {}


# --------------------------------------------------------------------------
# direction and magnitude
# --------------------------------------------------------------------------

def test_captions_too_low_raises_them():
    book, _ = fb.promote([note("captions", "too-low")] * 2, Playbook())
    assert book.caption_position < 0.72


def test_captions_too_high_lowers_them():
    book, _ = fb.promote([note("captions", "too-high")] * 2, Playbook())
    assert book.caption_position > 0.72


def test_too_many_zooms_widens_the_gap():
    book, _ = fb.promote([note("zooms", "too-many")] * 2, Playbook())
    assert book.min_punch_gap > Playbook().min_punch_gap


def test_repeating_a_complaint_compounds_it():
    """Saying it four times should move further than saying it twice."""
    twice, _ = fb.promote([note("emoji", "too-many")] * 2, Playbook())
    four, _ = fb.promote([note("emoji", "too-many")] * 4, Playbook())
    assert four.emoji_per_minute < twice.emoji_per_minute


def test_adjustments_are_clamped_to_sane_limits():
    """Twenty complaints must not drive a value to something absurd."""
    book, _ = fb.promote([note("emoji", "too-many")] * 30, Playbook())
    assert book.emoji_per_minute >= 0.0
    book, _ = fb.promote([note("zooms", "too-strong")] * 30, Playbook())
    assert book.punch_zoom >= 1.0


def test_a_value_already_at_its_limit_reports_no_change():
    book = Playbook(emoji_per_minute=0.0)
    _, promotions = fb.promote([note("emoji", "too-many")] * 2, book)
    assert promotions == []


def test_integer_fields_stay_integers():
    """A float in an int field produces a playbook that no longer round-trips."""
    book = Playbook()
    book.fade_ms = 20
    assert isinstance(book.fade_ms, int)


# --------------------------------------------------------------------------
# not counting the same note twice
# --------------------------------------------------------------------------

def test_already_applied_notes_are_not_reapplied():
    """Without this, every run would compound every past correction and the
    playbook would drift to its limits."""
    notes = [note("emoji", "too-many")] * 2
    book, promotions = fb.promote(notes, Playbook(),
                                  already={"emoji:too-many": 2})
    assert promotions == []
    assert book.emoji_per_minute == Playbook().emoji_per_minute


def test_only_the_new_occurrences_are_applied():
    notes = [note("emoji", "too-many")] * 4
    once, _ = fb.promote([note("emoji", "too-many")] * 2, Playbook())
    incremental, _ = fb.promote(notes, Playbook(), already={"emoji:too-many": 2})
    assert incremental.emoji_per_minute == pytest.approx(once.emoji_per_minute)


# --------------------------------------------------------------------------
# the log
# --------------------------------------------------------------------------

def test_notes_round_trip_through_the_log(tmp_path):
    log = tmp_path / "decisions.jsonl"
    fb.append(log, note("captions", "too-low", quote="sat too low", edl="a.json"))
    loaded = fb.load(log)
    assert len(loaded) == 1
    assert loaded[0].quote == "sat too low"


def test_a_corrupt_line_does_not_lose_the_history(tmp_path):
    """Append-only and hand-editable, so a bad line is realistic -- and must
    not cost everything you have taught it."""
    log = tmp_path / "decisions.jsonl"
    fb.append(log, note("captions", "too-low"))
    with log.open("a") as fh:
        fh.write("{ this is not json\n")
    fb.append(log, note("emoji", "too-many"))
    assert len(fb.load(log)) == 2


def test_notes_with_a_retired_vocabulary_are_skipped(tmp_path):
    log = tmp_path / "decisions.jsonl"
    log.write_text(json.dumps({"aspect": "colour", "direction": "too-warm"}) + "\n")
    assert fb.load(log) == []


def test_an_invalid_note_cannot_be_appended(tmp_path):
    with pytest.raises(fb.UnknownCorrection):
        fb.append(tmp_path / "d.jsonl", note("captions", "nonsense"))


def test_loading_a_missing_log_is_empty(tmp_path):
    assert fb.load(tmp_path / "nope.jsonl") == []


# --------------------------------------------------------------------------
# end to end
# --------------------------------------------------------------------------

def test_the_full_loop_changes_the_playbook_on_disk(tmp_path):
    """The premise of the whole project: say it twice, and the next render
    is different."""
    memory = tmp_path / "memory"
    log = memory / "decisions.jsonl"
    fb.append(log, note("captions", "too-low", quote="captions sat too low"))
    fb.append(log, note("captions", "too-low", quote="still too low"))

    book, promotions = fb.apply_feedback(memory, Playbook(), when="2026-08-02")
    assert promotions

    reloaded = load(memory / "playbook.md")
    assert reloaded.caption_position == book.caption_position
    assert reloaded.caption_position < Playbook().caption_position


def test_provenance_is_written_into_the_playbook(tmp_path):
    memory = tmp_path / "memory"
    log = memory / "decisions.jsonl"
    for _ in range(2):
        fb.append(log, note("zooms", "too-many", quote="too many zooms"))
    fb.apply_feedback(memory, Playbook(), when="2026-08-02")

    text = (memory / "playbook.md").read_text()
    assert "min_punch_gap" in text
    assert "2026-08-02" in text
    assert "too many zooms" in text


def test_provenance_survives_later_rounds(tmp_path):
    """Rendering with only this round's notes would erase the reason behind
    every rule learned before it."""
    memory = tmp_path / "memory"
    log = memory / "decisions.jsonl"
    for _ in range(2):
        fb.append(log, note("zooms", "too-many", quote="too many zooms"))
    book, _ = fb.apply_feedback(memory, Playbook(), when="2026-08-02")

    for _ in range(2):
        fb.append(log, note("emoji", "too-many", quote="emoji everywhere"))
    fb.apply_feedback(memory, book, when="2026-09-01")

    text = (memory / "playbook.md").read_text()
    assert "too many zooms" in text          # the older rule kept its reason
    assert "emoji everywhere" in text


def test_running_twice_with_no_new_feedback_changes_nothing(tmp_path):
    memory = tmp_path / "memory"
    log = memory / "decisions.jsonl"
    for _ in range(2):
        fb.append(log, note("emoji", "too-many"))

    book, first = fb.apply_feedback(memory, Playbook(), when="2026-08-02")
    after_first = book.emoji_per_minute
    book, second = fb.apply_feedback(memory, book, when="2026-08-03")

    assert first and second == []
    assert book.emoji_per_minute == after_first


def test_the_loop_converges_rather_than_oscillating(tmp_path):
    """Contradicting yourself should settle near where you started, not swing."""
    memory = tmp_path / "memory"
    log = memory / "decisions.jsonl"
    for _ in range(2):
        fb.append(log, note("captions", "too-low"))
    book, _ = fb.apply_feedback(memory, Playbook(), when="2026-08-02")
    for _ in range(2):
        fb.append(log, note("captions", "too-high"))
    book, _ = fb.apply_feedback(memory, book, when="2026-08-03")

    assert book.caption_position == pytest.approx(Playbook().caption_position)
