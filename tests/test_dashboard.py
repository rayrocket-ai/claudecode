"""Tests for the read-only web dashboard (web/app.py)."""

import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

TOKEN = "test-secret-token"
NOW = datetime(2026, 7, 7, 16, 0)  # naive UTC


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """TestClient wired to a fresh temp SQLite DB and a known token."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import db.operations as ops
    from db.models import Base

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path/'dash.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(ops, "_engine", engine)
    monkeypatch.setattr(ops, "_session_factory", factory)

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init())

    monkeypatch.setenv("DASHBOARD_TOKEN", TOKEN)

    from web.app import app

    with TestClient(app) as c:
        yield c, ops
    asyncio.run(engine.dispose())


def _seed_deal(ops, chat_id=42):
    async def run():
        tx = await ops.create_transaction(chat_id, "aps", {
            "buyer_1": "John Smith",
            "seller_1": "Jane Doe",
            "purchase_price": 800000,
            "property_street_number": "123",
            "property_street_name": "Main St",
            "property_city": "Toronto",
            "closing_date": "2026-09-01",
        })
        await ops.create_reminders([{
            "telegram_chat_id": chat_id,
            "transaction_id": tx.id,
            "kind": "closing",
            "label": "Closing — 123 Main St, Toronto",
            "deadline_at": NOW + timedelta(days=30),
            "notify_at": NOW + timedelta(days=29),
        }])
        return tx

    return asyncio.run(run())


class TestAuth:
    def test_no_token_is_401(self, client):
        c, _ = client
        assert c.get("/").status_code == 401

    def test_wrong_token_is_401(self, client):
        c, _ = client
        assert c.get("/?token=wrong").status_code == 401

    def test_valid_token_is_200_and_sets_cookie(self, client):
        c, _ = client
        resp = c.get(f"/?token={TOKEN}")
        assert resp.status_code == 200
        assert "dash_token" in resp.cookies
        # Cookie now works without the query param.
        assert c.get("/").status_code == 200

    def test_header_token_accepted(self, client):
        c, _ = client
        assert c.get("/", headers={"x-dashboard-token": TOKEN}).status_code == 200

    def test_unconfigured_dashboard_is_503(self, client, monkeypatch):
        c, _ = client
        monkeypatch.setenv("DASHBOARD_TOKEN", "")
        assert c.get(f"/?token={TOKEN}").status_code == 503


class TestPages:
    def test_empty_deals_list(self, client):
        c, _ = client
        resp = c.get(f"/?token={TOKEN}")
        assert resp.status_code == 200
        assert "No deals yet" in resp.text

    def test_deals_list_shows_seeded_deal(self, client):
        c, ops = client
        _seed_deal(ops)
        resp = c.get(f"/?token={TOKEN}")
        assert "123 Main St, Toronto" in resp.text
        assert "John Smith" in resp.text
        assert "$800,000.00" in resp.text

    def test_deal_detail(self, client):
        c, ops = client
        tx = _seed_deal(ops)
        resp = c.get(f"/deal/{tx.id}?token={TOKEN}")
        assert resp.status_code == 200
        assert "Jane Doe" in resp.text
        assert "Closing — 123 Main St, Toronto" in resp.text  # its reminder

    def test_deal_detail_404(self, client):
        c, _ = client
        assert c.get(f"/deal/nope?token={TOKEN}").status_code == 404

    def test_deadlines_page(self, client):
        c, ops = client
        _seed_deal(ops)
        resp = c.get(f"/deadlines?token={TOKEN}")
        assert resp.status_code == 200
        assert "Closing — 123 Main St, Toronto" in resp.text
