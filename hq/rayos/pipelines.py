"""The three pipelines, as data.

Buyer 16 stages, Seller 15, Recruiting 13 -- exactly as frozen in
``hq/CRM-DATA-DICTIONARY.md``. Keeping them as data rather than as prompt
text is the E-Myth point of the whole system: the process is a documented
artifact that can be versioned, diffed, and improved, not something each
agent re-remembers slightly differently.

``max_idle`` is the quiet workhorse here. Every stage answers "how long may
a person sit here with nothing happening?", and the sweep in
:func:`idle_breaches` turns that into a list of leads going cold. New Lead
gets 120 seconds because speed-to-lead is the single metric with the most
leverage in the whole practice; Past Client gets no cap at all because it is
a home, not a waiting room -- it has a cadence instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR


@dataclass(frozen=True)
class Stage:
    number: int
    key: str
    name: str
    entry: str
    exit: str
    owner: str                      # "concierge" | "buyer_specialist" | ...
    max_idle: float | None = None   # seconds; None = governed by a cadence
    cadence: str | None = None      # key into checklists.CADENCES
    hard_deadline: bool = False     # missing this one has legal consequences


@dataclass(frozen=True)
class Pipeline:
    key: str
    name: str
    stages: tuple[Stage, ...]
    #: Moves that are legal but not "forward one" -- each is a real thing
    #: that happens in practice, named so nobody has to guess.
    extra_edges: frozenset[tuple[str, str]] = frozenset()
    #: Stages a nurtured lead may re-enter directly when they warm up.
    reentry_from_nurture: frozenset[str] = frozenset()
    nurture_key: str = "nurture"
    #: Stages that sit *beside* the main sequence rather than inside it.
    #: Nurture is numbered in the middle of the pipeline because that is
    #: where it belongs in the CRM's stage list, but a qualified lead's next
    #: step is a booked consultation, not nurture -- so "forward one" is
    #: computed over the main sequence with branches removed. Without this,
    #: every pipeline would force its leads through the parking lot.
    branch_keys: frozenset[str] = frozenset({"nurture"})

    def __post_init__(self) -> None:
        numbers = [s.number for s in self.stages]
        if numbers != list(range(1, len(self.stages) + 1)):
            raise ValueError(f"{self.key}: stage numbers must be 1..n, contiguous")
        keys = [s.key for s in self.stages]
        if len(set(keys)) != len(keys):
            raise ValueError(f"{self.key}: duplicate stage keys")

    def stage(self, key: str) -> Stage:
        for s in self.stages:
            if s.key == key:
                return s
        raise KeyError(f"{self.key} has no stage {key!r}")

    @property
    def main_sequence(self) -> tuple[Stage, ...]:
        """The linear path, branches removed."""
        return tuple(s for s in self.stages if s.key not in self.branch_keys)

    def next_stage(self, key: str) -> Stage | None:
        """The next step along the main path; ``None`` for branches and the end."""
        stage = self.stage(key)
        if stage.key in self.branch_keys:
            return None
        sequence = self.main_sequence
        index = sequence.index(stage)
        if index + 1 >= len(sequence):
            return None
        return sequence[index + 1]

    def can_transition(self, frm: str, to: str) -> bool:
        """Is this move legal?

        Forward by one along the main sequence is always legal. Falling back
        to nurture is legal from any stage before the deal is firm -- after
        firm there is a contract, and a contract does not go back to "maybe
        later". Re-entry from nurture is limited to the early stages, because
        a re-engaged lead restarts qualification rather than resuming a
        showing tour half-finished.
        """
        source, target = self.stage(frm), self.stage(to)
        if source.key == target.key:
            return False
        if (frm, to) in self.extra_edges:
            return True
        nxt = self.next_stage(frm)
        if nxt is not None and nxt.key == target.key:
            return True
        if target.key == self.nurture_key:
            firm = next((s for s in self.stages if s.key == "firm"), None)
            if firm is None or source.number < firm.number:
                return True
        if frm == self.nurture_key and to in self.reentry_from_nurture:
            return True
        return False

    def assert_transition(self, frm: str, to: str) -> None:
        if not self.can_transition(frm, to):
            raise ValueError(f"{self.key}: {frm} -> {to} is not a legal move")


# ---------------------------------------------------------------------------
# Buyer -- 16 stages
# ---------------------------------------------------------------------------

BUYER = Pipeline(
    key="buyer",
    name="Buyer",
    stages=(
        Stage(1, "new_lead", "New Lead",
              "intake row created", "first contact attempt logged",
              "concierge", max_idle=2 * MINUTE),
        Stage(2, "contact_attempted", "Contact Attempted",
              "attempt logged, no reply", "two-way reply",
              "concierge", max_idle=1 * DAY),
        Stage(3, "in_qualification", "In Qualification",
              "two-way conversation live",
              "intent, timeline, location, budget, financing captured",
              "concierge", max_idle=2 * DAY),
        Stage(4, "qualified", "Qualified",
              "qualification complete, timeline <= 12 months",
              "consult booked or moved to nurture",
              "concierge", max_idle=3 * DAY),
        Stage(5, "nurture", "Nurture",
              "not ready, or unresponsive", "re-engagement reply",
              "concierge", cadence="eight_by_eight"),
        Stage(6, "consult_booked", "Consult Booked",
              "buyer consultation on the calendar", "consultation held",
              "buyer_specialist", cadence="appointment_reminders"),
        Stage(7, "consult_done_bra", "Consult Done / BRA",
              "consultation held", "buyer representation agreement signed",
              "buyer_specialist", max_idle=5 * DAY),
        Stage(8, "vow_active_searching", "VOW Active - Searching",
              "BRA signed and VOW registered", "first showing requested",
              "buyer_specialist", max_idle=7 * DAY),
        Stage(9, "showing_scheduled", "Showing Scheduled",
              "showing booked in BrokerBay and Calendar", "showing completed",
              "buyer_specialist", cadence="appointment_reminders"),
        Stage(10, "actively_showing", "Actively Showing",
              "at least one showing done", "offer-prep appointment set",
              "buyer_specialist", max_idle=5 * DAY),
        Stage(11, "offer_prep", "Offer Prep",
              "offer-prep appointment held", "offer submitted",
              "buyer_specialist", max_idle=2 * DAY),
        Stage(12, "offer_submitted", "Offer Submitted",
              "offer out, irrevocability running",
              "accepted, rejected, or expired",
              "buyer_specialist", max_idle=1 * DAY, hard_deadline=True),
        Stage(13, "conditional", "Conditional",
              "offer accepted with conditions",
              "all conditions waived or fulfilled",
              "transaction_assistant", cadence="deal_conditional",
              hard_deadline=True),
        Stage(14, "firm", "Firm",
              "conditions cleared", "closing day",
              "transaction_assistant", cadence="pre_closing"),
        Stage(15, "closed", "Closed",
              "transaction closed", "post-close care complete",
              "transaction_assistant", cadence="buyer_post_close"),
        Stage(16, "past_client", "Past Client",
              "care sequence done", "permanent",
              "concierge", cadence="thirty_three_touch"),
    ),
    extra_edges=frozenset({
        # An offer that comes back rejected sends them looking again -- this
        # is the most common backward move in the whole system.
        ("offer_submitted", "actively_showing"),
        ("offer_prep", "actively_showing"),
        # Showings run in a loop until something is worth writing on.
        ("actively_showing", "showing_scheduled"),
        ("showing_scheduled", "actively_showing"),
        # Conditions can fail; the deal dies back to searching, not to firm.
        ("conditional", "actively_showing"),
    }),
    reentry_from_nurture=frozenset({"in_qualification", "qualified", "consult_booked"}),
)

# ---------------------------------------------------------------------------
# Seller -- 15 stages
# ---------------------------------------------------------------------------

SELLER = Pipeline(
    key="seller",
    name="Seller",
    stages=(
        Stage(1, "new_seller_lead", "New Seller Lead",
              "intake row created", "first contact attempt logged",
              "concierge", max_idle=2 * MINUTE),
        Stage(2, "contact_attempted", "Contact Attempted",
              "attempt logged, no reply", "two-way reply",
              "concierge", max_idle=1 * DAY),
        Stage(3, "in_qualification", "In Qualification",
              "two-way conversation live",
              "property, motivation, timeline captured",
              "concierge", max_idle=2 * DAY),
        Stage(4, "qualified_cma_prep", "Qualified - CMA Prep",
              "qualification complete", "CMA and pre-listing package ready",
              "listing_specialist", max_idle=3 * DAY),
        Stage(5, "nurture", "Nurture",
              "not ready to list", "re-engagement reply",
              "concierge", cadence="eight_by_eight"),
        Stage(6, "listing_appt_booked", "Listing Appt Booked",
              "consultation on the calendar", "appointment held",
              "listing_specialist", cadence="appointment_reminders"),
        Stage(7, "appt_done_proposal_out", "Appt Done - Proposal Out",
              "consultation held", "listing agreement signed or declined",
              "listing_specialist", max_idle=5 * DAY),
        Stage(8, "listing_signed", "Listing Signed",
              "agreement executed", "pre-market checklist complete",
              "listing_specialist", cadence="seller_pre_market"),
        Stage(9, "pre_market_prep", "Pre-Market Prep",
              "photos, staging, media, campaign in motion", "live on MLS",
              "listing_specialist", max_idle=10 * DAY),
        Stage(10, "active_on_market", "Active on Market",
              "listed", "offer registered",
              "listing_specialist", cadence="listing_active"),
        Stage(11, "offers_received", "Offer(s) Received",
              "offer registered", "acceptance",
              "listing_specialist", max_idle=1 * DAY, hard_deadline=True),
        Stage(12, "conditional", "Conditional",
              "accepted with conditions", "conditions cleared",
              "transaction_assistant", cadence="deal_conditional",
              hard_deadline=True),
        Stage(13, "firm", "Firm",
              "conditions cleared", "closing day",
              "transaction_assistant", cadence="pre_closing"),
        Stage(14, "closed", "Closed",
              "transaction closed", "post-close care complete",
              "transaction_assistant", cadence="seller_post_close"),
        Stage(15, "past_client", "Past Client",
              "care sequence done", "permanent",
              "concierge", cadence="thirty_three_touch"),
    ),
    extra_edges=frozenset({
        # Offers fall apart and the listing goes back on the market. If this
        # edge did not exist the system would strand real listings.
        ("offers_received", "active_on_market"),
        ("conditional", "active_on_market"),
        # An expired or terminated listing goes to nurture with a relist watch.
        ("active_on_market", "nurture"),
    }),
    reentry_from_nurture=frozenset(
        {"in_qualification", "qualified_cma_prep", "listing_appt_booked"}
    ),
)

# ---------------------------------------------------------------------------
# Recruiting -- 13 stages. Dormant until Phase 6; separate consent basis.
# ---------------------------------------------------------------------------

RECRUITING = Pipeline(
    key="recruiting",
    name="Agent Recruiting",
    stages=(
        Stage(1, "prospect_identified", "Prospect Identified",
              "added from research", "enrichment done",
              "operations", max_idle=7 * DAY),
        Stage(2, "researched", "Researched",
              "production and brokerage profile built", "outreach drafted",
              "operations", max_idle=5 * DAY),
        Stage(3, "outreach_approved", "Outreach Approved",
              "campaign and draft approved by Ray", "first send",
              "operations", max_idle=2 * DAY),
        Stage(4, "outreach_sent", "Outreach Sent",
              "sequence running", "reply",
              "operations", max_idle=5 * DAY),
        Stage(5, "in_conversation", "In Conversation",
              "two-way reply", "discovery call booked",
              "operations", max_idle=3 * DAY),
        Stage(6, "discovery_call_set", "Discovery Call Set",
              "call on the calendar", "call held",
              "operations", cadence="appointment_reminders"),
        Stage(7, "discovery_done", "Discovery Done",
              "call held", "decision path chosen",
              "operations", max_idle=3 * DAY),
        Stage(8, "nurture", "Nurture",
              "interested, not now", "re-engagement",
              "operations", max_idle=30 * DAY),
        Stage(9, "objections_considering", "Objections / Considering",
              "active objections", "resolved either way",
              "operations", max_idle=7 * DAY),
        Stage(10, "committed_paperwork", "Committed - Paperwork",
              "verbal yes", "application sent",
              "operations", max_idle=2 * DAY),
        Stage(11, "signed", "Signed",
              "application executed", "onboarding started",
              "operations", max_idle=2 * DAY),
        Stage(12, "onboarding", "Onboarding",
              "checklist running", "checklist complete",
              "operations", max_idle=7 * DAY),
        Stage(13, "onboarded_producing", "Onboarded - Producing",
              "fully active", "permanent",
              "operations", max_idle=90 * DAY),
    ),
    extra_edges=frozenset({
        ("objections_considering", "discovery_call_set"),
        ("in_conversation", "nurture"),
    }),
    reentry_from_nurture=frozenset({"in_conversation", "discovery_call_set"}),
)

PIPELINES: dict[str, Pipeline] = {p.key: p for p in (BUYER, SELLER, RECRUITING)}


@dataclass(frozen=True)
class LeadPosition:
    """Where one person sits, and when they last moved."""

    person_id: str
    pipeline: str
    stage: str
    last_activity_at: float
    owner: str | None = None


@dataclass(frozen=True)
class IdleBreach:
    position: LeadPosition
    stage: Stage
    idle_seconds: float
    over_by: float


def idle_breaches(
    positions: list[LeadPosition], *, now: float
) -> list[IdleBreach]:
    """Every lead sitting past its stage's patience, worst first.

    This is the sweep behind "who needs a response now" on the dashboard and
    behind the escalation alerts. Sorting by how far over the limit they are,
    rather than by absolute idle time, keeps a two-minute new-lead breach
    above a stale seven-day one -- which is the correct urgency ordering,
    because the new lead is still winnable.
    """
    out: list[IdleBreach] = []
    for pos in positions:
        pipeline = PIPELINES.get(pos.pipeline)
        if pipeline is None:
            continue
        stage = pipeline.stage(pos.stage)
        if stage.max_idle is None:
            continue
        idle = now - pos.last_activity_at
        if idle > stage.max_idle:
            out.append(IdleBreach(pos, stage, idle, idle - stage.max_idle))
    out.sort(key=lambda b: b.over_by / b.stage.max_idle, reverse=True)
    return out
