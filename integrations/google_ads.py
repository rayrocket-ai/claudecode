"""Google Ads API integration (REST, no SDK dependency).

Reads the reports ADMAX needs and applies account fixes directly on Ray's
own Google Ads account, using a developer token plus an OAuth refresh
token. Anything that changes the account (pause, exclude, geo option) is
an explicit call — reports are read-only.

Credentials come from Settings (config.py / .env, see GOOGLE_ADS_SETUP.md):
  GOOGLE_ADS_DEVELOPER_TOKEN
  GOOGLE_ADS_CLIENT_ID, GOOGLE_ADS_CLIENT_SECRET   OAuth client (Desktop app)
  GOOGLE_ADS_REFRESH_TOKEN                          minted once via CLI `auth`
  GOOGLE_ADS_CUSTOMER_ID                            e.g. 1344350136 (digits only)
  GOOGLE_ADS_LOGIN_CUSTOMER_ID                      manager (MCC) id if the
                                                    token lives on a manager

No network calls at import time. Every API failure raises GoogleAdsError
carrying Google's own message so the CLI can print something actionable.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

import httpx

API_VERSION = "v20"
BASE = f"https://googleads.googleapis.com/{API_VERSION}"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/adwords"

# Geo target constant ids (Google's fixed criterion ids).
GEO = {"CA": 2124, "US": 2840, "PH": 2608, "IN": 2356, "NG": 2566}


class GoogleAdsError(RuntimeError):
    """A Google Ads API call failed. Message carries the API's error text."""


@dataclass
class GoogleAdsCreds:
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    customer_id: str  # digits only
    login_customer_id: str = ""

    @classmethod
    def from_settings(cls, s: Any) -> "GoogleAdsCreds":
        g = lambda k: (getattr(s, k, "") or "").replace("-", "").strip()  # noqa: E731
        return cls(
            developer_token=getattr(s, "google_ads_developer_token", "") or "",
            client_id=getattr(s, "google_ads_client_id", "") or "",
            client_secret=getattr(s, "google_ads_client_secret", "") or "",
            refresh_token=getattr(s, "google_ads_refresh_token", "") or "",
            customer_id=g("google_ads_customer_id"),
            login_customer_id=g("google_ads_login_customer_id"),
        )

    def missing(self) -> list[str]:
        need = {
            "GOOGLE_ADS_DEVELOPER_TOKEN": self.developer_token,
            "GOOGLE_ADS_CLIENT_ID": self.client_id,
            "GOOGLE_ADS_CLIENT_SECRET": self.client_secret,
            "GOOGLE_ADS_REFRESH_TOKEN": self.refresh_token,
            "GOOGLE_ADS_CUSTOMER_ID": self.customer_id,
        }
        return [k for k, v in need.items() if not v]


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    """{'campaign': {'id': 1}} -> {'campaign.id': 1}."""
    out: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            out.update(_flatten(v, key))
    else:
        out[prefix] = obj
    return out


