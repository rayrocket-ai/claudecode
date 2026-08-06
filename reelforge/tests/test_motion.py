"""Animated overlay backends: composition rendering and honest degradation."""

from pathlib import Path

import pytest

from core.edl import Overlay, Target
from core.render import motion
from core.render.filters import SequenceOverlay, finish_cmd

TARGET = Target()


# --------------------------------------------------------------------------
# compositions are pure functions of time
# --------------------------------------------------------------------------

def test_every_built_in_composition_renders():
    for comp in motion.COMPOSITIONS:
        page = motion.compose_html(comp, 0.5, 2.0, {"title": "Hi", "text": "Hi",
                                                    "words": ["a", "b"]}, TARGET)
        assert "<div class=\"stage\">" in page
        assert f"{TARGET.width}px" in page


def test_unknown_composition_raises_and_lists_the_options():
    with pytest.raises(motion.UnknownComposition, match="lower-third"):
        motion.compose_html("fancy-thing", 0.0, 1.0, {}, TARGET)


def test_the_same_instant_renders_identically():
    # The whole capture design rests on this: frames are independent and
    # reproducible because the page is a function of t and nothing else.
    a = motion.compose_html("lower-third", 0.4, 2.0, {"title": "Ray"}, TARGET)
    b = motion.compose_html("lower-third", 0.4, 2.0, {"title": "Ray"}, TARGET)
    assert a == b


def test_different_instants_render_differently():
    early = motion.compose_html("lower-third", 0.05, 2.0, {"title": "Ray"}, TARGET)
    later = motion.compose_html("lower-third", 1.0, 2.0, {"title": "Ray"}, TARGET)
    assert early != later


def test_the_page_background_is_transparent():
    page = motion.compose_html("callout", 0.5, 2.0, {"text": "x"}, TARGET)
    assert "background:transparent" in page


def test_text_is_escaped_not_injected():
    page = motion.compose_html("callout", 0.5, 2.0, {"text": "<script>x</script>"}, TARGET)
    assert "<script>" not in page
    assert "&lt;script&gt;" in page


def test_a_composition_fades_out_before_it_ends():
    end = motion.compose_html("lower-third", 1.99, 2.0, {"title": "Ray"}, TARGET)
    middle = motion.compose_html("lower-third", 1.0, 2.0, {"title": "Ray"}, TARGET)
    assert "opacity:0.0" in end or "opacity:0.1" in end
    assert "opacity:1.000" in middle


def test_kinetic_words_appear_in_sequence():
    props = {"words": ["one", "two", "three"]}
    early = motion.compose_html("kinetic", 0.05, 3.0, props, TARGET)
    late = motion.compose_html("kinetic", 2.4, 3.0, props, TARGET)
    # The last word is still invisible early on, and visible by the end.
    assert early.count("opacity:0.000") >= 2
    assert late.count("opacity:0.000") == 0


def test_progress_bar_grows_monotonically():
    widths = []
    for t in (0.0, 0.5, 1.0):
        page = motion.compose_html("progress", t, 1.0, {}, TARGET)
        rule = page.split(".prog {")[1]
        widths.append(float(rule.split("width:")[1].split("%")[0]))
    assert widths == sorted(widths)
    assert widths[-1] == pytest.approx(100.0)


# --------------------------------------------------------------------------
# Chromium capture
# --------------------------------------------------------------------------

def test_capture_requests_a_transparent_background(tmp_path):
    cmd = motion.chromium_cmd(tmp_path / "chrome", tmp_path / "p.html",
                              tmp_path / "f.png", TARGET)
    # Without this flag every overlay arrives as an opaque rectangle covering
    # the video -- the single most destructive way this can go wrong.
    assert "--default-background-color=00000000" in cmd
    assert f"--window-size={TARGET.width},{TARGET.height}" in cmd
    assert any(a.startswith("--screenshot=") for a in cmd)


