"""CSV importer for TRREB Matrix / Stratus exports.

Matrix's "Export to CSV" is the fastest path to real data while we wait
for AMP Data API access. Column names vary slightly between exports and
display settings, so we accept a lenient set of aliases.

Usage:
    async with session_scope() as session:
        summary = await import_csv(session, Path("matrix_export.csv"))
        print(summary)
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import IO, Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.listing_source import RawListing
from workers.upsert import upsert_listing

logger = logging.getLogger(__name__)


# ── Column aliasing ────────────────────────────────────────────────────
#
# Matrix lets the user pick any "display" to export. We accept many common
# aliases so the importer works across customizations. Header matching is
# case-insensitive; whitespace and punctuation are stripped.

_ALIASES: dict[str, tuple[str, ...]] = {
    "mls_number": ("mlsnumber", "mls", "mlsno", "listingid", "listingnumber", "ml"),
    "status": ("status", "listingstatus", "stat", "mlsstatus"),
    "address": ("address", "streetaddress", "fulladdress", "propertyaddress"),
    "street_number": ("stno", "streetnumber", "houseno", "housenumber"),
    "street_name": ("streetname", "stname", "street"),
    "street_type": ("streettype", "sttype", "streetabbrev"),
    "street_dir": ("streetdirection", "stdir", "direction", "streetdir"),
    "unit": ("unit", "unitnumber", "apt", "suite", "unitno"),
    "city": ("city", "municipality", "town"),
    "province": ("province", "prov", "state"),
    "postal_code": ("postalcode", "postal", "zip", "zipcode"),
    "lat": ("latitude", "lat"),
    "lng": ("longitude", "lng", "long", "lon"),
    "list_price": ("listprice", "price", "askingprice", "lp"),
    "sold_price": ("soldprice", "saleprice", "closedprice", "sp"),
    "commencement_date": ("listdate", "listingdate", "commencementdate", "startdate", "onmarketdate"),
    "expiry_date": ("expirydate", "expirationdate", "expires", "expiry"),
    "sold_date": ("solddate", "closedate", "closingdate", "saledate"),
    "terminated_date": ("terminateddate", "terminationdate", "cancelleddate", "canceldate"),
    "listing_agent_name": ("listagent", "listingagent", "agent", "listagentname"),
    "listing_agent_id": ("listagentid", "agentid", "listingagentid"),
    "brokerage_name": ("listoffice", "listingoffice", "brokerage", "office"),
    "brokerage_id": ("listofficeid", "brokerageid", "officeid"),
    "property_type": ("propertytype", "type", "type1", "propertysubtype"),
    "beds": ("beds", "bedrooms", "bedroomstotal", "br"),
    "baths": ("baths", "bathrooms", "bathroomstotal", "ba"),
    "sqft": ("sqft", "squarefeet", "livingarea"),
    "days_on_market": ("dom", "daysonmarket", "cdom"),
    "remarks": ("remarks", "publicremarks", "description", "comments"),
}

_ALIAS_INDEX: dict[str, str] = {
    alias: canonical for canonical, aliases in _ALIASES.items() for alias in aliases
}

_TRREB_STATUS_MAP = {
    # Matrix / Stratus short codes -> our canonical enum
    "A": "Active", "ACT": "Active", "ACTIVE": "Active", "AVL": "Active",
    "S": "Sold", "SLD": "Sold", "SOLD": "Sold", "CLD": "Sold", "CLOSED": "Sold",
    "SC": "Conditional", "SC-LB": "Conditional", "PC": "Conditional",
    "CONDITIONAL": "Conditional", "PENDING": "Conditional",
    "EXP": "Expired", "EXPIRED": "Expired",
    "TER": "Terminated", "TERM": "Terminated", "TERMINATED": "Terminated",
    "SUS": "Suspended", "SUSP": "Suspended", "SUSPENDED": "Suspended",
    "U": "Suspended",  # "Unavailable" in some boards
}


def _key(header: str) -> str:
    return "".join(ch for ch in header.lower() if ch.isalnum())


def _map_headers(headers: Iterable[str]) -> dict[str, str]:
    """Return {canonical_field: original_header}."""
    mapped: dict[str, str] = {}
    for h in headers:
        k = _key(h)
        if k in _ALIAS_INDEX:
            canonical = _ALIAS_INDEX[k]
            mapped.setdefault(canonical, h)
    return mapped


def _parse_money(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return float(v.replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _parse_int(v: str | None) -> int | None:
    if not v:
        return None
    try:
        return int(float(v.replace(",", "").strip()))
    except (ValueError, AttributeError):
        return None


def _parse_float(v: str | None) -> float | None:
    if not v:
        return None
    try:
        return float(v.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


_DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d",
    "%m/%d/%Y", "%m-%d-%Y",
    "%d/%m/%Y", "%d-%m-%Y",
    "%b %d, %Y", "%B %d, %Y",
    "%Y-%m-%dT%H:%M:%S",
)


def _parse_date(v: str | None) -> date | None:
    if not v:
        return None
    v = v.strip()
    if not v:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_status(v: str | None) -> str | None:
    if not v:
        return None
    key = v.strip().upper()
    return _TRREB_STATUS_MAP.get(key, v.strip().title())


def _compose_address(row: dict[str, str], cols: dict[str, str]) -> str:
    """Build a raw address string from whichever columns are present."""
    if "address" in cols and row.get(cols["address"]):
        return row[cols["address"]]
    parts: list[str] = []
    for c in ("street_number", "street_name", "street_type", "street_dir", "unit"):
        if c in cols and row.get(cols[c]):
            parts.append(row[cols[c]].strip())
    street = " ".join(p for p in parts if p)
    tail: list[str] = [street]
    for c in ("city", "province", "postal_code"):
        if c in cols and row.get(cols[c]):
            tail.append(row[cols[c]].strip())
    return ", ".join(p for p in tail if p)


def row_to_raw(row: dict[str, str], cols: dict[str, str], source: str) -> RawListing | None:
    """Map one CSV row to a RawListing. Returns None if required fields missing."""

    def g(field: str) -> str | None:
        col = cols.get(field)
        if not col:
            return None
        v = row.get(col)
        if v is None:
            return None
        v = v.strip()
        return v or None

    mls = g("mls_number")
    status = _normalize_status(g("status"))
    address = _compose_address(row, cols)
    if not mls or not status or not address:
        return None

    return RawListing(
        source=source,
        mls_number=mls,
        status=status,
        address_raw=address,
        street_number=g("street_number"),
        street_name=g("street_name"),
        unit=g("unit"),
        city=g("city"),
        province=g("province") or "ON",
        postal_code=g("postal_code"),
        lat=_parse_float(g("lat")),
        lng=_parse_float(g("lng")),
        list_price=_parse_money(g("list_price")),
        sold_price=_parse_money(g("sold_price")),
        commencement_date=_parse_date(g("commencement_date")),
        expiry_date=_parse_date(g("expiry_date")),
        sold_date=_parse_date(g("sold_date")),
        terminated_date=_parse_date(g("terminated_date")),
        listing_agent_name=g("listing_agent_name"),
        listing_agent_id=g("listing_agent_id"),
        brokerage_name=g("brokerage_name"),
        brokerage_id=g("brokerage_id"),
        property_type=g("property_type"),
        beds=_parse_int(g("beds")),
        baths=_parse_float(g("baths")),
        sqft=_parse_int(g("sqft")),
        days_on_market=_parse_int(g("days_on_market")),
        remarks=g("remarks"),
        raw_payload=dict(row),
        last_seen_at=datetime.now(timezone.utc),
    )


@dataclass
class ImportSummary:
    rows_read: int = 0
    rows_skipped: int = 0
    listings_new: int = 0
    listings_updated: int = 0
    properties_new: int = 0


async def import_csv(
    session: AsyncSession,
    path_or_stream: Path | IO[str],
    source: str = "TRREB-CSV",
) -> ImportSummary:
    """Import a Matrix/Stratus CSV into the database.

    Accepts a file path or an already-opened text stream (for FastAPI uploads).
    The caller commits.
    """
    summary = ImportSummary()

    if isinstance(path_or_stream, Path):
        stream = path_or_stream.open("r", encoding="utf-8-sig", newline="")
        close_after = True
    else:
        stream = path_or_stream
        close_after = False

    try:
        reader = csv.DictReader(stream)
        cols = _map_headers(reader.fieldnames or [])
        if "mls_number" not in cols or "status" not in cols:
            raise ValueError(
                "CSV missing required columns (MLS number + status). "
                f"Detected columns: {sorted(cols.keys())}"
            )

        for row in reader:
            summary.rows_read += 1
            raw = row_to_raw(row, cols, source)
            if raw is None:
                summary.rows_skipped += 1
                continue
            result = await upsert_listing(session, raw)
            if result.is_new_property:
                summary.properties_new += 1
            if result.is_new_listing:
                summary.listings_new += 1
            else:
                summary.listings_updated += 1
    finally:
        if close_after:
            stream.close()

    return summary
