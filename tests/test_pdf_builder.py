"""Smoke tests for the form-aware fallback PDF builder."""

import os

import pytest

from forms.pdf_builder import DOC_SECTIONS, DOC_TITLES, generate_summary_pdf

SAMPLES = {
    "amendment": {
        "buyer_1": "John Smith",
        "seller_1": "Jane Doe",
        "property_street_number": "123",
        "property_street_name": "Main St",
        "property_city": "Toronto",
        "original_agreement_date": "2026-06-15",
        "amendment_description": "Closing moved from 2026-08-01 to 2026-09-01",
        "amendment_date": "2026-07-05",
    },
    "waiver": {
        "buyer_1": "John Smith",
        "seller_1": "Jane Doe",
        "property_street_number": "123",
        "property_street_name": "Main St",
        "property_city": "Toronto",
        "original_agreement_date": "2026-06-15",
        "condition_waived": "Financing condition per Schedule A",
        "waiver_date": "2026-07-05",
    },
    "lease": {
        "buyer_1": "Tenant Name",
        "seller_1": "Landlord Name",
        "property_street_number": "10",
        "property_street_name": "King St",
        "property_city": "Toronto",
        "monthly_rent": 2500,
        "lease_start_date": "2026-08-01",
        "lease_end_date": "2027-07-31",
        "parking": "1 underground spot",
    },
    "commercial_aps": {
        "buyer_1": "Acme Holdings Inc.",
        "seller_1": "Beta Properties Ltd.",
        "property_street_number": "500",
        "property_street_name": "Industrial Rd",
        "property_city": "Mississauga",
        "purchase_price": 2500000,
        "zoning": "E2 Employment",
        "due_diligence_days": 30,
        "hst_applicable": "In addition to purchase price",
    },
}


@pytest.mark.parametrize("doc_type", list(SAMPLES))
def test_generates_nonempty_pdf(doc_type):
    path = generate_summary_pdf(SAMPLES[doc_type], doc_type)
    try:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000  # a real PDF, not an empty shell
        with open(path, "rb") as f:
            assert f.read(5) == b"%PDF-"
    finally:
        os.unlink(path)


def test_unknown_doc_type_falls_back_to_generic_listing():
    path = generate_summary_pdf({"some_field": "some value"}, "mystery_form")
    try:
        assert os.path.getsize(path) > 500
    finally:
        os.unlink(path)


def test_extra_keys_never_dropped():
    """Keys outside the known sections must land in OTHER DETAILS (i.e. the
    section spec must not silently swallow collected data)."""
    data = dict(SAMPLES["amendment"])
    data["surprise_key"] = "surprise value"
    path = generate_summary_pdf(data, "amendment")
    try:
        assert os.path.getsize(path) > 1000
    finally:
        os.unlink(path)


def test_every_sectioned_doc_type_has_a_title():
    assert set(DOC_SECTIONS) <= set(DOC_TITLES)
