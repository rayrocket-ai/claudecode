"""Tests for emoji rasterisation and renderer orchestration helpers.

The ffmpeg-executing parts are covered by the command tests in test_filters.py;
what is left here is the glue, which is where path escaping and overlay
resolution can quietly go wrong.
"""

from pathlib import Path

import pytest

from reelforge.core.edl import EDL, Overlay, Segment, Target
from reelforge.core.render import emoji, ffmpeg_renderer

TARGET = Target(aspect="9:16", width=1080, fps=30)


# --------------------------------------------------------------------------
# emoji cache keys
# --------------------------------------------------------------------------

def test_cache_key_uses_codepoints_not_the_glyph():
    """A filename containing a ZWJ sequence is a portability problem."""
    assert emoji.cache_path(Path("/tmp"), "\U0001F525", 172).name == "1f525@172.png"


def test_long_zwj_sequences_are_hashed():
    family = "\U0001F468‍\U0001F469‍\U0001F467‍\U0001F466" * 4
    name = emoji.cache_path(Path("/tmp"), family, 172).name
    assert len(name) < 40


def test_size_is_part_of_the_key():
    a = emoji.cache_path(Path("/tmp"), "\U0001F525", 100)
    b = emoji.cache_path(Path("/tmp"), "\U0001F525", 200)
    assert a != b


# --------------------------------------------------------------------------
# pop animation
# --------------------------------------------------------------------------

def test_pop_settles_at_the_anchor_position():
    """However it enters, it must end exactly where it was anchored."""
    _, y = emoji.pop_expressions(1.0, 0.8, 100, 200, 172)
    assert y.startswith("200-")
    assert "clip(" in y                       # progress cannot exceed 1


def test_pop_settle_never_exceeds_the_overlay_duration():
    _, y = emoji.pop_expressions(0.0, 0.1, 0, 0, 100)
    assert "/0.040" in y                      # 40% of a 0.1s overlay


def test_no_animation_returns_static_coordinates():
    edl = EDL(source="/tmp/a.mp4", segments=[Segment("s1", 0, 5)],
              overlays=[Overlay(type="emoji", at=1.0, glyph="\U0001F525", anim="none")])
    overlays, _ = ffmpeg_renderer._prepare_overlays(edl, Path("/tmp/rf-test"))
    if overlays:                              # skipped when no emoji font present
        _, _, _, x, y = overlays[0]
        assert x.isdigit() and y.isdigit()


# --------------------------------------------------------------------------
# overlay preparation
# --------------------------------------------------------------------------

def test_unsupported_overlay_types_warn_rather_than_vanish():
    """Silently dropping an overlay yields a video that is quietly wrong."""
    edl = EDL(source="/tmp/a.mp4", segments=[Segment("s1", 0, 5)],
              overlays=[Overlay(type="remotion", at=1.0, comp="LowerThird")])
    overlays, warnings = ffmpeg_renderer._prepare_overlays(edl, Path("/tmp/rf-test"))
    assert overlays == []
    assert any("not yet supported" in w for w in warnings)


def test_missing_font_warns_with_the_fix(monkeypatch):
    monkeypatch.setattr(emoji, "render", lambda *a, **k: None)
    edl = EDL(source="/tmp/a.mp4", segments=[Segment("s1", 0, 5)],
              overlays=[Overlay(type="emoji", at=1.0, glyph="\U0001F525")])
    _, warnings = ffmpeg_renderer._prepare_overlays(edl, Path("/tmp/rf-test"))
    assert any("fonts-noto-color-emoji" in w for w in warnings)


# --------------------------------------------------------------------------
# path escaping -- ffmpeg parses filter arguments twice
# --------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("/tmp/a.ass", "/tmp/a.ass"),
    ("/tmp/o:dd/a.ass", "/tmp/o\\:dd/a.ass"),
    ("/tmp/it's/a.ass", "/tmp/it\\'s/a.ass"),
])
def test_filter_paths_are_escaped(raw, expected):
    assert ffmpeg_renderer._escape_for_filter(Path(raw)) == expected


# --------------------------------------------------------------------------
# concat list
# --------------------------------------------------------------------------

def test_concat_list_escapes_single_quotes(tmp_path):
    """The concat demuxer's escape for ' is the unusual '\\'' sequence."""
    part = tmp_path / "it's.mp4"
    part.write_bytes(b"x")
    monkey = []
    original = ffmpeg_renderer.media.run
    ffmpeg_renderer.media.run = lambda cmd, **kw: monkey.append(cmd)
    try:
        ffmpeg_renderer._concat([part], tmp_path)
    finally:
        ffmpeg_renderer.media.run = original

    written = (tmp_path / "concat.txt").read_text()
    assert "'\\''" in written


# --------------------------------------------------------------------------
# guard rails
# --------------------------------------------------------------------------

def test_empty_edl_refuses_to_render(tmp_path):
    from reelforge.core.hardware import profile
    with pytest.raises(ffmpeg_renderer.RenderError, match="no segments"):
        ffmpeg_renderer.render(EDL(source="/tmp/a.mp4"), tmp_path / "o.mp4", profile())


def test_missing_source_is_reported_clearly(tmp_path, monkeypatch):
    from reelforge.core.hardware import profile
    monkeypatch.setattr(ffmpeg_renderer.media, "available", lambda: True)
    edl = EDL(source="/definitely/missing.mp4", segments=[Segment("s1", 0, 5)])
    with pytest.raises(ffmpeg_renderer.RenderError, match="source not found"):
        ffmpeg_renderer.render(edl, tmp_path / "o.mp4", profile())
