"""Learning a style from reference videos."""

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from core import media, study
from core.playbook import load
from core.study import Reading, Suggestion


def reading(**overrides) -> Reading:
    base = dict(name="ref", source="/r.mp4", measured_at="2026-09-04",
                duration=30.0, width=1080, height=1920, fps=30.0)
    base.update(overrides)
    return Reading(**base)


# --------------------------------------------------------------------------
# derived numbers
# --------------------------------------------------------------------------

def test_shot_lengths_span_the_whole_file():
    r = reading(duration=10.0, cuts=[2.0, 5.0, 9.0])
    assert r.shot_lengths == [2.0, 3.0, 4.0, 1.0]
    assert r.median_shot == 2.5


def test_no_cuts_means_one_shot_the_length_of_the_file():
    r = reading(duration=12.0)
    assert r.median_shot == 12.0
    assert r.cuts_per_minute == 0.0


def test_silence_fraction_and_median_pause():
    r = reading(duration=10.0, silences=[(1.0, 1.5), (4.0, 5.0), (8.0, 8.2)])
    assert r.silence_fraction == pytest.approx(0.17)
    assert r.median_pause == pytest.approx(0.5)


def test_no_pauses_is_none_not_zero():
    # Zero would suggest "tight"; None says "unknown", which is the truth.
    assert reading().median_pause is None


def test_flat_energy_has_no_dynamics():
    assert reading(energy=[0.5] * 20).energy_dynamics == 0.0
    spiky = reading(energy=[0.2, 0.9, 0.2, 0.9, 0.2, 0.9])
    assert spiky.energy_dynamics > 0.4


def test_round_trips_through_json():
    r = reading(cuts=[1.0], silences=[(2.0, 2.5)], caption_position=0.7)
    back = Reading.from_json(r.to_json())
    assert back == r
    assert isinstance(back.silences[0], tuple)


# --------------------------------------------------------------------------
# the caption band
# --------------------------------------------------------------------------

def frame_with_text(y_fraction: float | None, size=(270, 480)) -> Image.Image:
    """A frame with a noisy background and, optionally, a text line."""
    rng = np.random.default_rng(7)
    noise = (rng.normal(120, 8, (size[1], size[0]))).clip(0, 255).astype("uint8")
    image = Image.fromarray(noise).convert("RGB")
    if y_fraction is not None:
        draw = ImageDraw.Draw(image)
        y = int(size[1] * y_fraction)
        # Dense vertical strokes are what text looks like to an edge filter.
        for x in range(20, size[0] - 20, 4):
            draw.line([(x, y - 12), (x, y + 12)], fill=(255, 255, 255), width=2)
    return image


def test_row_profile_is_normalised_to_the_frame():
    profile = study.row_edge_profile(frame_with_text(0.7))
    assert profile.shape[0] == 480
    assert profile.mean() == pytest.approx(1.0, abs=0.05)


def test_uniform_frame_has_no_edges_and_does_not_divide_by_zero():
    flat = Image.new("RGB", (64, 64), (40, 40, 40))
    assert study.row_edge_profile(flat).max() == 0.0


def test_caption_band_is_found_where_the_text_recurs():
    frames = [study.row_edge_profile(frame_with_text(0.72)) for _ in range(12)]
    presence, position = study.caption_band(frames)
    assert presence == 1.0
    assert position == pytest.approx(0.72, abs=0.04)


def test_presence_reflects_how_many_frames_carry_text():
    with_text = [study.row_edge_profile(frame_with_text(0.72)) for _ in range(6)]
    without = [study.row_edge_profile(frame_with_text(None)) for _ in range(6)]
    presence, _ = study.caption_band(with_text + without)
    assert 0.4 <= presence <= 0.6


def test_no_text_anywhere_reports_no_captions():
    frames = [study.row_edge_profile(frame_with_text(None)) for _ in range(8)]
    presence, position = study.caption_band(frames)
    assert presence == 0.0
    assert position is None


def test_a_fence_in_one_frame_is_not_a_caption():
    # Recurrence is the signal: one edgy frame among many quiet ones must not
    # register as a caption track.
    frames = [study.row_edge_profile(frame_with_text(None)) for _ in range(11)]
    frames.append(study.row_edge_profile(frame_with_text(0.5)))
    presence, _ = study.caption_band(frames)
    assert presence < 0.15


# --------------------------------------------------------------------------
# suggestions: direction is what matters
# --------------------------------------------------------------------------

def suggestions_for(*readings) -> dict[str, Suggestion]:
    return {s.field: s for s in study.suggest(list(readings))}


def test_no_readings_no_suggestions():
    assert study.suggest([]) == []


def test_snappier_reference_yields_shorter_minimum_shot():
    snappy = suggestions_for(reading(duration=30, cuts=list(np.arange(1.0, 30, 1.0))))
    slow = suggestions_for(reading(duration=30, cuts=[10.0, 20.0]))
    assert snappy["min_shot"].value < slow["min_shot"].value


def test_tighter_pauses_in_the_reference_mean_tighter_pauses_kept():
    tight = suggestions_for(reading(silences=[(1, 1.2), (5, 5.25), (9, 9.15)]))
    loose = suggestions_for(reading(silences=[(1, 1.9), (5, 6.1), (9, 9.8)]))
    assert tight["keep_pause"].value < loose["keep_pause"].value
    assert tight["min_gap_to_cut"].value < loose["min_gap_to_cut"].value


def test_frequent_reframing_shortens_the_punch_gap():
    busy = suggestions_for(reading(duration=60, soft_cuts=list(range(2, 60, 3))))
    still = suggestions_for(reading(duration=60, soft_cuts=[]))
    assert busy["min_punch_gap"].value < still["min_punch_gap"].value
    assert still["min_punch_gap"].value == 6.0


