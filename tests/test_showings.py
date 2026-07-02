"""Unit tests for BrokerBay showing formatting and tour parsing."""

from bot.handlers.tour import _parse_addresses, _parse_time_window
from integrations.brokerbay import (
    _md,
    format_showing,
    get_showing_address,
    get_showing_id,
    google_maps_link,
)


class TestFormatShowing:
    def test_basic_fields(self):
        msg = format_showing({
            "id": "42",
            "status": "confirmed",
            "address": "12 Main St, Toronto",
            "date": "2026-07-15",
            "startTime": "2:00 PM",
            "endTime": "2:30 PM",
        })
        assert "Showing #42" in msg
        assert "CONFIRMED" in msg
        assert "12 Main St, Toronto" in msg
        assert "2:00 PM - 2:30 PM" in msg

    def test_alternate_field_names(self):
        msg = format_showing({
            "showingId": "7",
            "showingStatus": "pending",
            "listing": {"fullAddress": "9 Elm Ave", "mls": "W1234567"},
            "requestingAgent": {"fullName": "Jane Roe", "officeName": "ABC Realty"},
        })
        assert "Showing #7" in msg
        assert "9 Elm Ave" in msg
        assert "W1234567" in msg
        assert "Jane Roe" in msg

    def test_markdown_unsafe_data_escaped(self):
        msg = format_showing({
            "id": "1",
            "status": "pending",
            "address": "12 King_West *Unit 5*",
            "notes": "lockbox_code follows",
        })
        assert r"King\_West" in msg
        assert r"\*Unit 5\*" in msg
        assert r"lockbox\_code" in msg


class TestShowingAccessors:
    def test_id_variants(self):
        assert get_showing_id({"id": 5}) == "5"
        assert get_showing_id({"showingId": "abc"}) == "abc"
        assert get_showing_id({}) == ""

    def test_address_variants(self):
        assert get_showing_address({"address": "1 A St"}) == "1 A St"
        assert get_showing_address({"property": {"address": "2 B St"}}) == "2 B St"
        assert get_showing_address({}) == ""

    def test_maps_link_encodes(self):
        link = google_maps_link("12 Main St, Toronto")
        assert link.startswith("https://www.google.com/maps/search/")
        assert " " not in link


class TestTourParsers:
    def test_parse_addresses_strips_bullets(self):
        text = "123 Maple Ave, Toronto\n- 456 Oak Blvd, Vaughan\n• 789 Pine Rd"
        assert _parse_addresses(text) == [
            "123 Maple Ave, Toronto",
            "456 Oak Blvd, Vaughan",
            "789 Pine Rd",
        ]

    def test_parse_addresses_filters_junk(self):
        assert _parse_addresses("hello there\nno digits here") == []

    def test_time_window_formats(self):
        assert _parse_time_window("10am - 4pm") == ("10:00 AM", "04:00 PM")
        assert _parse_time_window("10:00-16:00") == ("10:00 AM", "04:00 PM")
        assert _parse_time_window("10am to 4pm") == ("10:00 AM", "04:00 PM")

    def test_time_window_invalid(self):
        assert _parse_time_window("whenever") is None


class TestMdEscape:
    def test_escapes_markdown_chars(self):
        assert _md("a_b*c`d[e") == r"a\_b\*c\`d\[e"

    def test_non_string(self):
        assert _md(42) == "42"
