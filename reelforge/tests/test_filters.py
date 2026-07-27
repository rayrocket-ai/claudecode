"""Tests for filter graph construction.

A wrong filter graph is the most expensive bug in a video pipeline and the
hardest to notice -- it renders happily and looks wrong. These assert the graph
itself, with no ffmpeg present.
"""

import re

import pytest

from reelforge.core.edl import Audio, Framing, Segment, Target
from reelforge.core.render import filters

LANDSCAPE = (1920, 1080)
VERTICAL_TARGET = Target(aspect="9:16", width=1080, fps=30)


# --------------------------------------------------------------------------
# crop geometry -- the 16:9 -> 9:16 reframe
# --------------------------------------------------------------------------

def test_base_crop_pillars_a_landscape_source():
    """1920x1080 to 9:16 keeps full height and throws away 44% of the width."""
    assert filters.base_crop(1920, 1080, VERTICAL_TARGET) == (606, 1080)


def test_base_crop_letterboxes_a_vertical_source_for_youtube():
    assert filters.base_crop(1080, 1920, Target(aspect="16:9", width=1920)) == (1080, 606)


def test_matching_aspect_crops_nothing():
    assert filters.base_crop(1080, 1920, VERTICAL_TARGET) == (1080, 1920)


def test_crop_dimensions_are_always_even():
    for w, h in [(1919, 1079), (1281, 721), (999, 555)]:
        window = filters.crop_window(w, h, VERTICAL_TARGET, (0.5, 0.5))
        assert window.w % 2 == 0 and window.h % 2 == 0
        assert window.x % 2 == 0 and window.y % 2 == 0


def test_crop_follows_the_subject():
    left = filters.crop_window(*LANDSCAPE, VERTICAL_TARGET, (0.25, 0.5))
    right = filters.crop_window(*LANDSCAPE, VERTICAL_TARGET, (0.75, 0.5))
    assert left.x < right.x


def test_crop_clamps_at_the_frame_edge():
    """A subject near the border must not produce black bars down one side."""
    window = filters.crop_window(*LANDSCAPE, VERTICAL_TARGET, (0.98, 0.5))
    assert window.x + window.w <= 1920
    assert filters.crop_window(*LANDSCAPE, VERTICAL_TARGET, (0.0, 0.5)).x == 0


def test_zoom_tightens_the_window():
    wide = filters.crop_window(*LANDSCAPE, VERTICAL_TARGET, (0.5, 0.5), zoom=1.0)
    tight = filters.crop_window(*LANDSCAPE, VERTICAL_TARGET, (0.5, 0.5), zoom=1.5)
    assert tight.w < wide.w and tight.h < wide.h


def test_zero_dimensions_rejected():
    with pytest.raises(ValueError):
        filters.base_crop(0, 1080, VERTICAL_TARGET)


# --------------------------------------------------------------------------
# static vs animated zoom
# --------------------------------------------------------------------------

def test_static_framing_avoids_zoompan():
    """A constant zoom is just a tighter crop -- zoompan would only add jitter."""
    chain = filters.video_chain(*LANDSCAPE, VERTICAL_TARGET,
                                Framing(seg="a", zoom_from=1.2, zoom_to=1.2), 5.0)
    assert "zoompan" not in chain
    assert chain.startswith("crop=")


def test_punch_in_animates_scale_not_zoompan():
    """zoompan is 27x slower than this on the same segment. Never use it."""
    chain = filters.video_chain(
        *LANDSCAPE, VERTICAL_TARGET,
        Framing(seg="a", mode="punch", zoom_from=1.0, zoom_to=1.15), 5.0)
    assert "zoompan" not in chain
    assert "eval=frame" in chain
    # Output size stays fixed -- the encoder requires it -- while the sampled
    # region shrinks, which is what the eye reads as a push-in.
    assert chain.endswith("setsar=1,fps=30")
    assert f"crop={VERTICAL_TARGET.width}:{VERTICAL_TARGET.height}" in chain