def test_capture_url_is_absolute_even_from_a_relative_path(tmp_path, monkeypatch):
    """A relative file:// URL makes Chromium screenshot its own error page.

    It does so with exit status 0 and a valid PNG, so nothing downstream
    notices -- the only symptom is an opaque rectangle over the whole video.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "p.html").write_text("<p>hi</p>")
    cmd = motion.chromium_cmd(tmp_path / "chrome", Path("p.html"),
                              tmp_path / "f.png", TARGET)
    url = cmd[-1]
    assert url.startswith("file:///")
    assert str(tmp_path) in url


def test_an_opaque_capture_is_rejected(tmp_path):
    from PIL import Image

    rgb = tmp_path / "rgb.png"
    Image.new("RGB", (8, 8), (255, 255, 255)).save(rgb)
    with pytest.raises(motion.BackendUnavailable, match="no alpha channel"):
        motion.assert_capture_is_transparent(rgb)

    solid = tmp_path / "solid.png"
    Image.new("RGBA", (8, 8), (0, 0, 0, 255)).save(solid)
    with pytest.raises(motion.BackendUnavailable, match="fully opaque"):
        motion.assert_capture_is_transparent(solid)


def test_a_transparent_capture_passes(tmp_path):
    from PIL import Image

    good = tmp_path / "good.png"
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    image.putpixel((0, 0), (255, 0, 0, 255))
    image.save(good)
    motion.assert_capture_is_transparent(good)      # must not raise


@pytest.mark.skipif(motion.find_chromium() is None, reason="no Chromium")
def test_chromium_really_produces_transparent_frames(tmp_path):
    overlay = Overlay(type="hyperframes", at=0.0, dur=0.1, comp="callout",
                      props={"text": "Live"})
    outdir = motion.render_hyperframes(overlay, TARGET, tmp_path, fps=10)
    frames = sorted(outdir.glob("frame_*.png"))
    assert frames
    for frame in frames:
        motion.assert_capture_is_transparent(frame)


@pytest.mark.skipif(motion.find_chromium() is None, reason="no Chromium")
def test_frames_are_cached_between_runs(tmp_path):
    overlay = Overlay(type="hyperframes", at=0.0, dur=0.1, comp="progress",
                      props={})
    first = motion.render_hyperframes(overlay, TARGET, tmp_path, fps=10)
    stamp = (first / "frame_00000.png").stat().st_mtime_ns
    again = motion.render_hyperframes(overlay, TARGET, tmp_path, fps=10)
    assert again == first
    assert (again / "frame_00000.png").stat().st_mtime_ns == stamp


def test_missing_chromium_names_the_fix(tmp_path, monkeypatch):
    monkeypatch.setattr(motion, "find_chromium", lambda: None)
    overlay = Overlay(type="hyperframes", at=0.0, dur=1.0, comp="callout")
    with pytest.raises(motion.BackendUnavailable, match="REELFORGE_CHROMIUM"):
        motion.render_hyperframes(overlay, TARGET, tmp_path, fps=30)


# --------------------------------------------------------------------------
# Remotion
# --------------------------------------------------------------------------

def test_remotion_renders_a_png_sequence_with_alpha(tmp_path):
    cmd = motion.remotion_cmd(tmp_path, "LowerThird", tmp_path / "out",
                              {"title": "Ray"}, fps=30, target=TARGET,
                              browser=tmp_path / "chrome")
    assert "--sequence" in cmd            # per-frame files, not a video
    assert "--image-format=png" in cmd    # PNG is what carries the alpha
    assert "--pixel-format=yuva420p" in cmd
    assert any(a.startswith("--props=") for a in cmd)


def test_remotion_reuses_a_local_browser(tmp_path):
    # Left alone Remotion downloads its own ~150MB headless shell on first
    # run: slow on a fresh box, and an outright failure on a network that
    # does not allow it. The same Chromium already serves HyperFrames.
    cmd = motion.remotion_cmd(tmp_path, "LowerThird", tmp_path / "out", {},
                              fps=30, target=TARGET, browser=tmp_path / "chrome")
    assert f"--browser-executable={tmp_path / 'chrome'}" in cmd


def test_missing_remotion_project_names_the_fix(tmp_path):
    overlay = Overlay(type="remotion", at=0.0, dur=1.0, comp="LowerThird")
    with pytest.raises(motion.BackendUnavailable, match="create-video"):
        motion.render_remotion(overlay, TARGET, tmp_path, fps=30,
                               project=tmp_path / "absent")


def test_remotion_availability_is_checked_by_installed_package(tmp_path):
    assert not motion.remotion_available(tmp_path)
    (tmp_path / "node_modules" / "remotion").mkdir(parents=True)
    assert motion.remotion_available(tmp_path)


# --------------------------------------------------------------------------
# sequence discovery and compositing
# --------------------------------------------------------------------------

def test_both_backends_naming_schemes_are_recognised(tmp_path):
    ours = tmp_path / "ours"
    ours.mkdir()
    (ours / "frame_00000.png").write_bytes(b"")
    assert motion.sequence_pattern(ours).endswith("frame_%05d.png")

    theirs = tmp_path / "theirs"
    theirs.mkdir()
    (theirs / "element-0.png").write_bytes(b"")
    assert motion.sequence_pattern(theirs).endswith("element-%d.png")


def test_an_empty_frame_directory_is_an_error(tmp_path):
    with pytest.raises(motion.BackendUnavailable):
        motion.sequence_pattern(tmp_path)


def test_sequence_is_time_shifted_rather_than_padded():
    # Padding would mean generating hundreds of transparent PNGs to place a
    # short graphic late in a long video.
    seq = SequenceOverlay(pattern="/f/frame_%05d.png", at=12.0, dur=2.0, fps=30)
    cmd = finish_cmd("/a.mp4", "/b.mp4", TARGET, subtitles=None, overlays=[],
                     encode_args=[], sequences=[seq])
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert "setpts=PTS-STARTPTS+12.000/TB" in graph
    assert "between(t,12.000,14.000)" in graph


def test_sequence_framerate_precedes_its_input():
    # As an output option -framerate is silently ignored and the sequence
    # plays at 25fps regardless of what was intended.
    seq = SequenceOverlay(pattern="/f/frame_%05d.png", at=0.0, dur=1.0, fps=30)
    cmd = finish_cmd("/a.mp4", "/b.mp4", TARGET, subtitles=None, overlays=[],
                     encode_args=[], sequences=[seq])
    assert cmd[cmd.index("-framerate") + 2] == "-i"


def test_captions_are_layered_above_animated_graphics():
    seq = SequenceOverlay(pattern="/f/frame_%05d.png", at=0.0, dur=1.0, fps=30)
    cmd = finish_cmd("/a.mp4", "/b.mp4", TARGET, subtitles="/subs.ass",
                     overlays=[], encode_args=[], sequences=[seq])
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert graph.index("overlay=") < graph.index("subtitles=")