def _date_range(days: int) -> tuple[str, str]:
    end = date.today() - timedelta(days=1)  # yesterday: complete data
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def presence_leak_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """From geographic_view rows, how much cost went to 'area of interest'
    (people NOT physically in the target) vs. 'location of presence'.

    This is the diagnostic for the 'Presence or interest' budget leak, and
    the top countries by cost show where the money actually went.
    """
    total = 0.0
    interest = 0.0
    by_country: dict[str, float] = {}
    for r in rows:
        cost = float(r.get("metrics.costMicros", r.get("metrics.cost_micros", 0)) or 0) / 1e6
        total += cost
        if r.get("geographicView.locationType", r.get("geographic_view.location_type")) == "AREA_OF_INTEREST":
            interest += cost
        country = str(r.get("geographicView.countryCriterionId",
                            r.get("geographic_view.country_criterion_id", "?")))
        by_country[country] = by_country.get(country, 0.0) + cost
    top = sorted(by_country.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return {
        "total_cost": round(total, 2),
        "area_of_interest_cost": round(interest, 2),
        "area_of_interest_share": round(interest / total, 3) if total else 0.0,
        "top_countries_by_cost": [(c, round(v, 2)) for c, v in top],
    }


class GoogleAdsClient:
    """Thin, testable wrapper over the Google Ads REST API."""

    def __init__(self, creds: GoogleAdsCreds, client: httpx.Client | None = None):
        self.creds = creds
        self._client = client or httpx.Client(timeout=60.0)
        self._access_token: str | None = None

    # -- auth --------------------------------------------------------------
    def access_token(self) -> str:
        if self._access_token:
            return self._access_token
        resp = self._client.post(
            TOKEN_URL,
            data={
                "client_id": self.creds.client_id,
                "client_secret": self.creds.client_secret,
                "refresh_token": self.creds.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        body = self._json(resp)
        if resp.status_code >= 400 or "access_token" not in body:
            raise GoogleAdsError(f"OAuth refresh failed: {body.get('error_description') or body}")
        self._access_token = body["access_token"]
        return self._access_token

    def _headers(self) -> dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.access_token()}",
            "developer-token": self.creds.developer_token,
            "Content-Type": "application/json",
        }
        if self.creds.login_customer_id:
            h["login-customer-id"] = self.creds.login_customer_id
        return h

    @staticmethod
    def _json(resp: httpx.Response) -> Any:
        try:
            return resp.json()
        except ValueError:
            raise GoogleAdsError(f"Non-JSON response ({resp.status_code}): {resp.text[:300]}")

    @staticmethod
    def _raise_for_error(resp: httpx.Response, body: Any) -> None:
        if resp.status_code < 400:
            return
        msg = body
        if isinstance(body, dict) and "error" in body:
            err = body["error"]
            details = err.get("details", [])
            gerr = []
            for d in details:
                for e in d.get("errors", []):
                    gerr.append(e.get("message", ""))
            msg = "; ".join(gerr) or err.get("message") or str(err)
        elif isinstance(body, list) and body and isinstance(body[0], dict) and "error" in body[0]:
            msg = body[0]["error"].get("message", str(body[0]))
        raise GoogleAdsError(f"{resp.status_code}: {msg}")

    # -- read --------------------------------------------------------------
    def search(self, gaql: str) -> list[dict[str, Any]]:
        """Run GAQL via searchStream, return flattened rows."""
        url = f"{BASE}/customers/{self.creds.customer_id}/googleAds:searchStream"
        resp = self._client.post(url, json={"query": gaql}, headers=self._headers())
        body = self._json(resp)
        self._raise_for_error(resp, body)
        rows: list[dict[str, Any]] = []
        for batch in body if isinstance(body, list) else [body]:
            for result in batch.get("results", []):
                rows.append(_flatten(result))
        return rows

    def verify(self) -> dict[str, Any]:
        rows = self.search(
            "SELECT customer.id, customer.descriptive_name, customer.currency_code, "
            "customer.time_zone FROM customer LIMIT 1"
        )
        return rows[0] if rows else {}

    def campaigns(self, days: int = 90) -> list[dict[str, Any]]:
        s, e = _date_range(days)
        return self.search(
            "SELECT campaign.id, campaign.name, campaign.status, "
            "campaign.advertising_channel_type, "
            "campaign.geo_target_type_setting.positive_geo_target_type, "
            "campaign_budget.amount_micros, "
            "metrics.impressions, metrics.clicks, metrics.ctr, "
            "metrics.average_cpc, metrics.cost_micros, metrics.conversions "
            f"FROM campaign WHERE segments.date BETWEEN '{s}' AND '{e}' "
            "AND campaign.status != 'REMOVED' ORDER BY metrics.cost_micros DESC"
        )

    def search_terms(self, days: int = 90) -> list[dict[str, Any]]:
        s, e = _date_range(days)
        return self.search(
            "SELECT campaign.name, ad_group.name, search_term_view.search_term, "
            "search_term_view.status, metrics.impressions, metrics.clicks, "
            "metrics.cost_micros, metrics.conversions "
            f"FROM search_term_view WHERE segments.date BETWEEN '{s}' AND '{e}' "
            "ORDER BY metrics.cost_micros DESC"
        )

    def user_locations(self, days: int = 90) -> list[dict[str, Any]]:
        """Where the people who saw/clicked actually were, and whether they
        matched by presence or mere 'interest'."""
        s, e = _date_range(days)
        return self.search(
            "SELECT campaign.name, geographic_view.country_criterion_id, "
            "geographic_view.location_type, segments.geo_target_region, "
            "segments.geo_target_city, metrics.impressions, metrics.clicks, "
            "metrics.cost_micros, metrics.conversions "
            f"FROM geographic_view WHERE segments.date BETWEEN '{s}' AND '{e}' "
            "ORDER BY metrics.cost_micros DESC"
        )

    # -- write -------------------------------------------------------------
    def _mutate(self, service: str, operations: list[dict[str, Any]]) -> Any:
        url = f"{BASE}/customers/{self.creds.customer_id}/{service}:mutate"
        resp = self._client.post(url, json={"operations": operations}, headers=self._headers())
        body = self._json(resp)
        self._raise_for_error(resp, body)
        return body

    def _campaign_rn(self, campaign_id: str | int) -> str:
        return f"customers/{self.creds.customer_id}/campaigns/{campaign_id}"

    def set_presence_only(self, campaign_id: str | int) -> Any:
        """Stop serving to people merely 'interested in' the target area."""
        return self._mutate("campaigns", [{
            "update": {
                "resourceName": self._campaign_rn(campaign_id),
                "geoTargetTypeSetting": {
                    "positiveGeoTargetType": "PRESENCE",
                    "negativeGeoTargetType": "PRESENCE",
                },
            },
            "updateMask": "geo_target_type_setting.positive_geo_target_type,"
                          "geo_target_type_setting.negative_geo_target_type",
        }])

    def exclude_locations(self, campaign_id: str | int, geo_ids: Iterable[int]) -> Any:
        ops = [{
            "create": {
                "campaign": self._campaign_rn(campaign_id),
                "negative": True,
                "location": {"geoTargetConstant": f"geoTargetConstants/{gid}"},
            }
        } for gid in geo_ids]
        return self._mutate("campaignCriteria", ops)

    def set_campaign_status(self, campaign_id: str | int, status: str) -> Any:
        if status not in ("ENABLED", "PAUSED"):
            raise ValueError("status must be ENABLED or PAUSED")
        return self._mutate("campaigns", [{
            "update": {"resourceName": self._campaign_rn(campaign_id), "status": status},
            "updateMask": "status",
        }])

    def pause_campaign(self, campaign_id: str | int) -> Any:
        return self.set_campaign_status(campaign_id, "PAUSED")


def write_csv(rows: list[dict[str, Any]], path: Path) -> Path:
    """Write flattened rows to CSV, cost_micros also expressed as CAD."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return path
    out_rows = []
    for r in rows:
        r = dict(r)
        for k in list(r):
            if k.lower().endswith(("costmicros", "cost_micros", "amountmicros", "amount_micros",
                                   "averagecpc", "average_cpc")):
                try:
                    r[k + "_cad"] = round(float(r[k]) / 1e6, 2)
                except (TypeError, ValueError):
                    pass
        out_rows.append(r)
    fields = sorted({k for r in out_rows for k in r})
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)
    return path
