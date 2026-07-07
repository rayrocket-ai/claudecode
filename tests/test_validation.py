"""Unit tests for forms.validation."""

import pytest

from forms.validation import validate_deal, ValidationResult


def _valid_aps() -> dict:
    """A minimal, internally-consistent APS deal."""
    return {
        "buyer_1": "John Smith",
        "seller_1": "Jane Doe",
        "purchase_price": 800000,
        "deposit": 40000,
        "property_street_number": "123",
        "property_street_name": "Main St",
        "property_city": "Toronto",
        "property_postal_code": "M5V 2T6",
        "offer_date": "2026-07-01",
        "irrevocability_date": "2026-07-03",
        "closing_date": "2026-09-01",
    }


class TestHappyPath:
    def test_valid_deal_passes(self):
        result = validate_deal(_valid_aps(), "aps")
        assert result.ok
        assert result.errors == []
        assert result.warnings == []

    def test_summary_when_clean(self):
        result = validate_deal(_valid_aps(), "aps")
        assert "All checks passed" in result.summary()


class TestRequiredFields:
    @pytest.mark.parametrize("missing", [
        "buyer_1", "seller_1", "purchase_price",
        "property_street_number", "property_street_name", "property_city",
    ])
    def test_missing_required_field_is_error(self, missing):
        data = _valid_aps()
        del data[missing]
        result = validate_deal(data, "aps")
        assert not result.ok
        assert any(missing.split("_")[0].lower() in e.lower() or
                   "required" in e.lower() for e in result.errors)

    def test_blank_string_counts_as_missing(self):
        data = _valid_aps()
        data["buyer_1"] = "   "
        result = validate_deal(data, "aps")
        assert not result.ok


class TestPrice:
    def test_zero_price_is_error(self):
        data = _valid_aps()
        data["purchase_price"] = 0
        result = validate_deal(data, "aps")
        assert not result.ok

    def test_unparseable_price_is_error(self):
        data = _valid_aps()
        data["purchase_price"] = "lots of money"
        result = validate_deal(data, "aps")
        assert not result.ok

    def test_low_price_is_warning_not_error(self):
        data = _valid_aps()
        data["purchase_price"] = 500
        data["deposit"] = 50
        result = validate_deal(data, "aps")
        assert result.ok
        assert any("low" in w.lower() for w in result.warnings)


class TestDeposit:
    def test_deposit_exceeds_price_is_error(self):
        data = _valid_aps()
        data["deposit"] = 900000  # > 800000 price
        result = validate_deal(data, "aps")
        assert not result.ok
        assert any("greater than" in e.lower() for e in result.errors)

    def test_missing_deposit_on_aps_is_warning(self):
        data = _valid_aps()
        del data["deposit"]
        result = validate_deal(data, "aps")
        assert result.ok  # warning, not error
        assert any("deposit" in w.lower() for w in result.warnings)

    def test_tiny_deposit_is_warning(self):
        data = _valid_aps()
        data["deposit"] = 100  # < 1% of 800k
        result = validate_deal(data, "aps")
        assert result.ok
        assert any("1%" in w or "less than" in w.lower() for w in result.warnings)

    def test_negative_deposit_is_error(self):
        data = _valid_aps()
        data["deposit"] = "-5000"
        result = validate_deal(data, "aps")
        assert not result.ok


class TestDates:
    def test_closing_before_offer_is_error(self):
        data = _valid_aps()
        data["offer_date"] = "2026-07-01"
        data["closing_date"] = "2026-06-01"
        result = validate_deal(data, "aps")
        assert not result.ok
        assert any("closing" in e.lower() for e in result.errors)

    def test_irrevocability_before_offer_is_error(self):
        data = _valid_aps()
        data["offer_date"] = "2026-07-01"
        data["irrevocability_date"] = "2026-06-30"
        result = validate_deal(data, "aps")
        assert not result.ok
        assert any("irrevocability" in e.lower() for e in result.errors)

    def test_unparseable_date_is_error(self):
        data = _valid_aps()
        data["closing_date"] = "next tuesday-ish"
        result = validate_deal(data, "aps")
        assert not result.ok

    def test_irrevocability_after_closing_is_warning(self):
        data = _valid_aps()
        data["offer_date"] = "2026-07-01"
        data["closing_date"] = "2026-07-10"
        data["irrevocability_date"] = "2026-07-20"
        result = validate_deal(data, "aps")
        assert result.ok
        assert any("closing" in w.lower() for w in result.warnings)


