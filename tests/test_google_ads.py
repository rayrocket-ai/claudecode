"""Tests for the Google Ads integration — fully mocked, no live calls."""

import json

import pytest

from integrations.google_ads import (
    GEO, GoogleAdsClient, GoogleAdsCreds, GoogleAdsError, _flatten,
    presence_leak_summary, write_csv,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeHttpx:
    def __init__(self, responses):
        self._responses, self.requests = list(responses), []

    def post(self, url, data=None, json=None, headers=None):
        self.requests.append({"url": url, "data": data, "json": json, "headers": headers})
        return self._responses.pop(0)


TOKEN_OK = FakeResponse({"access_token": "acc", "expires_in": 3600})


def creds():
    return GoogleAdsCreds(developer_token="dev", client_id="cid", client_secret="sec",
                          refresh_token="ref", customer_id="1344350136",
                          login_customer_id="")


def test_missing_credentials_named():
    c = GoogleAdsCreds("", "", "", "", "")
    assert set(c.missing()) == {"GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID",
                                "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN",
                                "GOOGLE_ADS_CUSTOMER_ID"}


def test_from_settings_strips_dashes_from_ids():
    class S:
        google_ads_developer_token = "d"; google_ads_client_id = "c"
        google_ads_client_secret = "s"; google_ads_refresh_token = "r"
        google_ads_customer_id = "134-435-0136"; google_ads_login_customer_id = "156-142-2047"
    c = GoogleAdsCreds.from_settings(S())
    assert c.customer_id == "1344350136" and c.login_customer_id == "1561422047"


def test_flatten():
    assert _flatten({"campaign": {"id": "1", "name": "x"}, "metrics": {"clicks": "3"}}) == {
        "campaign.id": "1", "campaign.name": "x", "metrics.clicks": "3"}


def test_search_refreshes_token_and_flattens_rows():
    stream = [{"results": [{"campaign": {"id": "11", "name": "Buyers"},
                            "metrics": {"costMicros": "2500000", "clicks": "7"}}]}]
    fake = FakeHttpx([TOKEN_OK, FakeResponse(stream)])
    c = GoogleAdsClient(creds(), client=fake)
    rows = c.campaigns(days=30)
    assert rows == [{"campaign.id": "11", "campaign.name": "Buyers",
                     "metrics.costMicros": "2500000", "metrics.clicks": "7"}]
    # first call = OAuth refresh, second = searchStream with dev token header
    assert fake.requests[0]["data"]["grant_type"] == "refresh_token"
    req = fake.requests[1]
    assert req["url"].endswith("/customers/1344350136/googleAds:searchStream")
    assert req["headers"]["developer-token"] == "dev"
    assert "login-customer-id" not in req["headers"]
    q = req["json"]["query"]
    assert "FROM campaign" in q and "BETWEEN" in q and "!= 'REMOVED'" in q


def test_user_locations_query_includes_location_type():
    fake = FakeHttpx([TOKEN_OK, FakeResponse([{"results": []}])])
    GoogleAdsClient(creds(), client=fake).user_locations()
    q = fake.requests[1]["json"]["query"]
    assert "geographic_view.location_type" in q and "FROM geographic_view" in q


def test_set_presence_only_payload():
    fake = FakeHttpx([TOKEN_OK, FakeResponse({"results": [{}]})])
    GoogleAdsClient(creds(), client=fake).set_presence_only(11)
    req = fake.requests[1]
    assert req["url"].endswith("/customers/1344350136/campaigns:mutate")
    op = req["json"]["operations"][0]
    assert op["update"]["resourceName"] == "customers/1344350136/campaigns/11"
    assert op["update"]["geoTargetTypeSetting"] == {
        "positiveGeoTargetType": "PRESENCE", "negativeGeoTargetType": "PRESENCE"}
    assert "positive_geo_target_type" in op["updateMask"]


def test_exclude_locations_uses_negative_geo_constants():
    fake = FakeHttpx([TOKEN_OK, FakeResponse({"results": [{}, {}]})])
    GoogleAdsClient(creds(), client=fake).exclude_locations(11, [GEO["PH"], GEO["US"]])
    ops = fake.requests[1]["json"]["operations"]
    assert fake.requests[1]["url"].endswith("/campaignCriteria:mutate")
    assert [o["create"]["location"]["geoTargetConstant"] for o in ops] == [
        "geoTargetConstants/2608", "geoTargetConstants/2840"]
    assert all(o["create"]["negative"] is True for o in ops)


def test_pause_sets_status():
    fake = FakeHttpx([TOKEN_OK, FakeResponse({"results": [{}]})])
    GoogleAdsClient(creds(), client=fake).pause_campaign("11")
    op = fake.requests[1]["json"]["operations"][0]
    assert op["update"]["status"] == "PAUSED" and op["updateMask"] == "status"


def test_status_validation():
    with pytest.raises(ValueError):
        GoogleAdsClient(creds(), client=FakeHttpx([])).set_campaign_status(1, "RUNNING")


def test_api_error_surfaces_google_message():
    err = {"error": {"message": "outer", "details": [
        {"errors": [{"message": "The developer token is not approved."}]}]}}
    fake = FakeHttpx([TOKEN_OK, FakeResponse(err, status=403)])
    with pytest.raises(GoogleAdsError) as e:
        GoogleAdsClient(creds(), client=fake).verify()
    assert "developer token is not approved" in str(e.value)


def test_oauth_failure_is_clear():
    fake = FakeHttpx([FakeResponse({"error": "invalid_grant",
                                    "error_description": "Token has been revoked."}, status=400)])
    with pytest.raises(GoogleAdsError) as e:
        GoogleAdsClient(creds(), client=fake).verify()
    assert "revoked" in str(e.value)


def test_presence_leak_summary():
    rows = [
        {"metrics.costMicros": "60000000", "geographicView.locationType": "AREA_OF_INTEREST",
         "geographicView.countryCriterionId": "2608"},
        {"metrics.costMicros": "30000000", "geographicView.locationType": "LOCATION_OF_PRESENCE",
         "geographicView.countryCriterionId": "2124"},
        {"metrics.costMicros": "10000000", "geographicView.locationType": "AREA_OF_INTEREST",
         "geographicView.countryCriterionId": "2840"},
    ]
    s = presence_leak_summary(rows)
    assert s["total_cost"] == 100.0
    assert s["area_of_interest_cost"] == 70.0
    assert s["area_of_interest_share"] == 0.7
    assert s["top_countries_by_cost"][0] == ("2608", 60.0)


def test_write_csv_adds_cad_columns(tmp_path):
    p = write_csv([{"campaign.name": "A", "metrics.costMicros": "1234567"}], tmp_path / "x.csv")
    text = p.read_text()
    assert "metrics.costMicros_cad" in text and "1.23" in text
