"""Tests for deterministic signal extraction."""

import pytest

from reelforge.core.analyze import Signals, parse_energy, peaks, smooth_focus


# --------------------------------------------------------------------------
# energy
# --------------------------------------------------------------------------

ASTATS = """
[Parsed_ametadata_1 @ 0x1] lavfi.astats.Overall.RMS_level=-30.000000
[Parsed_ametadata_1 @ 0x1] lavfi.astats.Overall.RMS_level=-15.000000
[Parsed_ametadata_1 @ 0x1] lavfi.astats.Overall.RMS_level=-inf
"""


def test_parse_energy_normalises_to_unit_range():
    assert parse_energy(ASTATS) == [0.5, 0.75, 0.0]


def test_digital_silence_clamps_instead_of_propagating_inf():
    """-inf would poison every downstream average."""
    assert all(v == v and v >= 0 for v in parse_energy(ASTATS))


def test_energy_clamps_positive_levels():
    assert parse_energy("RMS_level=3.0") == [1.0]


def test_parse_energy_on_silent_source():
    assert parse_energy("") == []


# --------------------------------------------------------------------------
# peaks
# --------------------------------------------------------------------------

def test_peaks_finds_energy_spikes():
    energy = [0.2] * 10 + [0.9] + [0.2] * 10
    assert peaks(energy) == [10]


def test_peaks_enforces_a_minimum_gap():
    """Adjacent loud seconds are one moment, not four."""
    energy = [0.1] * 5 + [0.9, 0.9, 0.9, 0.9] + [0.1] * 5
    assert peaks(energy, min_gap=3) == [5, 8]


def test_flat_audio_has_no_peaks():
    assert peaks([0.5] * 30, above=1.25) == []


def test_peaks_on_empty_and_all_silent():
    assert peaks([]) == []
    assert peaks([0.0] * 10) == []


# --------------------------------------------------------------------------
# focus smoothing -- what stops a reframe looking handheld
# --------------------------------------------------------------------------

def test_smoothing_rate_limits_a_jump():
    raw = [(0.0, 0.5, 0.5), (5.0, 0.9, 0.5)]
    _, x, _ = smooth_focus(raw, max_step=0.06)[1]
    assert x == pytest.approx(0.56)


def test_small_movements_pass_through_untouched():
    raw = [(0.0, 0.5, 0.5), (5.0, 0.52, 0.51)]
    assert smooth_focus(raw, max_step=0.06)[1] == (5.0, 0.52, 0.51)


def test_smoothing_converges_over_successive_frames():
    """A real move should still arrive -- just gradually."""
    raw = [(float(i), 0.5 if i == 0 else 0.9, 0.5) for i in range(20)]
    _, x, _ = smooth_focus(raw, max_step=0.06)[-1]
    assert x == pytest.approx(0.9, abs=0.01)


def test_smoothing_handles_empty_and_single():
    assert smooth_focus([]) == []
    assert len(smooth_focus([(0.0, 0.5, 0.5)])) == 1


# --------------------------------------------------------------------------
# lookups
# --------------------------------------------------------------------------

def test_focus_defaults_to_centre_when_detection_failed():
    """Holding a stale position is how a crop locks onto an empty chair."""
    assert Signals(duration=10).focus_at(5.0) == (0.5, 0.5)


def test_focus_uses_most_recent_preceding_sample():
    s = Signals(duration=30, focus=[(0.0, 0.4, 0.5), (10.0, 0.7, 0.5)])
    assert s.focus_at(9.9)[0] == pytest.approx(0.4)
    assert s.focus_at(10.1)[0] == pytest.approx(0.7)


def test_energy_lookup_is_bounds_safe():
    s = Signals(duration=3, energy=[0.1, 0.2, 0.3])
    assert s.energy_at(1.7) == 0.2
    assert s.energy_at(99) == 0.0
    assert s.energy_at(-1) == 0.0


def test_signals_survive_a_json_roundtrip():
    s = Signals(duration=12.0, silence=[(1.0, 2.0)], scenes=[3.0],
                energy=[0.1], focus=[(0.0, 0.5, 0.5)], filmstrip=["a/f-1.jpg"])
    assert Signals.from_dict(s.as_dict()).silence == [(1.0, 2.0)]
