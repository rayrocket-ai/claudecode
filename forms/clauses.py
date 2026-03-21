"""Ontario real estate clause library for OREA forms."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Clause:
    id: str
    category: str
    title: str
    text: str
    applicable_forms: list[str]


CLAUSES: list[Clause] = [
    # ── Financing ─────────────────────────────────────────────
    Clause(
        id="fin_01",
        category="financing",
        title="Financing Condition — Standard",
        text=(
            "This Offer is conditional upon the Buyer arranging, at the Buyer's "
            "own expense, a new first Charge/Mortgage satisfactory to the Buyer "
            "in the Buyer's sole and absolute discretion. Unless the Buyer gives "
            "notice in writing delivered to the Seller not later than 11:59 p.m. "
            "on the _____ day of __________, 20___, that this condition is "
            "fulfilled, this Offer shall be null and void and the deposit shall "
            "be returned to the Buyer in full without deduction."
        ),
        applicable_forms=["aps", "commercial_aps"],
    ),
    # ── Inspection ────────────────────────────────────────────
    Clause(
        id="insp_01",
        category="inspection",
        title="Home Inspection Condition",
        text=(
            "This Offer is conditional upon the inspection of the subject "
            "property by a home inspector at the Buyer's own expense, and the "
            "obtaining of a report satisfactory to the Buyer in the Buyer's sole "
            "and absolute discretion."
        ),
        applicable_forms=["aps"],
    ),
    # ── Status Certificate ────────────────────────────────────
    Clause(
        id="status_01",
        category="status_certificate",
        title="Status Certificate Review — Condo",
        text=(
            "This Offer is conditional upon the Buyer's lawyer reviewing the "
            "Status Certificate and attachments and finding them satisfactory in "
            "the Buyer's Lawyer's sole and absolute discretion. The Seller agrees "
            "to request the Status Certificate within 3 days after acceptance."
        ),
        applicable_forms=["aps"],
    ),
    # ── Sale of Buyer's Property ──────────────────────────────
    Clause(
        id="sale_01",
        category="sale_of_buyers_property",
        title="Sale of Buyer's Property",
        text=(
            "This Offer is conditional upon the sale of the Buyer's property "
            "known as ____________________."
        ),
        applicable_forms=["aps"],
    ),
    # ── Lawyer Approval ───────────────────────────────────────
    Clause(
        id="law_01",
        category="lawyer_approval",
        title="Lawyer's Approval",
        text=(
            "This Offer is conditional upon the approval of the terms hereof by "
            "the Buyer's Solicitor. Unless the Buyer gives notice in writing to "
            "the Seller not later than 11:59 p.m. on the _____ day of "
            "__________, 20___, that this condition is fulfilled, this Offer "
            "shall be null and void."
        ),
        applicable_forms=["aps", "lease"],
    ),
    # ── UFFI ──────────────────────────────────────────────────
    Clause(
        id="uffi_01",
        category="environmental",
        title="UFFI Warranty",
        text=(
            "The Seller represents and warrants to the Buyer that during the "
            "time the Seller has owned the property, the Seller has not caused "
            "any building on the property to be insulated with insulation "
            "containing urea-formaldehyde, and that to the best of the Seller's "
            "knowledge no building on the property contains or has ever contained "
            "insulation that contains urea-formaldehyde."
        ),
        applicable_forms=["aps"],
    ),
    # ── Chattels / Inclusions ─────────────────────────────────
    Clause(
        id="chat_01",
        category="chattels",
        title="Standard Chattels Included",
        text=(
            "Unless otherwise stated in this Agreement, all fixtures and "
            "chattels shall be in good working order on completion. The Seller "
            "represents that the chattels and fixtures as included are not "
            "subject to any chattel mortgage, lien, or encumbrance."
        ),
        applicable_forms=["aps"],
    ),
    # ── Survey ────────────────────────────────────────────────
    Clause(
        id="surv_01",
        category="survey",
        title="Survey Clause",
        text=(
            "The Buyer shall be allowed until completion to examine the title "
            "and to satisfy himself that the boundaries and area are as stated. "
            "If within that time any valid objection to title is made which the "
            "Seller is unable or unwilling to remove, the Agreement shall be "
            "null and void."
        ),
        applicable_forms=["aps"],
    ),
    # ── Insurance ─────────────────────────────────────────────
    Clause(
        id="ins_01",
        category="insurance",
        title="Insurance Condition",
        text=(
            "This Offer is conditional upon the Buyer obtaining insurance for "
            "the property satisfactory to the Buyer in the Buyer's sole and "
            "absolute discretion."
        ),
        applicable_forms=["aps"],
    ),
    # ── Commercial Due Diligence ──────────────────────────────
    Clause(
        id="comm_dd_01",
        category="commercial",
        title="Due Diligence Period — Commercial",
        text=(
            "This Offer is conditional upon the Buyer completing its due "
            "diligence investigations within _____ days of acceptance and being "
            "satisfied in the Buyer's sole and absolute discretion."
        ),
        applicable_forms=["commercial_aps"],
    ),
    # ── Appraisal ─────────────────────────────────────────────
    Clause(
        id="appr_01",
        category="appraisal",
        title="Appraisal Condition",
        text=(
            "This Offer is conditional upon the property appraising at or above "
            "the purchase price as determined by an accredited appraiser "
            "retained by the Buyer or the Buyer's lender."
        ),
        applicable_forms=["aps"],
    ),
]


def get_clauses_for_form(form_type: str) -> list[Clause]:
    """Return all clauses applicable to a given form type."""
    return [c for c in CLAUSES if form_type in c.applicable_forms]


def get_clause_by_id(clause_id: str) -> Clause | None:
    """Return a specific clause by its ID."""
    for c in CLAUSES:
        if c.id == clause_id:
            return c
    return None


def get_clauses_by_category(category: str) -> list[Clause]:
    """Return all clauses in a category."""
    return [c for c in CLAUSES if c.category == category]
