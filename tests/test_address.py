"""Golden tests for the address normalizer.

These are the shapes Matrix / Stratus actually output — variations
include unit markers in several positions, postal codes with/without
spaces, and comma-separated vs space-separated segments.
"""

from __future__ import annotations

import pytest

from core.address import normalize


def test_basic_address_with_postal():
    n = normalize("123 Main St, Toronto, ON M5V 2T6")
    assert n.street_number == "123"
    assert n.street_name == "MAIN"
    assert n.street_type == "ST"
    assert n.unit is None
    assert n.city == "Toronto"
    assert n.postal_code == "M5V 2T6"
    assert n.canonical_key == "M5V2T6|123|MAIN|"


def test_directional_suffix():
    n = normalize("456 Queen Street W, Toronto, ON M5V 2B3")
    assert n.street_number == "456"
    assert n.street_name == "QUEEN"
    assert n.street_type == "ST"
    assert n.street_dir == "W"
    assert n.canonical_key == "M5V2B3|456|QUEEN|"


def test_unit_hash_prefix():
    n = normalize("#4B - 123 Main St, Toronto, ON M5V 2T6")
    assert n.unit == "4B"
    assert n.street_number == "123"
    assert n.street_name == "MAIN"
    assert n.canonical_key == "M5V2T6|123|MAIN|4B"


def test_unit_comma_separated():
    n = normalize("123 Main St, Unit 4B, Toronto, ON M5V 2T6")
    assert n.unit == "4B"
    assert n.street_number == "123"
    assert n.street_name == "MAIN"
    assert n.canonical_key == "M5V2T6|123|MAIN|4B"


def test_unit_suite_keyword():
    n = normalize("789 King West, Suite 305, Toronto, ON M5V 1K1")
    assert n.unit == "305"
    assert n.street_number == "789"
    assert n.street_name == "KING"
    # "WEST" here is a directional
    assert n.street_dir == "W"


def test_expands_street_type_abbreviation():
    n = normalize("10 Dundas Square, Toronto, ON M5B 1C4")
    assert n.street_type == "SQ"
    n2 = normalize("10 Dundas Sq, Toronto, ON M5B 1C4")
    assert n.canonical_key == n2.canonical_key


def test_same_property_different_unit_formats_match():
    a = normalize("123 Main St, Unit 4B, Toronto, ON M5V 2T6")
    b = normalize("#4B - 123 Main St, Toronto, ON M5V 2T6")
    c = normalize("123 MAIN ST #4B, TORONTO, ON M5V 2T6")
    assert a.canonical_key == b.canonical_key == c.canonical_key


def test_missing_postal_falls_back_to_city():
    n = normalize("99 Yonge St, Toronto")
    assert n.postal_code is None
    assert n.canonical_key.startswith("TORONTO|99|YONGE|")


def test_different_unit_produces_different_key():
    a = normalize("123 Main St, Unit 4B, Toronto, ON M5V 2T6")
    b = normalize("123 Main St, Unit 5C, Toronto, ON M5V 2T6")
    assert a.canonical_key != b.canonical_key


def test_no_postal_in_raw_but_hint_provided():
    n = normalize("99 Yonge St, Toronto", postal_hint="M5E 1J1")
    assert n.postal_code == "M5E 1J1"


def test_empty_raises():
    with pytest.raises(ValueError):
        normalize("")


def test_case_insensitive_and_whitespace_tolerant():
    a = normalize("  123  main   st, toronto,  on  m5v 2t6  ")
    b = normalize("123 MAIN ST, TORONTO, ON M5V 2T6")
    assert a.canonical_key == b.canonical_key
