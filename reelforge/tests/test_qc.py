"""Tests for quality control and repair.

The measurement functions need ffmpeg; the judgment functions do not, and the
judgment is where the editorial thresholds live. Only the judgments are tested
here -- that split is deliberate.
"""

import pytest

from reelforge.core import qc
from reelforge.core.edl import (
    EDL, Captions, CaptionWord, Framing, Overlay, Segment, Target,
)
from reelforge.core.playbook import Playbook
from reelforge.core.render.ass import STYLES
from reelforge.core.transcribe import Transcript, Word

TARGET = Target(aspect="9:16", width=1080, fps=30, max_dur=59.0)
BOOK = Playbook()


def edl(*segments, **kw) -> EDL:
    return EDL(source="/a.mp4", target=kw.pop("target", TARGET),
               segments=list(segments) or [Segment("s1", 0.0, 10.0)], **kw)


def speech(*specs) -> Transcript:
    return Transcript([Word(t, s, e) for t, s, e in specs], "en", 120.0, "test")


# --------------------------------------------------------------------------
# mid-word cuts
# --------------------------------------------------------------------------

def test_a_cut_inside_a_word_fails():
    """The most audible failure in machine editing."""
    t = speech(("hello", 1.0, 1.8))
    findings = qc.check_midword_cuts(edl(Segment("s1", 1.4, 5.0)), t)
    assert findings and findings[0].severity == "fail"
    assert "hello" in findings[0].detail


def test_a_cut_at_a_word_boundary_is_fine():
    t = speech(("hello", 1.0, 1.8), ("there", 2.0, 2.6))
    assert qc.check_midword_cuts(edl(Segment("s1", 1.8, 2.6)), t) == []


def test_boundary_tolerance_avoids_flagging_noise():
    """Whisper's boundaries are good to a few tens of ms, not exact."""
    t = speech(("hello", 1.0, 1.8))
    assert qc.check_midword_cuts(edl(Segment("s1", 1.03, 5.0)), t) == []


def test_repair_snaps_an_in_point_to_the_word_start():
    """An in-point must not clip the attack of the consonant."""
    t = speech(("hello", 1.0, 1.8))
    e = edl(Segment("s1", 1.4, 5.0))
    repaired, changes = qc.repair(e, qc.check_midword_cuts(e, t), t, BOOK)
    assert repaired.segments[0].src_in == pytest.approx(1.0)
    assert changes


def test_repair_snaps_an_out_point_to_the_word_end():
    """An out-point must let the word finish."""
    t = speech(("hello", 1.0, 1.8))
    e = edl(Segment("s1", 0.0, 1.4))
    repaired, _ = qc.repair(e, qc.check_midword_cuts(e, t), t, BOOK)
    assert repaired.segments[0].src_out == pytest.approx(1.8)


def test_repair_is_idempotent():
    """A second pass must not keep nudging boundaries around."""
    t = speech(("hello", 1.0, 1.8))
    e = edl(Segment("s1", 1.4, 5.0))
    once, _ = qc.repair(e, qc.check_midword_cuts(e, t), t, BOOK)
    assert qc.check_midword_cuts(once, t) == []


# --------------------------------------------------------------------------
# caption safe area
# --------------------------------------------------------------------------

def test_captions_below_the_safe_line_fail():
    """Text there is not small, it is invisible behind the share tray."""
    from dataclasses import replace
    STYLES["test-low"] = replace(STYLES["karaoke-bold"], name="test-low",
                                 position=0.95)
    e = edl(captions=Captions(style="test-low",
                              words=[CaptionWord("a", 0.0, 0.4)]))
    findings = qc.check_caption_safe_area(e)
    assert findings and findings[0].severity == "fail"


def test_repair_moves_captions_into_the_safe_area():
    from dataclasses import replace
    STYLES["test-low2"] = replace(STYLES["karaoke-bold"], name="test-low2",
                                  position=0.95)
    e = edl(captions=Captions(style="test-low2",
                              words=[CaptionWord("a", 0.0, 0.4)]))
    repaired, changes = qc.repair(e, qc.check_caption_safe_area(e), None, BOOK)
    assert qc.check_caption_safe_area(repaired) == []
    assert changes


def test_repair_does_not_mutate_the_shared_style():
    """Fixing one reel must not silently move captions in every other render."""
    from dataclasses import replace
    STYLES["test-low3"] = replace(STYLES["karaoke-bold"], name="test-low3",
                                  position=0.95)
    e = edl(captions=Captions(style="test-low3",
                              words=[CaptionWord("a", 0.0, 0.4)]))
    qc.repair(e, qc.check_caption_safe_area(e), None, BOOK)
    assert STYLES["test-low3"].position == 0.95


