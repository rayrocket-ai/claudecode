"""Canadian address normalization.

Produces a `canonical_key` used to collapse multiple listings of the same
physical property (each relisting gets a new MLS number) into one
`CanonicalProperty` row.

Strategy:
  1. Uppercase, trim, collapse whitespace.
  2. Strip unit markers ("#4B", "UNIT 4B", "APT 4B", "4B -", ", UNIT 4B",
     "suite 4B") and remember the unit separately.
  3. Parse street number, name, type, and directional.
  4. If libpostal / `postal` is installed, use it as the authoritative
     parser; otherwise use regex parsing (good enough for Matrix/TRREB
     exports, which are fairly structured).
  5. Compose `canonical_key = POSTAL|NUMBER|STREET_NAME|UNIT`
     (fallback to `CITY|NUMBER|STREET_NAME|UNIT` when no postal code).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

try:  # libpostal is optional
    from postal.parser import parse_address as _libpostal_parse  # type: ignore[import-not-found]

    _HAS_LIBPOSTAL = True
except Exception:  # pragma: no cover — only triggered when libpostal absent
    _HAS_LIBPOSTAL = False


_STREET_TYPES = {
    "STREET": "ST", "ST": "ST", "ST.": "ST",
    "AVENUE": "AVE", "AVE": "AVE", "AVE.": "AVE", "AV": "AVE",
    "ROAD": "RD", "RD": "RD", "RD.": "RD",
    "DRIVE": "DR", "DR": "DR", "DR.": "DR",
    "BOULEVARD": "BLVD", "BLVD": "BLVD", "BLVD.": "BLVD",
    "COURT": "CRT", "CRT": "CRT", "CT": "CRT",
    "CRESCENT": "CRES", "CRES": "CRES",
    "CIRCLE": "CIR", "CIR": "CIR", "CIRC": "CIR",
    "LANE": "LANE", "LN": "LANE",
    "PLACE": "PL", "PL": "PL",
    "PARKWAY": "PKWY", "PKWY": "PKWY", "PKY": "PKWY",
    "TERRACE": "TERR", "TER": "TERR", "TERR": "TERR",
    "SQUARE": "SQ", "SQ": "SQ",
    "TRAIL": "TRL", "TRL": "TRL",
    "WAY": "WAY",
    "GARDENS": "GDNS", "GDNS": "GDNS",
    "HEIGHTS": "HTS", "HTS": "HTS",
    "GROVE": "GRV", "GRV": "GRV",
    "GATE": "GATE",
    "ROW": "ROW",
    "MEWS": "MEWS",
    "COMMON": "COMMON",
    "COMMONS": "COMMONS",
    "PROMENADE": "PROM", "PROM": "PROM",
    "HIGHWAY": "HWY", "HWY": "HWY",
    "CLOSE": "CLOSE",
}

_DIR_MAP = {
    "NORTH": "N", "N": "N",
    "SOUTH": "S", "S": "S",
    "EAST": "E", "E": "E",
    "WEST": "W", "W": "W",
    "NORTHEAST": "NE", "NE": "NE",
    "NORTHWEST": "NW", "NW": "NW",
    "SOUTHEAST": "SE", "SE": "SE",
    "SOUTHWEST": "SW", "SW": "SW",
}

_POSTAL_RE = re.compile(r"\b([A-Z]\d[A-Z])\s*(\d[A-Z]\d)\b")
_UNIT_PATTERNS = [
    # "#4B - 123 Main St"  or  "4B - 123 Main St"
    re.compile(r"^\s*#?\s*([A-Z0-9\-]+)\s*[-,]\s*(?=\d)", re.IGNORECASE),
    # ", Unit 4B" / ", Apt 4B" / ", Suite 4B"
    re.compile(r",\s*(?:UNIT|APT|APARTMENT|SUITE|STE|PH)\s*\.?\s*([A-Z0-9\-]+)", re.IGNORECASE),
    # "UNIT 4B" / "APT 4B" anywhere before the street number
    re.compile(r"\b(?:UNIT|APT|APARTMENT|SUITE|STE|PH)\s*\.?\s*([A-Z0-9\-]+)\b", re.IGNORECASE),
    # "#4B" token
    re.compile(r"#\s*([A-Z0-9\-]+)"),
]


@dataclass
class NormalizedAddress:
    address_raw: str
    canonical_key: str
    street_number: str | None = None
    street_name: str | None = None
    street_type: str | None = None
    street_dir: str | None = None
    unit: str | None = None
    city: str | None = None
    province: str = "ON"
    postal_code: str | None = None


def _extract_postal(text: str) -> tuple[str | None, str]:
    m = _POSTAL_RE.search(text)
    if not m:
        return None, text
    postal = f"{m.group(1)} {m.group(2)}"
    text = _POSTAL_RE.sub("", text).rstrip(", ").strip()
    return postal, text


def _extract_unit(text: str) -> tuple[str | None, str]:
    for pat in _UNIT_PATTERNS:
        m = pat.search(text)
        if m:
            unit = m.group(1).upper().strip()
            text = pat.sub(" ", text, count=1)
            text = re.sub(r"\s+", " ", text).strip(" ,-")
            return unit, text
    return None, text


def _split_commas(text: str) -> list[str]:
    return [p.strip() for p in text.split(",") if p.strip()]


def _classify_street_type(token: str) -> str | None:
    return _STREET_TYPES.get(token.upper())


def _classify_dir(token: str) -> str | None:
    return _DIR_MAP.get(token.upper())


def _parse_street_line(line: str) -> dict[str, str | None]:
    """Parse "123 Main St W" → number/name/type/dir."""
    tokens = line.split()
    if not tokens:
        return {"number": None, "name": None, "type": None, "dir": None}

    number = None
    if re.match(r"^\d+[A-Z]?$", tokens[0], re.IGNORECASE):
        number = tokens[0].upper()
        tokens = tokens[1:]

    # Trailing directional? ("123 MAIN ST W")
    street_dir = None
    if tokens and _classify_dir(tokens[-1]):
        street_dir = _classify_dir(tokens[-1])
        tokens = tokens[:-1]

    # Trailing street type? ("123 MAIN ST")
    street_type = None
    if tokens and _classify_street_type(tokens[-1]):
        street_type = _classify_street_type(tokens[-1])
        tokens = tokens[:-1]

    street_name = " ".join(tokens).upper() if tokens else None
    return {
        "number": number,
        "name": street_name,
        "type": street_type,
        "dir": street_dir,
    }


def _compose_key(
    postal: str | None,
    number: str | None,
    name: str | None,
    unit: str | None,
    city: str | None,
) -> str:
    unit_part = (unit or "").upper()
    num_part = (number or "").upper()
    name_part = (name or "").upper()
    if postal:
        return f"{postal.replace(' ', '')}|{num_part}|{name_part}|{unit_part}"
    city_part = (city or "").upper()
    return f"{city_part}|{num_part}|{name_part}|{unit_part}"


def normalize(raw: str, city_hint: str | None = None, postal_hint: str | None = None) -> NormalizedAddress:
    """Normalize a free-form Canadian address string.

    `city_hint` / `postal_hint` are used when the raw string doesn't contain
    them (e.g. CSVs that split address across multiple columns).
    """
    if not raw or not raw.strip():
        raise ValueError("empty address")

    original = raw
    text = re.sub(r"\s+", " ", raw.strip().upper())

    # 1. Extract postal code (from anywhere in the string)
    postal, text = _extract_postal(text)
    if not postal and postal_hint:
        postal, _ = _extract_postal(postal_hint.upper())

    # 2. Extract unit
    unit, text = _extract_unit(text)

    # 3. Split by comma: first segment is usually street, later segments are city/province
    segments = _split_commas(text)

    street_line: str = ""
    city: str | None = None
    province = "ON"
    if segments:
        street_line = segments[0]
        if len(segments) >= 2:
            city = segments[1]
        if len(segments) >= 3:
            prov_token = segments[2].strip().split()[0]
            if len(prov_token) == 2:
                province = prov_token
    if not city and city_hint:
        city = city_hint.upper().strip()

    # 4. Prefer libpostal if installed (wraps our segments with a more forgiving parse)
    if _HAS_LIBPOSTAL:
        parsed = dict(_libpostal_parse(original))
        number = (parsed.get("house_number") or "").strip().upper() or None
        name_raw = (parsed.get("road") or "").strip().upper() or street_line
        parts = _parse_street_line(name_raw) if name_raw else {}
        street_number = number or parts.get("number")
        street_name = parts.get("name") or (name_raw if name_raw else None)
        street_type = parts.get("type")
        street_dir = parts.get("dir")
        if not unit:
            unit_lp = (parsed.get("unit") or "").strip().upper() or None
            if unit_lp:
                unit = unit_lp
        if not city:
            city_lp = parsed.get("city")
            city = city_lp.upper().strip() if city_lp else city
        if not postal:
            postal_lp = parsed.get("postcode")
            postal = postal_lp.upper().strip() if postal_lp else postal
    else:
        parts = _parse_street_line(street_line)
        street_number = parts["number"]
        street_name = parts["name"]
        street_type = parts["type"]
        street_dir = parts["dir"]

    canonical_key = _compose_key(postal, street_number, street_name, unit, city)

    return NormalizedAddress(
        address_raw=original,
        canonical_key=canonical_key,
        street_number=street_number,
        street_name=street_name,
        street_type=street_type,
        street_dir=street_dir,
        unit=unit,
        city=city.title() if city else None,
        province=province,
        postal_code=postal,
    )
