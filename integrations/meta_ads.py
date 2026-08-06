"""Meta (Facebook/Instagram) Marketing API integration.

Creates and manages lead-generation campaigns for Ray Homes directly
through the Graph API — no browser, no manual Ads Manager step. Talks to
the user's own ad account with a System User access token.

Safety model (matches the ADMAX approval rules):
- Everything is created PAUSED. Nothing spends until `activate()` is
  called, which the daily loop only does after Ray's explicit approval.
- Housing Special Ad Category is declared on every campaign — mandatory
  for real estate and enforced here, not left to the caller.

Credentials come from Settings (see config.py / .env):
- META_ACCESS_TOKEN     System User token with ads_management
- META_AD_ACCOUNT_ID    e.g. act_1234567890
- META_PAGE_ID          the Facebook Page ads run from
- META_INSTAGRAM_ID     (optional) IG account id for IG placements
- META_API_VERSION      defaults to v21.0

This module makes no network calls at import time. Construct a
MetaAdsClient and call methods; every call raises MetaAdsError with the
Graph API message on failure so the CLI can print something actionable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

GRAPH = "https://graph.facebook.com"


class MetaAdsError(RuntimeError):
    """A Graph API call failed. Message carries the API's own error text."""


@dataclass
class MetaCreds:
    access_token: str
    ad_account_id: str  # act_XXXXXXXXX
    page_id: str = ""
    instagram_id: str = ""
    api_version: str = "v21.0"

    @classmethod
    def from_settings(cls, settings: Any) -> "MetaCreds":
        return cls(
            access_token=getattr(settings, "meta_access_token", "") or "",
            ad_account_id=getattr(settings, "meta_ad_account_id", "") or "",
            page_id=getattr(settings, "meta_page_id", "") or "",
            instagram_id=getattr(settings, "meta_instagram_id", "") or "",
            api_version=getattr(settings, "meta_api_version", "") or "v21.0",
        )

    def missing(self) -> list[str]:
        """Names of the required credentials that are not set."""
        need = {"META_ACCESS_TOKEN": self.access_token,
                "META_AD_ACCOUNT_ID": self.ad_account_id,
                "META_PAGE_ID": self.page_id}
        return [k for k, v in need.items() if not v]