class TestPostalCode:
    def test_valid_postal_passes(self):
        data = _valid_aps()
        data["property_postal_code"] = "M5V 2T6"
        result = validate_deal(data, "aps")
        assert not any("postal" in w.lower() for w in result.warnings)

    def test_valid_postal_without_space(self):
        data = _valid_aps()
        data["property_postal_code"] = "M5V2T6"
        result = validate_deal(data, "aps")
        assert not any("postal" in w.lower() for w in result.warnings)

    def test_invalid_postal_is_warning(self):
        data = _valid_aps()
        data["property_postal_code"] = "12345"  # US zip
        result = validate_deal(data, "aps")
        assert result.ok
        assert any("postal" in w.lower() for w in result.warnings)


def _valid_lease() -> dict:
    return {
        "buyer_1": "Tenant Name",
        "seller_1": "Landlord Name",
        "property_street_number": "10",
        "property_street_name": "King St",
        "property_city": "Toronto",
        "monthly_rent": 2500,
        "rent_deposit": 5000,
        "lease_start_date": "2026-08-01",
        "lease_end_date": "2027-07-31",
    }


def _valid_amendment() -> dict:
    return {
        "buyer_1": "John Smith",
        "seller_1": "Jane Doe",
        "property_street_number": "123",
        "property_street_name": "Main St",
        "property_city": "Toronto",
        "original_agreement_date": "2026-06-15",
        "amendment_description": "Closing date changed from 2026-08-01 to 2026-09-01",
        "amendment_date": "2026-07-05",
    }


class TestDocTypes:
    def test_lease_does_not_require_price(self):
        result = validate_deal(_valid_lease(), "lease")
        assert result.ok

    def test_unknown_doc_type_falls_back_to_aps_rules(self):
        result = validate_deal({}, "some_future_form")
        assert not result.ok  # APS required fields kick in


class TestLease:
    def test_valid_lease_passes(self):
        assert validate_deal(_valid_lease(), "lease").ok

    def test_missing_rent_is_error(self):
        data = _valid_lease()
        del data["monthly_rent"]
        assert not validate_deal(data, "lease").ok

    def test_zero_rent_is_error(self):
        data = _valid_lease()
        data["monthly_rent"] = "free"
        assert not validate_deal(data, "lease").ok

    def test_lease_end_before_start_is_error(self):
        data = _valid_lease()
        data["lease_start_date"] = "2027-08-01"
        data["lease_end_date"] = "2026-08-01"
        result = validate_deal(data, "lease")
        assert not result.ok
        assert any("lease end" in e.lower() for e in result.errors)

    def test_oversized_deposit_is_warning(self):
        data = _valid_lease()
        data["rent_deposit"] = 10000  # 4 months of 2500
        result = validate_deal(data, "lease")
        assert result.ok
        assert any("deposit" in w.lower() for w in result.warnings)

    def test_negative_deposit_is_error(self):
        data = _valid_lease()
        data["rent_deposit"] = "-100"
        assert not validate_deal(data, "lease").ok


class TestAmendmentAndWaiver:
    def test_valid_amendment_passes(self):
        assert validate_deal(_valid_amendment(), "amendment").ok

    def test_amendment_requires_original_date_and_description(self):
        for missing in ("original_agreement_date", "amendment_description"):
            data = _valid_amendment()
            del data[missing]
            assert not validate_deal(data, "amendment").ok, missing

    def test_amendment_bad_date_is_error(self):
        data = _valid_amendment()
        data["amendment_date"] = "sometime in july"
        assert not validate_deal(data, "amendment").ok

    def test_waiver_requires_condition_and_original_date(self):
        data = {
            "buyer_1": "John Smith",
            "seller_1": "Jane Doe",
            "property_street_number": "123",
            "property_street_name": "Main St",
            "property_city": "Toronto",
            "original_agreement_date": "2026-06-15",
            "condition_waived": "Financing condition per Schedule A",
            "waiver_date": "2026-07-05",
        }
        assert validate_deal(data, "waiver").ok

        for missing in ("original_agreement_date", "condition_waived"):
            broken = dict(data)
            del broken[missing]
            assert not validate_deal(broken, "waiver").ok, missing


class TestValidationResult:
    def test_summary_lists_errors_and_warnings(self):
        r = ValidationResult()
        r.add_error("bad thing")
        r.add_warning("iffy thing")
        s = r.summary()
        assert "bad thing" in s
        assert "iffy thing" in s
        assert not r.ok
