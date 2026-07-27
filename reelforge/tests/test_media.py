"""Tests for command construction and output parsing.

These run anywhere -- no ffmpeg required. That is the point of keeping command
building pure: the parts that break are testable on any machine, including CI
and a laptop with nothing installed.
"""

from pathlib import Path

import pytest

from reelforge.core import media


SRC = Path("/tmp/talk.mp4")


# --------------------------------------------------------------------------
# command builders
# --------------------------------------------------------------------------

def test_extract_audio_targets_asr_format():
    cmd = media.extract_audio_cmd(SRC, Path("/tmp/out.wav"))
    assert "-vn" in cmd, "video stream must be dropped"
    assert cmd[cmd.index("-ar") + 1] == "16000"
    assert cmd[cmd.index("-ac") + 1] == "1"


def test_commands_are_non_interactive():
    """A watcher runs unattended; a prompt would hang the service forever."""
    for cmd in (
        media.extract_audio_cmd(SRC, Path("/tmp/o.wav")),
        media.silence_cmd(SRC),
        media.scene_cmd(SRC),
        media.filmstrip_cmd(SRC, Path("/tmp/f-%04d.jpg")),
    ):
        assert "-nostdin" in cmd


def test_silence_threshold_is_above_room_tone():
    """ffmpeg's -60dB default finds nothing in real footage; we use -32."""
    cmd = media.silence_cmd(SRC)
    af = cmd[cmd.index("-af") + 1]
    assert "noise=-32.0dB" in af
    assert "d=0.35" in af


def test_filmstrip_samples_rather_than_dumping_frames():
    cmd = media.filmstrip_cmd(SRC, Path("/tmp/f-%04d.jpg"), every_seconds=5, width=320)
    vf = cmd[cmd.index("-vf") + 1]
    assert "fps=1/5" in vf
    assert "scale=320:-2" in vf


# --------------------------------------------------------------------------
# probe parsing
# --------------------------------------------------------------------------

PROBE_JSON = """
{
  "streams": [
    {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080,
     "avg_frame_rate": "30000/1001", "duration": "3612.5"},
    {"codec_type": "audio", "codec_name": "aac"}
  ],
  "format": {"duration": "3612.5", "size": "4294967296"}
}
"""


def test_parse_probe_extracts_geometry_and_fps():
    info = media.parse_probe(PROBE_JSON, SRC)
    assert (info.width, info.height) == (1920, 1080)
    assert info.fps == pytest.approx(29.97, abs=0.01)
    assert info.duration == pytest.approx(3612.5)
    assert info.has_audio
    assert not info.is_vertical


def test_parse_probe_falls_back_to_container_duration():
    """Some MKVs carry duration only on the container, not the stream."""
    raw = PROBE_JSON.replace(', "duration": "3612.5"},', "},", 1)
    assert media.parse_probe(raw, SRC).duration == pytest.approx(3612.5)


def test_parse_probe_rejects_audio_only_input():
    raw = '{"streams": [{"codec_type": "audio", "codec_name": "aac"}], "format": {}}'
    with pytest.raises(ValueError, match="no video stream"):
        media.parse_probe(raw, SRC)


def test_silent_source_is_flagged_not_crashed():
    """Screen recordings with no audio track must survive ingest."""
    raw = """{"streams": [{"codec_type": "video", "codec_name": "h264",
              "width": 1080, "height": 1920, "avg_frame_rate": "30/1",
              "duration": "10"}], "format": {"duration": "10", "size": "100"}}"""
    info = media.parse_probe(raw, SRC)
    assert info.has_audio is False
    assert info.is_vertical


def test_unknown_frame_rate_does_not_raise():
    raw = PROBE_JSON.replace('"30000/1001"', '"0/0"')
    assert media.parse_probe(raw, SRC).fps == 0.0


# --------------------------------------------------------------------------
# stderr parsing
# --------------------------------------------------------------------------

SILENCE_STDERR = """
[silencedetect @ 0x1] silence_start: 12.4
[silencedetect @ 0x1] silence_end: 13.9 | silence_duration: 1.5
[silencedetect @ 0x1] silence_start: 40.0
[silencedetect @ 0x1] silence_end: 41.2 | silence_duration: 1.2
"""


def test_parse_silence_pairs_starts_with_ends():
    assert media.parse_silence(SILENCE_STDERR) == [(12.4, 13.9), (40.0, 41.2)]


def test_unterminated_silence_span_is_dropped():
    """ffmpeg omits the final silence_end when a file ends in silence."""
    truncated = SILENCE_STDERR.rstrip().rsplit("\n", 1)[0]
    assert media.parse_silence(truncated) == [(12.4, 13.9)]


def test_parse_scenes_dedupes_and_sorts():
    stderr = (
        "[Parsed_showinfo_1 @ 0x1] n:0 pts_time:8.9 ...\n"
        "[Parsed_showinfo_1 @ 0x1] n:1 pts_time:2.5 ...\n"
        "[Parsed_showinfo_1 @ 0x1] n:2 pts_time:8.9 ...\n"
    )
    assert media.parse_scenes(stderr) == [2.5, 8.9]


def test_parsers_return_empty_on_garbage():
    """Detect filters vary across builds; a bad parse must not crash ingest."""
    assert media.parse_silence("Segmentation fault") == []
    assert media.parse_scenes("") == []
