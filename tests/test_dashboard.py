"""Tests for the multi-campaign dashboard service."""

import pytest
from fastapi.testclient import TestClient

from dashboard import app as dash


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHBOARD_STORE", str(tmp_path / "dashboard.json"))
    monkeypatch.setenv("DASHBOARD_KEY", "test-key")
    # Isolate the git-file source so seeded results.json files on disk
    # don't leak into store-based tests.
    monkeypatch.setenv("CAMPAIGN_DATA_DIR", str(tmp_path / "campaigns"))
    return TestClient(dash.app)


def test_git_file_is_source_of_truth(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHBOARD_STORE", str(tmp_path / "dashboard.json"))
    monkeypatch.setenv("DASHBOARD_KEY", "test-key")
    data_dir = tmp_path / "campaigns"
    monkeypatch.setenv("CAMPAIGN_DATA_DIR", str(data_dir))
    # A committed results.json for a brand-new campaign the store never saw.
    cdir = data_dir / "aurora-sellers"
    cdir.mkdir(parents=True)
    (cdir / "results.json").write_text(
        '{"name": "Aurora Sellers", "status": "live", "playbook": "Seller",'
        ' "daily": [{"date": "2026-08-01", "spend": 10.0, "leads": 2}], "log": []}'
    )
    client = TestClient(dash.app)
    listing = client.get("/api/campaigns").json()
    assert "aurora-sellers" in listing
    assert listing["aurora-sellers"]["leads"] == 2
    page = client.get("/c/aurora-sellers")
    assert page.status_code == 200
    assert "Aurora Sellers" in page.text


def test_bad_git_file_is_skipped_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHBOARD_STORE", str(tmp_path / "dashboard.json"))
    monkeypatch.setenv("DASHBOARD_KEY", "test-key")
    data_dir = tmp_path / "campaigns"
    monkeypatch.setenv("CAMPAIGN_DATA_DIR", str(data_dir))
    bad = data_dir / "broken"
    bad.mkdir(parents=True)
    (bad / "results.json").write_text("{not valid json")
    client = TestClient(dash.app)
    # Dashboard still serves (seeded campaigns), bad file ignored.
    assert client.get("/").status_code == 200
    assert "broken" not in client.get("/api/campaigns").json()


def test_index_seeds_and_lists_buttonleaf(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "34 Buttonleaf" in resp.text


def test_campaign_page_renders(client):
    resp = client.get("/c/34-buttonleaf")
    assert resp.status_code == 200
    assert "Kill" in resp.text
    assert "Awaiting day 1" in resp.text


def test_unknown_campaign_404(client):
    assert client.get("/c/nope").status_code == 404


def test_write_requires_key(client):
    row = {"date": "2026-07-21", "spend": 15.0, "leads": 1}
    assert client.post("/api/campaigns/34-buttonleaf/daily", json=row).status_code == 401
    bad = client.post(
        "/api/campaigns/34-buttonleaf/daily", json=row, headers={"X-Dashboard-Key": "wrong"}
    )
    assert bad.status_code == 401


def test_writes_disabled_without_server_key(client, monkeypatch):
    monkeypatch.setenv("DASHBOARD_KEY", "")
    row = {"date": "2026-07-21", "spend": 15.0, "leads": 1}
    resp = client.post(
        "/api/campaigns/34-buttonleaf/daily", json=row, headers={"X-Dashboard-Key": ""}
    )
    assert resp.status_code == 503


def test_daily_ingest_updates_kpis_and_dedupes_by_date(client):
    headers = {"X-Dashboard-Key": "test-key"}
    day1 = {"date": "2026-07-21", "spend": 15.0, "leads": 1, "ctr_pct": 1.1, "views": 120}
    resp = client.post("/api/campaigns/34-buttonleaf/daily", json=day1, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["spend"] == 15.0

    # Re-reporting the same date is a correction, not a second day.
    correction = {**day1, "spend": 14.5, "leads": 2}
    resp = client.post("/api/campaigns/34-buttonleaf/daily", json=correction, headers=headers)
    body = resp.json()
    assert body["days"] == 1
    assert body["spend"] == 14.5
    assert body["leads"] == 2
    assert body["cpl"] == 7.25

    page = client.get("/c/34-buttonleaf")
    assert "$14.50" in page.text


def test_upsert_new_campaign_and_log(client):
    headers = {"X-Dashboard-Key": "test-key"}
    meta = {
        "name": "Richmond Hill Seller Leads",
        "status": "live",
        "playbook": "Seller Lead Gen · Playbook C",
    }
    assert client.put("/api/campaigns/rh-sellers", json=meta, headers=headers).status_code == 200

    entry = {"date": "2026-07-21", "title": "Launched", "entry": "Valuation funnel live."}
    assert (
        client.post("/api/campaigns/rh-sellers/log", json=entry, headers=headers).status_code
        == 200
    )

    index = client.get("/")
    assert "Richmond Hill Seller Leads" in index.text
    listing = client.get("/api/campaigns").json()
    assert set(listing) == {"34-buttonleaf", "16-curry", "rh-sellers"}
