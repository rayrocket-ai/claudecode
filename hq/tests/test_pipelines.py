import pytest

from rayos.checklists import CHECKLISTS
from rayos.pipelines import (
    BUYER,
    PIPELINES,
    RECRUITING,
    SELLER,
    LeadPosition,
    idle_breaches,
)

NOW = 1_700_000_000.0


# -- the dictionary contract ---------------------------------------------

def test_stage_counts_match_the_data_dictionary():
    assert len(BUYER.stages) == 16
    assert len(SELLER.stages) == 15
    assert len(RECRUITING.stages) == 13


def test_every_pipeline_is_contiguous_and_unique():
    # Enforced in __post_init__; this asserts construction actually ran it.
    for pipeline in PIPELINES.values():
        numbers = [s.number for s in pipeline.stages]
        assert numbers == list(range(1, len(numbers) + 1))
        assert len({s.key for s in pipeline.stages}) == len(numbers)


def test_every_stage_has_an_owner_and_a_governor():
    # A stage with neither an idle cap nor a cadence is a place leads go to
    # die quietly -- the one thing this whole design exists to prevent. This
    # invariant caught a real gap: "Offer Submitted" had a hard deadline but
    # nothing chasing the other side while irrevocability ran down.
    for pipeline in PIPELINES.values():
        for stage in pipeline.stages:
            assert stage.owner, f"{pipeline.key}:{stage.key} has no owner"
            assert stage.max_idle is not None or stage.cadence is not None, \
                f"{pipeline.key}:{stage.key} is ungoverned"


def test_every_referenced_cadence_exists():
    # A stage pointing at a cadence nobody wrote is a lead in a stage where
    # nothing will ever happen -- silently.
    for pipeline in PIPELINES.values():
        for stage in pipeline.stages:
            if stage.cadence is not None:
                assert stage.cadence in CHECKLISTS, \
                    f"{pipeline.key}:{stage.key} -> missing cadence {stage.cadence}"


def test_speed_to_lead_is_two_minutes():
    assert BUYER.stage("new_lead").max_idle == 120
    assert SELLER.stage("new_seller_lead").max_idle == 120


# -- movement -------------------------------------------------------------

def test_forward_one_is_always_legal():
    for pipeline in PIPELINES.values():
        for stage in pipeline.main_sequence[:-1]:
            nxt = pipeline.next_stage(stage.key)
            assert nxt is not None
            assert pipeline.can_transition(stage.key, nxt.key)


def test_next_stage_of_last_is_none():
    assert BUYER.next_stage("past_client") is None


def test_nurture_is_a_branch_not_a_step_in_the_line():
    # Nurture is numbered 5 because that is where it sits in the CRM's stage
    # list, but a qualified lead's next step is a booked consultation. If
    # nurture were treated as linear, every lead would be routed through the
    # parking lot on the way to an appointment.
    assert BUYER.next_stage("qualified").key == "consult_booked"
    assert BUYER.next_stage("nurture") is None
    assert "nurture" not in {s.key for s in BUYER.main_sequence}


def test_skipping_ahead_is_illegal():
    # A lead cannot jump from "new" to "firm" -- if the data says it did,
    # something upstream is wrong and should be caught, not recorded.
    assert not BUYER.can_transition("new_lead", "firm")
    with pytest.raises(ValueError):
        BUYER.assert_transition("new_lead", "firm")


def test_rejected_offer_returns_to_showing():
    assert BUYER.can_transition("offer_submitted", "actively_showing")


def test_showings_can_loop():
    assert BUYER.can_transition("actively_showing", "showing_scheduled")
    assert BUYER.can_transition("showing_scheduled", "actively_showing")


def test_anything_before_firm_can_fall_back_to_nurture():
    assert BUYER.can_transition("qualified", "nurture")
    assert BUYER.can_transition("actively_showing", "nurture")


def test_a_firm_deal_cannot_fall_back_to_nurture():
    # There is a contract. "Maybe later" is no longer a state it can occupy.
    assert not BUYER.can_transition("firm", "nurture")
    assert not BUYER.can_transition("closed", "nurture")


def test_reentry_from_nurture_restarts_qualification_not_showings():
    assert BUYER.can_transition("nurture", "in_qualification")
    assert not BUYER.can_transition("nurture", "actively_showing")


def test_a_stage_cannot_transition_to_itself():
    assert not BUYER.can_transition("qualified", "qualified")


def test_expired_listing_goes_to_nurture():
    assert SELLER.can_transition("active_on_market", "nurture")


def test_unknown_stage_raises():
    with pytest.raises(KeyError):
        BUYER.stage("no_such_stage")


# -- the idle sweep -------------------------------------------------------

def test_idle_breach_detected():
    positions = [LeadPosition("p1", "buyer", "new_lead", NOW - 300)]
    breaches = idle_breaches(positions, now=NOW)
    assert len(breaches) == 1
    assert breaches[0].over_by == 180


def test_stage_within_its_limit_is_not_flagged():
    positions = [LeadPosition("p1", "buyer", "new_lead", NOW - 60)]
    assert idle_breaches(positions, now=NOW) == []


def test_cadence_stages_are_never_idle_breaches():
    positions = [LeadPosition("p1", "buyer", "past_client", NOW - 10_000_000)]
    assert idle_breaches(positions, now=NOW) == []


def test_urgency_is_relative_not_absolute():
    # A new lead 10 minutes cold (5x over a 2-minute limit) outranks a
    # 9-day-idle qualified lead (2x over 3 days), because it is still winnable.
    positions = [
        LeadPosition("stale", "buyer", "qualified", NOW - 9 * 86400),
        LeadPosition("fresh", "buyer", "new_lead", NOW - 600),
    ]
    breaches = idle_breaches(positions, now=NOW)
    assert [b.position.person_id for b in breaches] == ["fresh", "stale"]


def test_unknown_pipeline_is_skipped_not_crashed():
    positions = [LeadPosition("p1", "not_a_pipeline", "whatever", NOW - 99999)]
    assert idle_breaches(positions, now=NOW) == []
