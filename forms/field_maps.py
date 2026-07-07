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
# Only field names confirmed to be shared across OREA WebForms forms are
# active. The commented entries are the expected mappings — capture the real
# HTML `name` attributes from the live form editor and uncomment/correct them.
# See docs/field-map-calibration.md. Unknown names are harmless (fill_form
# skips fields it can't find), but a WRONG name could fill the wrong box,
# so uncertain guesses stay commented out.

FORM_120_FIELDS: dict[str, str] = {
    "txtbuyer1": "buyer_1",
    "txtbuyer2": "buyer_2",
    "txtseller1": "seller_1",
    "txtseller2": "seller_2",
    "txtp_streetnum": "property_street_number",
    "txtp_unitNumber": "property_unit",
    "txtp_street": "property_street_name",
    "txtp_city": "property_city",
    "txtp_zipcode": "property_postal_code",
    # TODO(calibrate): capture real names from the live Form 120 editor:
    # "???": "original_agreement_date_d",
    # "???": "original_agreement_date_mmmm",
    # "???": "original_agreement_date_yy",
    # "???": "amendment_description",
    # "???": "irrev_expire_d" / "_mmmm" / "_yy",
}

# ── Form 122 — Waiver ───────────────────────────────────────────

FORM_122_FIELDS: dict[str, str] = {
    "txtbuyer1": "buyer_1",
    "txtbuyer2": "buyer_2",
    "txtseller1": "seller_1",
    "txtseller2": "seller_2",
    "txtp_streetnum": "property_street_number",
    "txtp_unitNumber": "property_unit",
    "txtp_street": "property_street_name",
    "txtp_city": "property_city",
    "txtp_zipcode": "property_postal_code",
    # TODO(calibrate): capture real names from the live Form 122 editor:
    # "???": "original_agreement_date_d" / "_mmmm" / "_yy",
    # "???": "condition_waived",
}

# ── Form 400 — Agreement to Lease (Residential) ──────────────────
# Tenant is stored under buyer_* keys, landlord under seller_* (see
# ai/prompts.py LEASE_COLLECTION_PROMPT).

FORM_400_FIELDS: dict[str, str] = {
    "txtbuyer1": "buyer_1",
    "txtbuyer2": "buyer_2",
    "txtseller1": "seller_1",
    "txtseller2": "seller_2",
    "txtp_streetnum": "property_street_number",
    "txtp_unitNumber": "property_unit",
    "txtp_street": "property_street_name",
    "txtp_city": "property_city",
    "txtp_zipcode": "property_postal_code",
    # TODO(calibrate): capture real names from the live Form 400 editor:
    # "???": "monthly_rent_formatted",
    # "???": "monthly_rent_words",
    # "???": "lease_start_date_d" / "_mmmm" / "_yy",
    # "???": "lease_end_date_d" / "_mmmm" / "_yy",
    # "???": "rent_deposit_formatted",
}

# ── Form 500 — Agreement of Purchase and Sale (Commercial) ───────
# Form 500 mirrors Form 100's core layout; the shared APS field names are
# active and the commercial-specific ones need calibration.

FORM_500_FIELDS: dict[str, str] = {
    **{k: v for k, v in FORM_100_FIELDS.items()
       if not k.startswith(("txtp_SchoolDistrict", "txtp_ZoningClass"))},
    # TODO(calibrate): capture real names from the live Form 500 editor:
    # "???": "zoning",
    # "???": "due_diligence_days",
    # "???": "hst_applicable",
}

# ── Form name → field map lookup ─────────────────────────────────

FIELD_MAPS: dict[str, dict[str, str]] = {
    "aps": FORM_100_FIELDS,
    "amendment": FORM_120_FIELDS,
    "waiver": FORM_122_FIELDS,
    "lease": FORM_400_FIELDS,
    "commercial_aps": FORM_500_FIELDS,
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
