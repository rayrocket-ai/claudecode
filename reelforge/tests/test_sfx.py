"""Synthesised sound effects and the audio mix graph."""

import wave

import numpy as np
import pytest

from core.edl import Audio
from core.render import sfx
from core.render.filters import AudioTrack, audio_mix_graph


# --------------------------------------------------------------------------
# synthesis
# --------------------------------------------------------------------------

def test_every_catalogued_effect_synthesises():
    for name in sfx.CATALOGUE:
        samples = sfx.synth(name)
        assert samples.ndim == 2 and samples.shape[1] == 2, name
        assert samples.shape[0] > 100, name


def test_unknown_effect_raises_and_lists_the_options():
    with pytest.raises(sfx.UnknownEffect, match="whoosh"):
        sfx.synth("airhorn")


def test_effects_are_deterministic():
    # The cache key is the name alone, which is only sound if synthesis is
    # reproducible. A re-render must never quietly change the audio.
    assert np.array_equal(sfx.synth("whoosh"), sfx.synth("whoosh"))
    assert np.array_equal(sfx.synth("riser"), sfx.synth("riser"))


def test_effects_are_normalised_and_never_clip():
    for name in sfx.CATALOGUE:
        peak = float(np.max(np.abs(sfx.synth(name))))
        assert 0.8 < peak <= 1.0, f"{name} peaked at {peak}"


def test_durations_match_the_catalogue():
    for name, effect in sfx.CATALOGUE.items():
        got = sfx.synth(name).shape[0] / sfx.SAMPLE_RATE
        assert abs(got - effect.duration) < 0.01, name


def test_effects_decay_rather_than_ending_abruptly():
    # A sound that stops mid-amplitude clicks. Every effect must be quiet by
    # its final samples.
    for name in sfx.CATALOGUE:
        samples = sfx.synth(name)
        tail = np.max(np.abs(samples[-int(0.005 * sfx.SAMPLE_RATE):]))
        assert tail < 0.2, f"{name} ends at {tail:.3f}"


def test_riser_builds_towards_its_end():
    samples = np.abs(sfx.synth("riser")).mean(axis=1)
    third = samples.shape[0] // 3
    assert samples[:third].mean() < samples[-third:].mean() * 0.5


def test_whoosh_directions_differ():
    assert not np.array_equal(sfx.synth("whoosh"), sfx.synth("whoosh_down"))


# --------------------------------------------------------------------------
# caching to disk
# --------------------------------------------------------------------------

def test_render_writes_a_valid_stereo_wav(tmp_path):
    path = sfx.render("pop", tmp_path)
    assert path.exists()
    with wave.open(str(path)) as handle:
        assert handle.getnchannels() == 2
        assert handle.getframerate() == sfx.SAMPLE_RATE
        assert handle.getsampwidth() == 2
        assert handle.getnframes() > 100


def test_render_is_cached(tmp_path):
    first = sfx.render("click", tmp_path)
    before = first.stat().st_mtime_ns
    again = sfx.render("click", tmp_path)
    assert again == first
    assert again.stat().st_mtime_ns == before


def test_cache_key_carries_the_synth_version(tmp_path):
    # Otherwise a change to the formula would only reach cold caches.
    assert f"v{sfx.SYNTH_VERSION}" in sfx.cache_path(tmp_path, "pop").name


def test_no_partial_file_is_left_behind(tmp_path):
    sfx.render("ding", tmp_path)
    assert list((tmp_path / "sfx").glob("*.partial")) == []


# --------------------------------------------------------------------------
# placement
# --------------------------------------------------------------------------

def test_covering_effects_lead_the_moment_they_mark():
    # A whoosh placed exactly on a cut is heard just after it, which reads as
    # a mistake. It has to start early.
    assert sfx.CATALOGUE["whoosh"].lead < 0
    assert sfx.CATALOGUE["riser"].lead < -1.0


def test_a_plain_cut_gets_no_effect():
    # Restraint is the default: a whoosh on every cut is how an edit starts
    # sounding like a template.
    assert sfx.suggest_for_transition("cut") is None
    assert sfx.suggest_for_transition("fade") is None
    assert sfx.suggest_for_transition("whip") == "whoosh"


# --------------------------------------------------------------------------
# the mix graph
# --------------------------------------------------------------------------

def test_speech_alone_is_just_normalised():
    _, steps, label = audio_mix_graph(
        first_index=1, tracks=[], audio=Audio(), duration=10.0, loudness=-14.0
    )
    assert label == "aout"
    assert len(steps) == 1 and "loudnorm" in steps[0]
    assert not any("amix" in s for s in steps)


def test_music_is_ducked_against_the_speech():
    tracks = [AudioTrack("/m.mp3", "music", 0.0, -18.0)]
    inputs, steps, _ = audio_mix_graph(
        first_index=1, tracks=tracks, audio=Audio(duck=True),
        duration=30.0, loudness=-14.0,
    )
    graph = ";".join(steps)
    assert "asplit=2[sp][duckkey]" in graph
    assert "sidechaincompress" in graph
    # Looped at the input so a short bed covers a long video.
    assert inputs[0][:2] == ["-stream_loop", "-1"]


def test_ducking_can_be_turned_off():
    tracks = [AudioTrack("/m.mp3", "music", 0.0, -18.0)]
    _, steps, _ = audio_mix_graph(
        first_index=1, tracks=tracks, audio=Audio(duck=False),
        duration=30.0, loudness=-14.0,
    )
    graph = ";".join(steps)
    assert "sidechaincompress" not in graph
    assert "asplit" not in graph


def test_mix_never_normalises_away_the_dialogue():
    # amix normalise would drop speech several dB the moment music appeared,
    # making a scored video quieter than an unscored one for no visible reason.
    tracks = [AudioTrack("/m.mp3", "music", 0.0, -18.0)]
    _, steps, _ = audio_mix_graph(
        first_index=1, tracks=tracks, audio=Audio(), duration=30.0, loudness=-14.0
    )
    amix = next(s for s in steps if "amix" in s)
    assert "normalize=0" in amix
    assert "duration=first" in amix       # audio stays as long as the picture


def test_effects_are_delayed_to_their_position():
    tracks = [AudioTrack("/fx.wav", "sfx", 2.5, -6.0)]
    _, steps, _ = audio_mix_graph(
        first_index=1, tracks=tracks, audio=Audio(), duration=30.0, loudness=-14.0
    )
    assert "adelay=2500|2500" in ";".join(steps)


def test_an_effect_starting_before_zero_is_trimmed_not_delayed():
    # A riser that must peak on the first frame is already running when the
    # video starts; delaying it by a negative amount is not a thing.
    tracks = [AudioTrack("/fx.wav", "sfx", -0.8, -6.0)]
    _, steps, _ = audio_mix_graph(
        first_index=1, tracks=tracks, audio=Audio(), duration=30.0, loudness=-14.0
    )
    graph = ";".join(steps)
    assert "atrim=start=0.800" in graph
    assert "adelay" not in graph


def test_input_indices_follow_the_video_inputs():
    tracks = [AudioTrack("/m.mp3", "music", 0.0, -18.0),
              AudioTrack("/fx.wav", "sfx", 1.0, -6.0)]
    _, steps, _ = audio_mix_graph(
        first_index=4, tracks=tracks, audio=Audio(), duration=30.0, loudness=-14.0
    )
    graph = ";".join(steps)
    assert "[4:a]" in graph and "[5:a]" in graph
