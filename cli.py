"""Command-line entry for the Off-Market Dashboard.

  python -m cli import-csv <path>        # import a Matrix/Stratus CSV export
  python -m cli summary                  # dump off-market counts by city
  python -m cli list --limit 20          # print off-market properties
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import func, select

from adapters.csv_import import import_csv
from core.status import OFF_MARKET_STATUSES
from db.models import CanonicalProperty, Listing
from db.operations import session_scope

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("cli")


async def _cmd_import_csv(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        log.error("file not found: %s", path)
        return 2

    async with session_scope() as session:
        summary = await import_csv(session, path, source=args.source)

    print(
        f"imported {summary.rows_read} rows "
        f"({summary.rows_skipped} skipped) → "
        f"{summary.listings_new} new listings, "
        f"{summary.listings_updated} updated, "
        f"{summary.properties_new} new properties"
    )
    return 0


async def _cmd_summary(_: argparse.Namespace) -> int:
    async with session_scope() as session:
        total = (await session.execute(select(func.count()).select_from(CanonicalProperty))).scalar_one()
        off_market = (
            await session.execute(
                select(func.count())
                .select_from(CanonicalProperty)
                .where(CanonicalProperty.current_status.in_(OFF_MARKET_STATUSES))
            )
        ).scalar_one()
        rows = (
            await session.execute(
                select(CanonicalProperty.city, CanonicalProperty.current_status, func.count())
                .group_by(CanonicalProperty.city, CanonicalProperty.current_status)
                .order_by(CanonicalProperty.city, CanonicalProperty.current_status)
            )
        ).all()
        listings_total = (await session.execute(select(func.count()).select_from(Listing))).scalar_one()

    print(f"properties: {total}  (off-market: {off_market})   listings: {listings_total}")
    print()
    print(f"{'City':<25} {'Status':<15} {'Count':>6}")
    print("-" * 48)
    for city, status, n in rows:
        print(f"{(city or '—'):<25} {(status or '—'):<15} {n:>6}")
    return 0


async def _cmd_list(args: argparse.Namespace) -> int:
    async with session_scope() as session:
        rows = (
            await session.execute(
                select(CanonicalProperty)
                .where(CanonicalProperty.current_status.in_(OFF_MARKET_STATUSES))
                .order_by(CanonicalProperty.updated_at.desc())
                .limit(args.limit)
            )
        ).scalars().all()

    if not rows:
        print("no off-market properties")
        return 0

    print(f"{'Status':<12} {'City':<20} {'Address':<50}")
    print("-" * 85)
    for p in rows:
        print(f"{p.current_status:<12} {(p.city or '—'):<20} {p.address_raw[:49]:<50}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Off-Market Property Dashboard CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_import = sub.add_parser("import-csv", help="Import a Matrix/Stratus CSV export")
    p_import.add_argument("path", help="Path to CSV file")
    p_import.add_argument("--source", default="TRREB-CSV", help="Source label (default: TRREB-CSV)")
    p_import.set_defaults(func=_cmd_import_csv)

    p_summary = sub.add_parser("summary", help="Print counts by city and status")
    p_summary.set_defaults(func=_cmd_summary)

    p_list = sub.add_parser("list", help="Print off-market properties")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
