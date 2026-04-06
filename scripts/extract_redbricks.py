#!/usr/bin/env python3
"""Extract all pre-construction condo data from Redbricks API.

Usage:
    python scripts/extract_redbricks.py

Requires REDBRICKS_API_KEY in .env or environment.
Saves output to storage/redbricks_data.json
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrations.redbricks import RedbricksClient
from config import get_settings

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
OUTPUT_FILE = STORAGE_DIR / "redbricks_data.json"


async def main() -> None:
    settings = get_settings()
    if not settings.is_redbricks_configured:
        print("ERROR: REDBRICKS_API_KEY not set. Add it to .env or environment.")
        sys.exit(1)

    client = RedbricksClient(settings.redbricks_api_key, settings.redbricks_api_url)

    # 1. Fetch all projects
    print("Fetching all condo projects...")
    projects = await client.get_all_projects(type_="Condo", per_page=200)
    print(f"  Found {len(projects)} condo projects")

    # 2. For each project, fetch floorplans
    print("\nFetching floorplans for each project...")
    for project in projects:
        pid = project["id"]
        name = project["name"]
        floorplans = await client.get_all_floorplans(pid)
        project["floorplans"] = floorplans
        print(f"  {name} (ID {pid}): {len(floorplans)} floorplans")

    # 3. Fetch all prices
    print("\nFetching all prices...")
    project_ids = ",".join(str(p["id"]) for p in projects)
    prices = await client.get_all_prices(project_ids=project_ids)
    print(f"  Found {len(prices)} price records")

    # 4. Build output
    output = {
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "total_projects": len(projects),
        "total_prices": len(prices),
        "projects": projects,
        "prices": prices,
    }

    # 5. Save
    STORAGE_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nData saved to {OUTPUT_FILE}")

    # 6. Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    for p in projects:
        price_from = p.get("current_price_from")
        price_to = p.get("current_price_to")
        price_str = ""
        if price_from and price_to:
            price_str = f"${price_from:,.0f} - ${price_to:,.0f}"
        elif price_from:
            price_str = f"From ${price_from:,.0f}"

        docs_count = len(p.get("latest_documents", []))
        hist_count = len(p.get("historical_documents", []))
        fp_count = len(p.get("floorplans", []))

        print(f"\n  {p['name']}")
        print(f"    Status: {p.get('current_sales_status', 'N/A')}")
        print(f"    Address: {p.get('address', 'N/A')}, {p.get('city_name', '')}")
        print(f"    Price: {price_str or 'N/A'}")
        print(f"    Storeys: {p.get('storeys', 'N/A')} | Suites: {p.get('suites', 'N/A')}")
        print(f"    Floorplans: {fp_count} | Docs: {docs_count} latest, {hist_count} historical")
        print(f"    Maintenance: ${p.get('maintenance_fees', 'N/A')}/sqft")
        print(f"    Developer: {p.get('developer_name', 'N/A')}")

    print(f"\nTotal price records: {len(prices)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
