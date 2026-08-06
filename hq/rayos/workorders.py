"""Work orders -- the universal artifact.

Every unit of work in the system is one of these, whatever produced it: a
nightly market scan, a reply to a lead, a listing campaign, a video render.
That uniformity is what makes the dashboard honest -- "results" is an
aggregation over work orders with real costs and real outcomes, not a
hand-maintained number.

The state machine is small on purpose::

    queued -> claimed -> running -> review -> done
                  |         |         |
                  +---------+---------+--> failed
                            |
                            +--> blocked (awaiting approval) -> running

``blocked`` is the interesting state. An APPROVE-tier action does not fail
and does not silently proceed: it parks, tells Ray, and waits. A work order
sitting in ``blocked`` for two days is a visible, queryable fact rather than
a message someone missed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from .policy import ApprovalToken, Decision, Tier, authorize


class State(str, Enum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    REVIEW = "review"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


#: Legal moves. Anything not listed is a bug in the caller, and raising is
#: better than a silent no-op -- a work order that quietly refuses to advance
#: is the hardest kind of stall to diagnose.
TRANSITIONS: dict[State, frozenset[State]] = {
    State.QUEUED: frozenset({State.CLAIMED, State.FAILED}),
    State.CLAIMED: frozenset({State.RUNNING, State.BLOCKED, State.FAILED, State.QUEUED}),
    State.RUNNING: frozenset({State.REVIEW, State.BLOCKED, State.DONE, State.FAILED}),
    State.REVIEW: frozenset({State.DONE, State.FAILED, State.RUNNING}),
    State.BLOCKED: frozenset({State.RUNNING, State.FAILED}),
    State.DONE: frozenset(),
    State.FAILED: frozenset({State.QUEUED}),  # retry re-queues
}

TERMINAL = frozenset({State.DONE, State.FAILED})


class IllegalTransition(RuntimeError):
    pass


@dataclass
class Cost:
    """What the work order consumed. Aggregated into the KPI ledger."""

    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    seconds: float = 0.0

    def add(self, other: "Cost") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.usd += other.usd
        self.seconds += other.seconds


@dataclass
class WorkOrder:
    """One unit of work, with its whole life recorded on it."""

    role: str                      # "concierge", "buyer_specialist", ...
    action_class: str              # keys into policy.ACTION_TIERS
    subject_id: str                # person_id, listing_id, campaign_id
    summary: str = ""
    state: State = State.QUEUED
    tier: Tier | None = None
    plan: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    result: str | None = None
    error: str | None = None
    cost: Cost = field(default_factory=Cost)
    parent_id: str | None = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = 0.0
    history: list[tuple[float, State, str]] = field(default_factory=list)

    # -- state machine ---------------------------------------------------
    def transition(self, new_state: State, *, now: float, note: str = "") -> None:
        allowed = TRANSITIONS[self.state]
        if new_state not in allowed:
            raise IllegalTransition(
                f"{self.id[:8]}: {self.state.value} -> {new_state.value} "
                f"is not legal (allowed: {sorted(s.value for s in allowed) or 'none'})"
            )
        self.state = new_state
        self.history.append((now, new_state, note))

    def note(self, text: str) -> None:
        self.decisions.append(text)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL

    # -- the approval handshake ------------------------------------------
    def start(
        self,
        *,
        now: float,
        token: ApprovalToken | None = None,
        ledger=None,
        inbound_auto: bool | None = None,
    ) -> Decision:
        """Claim and start, or park in ``blocked`` awaiting approval.

        Returns the :class:`~rayos.policy.Decision` either way, so the caller
        can put its reason in front of Ray rather than inventing one.
        """
        kwargs = {}
        if inbound_auto is not None:
            kwargs["inbound_auto"] = inbound_auto
        decision = authorize(
            action_class=self.action_class,
            subject_id=self.subject_id,
            now=now,
            token=token,
            ledger=ledger,
            **kwargs,
        )
        self.tier = decision.tier

        if self.state is State.QUEUED:
            self.transition(State.CLAIMED, now=now, note="claimed")

        if decision.allowed:
            self.transition(State.RUNNING, now=now, note=decision.reason)
        else:
            self.transition(State.BLOCKED, now=now, note=decision.reason)
        return decision

    def finish(self, result: str, *, now: float, needs_review: bool = False) -> None:
        if needs_review:
            self.transition(State.REVIEW, now=now, note="awaiting review")
        self.result = result
        self.transition(State.DONE, now=now, note="done")

    def fail(self, error: str, *, now: float) -> None:
        self.error = error
        self.transition(State.FAILED, now=now, note=error)


@dataclass
class WorkOrderQueue:
    """A minimal in-memory queue with the semantics the real table needs.

    The box uses Postgres with ``SELECT ... FOR UPDATE SKIP LOCKED``; this
    exists so the orchestration logic above it can be tested without one.
    """

    orders: dict[str, WorkOrder] = field(default_factory=dict)

    def submit(self, order: WorkOrder) -> WorkOrder:
        self.orders[order.id] = order
        return order

    def claim_next(self, *, role: str | None = None) -> WorkOrder | None:
        for order in self.orders.values():
            if order.state is not State.QUEUED:
                continue
            if role is not None and order.role != role:
                continue
            return order
        return None

    def blocked(self) -> list[WorkOrder]:
        """Everything waiting on Ray. This is the Telegram Decision Queue."""
        return [o for o in self.orders.values() if o.state is State.BLOCKED]

    def stalled(self, *, now: float, older_than_seconds: float) -> list[WorkOrder]:
        """Non-terminal orders whose last movement is older than the cutoff.

        Feeds the "failing automations" panel. An order with no history at
        all is judged by its creation time, so a queue that never started
        draining still shows up.
        """
        out = []
        for order in self.orders.values():
            if order.is_terminal:
                continue
            last = order.history[-1][0] if order.history else order.created_at
            if now - last > older_than_seconds:
                out.append(order)
        return out

    def cost_total(self) -> Cost:
        total = Cost()
        for order in self.orders.values():
            total.add(order.cost)
        return total
