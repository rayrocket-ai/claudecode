"""Unit tests for bot.reminders (pure logic) and the reminder DB operations."""

import asyncio
from datetime import datetime, time, timedelta, timezone

import pytest

from bot.reminders import (
    LOCAL_TZ,
    REMINDER_OFFSETS,
    build_reminders,
    format_deadline_local,
    parse_time_of_day,
    property_label,
)


def _utc_naive(dt_local: datetime) -> datetime:
    """Helper: convert an aware/naive local Toronto datetime to naive UTC."""
    if dt_local.tzinfo is None:
        dt_local = dt_local.replace(tzinfo=LOCAL_TZ)
    return dt_local.astimezone(timezone.utc).replace(tzinfo=None)


NOW_LOCAL = datetime(2026, 7, 7, 12, 0)  # noon Toronto
NOW = _utc_naive(NOW_LOCAL)


def _deal(**overrides) -> dict:
    base = {
        "property_street_number": "123",
        "property_street_name": "Main St",
        "property_city": "Toronto",
    }
    base.update(overrides)
    return base


class TestParseTimeOfDay:
    @pytest.mark.parametrize("value,expected", [
        ("5 PM", time(17, 0)),
        ("5:00 p.m.", time(17, 0)),
        ("11:59pm", time(23, 59)),
        ("12 AM", time(0, 0)),
        ("12 PM", time(12, 0)),
        ("17:00", time(17, 0)),
        ("9:30", time(9, 30)),
    ])
    def test_valid(self, value, expected):
        assert parse_time_of_day(value) == expected

    @pytest.mark.parametrize("value", ["", None, "sometime", "25:00", "13 PM"])
    def test_invalid(self, value):
        assert parse_time_of_day(value) is None

    def test_passthrough_time(self):
        t = time(8, 15)
        assert parse_time_of_day(t) is t


class TestPropertyLabel:
    def test_full_address(self):
        assert property_label(_deal()) == "123 Main St, Toronto"

    def test_fallback(self):
        assert property_label({}) == "your deal"


class TestBuildReminders:
    def test_deadline_72h_out_gets_both_offsets(self):
        # Irrevocability 3 days out at 11:59 PM → both 48h and 24h rows.
        deal = _deal(irrevocability_date="2026-07-10")
        rows = build_reminders(deal, "tx1", 42, now=NOW)
        irrev = [r for r in rows if r["kind"] == "irrevocability"]
        assert len(irrev) == len(REMINDER_OFFSETS) == 2

        deadline = irrev[0]["deadline_at"]
        assert deadline == _utc_naive(datetime(2026, 7, 10, 23, 59))
        notify_ats = sorted(r["notify_at"] for r in irrev)
        assert notify_ats == [deadline - timedelta(hours=48), deadline - timedelta(hours=24)]

    def test_deadline_36h_out_gets_only_24h_offset(self):
        # Closing tomorrow+1 at 9 AM local: ~45h away → only the 24h reminder.
        deal = _deal(closing_date="2026-07-09")
        rows = build_reminders(deal, "tx1", 42, now=NOW)
        closing = [r for r in rows if r["kind"] == "closing"]
        assert len(closing) == 1
        assert closing[0]["notify_at"] == closing[0]["deadline_at"] - timedelta(hours=24)

    def test_deadline_12h_out_gets_no_rows(self):
        # Closing tomorrow 9 AM is 21h away — both offsets already past.
        deal = _deal(closing_date="2026-07-08")
        rows = build_reminders(deal, "tx1", 42, now=NOW)
        assert [r for r in rows if r["kind"] == "closing"] == []

    def test_past_deadline_gets_no_rows(self):
        deal = _deal(irrevocability_date="2026-07-01")
        assert build_reminders(deal, "tx1", 42, now=NOW) == []

    def test_condition_date_keys_detected(self):
        deal = _deal(financing_condition_date="2026-07-12")
        rows = build_reminders(deal, "tx1", 42, now=NOW)
        conds = [r for r in rows if r["kind"] == "condition"]
        assert len(conds) == 2
        assert "Financing condition" in conds[0]["label"]
        assert "123 Main St, Toronto" in conds[0]["label"]

    def test_explicit_irrevocability_time_used(self):
        deal = _deal(irrevocability_date="2026-07-10", irrevocability_time="5:00 PM")
        rows = build_reminders(deal, "tx1", 42, now=NOW)
        assert rows[0]["deadline_at"] == _utc_naive(datetime(2026, 7, 10, 17, 0))

    def test_row_shape_matches_model_columns(self):
        deal = _deal(closing_date="2026-09-01")
        row = build_reminders(deal, "tx1", 42, now=NOW)[0]
        assert set(row) == {
            "telegram_chat_id", "transaction_id", "kind", "label",
            "deadline_at", "notify_at",
        }
        assert row["telegram_chat_id"] == 42
        assert row["transaction_id"] == "tx1"

    def test_unparseable_dates_skipped(self):
        deal = _deal(closing_date="whenever works", irrevocability_date="")
        assert build_reminders(deal, "tx1", 42, now=NOW) == []


class TestFormatDeadlineLocal:
    def test_renders_toronto_time(self):
        deadline = _utc_naive(datetime(2026, 7, 10, 23, 59))
        s = format_deadline_local(deadline)
        assert "Jul 10, 2026" in s
        assert "11:59 PM" in s


# ── DB operations, against an isolated temp database ─────────────────


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """Point db.operations at a fresh SQLite file for the duration of a test."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    import db.operations as ops
    from db.models import Base

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path/'test.db'}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(ops, "_engine", engine)
    monkeypatch.setattr(ops, "_session_factory", factory)

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init())
    yield ops
    asyncio.run(engine.dispose())


def _rows(chat_id=42, n=1, offset_hours=0):
    deadline = NOW + timedelta(hours=72)
    return [
        {
            "telegram_chat_id": chat_id,
            "transaction_id": None,
            "kind": "closing",
            "label": f"Closing — deal {i}",
            "deadline_at": deadline,
            "notify_at": NOW + timedelta(hours=offset_hours),
        }
        for i in range(n)
    ]


class TestReminderOperations:
    def test_create_and_fetch_due(self, temp_db):
        async def run():
            # One due now, one due in 10h.
            await temp_db.create_reminders(_rows(n=1, offset_hours=-1))
            await temp_db.create_reminders(_rows(n=1, offset_hours=10))
            due = await temp_db.get_due_reminders(NOW)
            assert len(due) == 1
            return due[0]

        due = asyncio.run(run())
        assert due.sent is False

    def test_mark_sent_removes_from_due(self, temp_db):
        async def run():
            await temp_db.create_reminders(_rows(n=1, offset_hours=-1))
            due = await temp_db.get_due_reminders(NOW)
            await temp_db.mark_reminder_sent(due[0].id)
            return await temp_db.get_due_reminders(NOW)

        assert asyncio.run(run()) == []

    def test_list_upcoming_scoped_to_chat(self, temp_db):
        async def run():
            await temp_db.create_reminders(_rows(chat_id=1, n=2, offset_hours=5))
            await temp_db.create_reminders(_rows(chat_id=2, n=1, offset_hours=5))
            mine = await temp_db.list_upcoming_reminders(1, NOW)
            theirs = await temp_db.list_upcoming_reminders(2, NOW)
            return len(mine), len(theirs)

        assert asyncio.run(run()) == (2, 1)

    def test_create_empty_is_noop(self, temp_db):
        assert asyncio.run(temp_db.create_reminders([])) == 0