def test_the_default_style_is_already_safe():
    e = edl(captions=Captions(words=[CaptionWord("a", 0.0, 0.4)]))
    assert qc.check_caption_safe_area(e) == []


def test_disabled_captions_are_not_checked():
    e = edl(captions=Captions(enabled=False))
    assert qc.check_caption_safe_area(e) == []


# --------------------------------------------------------------------------
# shot rhythm
# --------------------------------------------------------------------------

def test_a_flash_shot_fails():
    findings = qc.check_shot_rhythm(edl(Segment("s1", 0, 10),
                                        Segment("s2", 20, 20.2)), BOOK)
    assert any(f.check == "flash-shot" and f.severity == "fail" for f in findings)


def test_crowded_push_ins_are_flagged():
    """Two push-ins close together read as a nervous camera operator."""
    e = edl(Segment("s1", 0, 1.0), Segment("s2", 5, 6.0),
            framing=[Framing(seg="s1", mode="punch", zoom_to=1.1),
                     Framing(seg="s2", mode="punch", zoom_to=1.1)])
    findings = qc.check_shot_rhythm(e, BOOK)
    assert any(f.check == "punch-cadence" for f in findings)


def test_repair_relaxes_the_crowded_push_not_the_first():
    e = edl(Segment("s1", 0, 1.0), Segment("s2", 5, 6.0),
            framing=[Framing(seg="s1", mode="punch", zoom_to=1.1),
                     Framing(seg="s2", mode="punch", zoom_to=1.1)])
    repaired, changes = qc.repair(e, qc.check_shot_rhythm(e, BOOK), None, BOOK)
    assert repaired.framing_for("s1").mode == "punch"
    assert repaired.framing_for("s2").mode == "static"
    assert changes


def test_well_spaced_pushes_pass():
    e = edl(Segment("s1", 0, 10), Segment("s2", 20, 30),
            framing=[Framing(seg="s1", mode="punch", zoom_to=1.1),
                     Framing(seg="s2", mode="punch", zoom_to=1.1)])
    assert [f for f in qc.check_shot_rhythm(e, BOOK)
            if f.check == "punch-cadence"] == []


# --------------------------------------------------------------------------
# length
# --------------------------------------------------------------------------

def test_over_length_fails_and_is_trimmed():
    e = edl(Segment("s1", 0, 90))
    findings = qc.check_length(e, BOOK)
    assert findings[0].severity == "fail"
    repaired, changes = qc.repair(e, findings, None, BOOK)
    assert repaired.duration <= 59.0
    assert changes


def test_under_length_warns_without_blocking():
    e = edl(Segment("s1", 0, 8))
    findings = qc.check_length(e, BOOK)
    assert findings and all(f.severity == "warn" for f in findings)


def test_long_form_has_no_length_limit():
    e = edl(Segment("s1", 0, 1800),
            target=Target(platform="youtube", aspect="16:9", width=1920,
                          max_dur=None))
    assert qc.check_length(e, BOOK) == []


# --------------------------------------------------------------------------
# audio pops -- judgment only; measurement needs ffmpeg
# --------------------------------------------------------------------------

def test_a_large_sample_discontinuity_fails():
    findings = qc.judge_pop(0.6, at=4.0)
    assert findings and findings[0].severity == "fail"


def test_a_small_discontinuity_passes():
    assert qc.judge_pop(0.05, at=4.0) == []


def test_unmeasurable_audio_is_not_a_finding():
    """No numpy, or a source with no audio, must not fabricate a failure."""
    assert qc.judge_pop(None, at=4.0) == []


def test_repair_lengthens_the_fades():
    e = edl()
    before = e.audio.fade_ms
    repaired, changes = qc.repair(e, qc.judge_pop(0.6, at=4.0), None, BOOK)
    assert repaired.audio.fade_ms > before
    assert changes


def test_fade_repair_is_bounded():
    """Past about 60ms a fade stops reading as a cut."""
    e = edl()
    for _ in range(6):
        e, _ = qc.repair(e, qc.judge_pop(0.6, at=4.0), None, BOOK)
    assert e.audio.fade_ms <= 60


# --------------------------------------------------------------------------
# jump cuts
# --------------------------------------------------------------------------

def test_a_slightly_displaced_same_shot_is_flagged():
    """The ugly middle case: cutting filler from a locked-off camera leaves the
    subject displaced, and the eye reads it as a dropped frame."""
    assert qc.judge_jump_cut(0.04, at=3.0)