def test_punch_progress_is_driven_by_time():
    chain = filters.video_chain(
        *LANDSCAPE, VERTICAL_TARGET,
        Framing(seg="a", mode="punch", zoom_from=1.0, zoom_to=1.2), 4.0)
    assert "t/4.0000" in chain


def test_zoom_factor_starts_at_one_for_a_push_in():
    expr = filters.zoom_expr(Framing(seg="a", zoom_from=1.0, zoom_to=1.2), 5.0)
    assert expr.startswith("(1.00000+(1.20000-1.00000)")


def test_pull_out_is_normalised_to_never_scale_below_one():
    """A factor under 1 would ask crop for more than its input and fail."""
    expr = filters.zoom_expr(Framing(seg="a", zoom_from=1.4, zoom_to=1.0), 5.0)
    assert expr.startswith("(1.40000+(1.00000-1.40000)")
    assert "1.40000" in expr and expr.count("(") >= 1


def test_pull_out_crops_at_its_widest_point():
    """The base crop must cover the widest framing, or the end of the move
    would need pixels that were already thrown away."""
    pull = filters.video_chain(*LANDSCAPE, VERTICAL_TARGET,
                               Framing(seg="a", mode="punch",
                                       zoom_from=1.5, zoom_to=1.0), 5.0)
    push = filters.video_chain(*LANDSCAPE, VERTICAL_TARGET,
                               Framing(seg="a", mode="punch",
                                       zoom_from=1.0, zoom_to=1.5), 5.0)
    assert pull.split(",")[0] == push.split(",")[0]


def test_zero_duration_does_not_divide_by_zero():
    assert "t/0.0010" in filters.zoom_expr(Framing(seg="a", zoom_to=1.2), 0.0)


def test_every_chain_normalises_size_sar_and_fps():
    """concat refuses mismatched streams; a stray SAR poisons the whole join.

    Both paths must land on exactly the target geometry -- the static one via a
    plain scale, the animated one via the fixed centre crop after its moving
    scale.
    """
    for framing in (Framing(seg="a"),
                    Framing(seg="a", mode="punch", zoom_to=1.2)):
        chain = filters.video_chain(*LANDSCAPE, VERTICAL_TARGET, framing, 3.0)
        assert chain.endswith("setsar=1,fps=30")
        assert f"{VERTICAL_TARGET.width}:{VERTICAL_TARGET.height}" in chain


def test_speed_change_adjusts_pts():
    chain = filters.video_chain(*LANDSCAPE, VERTICAL_TARGET, Framing(seg="a"),
                                2.5, speed=2.0)
    assert re.search(r"setpts=0\.5\d*\*PTS", chain)


# --------------------------------------------------------------------------
# easing
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["linear", "outCubic", "inOutCubic"])
def test_easing_is_clipped_to_the_unit_interval(kind):
    """Filters keep evaluating past the nominal end; unclipped, the ease
    overshoots and the zoom keeps growing after the move should have settled."""
    assert "clip(" in filters.ease_expr(kind, "t/100")


def test_outcubic_is_the_default_shape():
    assert "pow(1-" in filters.ease_expr("anything-unknown", "p")


# --------------------------------------------------------------------------
# audio
# --------------------------------------------------------------------------

def test_cut_fades_are_present():
    """These are the entire reason cuts do not click."""
    chain = filters.audio_chain(5.0, Audio(fade_ms=20))
    assert "afade=t=in:st=0:d=0.020" in chain
    assert "afade=t=out:st=4.980" in chain


def test_fades_skipped_when_the_segment_is_shorter_than_them():
    assert "afade" not in filters.audio_chain(0.02, Audio(fade_ms=20))


def test_extreme_speed_chains_atempo_within_its_stable_range():
    """atempo is only stable 0.5-2.0; beyond that it must be chained."""
    chain = filters.audio_chain(5.0, Audio(), speed=4.0)
    assert chain.count("atempo") == 2


