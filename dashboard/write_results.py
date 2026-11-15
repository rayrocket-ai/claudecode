"""Write a campaign's results.json for the git-file dashboard path.

The ADMAX daily loop calls this to record a day's numbers and optionally a
log entry, then commits campaigns/<slug>/results.json to git. The server
picks it up on the next pull. No network call into the server is needed.

Usage:
  python dashboard/write_results.py <slug> \
      --date 2026-08-02 --spend 10.12 --leads 1 --ctr 1.4 \
      --views 130 --notes "launch day" \
      --log-title "Launched" --log-entry "Both ad sets live."

Meta (name/status/config/rules/targets) is seeded from dashboard/seed.json
the first time a campaign's results.json is created, then preserved.
"""

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent


def _seed_campaign(slug: str) -> dict:
    seed = json.loads((BASE_DIR / "seed.json").read_text())
    return seed.get("campaigns", {}).get(slug, {"name": slug, "status": "pre-launch"})


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("slug")
    p.add_argument("--date", required=True)
    p.add_argument("--spend", type=float, default=0.0)
    p.add_argument("--leads", type=int, default=0)
    p.add_argument("--ctr", type=float, default=None)
    p.add_argument("--impressions", type=int, default=None)
    p.add_argument("--views", type=int, default=None)
    p.add_argument("--notes", default="")
    p.add_argument("--status", default=None, help="set campaign status, e.g. live")
    p.add_argument("--log-title", default=None)
    p.add_argument("--log-entry", default=None)
    args = p.parse_args()

    path = REPO_DIR / "campaigns" / args.slug / "results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    campaign = json.loads(path.read_text()) if path.exists() else _seed_campaign(args.slug)
    campaign.setdefault("daily", [])
    campaign.setdefault("log", [])

    if args.status:
        campaign["status"] = args.status

    row = {
        "date": args.date,
        "spend": args.spend,
        "leads": args.leads,
        "ctr_pct": args.ctr,
        "impressions": args.impressions,
        "views": args.views,
        "notes": args.notes,
    }
    # Same date twice = correction, not a duplicate day.
    campaign["daily"] = [r for r in campaign["daily"] if r.get("date") != args.date]
    campaign["daily"].append(row)
    campaign["daily"].sort(key=lambda r: r["date"])

    if args.log_title and args.log_entry:
        campaign["log"].append(
            {"date": args.date, "title": args.log_title, "entry": args.log_entry}
        )

    path.write_text(json.dumps(campaign, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
