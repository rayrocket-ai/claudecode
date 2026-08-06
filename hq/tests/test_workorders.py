import pytest

from rayos.policy import Tier, TokenLedger, mint_from_telegram_callback
from rayos.workorders import (
    Cost,
    IllegalTransition,
    State,
    WorkOrder,
    WorkOrderQueue,
)

RAY = 42
ALLOWED = frozenset({RAY})
NOW = 1000.0


def order(action="draft_message", subject="lead-1"):
    return WorkOrder(
        role="concierge", action_class=action, subject_id=subject, created_at=NOW
    )


def test_auto_action_runs_immediately():
    wo = order("draft_message")
    decision = wo.start(now=NOW)
    assert decision.allowed
    assert wo.state is State.RUNNING
    assert wo.tier is Tier.AUTO


def test_approve_action_parks_in_blocked_instead_of_failing():
    wo = order("send_offer")
    decision = wo.start(now=NOW)
    assert not decision.allowed
    # The distinction that matters: it waits, visibly. It does not fail, and
    # it certainly does not proceed.
    assert wo.state is State.BLOCKED
    assert wo.error is None


def test_blocked_order_resumes_with_a_token():
    wo = order("send_offer")
    wo.start(now=NOW)
    assert wo.state is State.BLOCKED

    token = mint_from_telegram_callback(
        action_class="send_offer", subject_id="lead-1", approver_id=RAY,
        authorized_ids=ALLOWED, now=NOW + 5, nonce="n1",
    )
    decision = wo.start(now=NOW + 6, token=token, ledger=TokenLedger())
    assert decision.allowed
    assert wo.state is State.RUNNING


def test_unknown_action_blocks():
    wo = order("teleport_the_client")
    wo.start(now=NOW)
    assert wo.state is State.BLOCKED


def test_illegal_transition_raises_rather_than_silently_stalling():
    wo = order()
    with pytest.raises(IllegalTransition):
        wo.transition(State.DONE, now=NOW)


def test_done_is_terminal():
    wo = order()
    wo.start(now=NOW)
    wo.finish("sent", now=NOW + 1)
    assert wo.is_terminal
    with pytest.raises(IllegalTransition):
        wo.transition(State.RUNNING, now=NOW + 2)


def test_failed_can_be_requeued():
    wo = order()
    wo.start(now=NOW)
    wo.fail("timeout", now=NOW + 1)
    assert wo.state is State.FAILED
    wo.transition(State.QUEUED, now=NOW + 2, note="retry")
    assert wo.state is State.QUEUED


def test_history_records_every_move():
    wo = order()
    wo.start(now=NOW)
    wo.finish("done", now=NOW + 3)
    states = [h[1] for h in wo.history]
    assert states == [State.CLAIMED, State.RUNNING, State.DONE]


# -- the queue ------------------------------------------------------------

def test_blocked_list_is_the_decision_queue():
    queue = WorkOrderQueue()
    safe = queue.submit(order("draft_message"))
    risky = queue.submit(order("send_offer", subject="lead-2"))
    safe.start(now=NOW)
    risky.start(now=NOW)

    blocked = queue.blocked()
    assert [o.id for o in blocked] == [risky.id]


def test_claim_next_respects_role():
    queue = WorkOrderQueue()
    queue.submit(WorkOrder(role="media", action_class="draft_content",
                           subject_id="l1", created_at=NOW))
    assert queue.claim_next(role="concierge") is None
    assert queue.claim_next(role="media") is not None


def test_stalled_uses_creation_time_when_nothing_ever_happened():
    queue = WorkOrderQueue()
    queue.submit(order())
    # A queue that never started draining must still show up as stalled.
    assert queue.stalled(now=NOW + 100, older_than_seconds=60)


def test_stalled_ignores_terminal_orders():
    queue = WorkOrderQueue()
    wo = queue.submit(order())
    wo.start(now=NOW)
    wo.finish("ok", now=NOW + 1)
    assert queue.stalled(now=NOW + 10_000, older_than_seconds=60) == []


def test_costs_aggregate():
    queue = WorkOrderQueue()
    for _ in range(3):
        wo = queue.submit(order())
        wo.cost.add(Cost(input_tokens=100, output_tokens=50, usd=0.01))
    total = queue.cost_total()
    assert total.input_tokens == 300
    assert total.output_tokens == 150
    assert round(total.usd, 4) == 0.03