def test_audio_is_normalised_for_concat():
    assert "aformat=" in filters.audio_chain(5.0, Audio())


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def test_segment_seeks_before_input_for_speed():
    """-ss after -i decodes from zero; on an hour-long source that is minutes."""
    cmd = filters.segment_cmd(
        "/tmp/a.mp4", Segment("s1", 120.0, 125.0), Framing(seg="s1"),
        VERTICAL_TARGET, Audio(), "/tmp/s1.mp4",
        src_w=1920, src_h=1080, has_audio=True, encode_args=["-c:v", "libx264"])
    assert cmd.index("-ss") < cmd.index("-i")
    assert cmd[cmd.index("-t") + 1] == "5.000"


def test_silent_source_still_gets_an_audio_track():
    """Without this, concat yields a file whose audio stops partway through."""
    cmd = filters.segment_cmd(
        "/tmp/a.mp4", Segment("s1", 0, 5), Framing(seg="s1"), VERTICAL_TARGET,
        Audio(), "/tmp/s1.mp4", src_w=1920, src_h=1080, has_audio=False,
        encode_args=[])
    assert "anullsrc=r=48000:cl=stereo" in cmd
    assert "-shortest" in cmd


def test_concat_does_not_reencode():
    cmd = filters.concat_cmd("/tmp/list.txt", "/tmp/joined.mp4")
    assert cmd[cmd.index("-c") + 1] == "copy"
    assert "+genpts" in cmd


def test_finish_chains_overlays_then_subtitles():
    cmd = filters.finish_cmd(
        "/tmp/joined.mp4", "/tmp/final.mp4", VERTICAL_TARGET,
        subtitles="/tmp/c.ass",
        overlays=[("/tmp/fire.png", 1.0, 0.8, "100", "200")],
        encode_args=["-c:v", "libx264"])
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert graph.index("overlay=") < graph.index("subtitles=")
    assert "enable='between(t,1.000,1.800)'" in graph
    assert "-map" in cmd and "[vsub]" in cmd


def test_animated_overlay_positions_are_quoted():
    """An animated position contains commas from clip(v,0,1). Unquoted, ffmpeg
    reads the first one as the end of the filter and fails while pointing at a
    completely different part of the graph."""
    cmd = filters.finish_cmd(
        "/tmp/j.mp4", "/tmp/f.mp4", VERTICAL_TARGET, subtitles=None,
        overlays=[("/tmp/e.png", 1.2, 1.0, "860",
                   "48-60.2*(1-(1-pow(1-clip((t-1.200)/0.280,0,1),3)))")],
        encode_args=[])
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert "x='860'" in graph
    assert "y='48-60.2*" in graph


def test_finish_normalises_loudness_to_target():
    cmd = filters.finish_cmd("/tmp/a.mp4", "/tmp/b.mp4",
                             Target(loudness=-14.0), subtitles=None,
                             overlays=[], encode_args=[])
    assert "loudnorm=I=-14.0" in cmd[cmd.index("-filter:a") + 1]


def test_finish_without_captions_or_overlays_still_maps_video():
    cmd = filters.finish_cmd("/tmp/a.mp4", "/tmp/b.mp4", VERTICAL_TARGET,
                             subtitles=None, overlays=[], encode_args=[])
    assert "-filter_complex" not in cmd
    assert cmd[cmd.index("-map") + 1] == "0:v"


def test_faststart_is_set_for_streaming():
    cmd = filters.finish_cmd("/tmp/a.mp4", "/tmp/b.mp4", VERTICAL_TARGET,
                             subtitles=None, overlays=[], encode_args=[])
    assert "+faststart" in cmd


# --------------------------------------------------------------------------
# overlay anchoring
# --------------------------------------------------------------------------

@pytest.mark.parametrize("anchor", ["tl", "tr", "bl", "br", "c"])
def test_anchors_stay_inside_the_frame(anchor):
    x, y = filters.anchor_position(anchor, VERTICAL_TARGET, size=120, margin=48)
    assert 0 <= int(x) <= VERTICAL_TARGET.width - 120
    assert 0 <= int(y) <= VERTICAL_TARGET.height - 120
