from rayos.checklists import (
    CHECKLISTS,
    DAY,
    EIGHT_BY_EIGHT,
    PRECON_WORKSHEET,
    PRE_CLOSING,
    THIRTY_THREE_TOUCH,
    fan_out,
    hard_deadlines,
)

ANCHOR = 1_700_000_000.0


def test_eight_by_eight_has_eight_touches():
    assert len(EIGHT_BY_EIGHT) == 8


def test_eight_by_eight_front_loads_the_first_week():
    tasks = fan_out(EIGHT_BY_EIGHT, person_id="p1", anchor=ANCHOR)
    first_week = [t for t in tasks if t.due_at <= ANCHOR + 7 * DAY]
    # Three touches in week one. A lead that hears nothing for six days has
    # already formed an opinion about how attentive we are.
    assert len(first_week) == 3


def test_thirty_three_touch_has_exactly_thirty_three():
    # The number is the promise. A 33-touch that generates 24 is drift that
    # takes years to notice, so it is asserted rather than trusted.
    assert len(THIRTY_THREE_TOUCH) == 33


def test_thirty_three_touch_spans_a_year():
    tasks = fan_out(THIRTY_THREE_TOUCH, person_id="p1", anchor=ANCHOR)
    span = max(t.due_at for t in tasks) - ANCHOR
    assert 360 * DAY <= span <= 370 * DAY


def test_checklist_keys_are_unique_within_a_checklist():
    for checklist in CHECKLISTS.values():
        keys = [i.key for i in checklist.items]
        assert len(set(keys)) == len(keys), checklist.key


def test_fan_out_dates_from_the_anchor():
    tasks = fan_out(PRECON_WORKSHEET, person_id="p1", anchor=ANCHOR)
    rescission = next(t for t in tasks if t.key.endswith("rescission_deadline"))
    assert rescission.due_at == ANCHOR + 10 * DAY


def test_rescission_deadline_is_hard():
    tasks = fan_out(PRECON_WORKSHEET, person_id="p1", anchor=ANCHOR)
    rescission = next(t for t in tasks if t.key.endswith("rescission_deadline"))
    assert rescission.hard_deadline


def test_hard_deadlines_are_extractable_and_sorted():
    tasks = fan_out(PRECON_WORKSHEET, person_id="p1", anchor=ANCHOR)
    hard = hard_deadlines(tasks)
    assert hard
    assert all(t.hard_deadline for t in hard)
    assert hard == sorted(hard, key=lambda t: t.due_at)


def test_negative_offsets_run_backwards_from_the_anchor():
    # Pre-closing items are anchored on the closing date, so "confirm
    # financing" lands three weeks BEFORE it, not after.
    tasks = fan_out(PRE_CLOSING, person_id="p1", anchor=ANCHOR)
    lender = next(t for t in tasks if t.key.endswith("lender_check"))
    assert lender.due_at == ANCHOR - 21 * DAY


def test_tasks_carry_the_person_and_the_checklist():
    tasks = fan_out(PRECON_WORKSHEET, person_id="buyer-7", anchor=ANCHOR)
    assert all(t.person_id == "buyer-7" for t in tasks)
    assert all(t.checklist == "precon_worksheet" for t in tasks)


def test_owner_override_routes_a_whole_checklist_to_one_person():
    tasks = fan_out(
        PRECON_WORKSHEET, person_id="p1", anchor=ANCHOR, owner_override="ray"
    )
    assert {t.owner for t in tasks} == {"ray"}
