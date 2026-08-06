"""The lifecycle checklist library -- a system for every scenario.

This is the operations manual as executable data. Each checklist fans out
into real tasks with owners and due dates when its trigger fires, which is
what makes the difference between a practice that *has* a post-close process
and one that *runs* one.

Two things here earn their complexity:

**Hard deadlines.** Most items are "should happen around then". A few --
the pre-construction 10-day rescission window above all -- are statutory,
and missing one is not a service failure but a legal one. ``hard_deadline``
marks those, and the reminder engine escalates them differently: they alert
early, they alert again, and they alert a human rather than only writing a
task nobody opens.

**Counted cadences.** The 33-touch program is not "some contact, monthly-ish";
it is thirty-three touches in a year, and a test in this repo asserts that
number, because a 33-touch that quietly generates 24 touches is the kind of
drift that takes three years to notice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DAY = 24 * 3600


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    title: str
    offset_days: float          # from the anchor event
    owner: str
    hard_deadline: bool = False
    note: str = ""


@dataclass(frozen=True)
class Checklist:
    key: str
    name: str
    trigger: str                # the event that fires the fan-out
    items: tuple[ChecklistItem, ...]

    def __len__(self) -> int:
        return len(self.items)


@dataclass(frozen=True)
class Task:
    """One fanned-out task, ready for the CRM and the reminder engine."""

    key: str
    title: str
    owner: str
    due_at: float
    person_id: str
    checklist: str
    hard_deadline: bool = False
    note: str = ""


def fan_out(
    checklist: Checklist, *, person_id: str, anchor: float, owner_override: str | None = None
) -> list[Task]:
    """Turn a checklist into dated tasks hung off an anchor event."""
    return [
        Task(
            key=f"{checklist.key}:{item.key}",
            title=item.title,
            owner=owner_override or item.owner,
            due_at=anchor + item.offset_days * DAY,
            person_id=person_id,
            checklist=checklist.key,
            hard_deadline=item.hard_deadline,
            note=item.note,
        )
        for item in checklist.items
    ]


# ---------------------------------------------------------------------------
# Pre-construction -- the one with statutory teeth
# ---------------------------------------------------------------------------

PRECON_WORKSHEET = Checklist(
    key="precon_worksheet",
    name="Pre-construction: worksheet to firm",
    trigger="worksheet_submitted",
    items=(
        ChecklistItem("confirm_receipt", "Confirm worksheet receipt with the builder",
                      0, "buyer_specialist"),
        ChecklistItem("allocation_followup", "Chase allocation status",
                      3, "buyer_specialist"),
        ChecklistItem("review_agreement", "Review agreement of purchase and sale with the buyer",
                      0, "buyer_specialist",
                      note="Anchored on allocation, re-anchored when the APS arrives."),
        ChecklistItem("lawyer_review", "Send APS to the buyer's lawyer for review",
                      1, "transaction_assistant", hard_deadline=True,
                      note="Must complete inside the rescission window."),
        ChecklistItem("rescission_midpoint", "Rescission check-in: 5 days used, 5 remain",
                      5, "buyer_specialist", hard_deadline=True),
        ChecklistItem("rescission_deadline", "10-day rescission period ENDS today",
                      10, "buyer_specialist", hard_deadline=True,
                      note="Statutory cooling-off period. After today the buyer is bound."),
        ChecklistItem("deposit_1", "First deposit due", 30, "transaction_assistant",
                      hard_deadline=True),
        ChecklistItem("deposit_schedule", "Load the remaining deposit schedule as monitors",
                      1, "transaction_assistant"),
        ChecklistItem("occupancy_watch", "Set interim occupancy watch",
                      30, "transaction_assistant"),
        ChecklistItem("assignment_watch", "Set assignment-window watch",
                      90, "transaction_assistant"),
    ),
)

# ---------------------------------------------------------------------------
# Buyer post-close care
# ---------------------------------------------------------------------------

BUYER_POST_CLOSE = Checklist(
    key="buyer_post_close",
    name="Buyer: post-close care",
    trigger="deal_closed",
    items=(
        ChecklistItem("day_one", "Closing-day congratulations and key handover check",
                      0, "buyer_specialist"),
        ChecklistItem("week_one", "Week-one move-in check: utilities, mail, issues",
                      7, "concierge"),
        ChecklistItem("day_thirty", "30-day check-in and contractor referrals",
                      30, "concierge"),
        ChecklistItem("day_ninety", "90-day check-in; ask for the review",
                      90, "concierge"),
        ChecklistItem("tax_reminder", "First property-tax instalment reminder",
                      120, "concierge"),
        ChecklistItem("anniversary", "One-year anniversary: home value update",
                      365, "concierge",
                      note="Repeats yearly; re-anchors on itself."),
    ),
)

SELLER_POST_CLOSE = Checklist(
    key="seller_post_close",
    name="Seller: post-close care",
    trigger="deal_closed",
    items=(
        ChecklistItem("day_one", "Closing-day congratulations", 0, "listing_specialist"),
        ChecklistItem("week_one", "Week-one check: move complete, anything outstanding",
                      7, "concierge"),
        ChecklistItem("review_ask", "Ask for the review while it is fresh", 14, "concierge"),
        ChecklistItem("next_purchase", "Confirm next-purchase plans and re-open a buyer file",
                      21, "buyer_specialist"),
        ChecklistItem("anniversary", "One-year anniversary touch", 365, "concierge"),
    ),
)

SELLER_PRE_MARKET = Checklist(
    key="seller_pre_market",
    name="Seller: listing signed to live",
    trigger="listing_signed",
    items=(
        ChecklistItem("paperwork", "Complete listing paperwork and compliance file",
                      0, "transaction_assistant", hard_deadline=True,
                      note="TRESA: signed before any marketing goes out."),
        ChecklistItem("prep_walkthrough", "Prep walkthrough: repairs, declutter, staging plan",
                      1, "listing_specialist"),
        ChecklistItem("book_media", "Book photography, video, floorplan", 2, "media"),
        ChecklistItem("copy", "Write listing copy and feature card", 4, "media",
                      note="The feature card is what the showing-agent follow-up sells from."),
        ChecklistItem("campaign", "Build the launch campaign for approval", 5, "media"),
        ChecklistItem("coming_soon", "Coming-soon touches to the database and farm",
                      6, "concierge"),
        ChecklistItem("go_live", "Go live on MLS and verify every field", 7,
                      "listing_specialist", hard_deadline=True),
    ),
)

LISTING_ACTIVE = Checklist(
    key="listing_active",
    name="Listing: active-on-market rhythm",
    trigger="listing_live",
    items=(
        ChecklistItem("first_feedback_sweep", "Chase feedback from every showing agent so far",
                      3, "listing_specialist"),
        ChecklistItem("week_one_report", "Week-one seller report: traffic, feedback, position",
                      7, "listing_specialist"),
        ChecklistItem("open_house", "First open house", 5, "listing_specialist"),
        ChecklistItem("week_two_report", "Week-two seller report", 14, "listing_specialist"),
        ChecklistItem("price_review", "Price and strategy review against market mode",
                      21, "listing_specialist",
                      note="Produces a recommendation only -- Ray approves any change."),
        ChecklistItem("month_report", "Month-one report and refresh decision",
                      30, "listing_specialist"),
    ),
)

PRE_CLOSING = Checklist(
    key="pre_closing",
    name="Firm to close",
    trigger="deal_firm",
    items=(
        ChecklistItem("lawyer_package", "Send the complete file to the lawyer",
                      0, "transaction_assistant", hard_deadline=True),
        ChecklistItem("deposit_confirm", "Confirm deposit delivered and receipted",
                      1, "transaction_assistant", hard_deadline=True),
        ChecklistItem("lender_check", "Confirm financing funded with the lender",
                      -21, "transaction_assistant",
                      note="Negative offsets run backwards from the closing date."),
        ChecklistItem("insurance", "Confirm home insurance bound", -14, "transaction_assistant"),
        ChecklistItem("utilities", "Utility and address-change checklist to the client",
                      -10, "concierge"),
        ChecklistItem("walkthrough", "Book the pre-closing walkthrough", -3,
                      "buyer_specialist"),
        ChecklistItem("closing_day", "Closing day: confirm keys and funds",
                      0, "transaction_assistant", hard_deadline=True),
    ),
)

DEAL_CONDITIONAL = Checklist(
    key="deal_conditional",
    name="Conditional period",
    trigger="offer_accepted_conditional",
    items=(
        ChecklistItem("book_inspection", "Book the home inspection", 0,
                      "buyer_specialist", hard_deadline=True),
        ChecklistItem("lawyer_notify", "Notify the lawyer and send the APS", 0,
                      "transaction_assistant", hard_deadline=True),
        ChecklistItem("financing_submit", "Submit to the lender for financing approval",
                      1, "transaction_assistant", hard_deadline=True),
        ChecklistItem("status_certificate", "Order the status certificate (condo only)",
                      1, "transaction_assistant",
                      note="Condo files only; skipped for freehold."),
        ChecklistItem("inspection_review", "Review inspection findings with the buyer",
                      3, "buyer_specialist"),
        ChecklistItem("condition_midpoint", "Condition midpoint: everything on track?",
                      4, "buyer_specialist", hard_deadline=True),
        ChecklistItem("waiver", "Waiver or notice of fulfilment signed and delivered",
                      5, "transaction_assistant", hard_deadline=True,
                      note="Miss this and the deal dies by default."),
    ),
)

APPOINTMENT_REMINDERS = Checklist(
    key="appointment_reminders",
    name="Booked appointment: reminders and follow-up",
    trigger="appointment_booked",
    items=(
        # Anchored on the appointment start, so these run backwards from it.
        # The 48/24-hour pair is carried over from the reminders engine
        # already in daily use; the two-hour nudge is what actually moves
        # the no-show rate, and the next-day follow-up is where a showing
        # turns into the next appointment instead of into silence.
        ChecklistItem("confirm_48h", "Confirm the appointment (48 hours out)",
                      -2, "concierge"),
        ChecklistItem("remind_24h", "Reminder with details and directions",
                      -1, "concierge"),
        ChecklistItem("nudge_2h", "Same-day nudge", -0.083, "concierge"),
        ChecklistItem("followup", "Follow up: outcome, feedback, next appointment",
                      1, "concierge",
                      note="Every conversation drives to the next appointment."),
    ),
)

LEASE_LIFECYCLE = Checklist(
    key="lease_lifecycle",
    name="Lease: application to renewal",
    trigger="lease_application_started",
    items=(
        ChecklistItem("package", "Assemble the application package", 0, "concierge"),
        ChecklistItem("submit", "Submit to the listing brokerage", 1, "concierge"),
        ChecklistItem("signing", "Lease signing and deposit", 3, "transaction_assistant"),
        ChecklistItem("move_in", "Move-in day check", 30, "concierge"),
        ChecklistItem("renewal_watch", "Renewal decision window opens",
                      305, "concierge",
                      note="60 days before a one-year term ends -- a renewal is a "
                           "buyer or listing lead, not just an administrative date."),
    ),
)


# ---------------------------------------------------------------------------
# Cadence programs -- generated, then asserted
# ---------------------------------------------------------------------------

def _eight_by_eight() -> Checklist:
    """Eight touches in the first eight weeks of a new relationship.

    The offsets front-load deliberately: three touches in the first week,
    because a lead that gets nothing for six days has already decided you
    are not attentive, and no amount of week-seven diligence undoes that.
    """
    offsets = [0, 2, 5, 9, 16, 25, 40, 56]
    kinds = [
        "Introduction and what to expect",
        "Value: neighbourhood and market snapshot",
        "Check in: answer the question they actually have",
        "Value: listings or stats matched to their criteria",
        "Personal touch: call, not a message",
        "Value: rate and financing update",
        "Invitation: open house or consultation",
        "Direct ask: book the appointment",
    ]
    return Checklist(
        key="eight_by_eight",
        name="8x8 new-relationship program",
        trigger="lead_created",
        items=tuple(
            ChecklistItem(f"touch_{i + 1}", title, offset, "concierge")
            for i, (offset, title) in enumerate(zip(offsets, kinds))
        ),
    )


def _thirty_three_touch() -> Checklist:
    """Thirty-three touches across a year for the database.

    Composition: 12 monthly market updates, 4 quarterly calls, 4 seasonal
    cards, 1 anniversary, 1 birthday, 4 property-value updates, 4 local
    guides, 3 invitations. Thirty-three exactly -- see the test.
    """
    items: list[ChecklistItem] = []

    for month in range(12):
        items.append(ChecklistItem(
            f"market_{month + 1}", f"Monthly market update ({month + 1}/12)",
            month * 30 + 5, "concierge"))
    for q in range(4):
        items.append(ChecklistItem(
            f"call_{q + 1}", f"Quarterly personal call ({q + 1}/4)",
            q * 91 + 20, "concierge"))
    for i, (day, label) in enumerate(
        [(20, "New year"), (110, "Spring"), (250, "Fall"), (350, "Holiday")]
    ):
        items.append(ChecklistItem(f"card_{i + 1}", f"{label} card", day, "concierge"))
    items.append(ChecklistItem("anniversary", "Home anniversary touch", 365, "concierge"))
    items.append(ChecklistItem("birthday", "Birthday touch", 0, "concierge",
                               note="Re-anchored to the contact's birthday."))
    for q in range(4):
        items.append(ChecklistItem(
            f"value_{q + 1}", f"Property value update ({q + 1}/4)",
            q * 91 + 45, "concierge"))
    for i, topic in enumerate(
        ["Local guide: schools", "Local guide: contractors",
         "Local guide: taxes and assessments", "Local guide: transit and development"]
    ):
        items.append(ChecklistItem(f"guide_{i + 1}", topic, i * 91 + 60, "media"))
    for i, invite in enumerate(
        ["Client event invitation", "Open-house invitation", "Market briefing invitation"]
    ):
        items.append(ChecklistItem(f"invite_{i + 1}", invite, i * 120 + 75, "concierge"))

    return Checklist(
        key="thirty_three_touch",
        name="33-touch annual database program",
        trigger="entered_database",
        items=tuple(items),
    )


EIGHT_BY_EIGHT = _eight_by_eight()
THIRTY_THREE_TOUCH = _thirty_three_touch()

CHECKLISTS: dict[str, Checklist] = {
    c.key: c
    for c in (
        PRECON_WORKSHEET,
        BUYER_POST_CLOSE,
        SELLER_POST_CLOSE,
        SELLER_PRE_MARKET,
        LISTING_ACTIVE,
        PRE_CLOSING,
        DEAL_CONDITIONAL,
        LEASE_LIFECYCLE,
        APPOINTMENT_REMINDERS,
        EIGHT_BY_EIGHT,
        THIRTY_THREE_TOUCH,
    )
}


def hard_deadlines(tasks: list[Task]) -> list[Task]:
    """The subset that escalates to a human. Sorted soonest-first."""
    return sorted((t for t in tasks if t.hard_deadline), key=lambda t: t.due_at)