def test_a_genuine_shot_change_is_not_flagged():
    """A large difference is a clean cut and looks intentional."""
    assert qc.judge_jump_cut(0.30, at=3.0) == []


def test_effectively_identical_frames_are_not_flagged():
    """Below the floor the join is invisible, so there is nothing to fix."""
    assert qc.judge_jump_cut(0.002, at=3.0) == []


def test_the_band_excludes_both_extremes():
    """Judging by similarity alone fails every clean cut in a video shot in
    one room, and passes the ugly case whenever lighting shifts."""
    assert qc.judge_jump_cut(0.0, at=1.0) == []
    assert qc.judge_jump_cut(1.0, at=1.0) == []
    assert qc.judge_jump_cut(0.05, at=1.0) != []


def test_repair_covers_a_jump_with_a_dissolve():
    e = edl(Segment("s1", 0, 5), Segment("s2", 10, 15))
    repaired, changes = qc.repair(e, qc.judge_jump_cut(0.04, at=5.0), None, BOOK)
    assert repaired.transitions and repaired.transitions[0].type == "dissolve"
    assert changes


def test_the_same_jump_is_not_covered_twice():
    e = edl(Segment("s1", 0, 5), Segment("s2", 10, 15))
    e, _ = qc.repair(e, qc.judge_jump_cut(0.04, at=5.0), None, BOOK)
    e, _ = qc.repair(e, qc.judge_jump_cut(0.04, at=5.0), None, BOOK)
    assert len(e.transitions) == 1


# --------------------------------------------------------------------------
# loudness
# --------------------------------------------------------------------------

def test_loudness_drift_warns_rather_than_failing():
    """Platforms re-normalise anyway; this is a quality note, not a blocker."""
    findings = qc.judge_loudness(-9.0, target=-16.0)
    assert findings and findings[0].severity == "warn"


def test_loudness_within_tolerance_passes():
    assert qc.judge_loudness(-16.4, target=-16.0) == []


def test_unmeasurable_loudness_is_not_a_finding():
    assert qc.judge_loudness(None, target=-16.0) == []


# --------------------------------------------------------------------------
# cut times and orphans
# --------------------------------------------------------------------------

def test_cut_times_are_internal_boundaries_only():
    """The end of the last segment is the end of the video, not a cut."""
    e = edl(Segment("s1", 0, 5), Segment("s2", 10, 13), Segment("s3", 20, 22))
    assert qc.cut_times(e) == [5.0, 8.0]


def test_a_single_segment_has_no_cuts():
    assert qc.cut_times(edl()) == []


def test_an_orphaned_final_word_is_flagged():
    words = [CaptionWord("real", 0.0, 0.5), CaptionWord("oh", 3.0, 3.2)]
    words[1].break_before = True
    assert qc.check_orphan_ending(edl(captions=Captions(words=words)))


def test_a_proper_final_phrase_is_not_flagged():
    words = [CaptionWord("the", 0.0, 0.3), CaptionWord("end", 0.35, 0.9)]
    assert qc.check_orphan_ending(edl(captions=Captions(words=words))) == []


# --------------------------------------------------------------------------
# the whole static pass
# --------------------------------------------------------------------------

def test_static_checks_run_without_a_transcript():
    """Rendering an EDL by hand should still get most of the checks."""
    assert isinstance(qc.static_checks(edl(), None, BOOK), list)


def test_a_clean_edl_produces_no_findings():
    t = speech(("hello", 0.0, 0.8), ("there", 1.0, 1.9))
    e = edl(Segment("s1", 0.0, 20.0),
            captions=Captions(words=[CaptionWord("hello", 0.0, 0.8),
                                     CaptionWord("there", 1.0, 1.9)]))
    assert qc.static_checks(e, t, BOOK) == []


def test_repair_reports_every_change_it_made():
    """The changelog is what the user reads to know what QC did to their edit."""
    t = speech(("hello", 1.0, 1.8))
    e = edl(Segment("s1", 1.4, 95.0))
    _, changes = qc.repair(e, qc.static_checks(e, t, BOOK), t, BOOK)
    assert len(changes) >= 2


def test_a_join_already_carrying_a_dissolve_is_not_reflagged():
    """The dip mitigates the join without changing the frames either side, so
    re-measuring would raise the same finding forever and make the repair look
    ineffective."""
    from reelforge.core.edl import Transition
    e = edl(Segment("s1", 0, 5), Segment("s2", 10, 15),
            transitions=[Transition(at=5.0, type="dissolve", dur=0.16)])
    covered = {round(t.at, 2) for t in e.transitions
               if t.type != "cut" and t.dur > 0}
    assert 5.0 in covered
