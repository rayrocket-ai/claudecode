"""Idempotent upsert of raw listings into the normalized schema.

One entry point: `upsert_listing(session, raw)`. Given a `RawListing` from
any source, it:
  1. Normalizes the address → `canonical_key`.
  2. Finds or creates a `CanonicalProperty` for that key.
  3. Upserts the `Listing` row keyed on `(source, mls_number)`.
  4. Recomputes `CanonicalProperty.current_status` + `last_listing_id`
     from the full listing history.

Re-running with the same input is a no-op on the business fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.listing_source import RawListing
from core.address import normalize
from core.status import derive_current_status, latest_listing
from db.models import CanonicalProperty, Listing


@dataclass
class UpsertResult:
    canonical_property_id: str
    listing_id: str
    is_new_property: bool
    is_new_listing: bool


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _get_or_create_property(
    session: AsyncSession, raw: RawListing
) -> tuple[CanonicalProperty, bool]:
    address_source = raw.address_raw
    norm = normalize(
        address_source,
        city_hint=raw.city,
        postal_hint=raw.postal_code,
    )

    result = await session.execute(
        select(CanonicalProperty).where(
            CanonicalProperty.canonical_key == norm.canonical_key
        )
    )
    prop = result.scalar_one_or_none()
    if prop is not None:
        # Backfill any fields the earlier record was missing.
        if not prop.lat and raw.lat:
            prop.lat = raw.lat
        if not prop.lng and raw.lng:
            prop.lng = raw.lng
        if not prop.postal_code and norm.postal_code:
            prop.postal_code = norm.postal_code
        if not prop.property_type and raw.property_type:
            prop.property_type = raw.property_type
        if not prop.beds and raw.beds:
            prop.beds = raw.beds
        if not prop.baths and raw.baths:
            prop.baths = raw.baths
        if not prop.sqft and raw.sqft:
            prop.sqft = raw.sqft
        return prop, False

    prop = CanonicalProperty(
        address_raw=norm.address_raw,
        canonical_key=norm.canonical_key,
        street_number=norm.street_number,
        street_name=norm.street_name,
        street_type=norm.street_type,
        street_dir=norm.street_dir,
        unit=norm.unit,
        city=norm.city or raw.city,
        province=norm.province or (raw.province or "ON"),
        postal_code=norm.postal_code or raw.postal_code,
        lat=raw.lat,
        lng=raw.lng,
        property_type=raw.property_type,
        beds=raw.beds,
        baths=raw.baths,
        sqft=raw.sqft,
        current_status="Unknown",
    )
    session.add(prop)
    await session.flush()
    return prop, True


async def _upsert_listing_row(
    session: AsyncSession, prop: CanonicalProperty, raw: RawListing
) -> tuple[Listing, bool]:
    result = await session.execute(
        select(Listing).where(
            (Listing.source == raw.source) & (Listing.mls_number == raw.mls_number)
        )
    )
    listing = result.scalar_one_or_none()
    is_new = listing is None
    if is_new:
        listing = Listing(
            canonical_property_id=prop.id,
            source=raw.source,
            mls_number=raw.mls_number,
            status=raw.status,
        )
        session.add(listing)

    # Update mutable fields (re-importing a CSV should refresh values)
    listing.status = raw.status
    listing.list_price = raw.list_price
    listing.sold_price = raw.sold_price
    listing.commencement_date = raw.commencement_date
    listing.expiry_date = raw.expiry_date
    listing.sold_date = raw.sold_date
    listing.terminated_date = raw.terminated_date
    listing.listing_agent_name = raw.listing_agent_name
    listing.listing_agent_id = raw.listing_agent_id
    listing.brokerage_name = raw.brokerage_name
    listing.brokerage_id = raw.brokerage_id
    listing.days_on_market = raw.days_on_market
    listing.remarks = raw.remarks
    listing.raw_payload = raw.raw_payload or {}
    listing.last_seen_at = raw.last_seen_at or _utcnow()

    await session.flush()
    return listing, is_new


async def _recompute_property_status(
    session: AsyncSession, prop: CanonicalProperty
) -> None:
    result = await session.execute(
        select(Listing).where(Listing.canonical_property_id == prop.id)
    )
    listings = list(result.scalars().all())
    prop.current_status = derive_current_status(listings)
    latest = latest_listing(listings)
    prop.last_listing_id = latest.id if latest else None


async def upsert_listing(session: AsyncSession, raw: RawListing) -> UpsertResult:
    """Idempotent end-to-end upsert. Caller commits."""
    prop, is_new_prop = await _get_or_create_property(session, raw)
    listing, is_new_listing = await _upsert_listing_row(session, prop, raw)
    await _recompute_property_status(session, prop)
    return UpsertResult(
        canonical_property_id=prop.id,
        listing_id=listing.id,
        is_new_property=is_new_prop,
        is_new_listing=is_new_listing,
    )
