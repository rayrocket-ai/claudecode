"""Ontario real-estate transaction checklists.

Each checklist is a list of steps that fan out into individual `Task` rows when
a manager runs `/checklist <key> <deal ref>`. Steps carry a default `urgency`
and an optional `offset_days` (a suggested due date, counted from the day the
checklist is generated) so time-sensitive items (deposit to trust, condition
waivers) surface with tighter follow-up cadence.

These reflect common Ontario/TRREB practice under TRESA (Trust in Real Estate
Services Act) as of 2026. They are an operational starting point, NOT legal
advice — brokerages should adapt them to their own compliance policies.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChecklistItem:
    title: str
    description: str
    urgency: str = "standard"  # low, standard, high
    offset_days: int | None = None  # suggested due date, days from generation


@dataclass(frozen=True)
class Checklist:
    key: str
    name: str
    items: list[ChecklistItem]


# ── New Listing ─────────────────────────────────────────────────────

_LISTING = Checklist(
    key="listing",
    name="New Listing",
    items=[
        ChecklistItem(
            "Signed listing agreement (TRREB Form 200)",
            "Confirm the seller has signed the Listing Agreement and it's on file.",
            urgency="high",
            offset_days=1,
        ),
        ChecklistItem(
            "FINTRAC client ID verification",
            "Complete and record the seller's individual identification (FINTRAC).",
            urgency="high",
            offset_days=1,
        ),
        ChecklistItem(
            "Seller disclosures collected",
            "Gather known defects / SPIS (if used), status certificate for condos, "
            "and any required disclosures.",
            urgency="standard",
            offset_days=2,
        ),
        ChecklistItem(
            "Photos & measurements booked",
            "Schedule professional photos, floor plan, and room measurements.",
            urgency="standard",
            offset_days=2,
        ),
        ChecklistItem(
            "MLS / TRREB listing input",
            "Enter the listing on MLS/TRREB with correct details and pricing.",
            urgency="standard",
            offset_days=3,
        ),
        ChecklistItem(
            "Lockbox & showing setup (BrokerBay)",
            "Install lockbox and configure showing instructions in BrokerBay.",
            urgency="standard",
            offset_days=3,
        ),
        ChecklistItem(
            "Marketing launch",
            "Signage, social, feature sheet, and any brokerage marketing pushed live.",
            urgency="low",
            offset_days=4,
        ),
    ],
)


# ── Buyer Onboarding ────────────────────────────────────────────────

_BUYER = Checklist(
    key="buyer",
    name="Buyer Onboarding",
    items=[
        ChecklistItem(
            "Buyer Representation Agreement (BRA)",
            "Sign a written BRA under TRESA and provide the RECO Information Guide.",
            urgency="high",
            offset_days=1,
        ),
        ChecklistItem(
            "FINTRAC client ID verification",
            "Complete and record the buyer's individual identification (FINTRAC).",
            urgency="high",
            offset_days=1,
        ),
        ChecklistItem(
            "Mortgage pre-approval",
            "Confirm the buyer has a lender pre-approval and know the max budget.",
            urgency="standard",
            offset_days=2,
        ),
        ChecklistItem(
            "Needs assessment",
            "Document must-haves, areas, price range, and timeline.",
            urgency="low",
            offset_days=2,
        ),
        ChecklistItem(
            "Showing setup",
            "Set up saved searches / auto-alerts and start booking showings.",
            urgency="low",
            offset_days=3,
        ),
    ],
)


# ── Firm Deal / Post-Acceptance ─────────────────────────────────────

_DEAL = Checklist(
    key="deal",
    name="Firm Deal / Post-Acceptance",
    items=[
        ChecklistItem(
            "Deliver APS to lawyers",
            "Send the fully executed Agreement of Purchase and Sale to both lawyers.",
            urgency="high",
            offset_days=1,
        ),
        ChecklistItem(
            "Deposit to trust (within 24h)",
            "Confirm the buyer's deposit is delivered to the deposit holder's trust "
            "account within the timeframe required by the APS.",
            urgency="high",
            offset_days=1,
        ),
        ChecklistItem(
            "Financing condition",
            "Track the financing condition and obtain the waiver/notice before the "
            "condition date.",
            urgency="high",
            offset_days=3,
        ),
        ChecklistItem(
            "Home inspection",
            "Book the home inspection and satisfy/waive the condition before its date.",
            urgency="high",
            offset_days=3,
        ),
        ChecklistItem(
            "Status certificate (condo)",
            "Order and review the status certificate; waive before the condition date.",
            urgency="standard",
            offset_days=4,
        ),
        ChecklistItem(
            "Notify lender / arrange appraisal",
            "Ensure the lender has the firm deal and the appraisal is ordered.",
            urgency="standard",
            offset_days=4,
        ),
        ChecklistItem(
            "Title search",
            "Confirm the buyer's lawyer has started the title search.",
            urgency="low",
            offset_days=7,
        ),
        ChecklistItem(
            "Pre-closing walkthrough",
            "Schedule the buyer's final walkthrough before closing.",
            urgency="standard",
            offset_days=None,
        ),
        ChecklistItem(
            "Keys & possession",
            "Coordinate key handover / possession on the closing date.",
            urgency="standard",
            offset_days=None,
        ),
        ChecklistItem(
            "Trade record sheet / commission",
            "Complete the trade record sheet and submit commission paperwork to the "
            "brokerage.",
            urgency="low",
            offset_days=None,
        ),
    ],
)


CHECKLISTS: dict[str, Checklist] = {
    _LISTING.key: _LISTING,
    _BUYER.key: _BUYER,
    _DEAL.key: _DEAL,
}


def get_checklist(key: str) -> Checklist | None:
    return CHECKLISTS.get(key.strip().lower())


def checklist_keys() -> list[str]:
    return list(CHECKLISTS.keys())
