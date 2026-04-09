#!/usr/bin/env python3
"""Extract all pre-construction condo data from Livabl.com.

Usage:
    python scripts/extract_livabl.py
    python scripts/extract_livabl.py --cities toronto,mississauga
    python scripts/extract_livabl.py --max-projects 10
    python scripts/extract_livabl.py --listings-only

Saves output to storage/livabl_data.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations.livabl import LivablClient, DEFAULT_ONTARIO_CITIES

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
OUTPUT_FILE = STORAGE_DIR / "livabl_data.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Livabl.com pre-construction condo data")
    parser.add_argument(
        "--cities",
        type=str,
        default=None,
        help="Comma-separated city slugs (default: all Ontario cities)",
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        default=None,
        help="Max number of project detail pages to scrape",
    )
    parser.add_argument(
        "--listings-only",
        action="store_true",
        help="Only scrape listing pages, skip individual project details",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output file path (default: storage/livabl_data.json)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    cities = None
    if args.cities:
        cities = [c.strip() for c in args.cities.split(",") if c.strip()]

    output_file = Path(args.output) if args.output else OUTPUT_FILE

    city_display = ", ".join(cities) if cities else f"all {len(DEFAULT_ONTARIO_CITIES)} Ontario cities"
    print(f"Livabl.com Condo Extractor")
    print(f"  Cities: {city_display}")
    print(f"  Max projects: {args.max_projects or 'unlimited'}")
    print(f"  Detail pages: {'skip' if args.listings_only else 'yes'}")
    print()

    client = LivablClient()
    output = await client.scrape_ontario_condos(
        cities=cities,
        max_projects=args.max_projects,
        skip_detail_pages=args.listings_only,
    )

    # Save
    STORAGE_DIR.mkdir(exist_ok=True)
    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nData saved to {output_file}")

    # Print summary
    projects = output.get("projects", [])
    print("\n" + "=" * 60)
    print("LIVABL EXTRACTION SUMMARY")
    print("=" * 60)

    for p in projects:
        name = p.get("name", "Unknown")
        status = p.get("status") or "N/A"
        developer = p.get("developer") or "N/A"
        city = p.get("city") or "N/A"
        price_text = ""
        pr = p.get("price_range")
        if isinstance(pr, dict):
            price_text = pr.get("text") or ""
            if not price_text and pr.get("min"):
                price_text = f"From ${pr['min']:,.0f}"
        elif p.get("price_text"):
            price_text = p["price_text"]

        fp_count = len(p.get("floor_plans", []))
        detail = "detailed" if p.get("detail_scraped") else "listing only"

        print(f"\n  {name} ({detail})")
        print(f"    City: {city} | Status: {status}")
        print(f"    Developer: {developer}")
        if price_text:
            print(f"    Price: {price_text}")
        if fp_count:
            print(f"    Floor Plans: {fp_count}")

    errors = output.get("errors", [])
    print(f"\nTotal projects: {output.get('total_projects', 0)}")
    print(f"With details: {output.get('total_with_details', 0)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"  - {err}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
