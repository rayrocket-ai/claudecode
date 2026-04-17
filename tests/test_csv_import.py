"""CSV import tests against a synthetic Matrix-style export."""

from __future__ import annotations

import io

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.csv_import import import_csv
from db.models import CanonicalProperty, Listing


SAMPLE_CSV = """MLS Number,Status,Address,City,Postal Code,List Price,Sold Price,Listing Date,Expiry Date,Sold Date,Listing Agent,List Office,Property Type,Beds,Baths,SqFt,DOM,Public Remarks
W11111111,Expired,"123 Main St",Toronto,M5V 2T6,"$1,250,000",,2025-10-01,2026-04-01,,Jane Smith,Homes Brokerage,Detached,3,2,1800,182,Lovely family home.
W22222222,Terminated,"456 Queen St W",Toronto,M5V 2B3,"$899,000",,2025-11-15,,,John Doe,Urban Realty,Condo Apt,2,1,900,120,Bright condo near transit.
W33333333,Active,"789 King W Suite 305",Toronto,M5V 1K1,"$1,050,000",,2026-01-10,2026-07-10,,Sara Lee,City Properties,Condo Apt,1,1,650,95,Sleek downtown unit.
W44444444,Sold,"321 Bloor St E",Toronto,M4W 1A1,"$2,100,000","$2,050,000",2025-08-01,2026-02-01,2026-01-20,Mike Ross,Luxe Realty,Detached,4,3,2500,173,Premium location.
W55555555,Expired,"#4B - 123 Main St",Toronto,M5V 2T6,"$780,000",,2025-09-01,2026-03-01,,Ann Park,Homes Brokerage,Condo Apt,2,2,1100,180,Great unit in same building.
"""


@pytest.mark.asyncio
async def test_import_sample_csv(session: AsyncSession) -> None:
    summary = await import_csv(session, io.StringIO(SAMPLE_CSV), source="TRREB-CSV")
    await session.commit()

    assert summary.rows_read == 5
    assert summary.rows_skipped == 0
    assert summary.listings_new == 5

    # 5 unique physical properties — the two 123 Main St rows have different
    # units (none vs 4B) so they are DIFFERENT properties.
    props = (await session.execute(select(CanonicalProperty))).scalars().all()
    assert len(list(props)) == 5

    # Status spot-check
    by_mls = {
        l.mls_number: l
        for l in (await session.execute(select(Listing))).scalars().all()
    }
    assert by_mls["W11111111"].status == "Expired"
    assert by_mls["W22222222"].status == "Terminated"
    assert by_mls["W33333333"].status == "Active"
    assert by_mls["W44444444"].status == "Sold"
    assert by_mls["W55555555"].status == "Expired"

    # Prices parsed correctly with $ / , stripped
    assert by_mls["W11111111"].list_price == 1_250_000.0
    assert by_mls["W44444444"].sold_price == 2_050_000.0


@pytest.mark.asyncio
async def test_reimport_is_idempotent(session: AsyncSession) -> None:
    first = await import_csv(session, io.StringIO(SAMPLE_CSV), source="TRREB-CSV")
    await session.commit()
    second = await import_csv(session, io.StringIO(SAMPLE_CSV), source="TRREB-CSV")
    await session.commit()

    assert first.listings_new == 5
    assert second.listings_new == 0
    assert second.listings_updated == 5
    listings = (await session.execute(select(Listing))).scalars().all()
    assert len(list(listings)) == 5


@pytest.mark.asyncio
async def test_csv_with_status_short_codes(session: AsyncSession) -> None:
    csv_str = (
        "MLS Number,Status,Address,City,Postal Code,List Price,Listing Date,Expiry Date\n"
        "W10000001,EXP,\"10 Yonge St\",Toronto,M5E 1J1,\"$900,000\",2025-10-01,2026-04-01\n"
        "W10000002,TER,\"11 Yonge St\",Toronto,M5E 1J2,\"$850,000\",2025-10-01,\n"
        "W10000003,A,\"12 Yonge St\",Toronto,M5E 1J3,\"$950,000\",2026-01-01,2026-07-01\n"
        "W10000004,SLD,\"13 Yonge St\",Toronto,M5E 1J4,\"$800,000\",2025-08-01,2026-02-01\n"
    )
    summary = await import_csv(session, io.StringIO(csv_str))
    await session.commit()
    assert summary.listings_new == 4
    statuses = {
        l.mls_number: l.status
        for l in (await session.execute(select(Listing))).scalars().all()
    }
    assert statuses == {
        "W10000001": "Expired",
        "W10000002": "Terminated",
        "W10000003": "Active",
        "W10000004": "Sold",
    }
