"""Listing source adapter protocol.

Any data source (TRREB AMP API, Playwright scrape, Matrix CSV, CREB, etc.)
produces `RawListing` records that the upsert pipeline can consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, AsyncIterator, Protocol, runtime_checkable


@dataclass
class RawListing:
    """Normalized cross-source representation of one MLS listing cycle.

    Field values mirror the `listings` table columns so the upsert service
    doesn't need per-source branching.
    """

    # Identity (required)
    source: str               # "TRREB", "CREB", ...
    mls_number: str
    status: str               # Active | Sold | Expired | Terminated | Suspended | Conditional

    # Address (required — address_raw at minimum)
    address_raw: str
    street_number: str | None = None
    street_name: str | None = None
    unit: str | None = None
    city: str | None = None
    province: str | None = "ON"
    postal_code: str | None = None

    # Geocoding (optional — filled in later if source doesn't provide)
    lat: float | None = None
    lng: float | None = None

    # Listing details
    list_price: float | None = None
    sold_price: float | None = None
    commencement_date: date | None = None
    expiry_date: date | None = None
    sold_date: date | None = None
    terminated_date: date | None = None

    # Attribution
    listing_agent_name: str | None = None
    listing_agent_id: str | None = None
    brokerage_name: str | None = None
    brokerage_id: str | None = None

    # Property attributes
    property_type: str | None = None
    beds: int | None = None
    baths: float | None = None
    sqft: int | None = None
    days_on_market: int | None = None

    remarks: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    last_seen_at: datetime | None = None


@runtime_checkable
class ListingSource(Protocol):
    """A pluggable MLS data source."""

    name: str  # e.g. "TRREB", "TRREB-CSV", "TRREB-AMP-API"

    async def fetch_changes(self, since: datetime) -> AsyncIterator[RawListing]:
        """Yield listings whose status changed since `since`.

        Implementations may fetch a broader window and filter internally.
        Must be idempotent — callers can re-run with the same `since`.
        """
        ...
        # The following line is unreachable but tells type-checkers this is an async generator.
        if False:  # pragma: no cover
            yield  # type: ignore[unreachable]
