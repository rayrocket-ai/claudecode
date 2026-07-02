"""Unit tests for money/date formatting that lands on legal forms."""

from integrations.transactiondesk import (
    _flatten_deal_data,
    _normalize_number,
    _num_to_words,
    _parse_date,
)


class TestNumToWords:
    def test_zero(self):
        assert _num_to_words(0) == "Zero"

    def test_small(self):
        assert _num_to_words(7) == "Seven"
        assert _num_to_words(19) == "Nineteen"

    def test_tens(self):
        assert _num_to_words(42) == "Forty Two"
        assert _num_to_words(90) == "Ninety"

    def test_hundreds(self):
        assert _num_to_words(815) == "Eight Hundred Fifteen"

    def test_typical_prices(self):
        assert _num_to_words(800_000) == "Eight Hundred Thousand"
        assert _num_to_words(1_250_000) == "One Million Two Hundred Fifty Thousand"
        assert _num_to_words(999_999) == (
            "Nine Hundred Ninety Nine Thousand Nine Hundred Ninety Nine"
        )

    def test_billion(self):
        assert _num_to_words(2_000_000_000) == "Two Billion"


class TestNormalizeNumber:
    def test_int_and_float(self):
        assert _normalize_number(800000) == 800000.0
        assert _normalize_number(800000.5) == 800000.5

    def test_formatted_strings(self):
        assert _normalize_number("$800,000") == 800000.0
        assert _normalize_number(" 1 250 000 ") == 1250000.0

    def test_garbage(self):
        assert _normalize_number("eight hundred") == 0.0
        assert _normalize_number(None) == 0.0


class TestParseDate:
    def test_iso(self):
        assert _parse_date("2026-07-15") == ("15", "July", "2026")

    def test_us_format(self):
        assert _parse_date("07/15/2026") == ("15", "July", "2026")

    def test_long_format(self):
        assert _parse_date("July 15, 2026") == ("15", "July", "2026")

    def test_empty(self):
        assert _parse_date("") == ("", "", "")


class TestFlattenDealData:
    def test_price_and_words(self):
        flat = _flatten_deal_data({"purchase_price": 800000})
        assert flat["purchase_price_formatted"] == "800,000.00"
        assert flat["purchase_price_words"] == "Eight Hundred Thousand"

    def test_dates_split(self):
        flat = _flatten_deal_data({"closing_date": "2026-09-30"})
        assert flat["closing_date_d"] == "30"
        assert flat["closing_date_mmmm"] == "September"
        assert flat["closing_date_yy"] == "2026"

    def test_province_default(self):
        flat = _flatten_deal_data({})
        assert flat["property_province"] == "Ontario"

    def test_direct_copies(self):
        flat = _flatten_deal_data({"buyer_1": "Jane Doe", "property_city": "Toronto"})
        assert flat["buyer_1"] == "Jane Doe"
        assert flat["property_city"] == "Toronto"
