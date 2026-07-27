"""Tests for the EDL contract and its validation."""

import pytest

from reelforge.core.edl import (
    EDL, Captions, CaptionWord, Framing, Overlay, Segment, Target, validate,
)


def edl(*segs, **kw) -> EDL:
    return EDL(source="/tmp/a.mp4",
               segments=list(segs) or [Segment("s1", 0.0, 5.0)], **kw)


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

@pytest.mark.parametrize("aspect,width,height", [
    ("9:16", 1080, 1920),
    ("16:9", 1920, 1080),
    ("1:1", 1080, 1080),
    ("4:5", 1080, 1350),
])
def test_target_height_from_aspect(aspect, width, height):
    assert Target(aspect=aspect, width=width).height == height


def test_height_is_always_even():
    """h264 rejects odd dimensions with an error that names nothing useful."""
    for width in range(1000, 1010):
        assert Target(aspect="9:16", width=width).height % 2 == 0


# --------------------------------------------------------------------------
# timing
# --------------------------------------------------------------------------

def test_duration_sums_segments():
    e = edl(Segment("a", 0, 5), Segment("b", 10, 13))
    assert e.duration == pytest.approx(8.0)


def test_speed_changes_output_duration():
    assert edl(Segment("a", 0, 10, speed=2.0)).duration == pytest.approx(5.0)


def test_output_time_accumulates_across_segments():
    """The one sanctioned source-to-output conversion; drift starts here."""
    e = edl(Segment("a", 0, 5), Segment("b", 100, 105))
    assert e.output_time("a", 2.0) == pytest.approx(2.0)
    assert e.output_time("b", 102.0) == pytest.approx(7.0)


def test_output_time_respects_speed():
    e = edl(Segment("a", 0, 10, speed=2.0), Segment("b", 50, 55))
    assert e.output_time("b", 52.0) == pytest.approx(7.0)


def test_output_time_clamps_inside_the_segment():
    e = edl(Segment("a", 10, 20))
    assert e.output_time("a", 5.0) == pytest.approx(0.0)
    assert e.output_time("a", 99.0) == pytest.approx(10.0)


def test_output_time_rejects_unknown_segment():
    with pytest.raises(KeyError):
        edl().output_time("nope", 1.0)


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def test_valid_edl_has_no_problems():
    assert validate(edl(Segment("a", 0, 5))) == []


def test_reversed_segment_is_caught():
    assert any("must be after" in p for p in validate(edl(Segment("a", 5, 2))))


def test_segment_past_source_end_is_caught():
    problems = validate(edl(Segment("a", 0, 90)), source_duration=60.0)
    assert any("runs past the source" in p for p in problems)


def test_flash_frame_segment_is_caught():
    """Under ~0.3s a shot reads as a glitch, not an edit."""
    assert any("too short" in p for p in validate(edl(Segment("a", 0, 0.1))))


def test_duplicate_ids_are_caught():
    problems = validate(edl(Segment("a", 0, 5), Segment("a", 6, 10)))
    assert any("duplicate segment id" in p for p in problems)


def test_platform_length_limit_is_enforced():
    e = edl(Segment("a", 0, 90), target=Target(max_dur=59.0))
    assert any("exceeds the 59s" in p for p in validate(e))


def test_framing_referencing_a_missing_segment_is_caught():
    e = edl(Segment("a", 0, 5), framing=[Framing(seg="ghost")])
    assert any("unknown segment" in p for p in validate(e))


def test_focus_outside_the_frame_is_caught():
    e = edl(Segment("a", 0, 5), framing=[Framing(seg="a", focus=(1.4, 0.5))])
    assert any("outside the frame" in p for p in validate(e))


def test_caption_running_past_the_edit_is_caught():
    e = edl(Segment("a", 0, 5),
            captions=Captions(words=[CaptionWord("late", 9.0, 9.5)]))
    assert any("runs past the edit" in p for p in validate(e))


def test_overlay_past_the_end_is_caught():
    e = edl(Segment("a", 0, 5), overlays=[Overlay(type="emoji", at=99.0, glyph="X")])
    assert any("past the end" in p for p in validate(e))


def test_validate_reports_every_problem_at_once():
    """QC repairs in a loop; one fault per pass would take several rounds."""
    e = edl(Segment("a", 5, 2), Segment("a", 0, 0.1))
    assert len(validate(e)) >= 3


def test_empty_edl_is_rejected():
    assert any("no segments" in p for p in validate(EDL(source="/tmp/a.mp4")))


# --------------------------------------------------------------------------
# serialisation
# --------------------------------------------------------------------------

def test_roundtrip_preserves_the_edit(tmp_path):
    original = EDL(
        source="/tmp/a.mp4",
        segments=[Segment("a", 1.5, 6.5, why="hook")],
        framing=[Framing(seg="a", focus=(0.4, 0.35), mode="punch", zoom_to=1.15)],
        captions=Captions(words=[CaptionWord("hello", 0.0, 0.4)]),
        overlays=[Overlay(type="emoji", at=1.0, glyph="\U0001F525")],
    )
    path = original.save(tmp_path / "edl.json")
    loaded = EDL.load(path)

    assert loaded.segments[0].why == "hook"
    assert loaded.framing[0].focus == (0.4, 0.35)
    assert loaded.framing[0].zoom_to == 1.15
    assert loaded.overlays[0].glyph == "\U0001F525"
    assert loaded.duration == original.duration


def test_newer_schema_version_is_refused(tmp_path):
    """Rendering a future EDL with stale rules is worse than failing."""
    path = tmp_path / "edl.json"
    path.write_text('{"source": "/tmp/a.mp4", "version": 99, "segments": []}')
    with pytest.raises(ValueError, match="newer than this build"):
        EDL.load(path)


def test_missing_optional_sections_get_defaults():
    loaded = EDL.from_dict({"source": "/tmp/a.mp4",
                            "segments": [{"id": "a", "src_in": 0, "src_out": 5}]})
    assert loaded.target.aspect == "9:16"
    assert loaded.audio.fade_ms == 20
    assert loaded.framing_for("a").focus == (0.5, 0.5)
