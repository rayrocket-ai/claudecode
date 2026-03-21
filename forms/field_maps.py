"""TransactionDesk / WebForms field mappings for OREA forms.

These map the HTML input `name` attributes in TransactionDesk's form editor
to the deal data keys collected by the AI agent.

Discovered by inspecting live Form 100 at pr.transactiondesk.com.
"""

from __future__ import annotations

# ── Form 100 — Agreement of Purchase and Sale (Residential) ──────

FORM_100_FIELDS: dict[str, str] = {
    # Offer date
    "txtp_OfferDate_yy": "offer_date_yy",
    "txtp_OfferDate_d": "offer_date_d",
    "txtp_OfferDate_mmmm": "offer_date_mmmm",

    # Buyers
    "txtbuyer1": "buyer_1",
    "txtbuyer2": "buyer_2",

    # Sellers
    "txtseller1": "seller_1",
    "txtseller2": "seller_2",

    # Property address
    "txtp_streetnum": "property_street_number",
    "txtp_unitNumber": "property_unit",
    "txtp_street": "property_street_name",
    "txtp_city": "property_city",
    "txtp_state": "property_province",
    "txtp_zipcode": "property_postal_code",
    "txtp_legaldesc": "legal_description",

    # Price
    "txtp_price": "purchase_price_formatted",
    "txtp_pricewords": "purchase_price_words",

    # Deposit
    "txtp_deposit": "deposit_formatted",
    "txtp_depositwords": "deposit_words",
    "txtDepositHolder": "deposit_holder",

    # Irrevocability
    "txtp_irrev_t": "irrevocability_hours",
    "txtp_OfferExpireDate_d": "irrev_expire_d",
    "txtp_OfferExpireDate_mmmm": "irrev_expire_mmmm",
    "txtp_OfferExpireDate_yy": "irrev_expire_yy",

    # Closing date
    "txtp_closedate_d": "closing_date_d",
    "txtp_closedate_mmmm": "closing_date_mmmm",
    "txtp_closedate_yy": "closing_date_yy",

    # Schedules
    "txtAttachedSchedule": "attached_schedules",

    # Frontage / depth (sometimes mapped to unusual fields)
    "txtp_SchoolDistrict": "frontage_feet",
    "txtp_ZoningClass": "depth_feet",
}

# ── Form 120 — Amendment ─────────────────────────────────────────

FORM_120_FIELDS: dict[str, str] = {
    "txtbuyer1": "buyer_1",
    "txtseller1": "seller_1",
    "txtp_streetnum": "property_street_number",
    "txtp_street": "property_street_name",
    "txtp_city": "property_city",
}

# ── Form 122 — Waiver ───────────────────────────────────────────

FORM_122_FIELDS: dict[str, str] = {
    "txtbuyer1": "buyer_1",
    "txtseller1": "seller_1",
    "txtp_streetnum": "property_street_number",
    "txtp_street": "property_street_name",
    "txtp_city": "property_city",
}

# ── Form name → field map lookup ─────────────────────────────────

FIELD_MAPS: dict[str, dict[str, str]] = {
    "aps": FORM_100_FIELDS,
    "amendment": FORM_120_FIELDS,
    "waiver": FORM_122_FIELDS,
}

# ── TransactionDesk form name mapping ────────────────────────────
# Exact form names as they appear in TransactionDesk's form library

FORM_NAME_MAP: dict[str, str] = {
    "aps": "(Ontario) 100 - Agreement of Purchase and Sale",
    "amendment": "(Ontario) 120 - Amendment to Agreement",
    "waiver": "(Ontario) 122 - Waiver",
    "notice": "(Ontario) 124 - Notice to Remove Condition",
    "seller_info": "(Ontario) 145 - Seller Property Information Statement",
    "lease": "(Ontario) 400 - Agreement to Lease - Residential",
    "commercial_aps": "(Ontario) 500 - Agreement of Purchase and Sale - Commercial",
    "commercial_lease": "(Ontario) 510 - Agreement to Lease - Commercial",
    "mutual_release": "(Ontario) 122 - Mutual Release",
    "working_with_realtor": "(Ontario) 801 - Working with a REALTOR",
}

# Transaction type mapping for TransactionDesk
TRANSACTION_TYPE_MAP: dict[str, str] = {
    "aps": "Residential Sale",
    "amendment": "Residential Sale",
    "waiver": "Residential Sale",
    "lease": "Residential Lease",
    "commercial_aps": "Commercial Sale",
    "commercial_lease": "Commercial Lease",
}