def test_uncaptioned_reference_turns_captions_off_and_gives_no_position():
    s = suggestions_for(reading(caption_presence=0.1, caption_position=0.5))
    assert s["captions_enabled"].value is False
    assert "caption_position" not in s


def test_captioned_reference_keeps_its_position():
    s = suggestions_for(reading(caption_presence=0.9, caption_position=0.68))
    assert s["captions_enabled"].value is True
    assert s["caption_position"].value == pytest.approx(0.68)


def test_length_follows_the_reference():
    short = suggestions_for(reading(duration=20))
    long = suggestions_for(reading(duration=90))
    assert short["max_seconds"].value < long["max_seconds"].value
    assert short["min_seconds"].value < short["max_seconds"].value


def test_loudness_is_only_suggested_when_measured():
    assert "loudness" not in suggestions_for(reading(loudness_lufs=None))
    s = suggestions_for(reading(loudness_lufs=-14.3))
    assert s["loudness"].value == -14.0


def test_suggestions_are_medians_across_references_not_the_last_one():
    a = reading(name="a", duration=20)
    b = reading(name="b", duration=40)
    c = reading(name="c", duration=90)
    s = suggestions_for(a, b, c)
    # 1.15 * 40 = 46, which is the median reference, not the loudest one.
    assert s["max_seconds"].value == 46.0
    assert "a, b, c" in s["max_seconds"].reason


def test_every_suggestion_names_its_reference():
    for s in study.suggest([reading(name="tiktok-ref", loudness_lufs=-15)]):
        assert "tiktok-ref" in s.reason


# --------------------------------------------------------------------------
# persistence and applying
# --------------------------------------------------------------------------

def test_save_and_load_all(tmp_path):
    study.save(reading(name="one"), tmp_path)
    study.save(reading(name="two", duration=50), tmp_path)
    (tmp_path / "references" / "broken.json").write_text("{not json")
    loaded = study.load_all(tmp_path)
    # The corrupt file is skipped, not allowed to hide the others.
    assert [r.name for r in loaded] == ["one", "two"]


def test_apply_writes_the_playbook_with_provenance(tmp_path):
    sugg = [Suggestion("keep_pause", 0.15, "reference median pause 0.25s (ref)")]
    book = study.apply(sugg, tmp_path, when="2026-09-04")
    assert book.keep_pause == 0.15
    assert load(tmp_path / "playbook.md").keep_pause == 0.15
    provenance = json.loads((tmp_path / "provenance.json").read_text())
    assert "reference" in provenance["keep_pause"]
    assert "ref" in provenance["keep_pause"]


def test_apply_ignores_fields_the_playbook_does_not_have(tmp_path):
    book = study.apply([Suggestion("no_such_knob", 1, "x")], tmp_path, when="now")
    assert not hasattr(book, "no_such_knob")


def test_report_says_when_more_references_are_needed():
    r = reading(cuts=[1.0], loudness_lufs=-14.0)
    text = study.render_report(r, study.suggest([r]), total_references=1)
    assert "study two more" in text
    assert "Not measured" in text
    settled = study.render_report(r, study.suggest([r]), total_references=3)
    assert "study two more" not in settled


def test_clean_name_is_filesystem_safe():
    assert study.clean_name(Path("My Ref (v2).MP4")) == "my-ref-v2"
    assert study.clean_name(Path("x.mp4"), "TikTok Ref!") == "tiktok-ref"


# --------------------------------------------------------------------------
# the real thing: a synthetic reference with known cuts
# --------------------------------------------------------------------------

@pytest.mark.skipif(not media.available(), reason="ffmpeg not installed")
def test_measure_finds_known_cuts_and_pauses(tmp_path):
    """Build a reference whose cuts and silences are known, and measure it.

    Four visually distinct shots of 2, 3, 1.5 and 2.5 seconds, with a tone
    that drops out for a known gap. The measurement must find the cuts near
    their true positions and the pause near its true length.
    """
    # Textless sources on purpose. ffmpeg's testsrc/testsrc2 draw a running
    # timecode -- real, changing text in a fixed band -- and the detector
    # correctly reported it as captions the first time this test ran.
    shots = [(2.0, "color=c=blue"), (3.0, "smptebars"),
             (1.5, "rgbtestsrc"), (2.5, "color=c=orange")]
    parts = []
    for i, (dur, src) in enumerate(shots):
        part = tmp_path / f"p{i}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error",
            # A source that already carries options joins the rest with ':'.
            "-f", "lavfi", "-i",
            f"{src}{':' if '=' in src else '='}size=540x960:rate=30:duration={dur}",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(part),
        ], check=True)
        parts.append(part)
    concat = tmp_path / "list.txt"
    concat.write_text("".join(f"file '{p}'\n" for p in parts))
    ref = tmp_path / "reference.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat),
        # Mute a known 0.8s window in the middle of the second shot.
        "-af", "volume=enable='between(t,3.2,4.0)':volume=0",
        "-c:v", "copy", "-c:a", "aac", str(ref),
    ], check=True)

    r = study.measure(ref, tmp_path / "work", name="synthetic", when="2026-09-04")

    assert r.duration == pytest.approx(9.0, abs=0.2)
    assert r.is_vertical
    # Cuts at 2.0, 5.0 and 6.5 seconds, each within a couple of frames.
    for expected in (2.0, 5.0, 6.5):
        assert any(abs(c - expected) < 0.15 for c in r.cuts), (expected, r.cuts)
    assert r.median_pause == pytest.approx(0.8, abs=0.15)
    assert r.loudness_lufs is not None
    # Test patterns are not text; the band detector must not invent captions.
    assert r.caption_presence < 0.5
