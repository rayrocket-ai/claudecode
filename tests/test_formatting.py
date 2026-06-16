"""Unit tests for forms.formatting — pure helpers, no external deps."""

from datetime import datetime

import pytest

from forms.formatting import (
    normalize_number,
    format_currency,
    num_to_words,
    dollars_to_words,
    parse_date,
    date_parts,
)


class TestNormalizeNumber:
    @pytest.mark.parametrize("value,expected", [
        (800000, 800000.0),
        (800000.50, 800000.50),
        ("800000", 800000.0),
        ("$800,000", 800000.0),
        ("$ 1,250,000.00", 1250000.0),
        ("  500000 ", 500000.0),
        ("", 0.0),
        ("not a number", 0.0),
        (None, 0.0),
        ("$", 0.0),
        (True, 0.0),   # bool must not be treated as 1
    ])
    def test_normalize(self, value, expected):
        assert normalize_number(value) == expected


class TestFormatCurrency:
    def test_thousands_separators(self):
        assert format_currency(800000) == "800,000.00"

    def test_from_string(self):
        assert format_currency("$1,250,000") == "1,250,000.00"

    def test_cents(self):
        assert format_currency(1250.5) == "1,250.50"


class TestNumToWords:
    @pytest.mark.parametrize("n,expected", [
        (0, "Zero"),
        (5, "Five"),
        (19, "Nineteen"),
        (20, "Twenty"),
        (21, "Twenty One"),
        (100, "One Hundred"),
        (115, "One Hundred Fifteen"),
        (800000, "Eight Hundred Thousand"),
        (1000000, "One Million"),
        (1250000, "One Million Two Hundred Fifty Thousand"),
    ])
    def test_words(self, n, expected):
        assert num_to_words(n) == expected


class TestDollarsToWords:
    def test_whole_dollars(self):
        assert dollars_to_words(800000) == "Eight Hundred Thousand"

    def test_strips_currency_symbols(self):
        assert dollars_to_words("$800,000") == "Eight Hundred Thousand"

    def test_with_cents(self):
        assert dollars_to_words(1250.50) == "One Thousand Two Hundred Fifty and 50/100"

    def test_cents_rounding_guard(self):
        # 99.999 should round to 100.00 -> "One Hundred", not "Ninety Nine and 100/100"
        assert dollars_to_words(99.999) == "One Hundred"


class TestParseDate:
    @pytest.mark.parametrize("value", [
        "2026-07-15",
        "07/15/2026",
        "July 15, 2026",
        "Jul 15, 2026",
        "2026/07/15",
    ])
    def test_parses_common_formats_to_july_15(self, value):
        dt = parse_date(value)
        assert dt == datetime(2026, 7, 15)

    def test_north_american_day_order(self):
        # 03/04/2026 should be March 4 (month-first), not April 3.
        assert parse_date("03/04/2026") == datetime(2026, 3, 4)

    def test_unparseable_returns_none(self):
        assert parse_date("definitely not a date") is None

    def test_empty_returns_none(self):
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_passthrough_datetime(self):
        dt = datetime(2026, 1, 1)
        assert parse_date(dt) is dt


class TestDateParts:
    def test_iso_date(self):
        assert date_parts("2026-07-15") == ("15", "July", "2026")

    def test_unparseable_passthrough(self):
        # Preserves prior behaviour: original string, empty month/year.
        assert date_parts("sometime soon") == ("sometime soon", "", "")

    def test_empty(self):
        assert date_parts("") == ("", "", "")
