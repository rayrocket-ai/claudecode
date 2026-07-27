"""Tests for clip parsing and ranking."""

import pytest

from reelforge.core.highlights import Clip, Drop, parse, rank

BAND = (15.0, 59.0)


def clip(start, end, **scores) -> Clip:
    base = {"hook": 5, "self_contained": 5, "payoff": 5, "quotable": 5}
    base.update(scores)
    return Clip(start=start, end=end, scores=base)


# --------------------------------------------------------------------------
# duration
# --------------------------------------------------------------------------

def test_kept_duration_excludes_internal_drops():
    c = Clip(0.0, 30.0, drop=[Drop(5.0, 10.0, "repeat")])
    assert c.kept_duration == pytest.approx(25.0)


def test_drops_are_clamped_to_the_clip():
    """A drop the brain extended past the boundary must not over-subtract."""
    c = Clip(10.0, 20.0, drop=[Drop(5.0, 15.0, "tangent")])
    assert c.kept_duration == pytest.approx(5.0)


def test_drops_outside_the_clip_are_ignored():
    c = Clip(10.0, 20.0, drop=[Drop(50.0, 60.0, "tangent")])
    assert c.kept_duration == pytest.approx(10.0)


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------

def test_hook_outweighs_the_other_dimensions():
    """Short-form attention is decided in the first second."""
    strong_hook = clip(0, 30, hook=10, self_contained=0, payoff=0, quotable=0)
    strong_rest = clip(0, 30, hook=0, self_contained=10, payoff=0, quotable=0)
    assert strong_hook.score(target_seconds=BAND) > strong_rest.score(target_seconds=BAND)


def test_a_perfect_clip_in_band_scores_full_marks():
    assert clip(0, 30, hook=10, self_contained=10, payoff=10, quotable=10) \
        .score(target_seconds=BAND) == pytest.approx(10.0)


def test_too_short_is_penalised_proportionally():
    """A brilliant 4-second clip is not a reel."""
    good = clip(0, 30, hook=10, self_contained=10, payoff=10, quotable=10)
    tiny = clip(0, 4, hook=10, self_contained=10, payoff=10, quotable=10)
    assert tiny.score(target_seconds=BAND) < good.score(target_seconds=BAND) * 0.4


def test_the_length_penalty_ramps_rather_than_cliffs():
    """A 14s clip is nearly fine; a 5s one is not. One threshold cannot say both."""
    nearly = clip(0, 14, hook=10, self_contained=10, payoff=10, quotable=10)
    far = clip(0, 5, hook=10, self_contained=10, payoff=10, quotable=10)
    assert nearly.score(target_seconds=BAND) > far.score(target_seconds=BAND) * 2


def test_over_length_is_penalised_too():
    long_clip = clip(0, 180, hook=10, self_contained=10, payoff=10, quotable=10)
    assert long_clip.score(target_seconds=BAND) < 4.0


def test_missing_scores_do_not_raise():
    assert Clip(0.0, 30.0).score(target_seconds=BAND) == 0.0


# --------------------------------------------------------------------------
# parsing -- tolerant on purpose
# --------------------------------------------------------------------------

def test_parse_reads_a_well_formed_payload():
    clips = parse({"clips": [{
        "start": 10, "end": 40, "hook": "Here is the thing",
        "why": "self contained", "emphasis": [12.5],
        "drop": [{"start": 20, "end": 22, "reason": "repeat"}],
        "scores": {"hook": 8, "self_contained": 7, "payoff": 6, "quotable": 5},
    }]})
    assert len(clips) == 1
    assert clips[0].drop[0].reason == "repeat"
    assert clips[0].emphasis == [12.5]


def test_one_malformed_clip_does_not_lose_the_others():
    """Re-running an hour of analysis over a single bad entry is unacceptable."""
    clips = parse({"clips": [
        {"start": 0, "end": 30, "scores": {}},
        {"end": 40},                                  # no start
        {"start": "x", "end": 40, "scores": {}},      # unparseable
        {"start": 50, "end": 80, "scores": {}},
    ]})
    assert len(clips) == 2


def test_reversed_and_empty_clips_are_discarded():
    assert parse({"clips": [{"start": 40, "end": 10, "scores": {}},
                            {"start": 10, "end": 10, "scores": {}}]}) == []


def test_parse_of_an_empty_payload():
    assert parse({}) == []


# --------------------------------------------------------------------------
# ranking
# --------------------------------------------------------------------------

def test_ranking_returns_the_best_first():
    clips = [clip(0, 30, hook=2), clip(100, 130, hook=9), clip(200, 230, hook=5)]
    best = rank(clips, count=3, target_seconds=BAND)
    assert best[0].start == 100


def test_overlapping_clips_are_suppressed():
    """Asked for the best moments, a model returns the same passage three times
    with slightly different boundaries. Three near-identical reels is worse
    than two distinct ones."""
    clips = [clip(10, 40, hook=9), clip(12, 42, hook=8), clip(200, 230, hook=7)]
    best = rank(clips, count=3, target_seconds=BAND)
    assert len(best) == 2
    assert {c.start for c in best} == {10, 200}


def test_suppression_respects_the_gap_setting():
    clips = [clip(0, 30, hook=9), clip(31, 61, hook=8)]
    assert len(rank(clips, count=2, target_seconds=BAND, min_gap=0.5)) == 2
    assert len(rank(clips, count=2, target_seconds=BAND, min_gap=10.0)) == 1


def test_ranking_stops_at_the_requested_count():
    clips = [clip(i * 100, i * 100 + 30, hook=9) for i in range(10)]
    assert len(rank(clips, count=3, target_seconds=BAND)) == 3


def test_ranking_an_empty_list():
    assert rank([], count=3, target_seconds=BAND) == []
