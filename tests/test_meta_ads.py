"""Tests for the Meta Marketing API integration, fully mocked.

No live network calls: a fake httpx client returns canned Graph API
responses and records what was sent, so we assert on the request shape
(objective, Housing category, PAUSED status, budget, targeting).
"""

import json

import httpx
import pytest

from integrations.meta_ads import MetaAdsClient, MetaAdsError, MetaCreds


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeHttpx:
    """Stands in for httpx.Client. Queue responses, capture requests."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def post(self, url, data=None, files=None):
        self.requests.append(("POST", url, data, files))
        return self._responses.pop(0)

    def get(self, url, params=None):
        self.requests.append(("GET", url, params, None))
        return self._responses.pop(0)


def creds():
    return MetaCreds(access_token="tok", ad_account_id="act_1",
                     page_id="page_1", instagram_id="ig_1")


def test_missing_credentials_detected():
    c = MetaCreds(access_token="", ad_account_id="", page_id="")
    assert set(c.missing()) == {"META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_PAGE_ID"}


def test_create_campaign_is_housing_leads_and_paused():
    fake = FakeHttpx([FakeResponse({"id": "camp_1"})])
    client = MetaAdsClient(creds(), client=fake)
    cid = client.create_campaign("Buttonleaf")
    assert cid == "camp_1"
    _, url, data, _ = fake.requests[0]
    assert url.endswith("/act_1/campaigns")
    assert data["objective"] == "OUTCOME_LEADS"
    assert data["status"] == "PAUSED"
    assert json.loads(data["special_ad_categories"]) == ["HOUSING"]


def test_create_adset_budget_and_radius_targeting():
    fake = FakeHttpx([FakeResponse({"id": "adset_1"})])
    client = MetaAdsClient(creds(), client=fake)
    aid = client.create_adset("camp_1", "AdSet", 1000, 43.97, -79.24, 25, "form_1")
    assert aid == "adset_1"
    _, _, data, _ = fake.requests[0]
    assert data["daily_budget"] == 1000
    assert data["status"] == "PAUSED"
    assert data["optimization_goal"] == "LEAD_GENERATION"
    targeting = json.loads(data["targeting"])
    loc = targeting["geo_locations"]["custom_locations"][0]
    assert loc["radius"] == 25 and loc["distance_unit"] == "kilometer"


def test_graph_error_raises_with_message():
    fake = FakeHttpx([FakeResponse({"error": {"message": "Bad token"}}, status=400)])
    client = MetaAdsClient(creds(), client=fake)
    with pytest.raises(MetaAdsError) as e:
        client.create_campaign("x")
    assert "Bad token" in str(e.value)


def test_set_status_validates():
    client = MetaAdsClient(creds(), client=FakeHttpx([]))
    with pytest.raises(ValueError):
        client.set_status("camp_1", "RUNNING")


def test_activate_sets_active():
    fake = FakeHttpx([FakeResponse({"success": True})])
    client = MetaAdsClient(creds(), client=fake)
    client.set_status("camp_1", "ACTIVE")
    _, url, data, _ = fake.requests[0]
    assert url.endswith("/camp_1")
    assert data["status"] == "ACTIVE"


def test_insights_counts_leads_from_actions():
    payload = {"data": [{
        "spend": "9.87", "impressions": "1500", "ctr": "1.12",
        "actions": [
            {"action_type": "post_engagement", "value": "40"},
            {"action_type": "onsite_conversion.lead_grouped", "value": "3"},
        ],
    }]}
    fake = FakeHttpx([FakeResponse(payload)])
    client = MetaAdsClient(creds(), client=fake)
    out = client.insights("camp_1")
    assert out["spend"] == 9.87
    assert out["impressions"] == 1500
    assert out["ctr_pct"] == 1.12
    assert out["leads"] == 3


def test_insights_empty_is_zeroed():
    fake = FakeHttpx([FakeResponse({"data": []})])
    client = MetaAdsClient(creds(), client=fake)
    out = client.insights("camp_1")
    assert out == {"spend": 0.0, "impressions": 0, "ctr_pct": None, "leads": 0}
