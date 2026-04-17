"""End-to-end upsert tests covering the listing-lifecycle rules.

Scenarios:
  * New listing creates a CanonicalProperty.
  * Re-ingesting the same listing is idempotent.
  * A relisting (new MLS#, same address) attaches to the existing property.
  * current_status tracks the most recent listing — an expired listing
    followed by a new active listing flips current_status to Active (= off
    the dashboard).
  * A sold listing hides the property.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.listing_source import RawListing
from core.status import is_off_market
from db.models import CanonicalProperty, Listing
from workers.upsert import upsert_listing


def _raw(
    mls: str,
    status: str,
    *,
    address: str = "123 Main St, Toronto, ON M5V 2T6",
    commencement: date | None = None,
    expiry: date | None = None,
    sold: date | None = None,
) -> RawListing:
    return RawListing(
        source="TRREB",
        mls_number=mls,
        status=status,
        address_raw=address,
        commencement_date=commencement,
        expiry_date=expiry,
        sold_date=sold,
    )


@pytest.mark.asyncio
async def test_new_listing_creates_property(session: AsyncSession) -> None:
    r = _raw("W1234567", "Expired", commencement=date(2025, 10, 1), expiry=date(2026, 4, 1))
    result = await upsert_listing(session, r)
    await session.commit()

    assert result.is_new_property
    assert result.is_new_listing

    prop = (await session.execute(select(CanonicalProperty))).scalar_one()
    assert prop.current_status == "Expired"
    assert prop.canonical_key.startswith("M5V2T6|123|MAIN|")


@pytest.mark.asyncio
async def test_reingest_same_listing_is_idempotent(session: AsyncSession) -> None:
    r = _raw("W1234567", "Expired", commencement=date(2025, 10, 1), expiry=date(2026, 4, 1))
    await upsert_listing(session, r)
    await session.commit()
    r2 = _raw("W1234567", "Expired", commencement=date(2025, 10, 1), expiry=date(2026, 4, 1))
    result = await upsert_listing(session, r2)
    await session.commit()

    assert not result.is_new_listing
    assert not result.is_new_property
    assert (await session.scalar(select(Listing).where(Listing.mls_number == "W1234567"))) is not None
    all_listings = (await session.execute(select(Listing))).scalars().all()
    assert len(list(all_listings)) == 1


@pytest.mark.asyncio
async def test_relisting_attaches_to_same_property(session: AsyncSession) -> None:
    addr = "123 Main St, Toronto, ON M5V 2T6"
    await upsert_listing(
        session,
        _raw("W1111111", "Expired", address=addr,
             commencement=date(2025, 10, 1), expiry=date(2026, 4, 1)),
    )
    await upsert_listing(
        session,
        _raw("W2222222", "Active", address=addr,
             commencement=date(2026, 4, 10), expiry=date(2026, 10, 10)),
    )
    await session.commit()

    props = (await session.execute(select(CanonicalProperty))).scalars().all()
    assert len(list(props)) == 1
    prop = props[0]
    assert prop.current_status == "Active"

    listings = (await session.execute(select(Listing))).scalars().all()
    assert {l.mls_number for l in listings} == {"W1111111", "W2222222"}

    assert not is_off_market(listings)


@pytest.mark.asyncio
async def test_expired_only_is_on_dashboard(session: AsyncSession) -> None:
    await upsert_listing(
        session,
        _raw("W3333333", "Expired", commencement=date(2025, 10, 1), expiry=date(2026, 4, 1)),
    )
    await session.commit()
    prop = (await session.execute(select(CanonicalProperty))).scalar_one()
    assert prop.current_status == "Expired"
    listings = (await session.execute(select(Listing))).scalars().all()
    assert is_off_market(listings)


@pytest.mark.asyncio
async def test_sold_removes_from_dashboard(session: AsyncSession) -> None:
    addr = "456 Queen St W, Toronto, ON M5V 2B3"
    await upsert_listing(
        session,
        _raw("W4444444", "Expired", address=addr,
             commencement=date(2025, 10, 1), expiry=date(2026, 4, 1)),
    )
    await upsert_listing(
        session,
        _raw("W5555555", "Sold", address=addr,
             commencement=date(2026, 4, 10), sold=date(2026, 5, 5)),
    )
    await session.commit()
    prop = (await session.execute(select(CanonicalProperty))).scalar_one()
    assert prop.current_status == "Sold"
    listings = (await session.execute(select(Listing))).scalars().all()
    assert not is_off_market(listings)


@pytest.mark.asyncio
async def test_terminated_is_on_dashboard(session: AsyncSession) -> None:
    await upsert_listing(
        session,
        _raw("W6666666", "Terminated",
             commencement=date(2026, 1, 1), expiry=date(2026, 7, 1)),
    )
    await session.commit()
    prop = (await session.execute(select(CanonicalProperty))).scalar_one()
    assert prop.current_status == "Terminated"
    listings = (await session.execute(select(Listing))).scalars().all()
    assert is_off_market(listings)


@pytest.mark.asyncio
async def test_unit_variations_collapse_to_one_property(session: AsyncSession) -> None:
    await upsert_listing(
        session,
        _raw("W7777777", "Expired",
             address="123 Main St, Unit 4B, Toronto, ON M5V 2T6",
             commencement=date(2025, 10, 1), expiry=date(2026, 4, 1)),
    )
    await upsert_listing(
        session,
        _raw("W8888888", "Active",
             address="#4B - 123 Main St, Toronto, ON M5V 2T6",
             commencement=date(2026, 4, 10), expiry=date(2026, 10, 10)),
    )
    await session.commit()
    props = (await session.execute(select(CanonicalProperty))).scalars().all()
    assert len(list(props)) == 1
    assert props[0].unit == "4B"
    assert props[0].current_status == "Active"
