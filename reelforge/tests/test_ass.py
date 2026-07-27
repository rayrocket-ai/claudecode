"""Tests for ASS caption generation."""

import pytest

from reelforge.core.edl import CaptionWord, Target
from reelforge.core.render import ass

TARGET = Target(aspect="9:16", width=1080, fps=30)
STYLE = ass.STYLES["karaoke-bold"]


def words(*specs) -> list[CaptionWord]:
    return [CaptionWord(t, s, e) for t, s, e in specs]


# --------------------------------------------------------------------------
# timestamps
# --------------------------------------------------------------------------

@pytest.mark.parametrize("seconds,expected", [
    (0.0, "0:00:00.00"),
    (5.25, "0:00:05.25"),
    (61.5, "0:01:01.50"),
    (3661.0, "1:01:01.00"),
])
def test_ass_timestamp_format(seconds, expected):
    assert ass._ts(seconds) == expected


def test_negative_time_clamps_to_zero():
    assert ass._ts(-1.0) == "0:00:00.00"


# --------------------------------------------------------------------------
# grouping -- what stops captions overflowing or reading as stutter
# --------------------------------------------------------------------------

def test_group_breaks_on_word_count():
    w = words(*[(f"w{i}", i * 0.3, i * 0.3 + 0.25) for i in range(9)])
    groups = ass.group_words(w, STYLE, TARGET)
    assert all(len(g) <= STYLE.max_words for g in groups)


def test_group_breaks_on_character_count():
    """Word count alone overflows on long words."""
    w = words(("internationalisation", 0.0, 0.5), ("strategies", 0.6, 1.0))
    assert len(ass.group_words(w, STYLE, TARGET)) == 2


def test_max_chars_is_derived_from_size_and_width():
    """A hardcoded count is wrong the moment font size or width changes -- and
    the overflow is invisible in the EDL, only in the render."""
    assert STYLE.max_chars(TARGET) < 22
    big = ass.CaptionStyle(size_ratio=0.10)
    assert big.max_chars(TARGET) < STYLE.max_chars(TARGET)
    wide = Target(aspect="16:9", width=1920)
    assert STYLE.max_chars(wide) > STYLE.max_chars(TARGET)


def test_grouped_lines_fit_the_frame():
    w = words(*[("wonderful", i * 0.4, i * 0.4 + 0.35) for i in range(12)])
    limit = STYLE.max_chars(TARGET)
    for group in ass.group_words(w, STYLE, TARGET):
        assert len(" ".join(x.text for x in group)) <= limit + 1


def test_short_words_are_not_split_needlessly():
    """Character count alone would split 'I do' across two cards."""
    assert len(ass.group_words(words(("I", 0.0, 0.2), ("do", 0.3, 0.5)), STYLE, TARGET)) == 1


def test_a_pause_breaks_the_group():
    """When the speaker stops, the caption should stop with them."""
    w = words(("before", 0.0, 0.4), ("after", 3.0, 3.4))
    assert len(ass.group_words(w, STYLE, TARGET)) == 2


def test_grouping_preserves_every_word():
    w = words(*[(f"w{i}", i * 0.3, i * 0.3 + 0.25) for i in range(20)])
    assert sum(len(g) for g in ass.group_words(w, STYLE, TARGET)) == 20


# --------------------------------------------------------------------------
# document structure
# --------------------------------------------------------------------------

def test_header_matches_the_render_resolution():
    """Mismatched PlayRes silently scales every caption."""
    head = ass.header(TARGET, STYLE)
    assert "PlayResX: 1080" in head
    assert "PlayResY: 1920" in head


def test_style_line_field_count_matches_the_format_line():
    """A field-count mismatch makes libass drop the style without complaint."""
    head = ass.header(TARGET, STYLE)
    fmt = next(l for l in head.splitlines() if l.startswith("Format: Name,"))
    style = next(l for l in head.splitlines() if l.startswith("Style: "))
    assert len(fmt.split(":", 1)[1].split(",")) == len(style.split(":", 1)[1].split(","))


def test_build_emits_one_dialogue_per_group():
    out = ass.build(words(("a", 0.0, 0.3), ("b", 0.4, 0.7), ("c", 5.0, 5.3)), TARGET)
    assert out.count("Dialogue:") == 2


def test_empty_caption_track_still_produces_a_valid_file():
    out = ass.build([], TARGET)
    assert "[Events]" in out and "Dialogue:" not in out


def test_unknown_style_falls_back_rather_than_raising():
    assert "Dialogue:" in ass.build(words(("a", 0.0, 0.3)), TARGET, "no-such-style")


# --------------------------------------------------------------------------
# karaoke timing -- the per-word highlight
# --------------------------------------------------------------------------

def test_karaoke_durations_are_centiseconds():
    out = ass.build(words(("hello", 0.0, 0.5)), TARGET)
    assert "{\\kf50}hello" in out


def test_gaps_between_words_are_carried_explicitly():
    """Karaoke timing is relative; an uncarried gap drifts ahead of the speech."""
    out = ass.build(words(("a", 0.0, 0.2), ("b", 0.5, 0.7)), TARGET)
    assert "{\\k30}" in out          # the 0.3s gap


def test_zero_length_word_still_gets_a_visible_hold():
    out = ass.build(words(("x", 1.0, 1.0)), TARGET)
    assert "{\\kf1}" in out


# --------------------------------------------------------------------------
# escaping
# --------------------------------------------------------------------------

def test_braces_in_speech_cannot_open_an_override_block():
    """An unescaped brace swallows the rest of the line silently."""
    out = ass.build(words(("{drop}", 0.0, 0.4)), TARGET)
    assert "\\{drop\\}" in out


def test_backslashes_are_escaped():
    assert "\\\\" in ass.build(words(("a\\b", 0.0, 0.4)), TARGET)


# --------------------------------------------------------------------------
# safe areas
# --------------------------------------------------------------------------

def test_safe_area_excludes_platform_chrome():
    top, bottom = ass.safe_area(TARGET)
    assert top == pytest.approx(1920 * 0.14, abs=1)
    assert bottom == pytest.approx(1920 * 0.80, abs=1)


def test_default_caption_position_is_inside_the_safe_area():
    top, bottom = ass.safe_area(TARGET)
    assert top < STYLE.position * TARGET.height < bottom