class MetaAdsClient:
    """Thin, testable wrapper over the Marketing API."""

    def __init__(self, creds: MetaCreds, client: httpx.Client | None = None):
        self.creds = creds
        self._client = client or httpx.Client(timeout=30.0)

    # -- low-level ---------------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{GRAPH}/{self.creds.api_version}/{path}"

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = {**data, "access_token": self.creds.access_token}
        # Objects (targeting, creative) must be JSON-encoded strings.
        for key, value in list(payload.items()):
            if isinstance(value, (dict, list)):
                payload[key] = json.dumps(value)
        resp = self._client.post(self._url(path), data=payload)
        return self._parse(resp)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {**params, "access_token": self.creds.access_token}
        resp = self._client.get(self._url(path), params=params)
        return self._parse(resp)

    @staticmethod
    def _parse(resp: httpx.Response) -> dict[str, Any]:
        try:
            body = resp.json()
        except ValueError:
            raise MetaAdsError(f"Non-JSON response ({resp.status_code}): {resp.text[:200]}")
        if resp.status_code >= 400 or "error" in body:
            err = body.get("error", {})
            msg = err.get("error_user_msg") or err.get("message") or str(body)
            raise MetaAdsError(f"{resp.status_code}: {msg}")
        return body

    # -- health ------------------------------------------------------------
    def verify(self) -> dict[str, Any]:
        """Confirm the token can see the ad account. Cheap sanity check."""
        acct = self.creds.ad_account_id
        return self._get(acct, {"fields": "name,account_status,currency,amount_spent"})

    # -- build (all PAUSED) ------------------------------------------------
    def create_campaign(self, name: str) -> str:
        """Create a PAUSED Leads campaign in the Housing category."""
        out = self._post(
            f"{self.creds.ad_account_id}/campaigns",
            {
                "name": name,
                "objective": "OUTCOME_LEADS",
                "status": "PAUSED",
                "special_ad_categories": ["HOUSING"],
            },
        )
        return out["id"]

    def create_adset(
        self,
        campaign_id: str,
        name: str,
        daily_budget_cents: int,
        lat: float,
        lng: float,
        radius_km: float,
        form_id: str,
    ) -> str:
        """Create a PAUSED ad set: instant-form leads, radius targeting.

        Housing rules are respected: no age/gender narrowing, broad
        targeting, radius >= 24 km enforced by the caller/config.
        """
        targeting = {
            "geo_locations": {
                "custom_locations": [
                    {"latitude": lat, "longitude": lng,
                     "radius": radius_km, "distance_unit": "kilometer"}
                ]
            },
            "targeting_automation": {"advantage_audience": 1},
        }
        out = self._post(
            f"{self.creds.ad_account_id}/adsets",
            {
                "name": name,
                "campaign_id": campaign_id,
                "status": "PAUSED",
                "daily_budget": daily_budget_cents,
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "LEAD_GENERATION",
                "destination_type": "ON_AD",
                "promoted_object": {"page_id": self.creds.page_id},
                "targeting": targeting,
                "dsa_beneficiary": self.creds.page_id,
            },
        )
        return out["id"]

    def create_lead_form(self, name: str, questions: list[dict[str, Any]],
                         privacy_url: str, intro_headline: str,
                         thank_you: dict[str, str]) -> str:
        """Create an instant lead form on the Page."""
        out = self._post(
            f"{self.creds.page_id}/leadgen_forms",
            {
                "name": name,
                "questions": questions,
                "privacy_policy": {"url": privacy_url, "link_text": "Privacy Policy"},
                "context_card": {"title": intro_headline,
                                 "style": "PARAGRAPH_STYLE"},
                "thank_you_page": thank_you,
                "locale": "en_US",
            },
        )
        return out["id"]

    def create_carousel_creative(self, name: str, message: str,
                                 headline: str, description: str,
                                 image_hashes: list[str], link: str) -> str:
        """Create a carousel ad creative from already-uploaded image hashes."""
        child_attachments = [
            {"image_hash": h, "name": headline, "description": description}
            for h in image_hashes
        ]
        creative = {
            "name": name,
            "object_story_spec": {
                "page_id": self.creds.page_id,
                **({"instagram_actor_id": self.creds.instagram_id}
                   if self.creds.instagram_id else {}),
                "link_data": {
                    "message": message,
                    "link": link,
                    "child_attachments": child_attachments,
                },
            },
        }
        out = self._post(f"{self.creds.ad_account_id}/adcreatives", creative)
        return out["id"]

    def upload_image(self, path: str) -> str:
        """Upload a local image, return its image_hash."""
        with open(path, "rb") as fh:
            files = {"filename": fh}
            resp = self._client.post(
                self._url(f"{self.creds.ad_account_id}/adimages"),
                data={"access_token": self.creds.access_token},
                files=files,
            )
        body = self._parse(resp)
        # {"images": {"<name>": {"hash": "..."}}}
        first = next(iter(body.get("images", {}).values()))
        return first["hash"]

    def create_ad(self, adset_id: str, name: str, creative_id: str) -> str:
        """Create a PAUSED ad tying a creative to the ad set."""
        out = self._post(
            f"{self.creds.ad_account_id}/ads",
            {
                "name": name,
                "adset_id": adset_id,
                "creative": {"creative_id": creative_id},
                "status": "PAUSED",
            },
        )
        return out["id"]

    # -- control -----------------------------------------------------------
    def set_status(self, object_id: str, status: str) -> dict[str, Any]:
        """ACTIVE or PAUSED on a campaign / adset / ad."""
        if status not in ("ACTIVE", "PAUSED"):
            raise ValueError("status must be ACTIVE or PAUSED")
        return self._post(object_id, {"status": status})

    # -- read --------------------------------------------------------------
    def insights(self, object_id: str, date_preset: str = "yesterday") -> dict[str, Any]:
        """Return spend / impressions / CTR / leads for an object.

        Leads are read from the actions array (lead / leadgen.other).
        """
        body = self._get(
            f"{object_id}/insights",
            {"date_preset": date_preset,
             "fields": "spend,impressions,clicks,ctr,actions"},
        )
        rows = body.get("data", [])
        if not rows:
            return {"spend": 0.0, "impressions": 0, "ctr_pct": None, "leads": 0}
        row = rows[0]
        leads = 0
        for action in row.get("actions", []):
            if action.get("action_type") in ("lead", "leadgen.other",
                                             "onsite_conversion.lead_grouped"):
                leads += int(float(action.get("value", 0)))
        return {
            "spend": round(float(row.get("spend", 0)), 2),
            "impressions": int(row.get("impressions", 0)),
            "ctr_pct": round(float(row["ctr"]), 2) if row.get("ctr") else None,
            "leads": leads,
        }
