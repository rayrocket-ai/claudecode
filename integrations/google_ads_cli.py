"""CLI for the Google Ads integration.

  python -m integrations.google_ads_cli auth              # one-time: mint refresh token
  python -m integrations.google_ads_cli verify            # token + account sanity check
  python -m integrations.google_ads_cli export [--days 90]  # the 3 reports -> CSV + leak summary
  python -m integrations.google_ads_cli fix-geo <campaign_id> [--exclude PH,US]
  python -m integrations.google_ads_cli pause <campaign_id>

`export` writes campaigns/exports/<date>-{campaigns,search-terms,user-locations}.csv
and prints the presence-vs-interest leak summary. `fix-geo` sets the
campaign to Presence-only targeting and adds negative locations.
"""

from __future__ import annotations

import argparse
import http.server
import json
import secrets
import sys
import urllib.parse
from datetime import date
from pathlib import Path

import httpx

from config import Settings
from integrations.google_ads import (
    GEO, SCOPE, TOKEN_URL, GoogleAdsClient, GoogleAdsCreds, GoogleAdsError,
    presence_leak_summary, write_csv,
)

REPO = Path(__file__).resolve().parent.parent


def _client() -> GoogleAdsClient:
    creds = GoogleAdsCreds.from_settings(Settings())
    missing = creds.missing()
    if missing:
        print("Missing in .env: " + ", ".join(missing), file=sys.stderr)
        print("See GOOGLE_ADS_SETUP.md. Run `auth` to mint the refresh token.", file=sys.stderr)
        raise SystemExit(2)
    return GoogleAdsClient(creds)


# -- one-time OAuth (loopback) -------------------------------------------------
def cmd_auth(_args: argparse.Namespace) -> None:
    s = Settings()
    cid, csec = getattr(s, "google_ads_client_id", ""), getattr(s, "google_ads_client_secret", "")
    if not cid or not csec:
        print("Set GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET in .env first.", file=sys.stderr)
        raise SystemExit(2)
    port = 8765
    redirect = f"http://localhost:{port}/"
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state,
    })
    print("\n1) Open this URL in the browser that is signed in to the Google account "
          "that owns the Ads account:\n\n" + url + "\n\n2) Approve. You will be sent "
          "back to localhost and this command finishes.\n")

    code_holder: dict[str, str] = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                code_holder["code"] = q["code"][0]
                self.send_response(200); self.end_headers()
                self.wfile.write(b"Done. You can close this tab.")
            else:
                self.send_response(400); self.end_headers()
        def log_message(self, *_):  # silence
            pass

    srv = http.server.HTTPServer(("localhost", port), H)
    while "code" not in code_holder:
        srv.handle_request()
    resp = httpx.post(TOKEN_URL, data={
        "code": code_holder["code"], "client_id": cid, "client_secret": csec,
        "redirect_uri": redirect, "grant_type": "authorization_code",
    })
    body = resp.json()
    if "refresh_token" not in body:
        print("Token exchange failed: " + json.dumps(body), file=sys.stderr)
        raise SystemExit(1)
    print("\nAdd this line to .env and keep it secret:\n")
    print(f"GOOGLE_ADS_REFRESH_TOKEN={body['refresh_token']}\n")


# -- commands ------------------------------------------------------------------
def cmd_verify(_args: argparse.Namespace) -> None:
    print(json.dumps(_client().verify(), indent=2))


def cmd_export(args: argparse.Namespace) -> None:
    c = _client()
    out = REPO / "campaigns" / "exports"
    stamp = date.today().isoformat()
    camps = c.campaigns(args.days)
    terms = c.search_terms(args.days)
    locs = c.user_locations(args.days)
    p1 = write_csv(camps, out / f"{stamp}-campaigns.csv")
    p2 = write_csv(terms, out / f"{stamp}-search-terms.csv")
    p3 = write_csv(locs, out / f"{stamp}-user-locations.csv")
    print(f"wrote {p1}\nwrote {p2}\nwrote {p3}\n")
    print("Campaigns (last %d days):" % args.days)
    for r in camps:
        cost = float(r.get("metrics.costMicros", 0) or 0) / 1e6
        geo = r.get("campaign.geoTargetTypeSetting.positiveGeoTargetType", "?")
        print(f"  [{r.get('campaign.id')}] {r.get('campaign.name')} | {r.get('campaign.status')} "
              f"| {r.get('campaign.advertisingChannelType')} | geo={geo} | "
              f"clicks={r.get('metrics.clicks')} | CA${cost:.2f} | conv={r.get('metrics.conversions')}")
    print("\nPresence-vs-interest leak:")
    print(json.dumps(presence_leak_summary(locs), indent=2))


def cmd_fix_geo(args: argparse.Namespace) -> None:
    c = _client()
    c.set_presence_only(args.campaign_id)
    codes = [x.strip().upper() for x in args.exclude.split(",") if x.strip()]
    ids = [GEO[code] for code in codes if code in GEO]
    if ids:
        c.exclude_locations(args.campaign_id, ids)
    print(f"Campaign {args.campaign_id}: Presence-only targeting set; excluded {codes or 'nothing'}.")


def cmd_pause(args: argparse.Namespace) -> None:
    _client().pause_campaign(args.campaign_id)
    print(f"Campaign {args.campaign_id} paused.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Google Ads for Ray Homes.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth").set_defaults(fn=cmd_auth)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    e = sub.add_parser("export"); e.add_argument("--days", type=int, default=90); e.set_defaults(fn=cmd_export)
    f = sub.add_parser("fix-geo"); f.add_argument("campaign_id"); f.add_argument("--exclude", default="PH,US"); f.set_defaults(fn=cmd_fix_geo)
    z = sub.add_parser("pause"); z.add_argument("campaign_id"); z.set_defaults(fn=cmd_pause)
    args = p.parse_args(argv)
    try:
        args.fn(args)
    except GoogleAdsError as err:
        print(f"Google Ads API error: {err}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
