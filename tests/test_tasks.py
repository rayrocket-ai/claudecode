"""Unit tests for the team task-management layer.

Covers the pure cadence logic (ops/followups), the Ontario checklist templates
(ops/checklists), and the async DB helpers (db/operations) against a temporary
SQLite database — no pytest-asyncio needed (we drive coroutines with
asyncio.run) and the real app DB is never touched.
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import db.operations as ops_db
from db.models import Base
from ops import checklists, followups


# ── Cadence logic ───────────────────────────────────────────────────


class TestCadence:
    def test_urgency_ordering(self):
        """High nags sooner and escalates sooner than standard, which beats low."""
        hi_fu, hi_esc = followups.cadence_for("high", 4.0, 24.0)
        std_fu, std_esc = followups.cadence_for("standard", 4.0, 24.0)
        lo_fu, lo_esc = followups.cadence_for("low", 4.0, 24.0)
        assert hi_fu < std_fu < lo_fu
        assert hi_esc < std_esc < lo_esc

    def test_standard_uses_config_values(self):
        fu, esc = followups.cadence_for("standard", 4.0, 24.0)
        assert fu == 4.0
        assert esc == 24.0

    def test_unknown_urgency_defaults_to_standard(self):
        assert followups.cadence_for("banana", 4.0, 24.0) == (4.0, 24.0)

    def test_minimum_floor(self):
        """An aggressive config can't produce sub-minute nagging."""
        fu, esc = followups.cadence_for("high", 0.0, 0.0)
        assert fu >= 1.0 / 60.0
        assert esc >= 1.0 / 60.0


class TestFollowupScheduling:
    def test_initial_followup_uses_future_due_date(self):
        now = datetime(2026, 7, 11, 9, 0)
        due = datetime(2026, 7, 14, 12, 0)
        assert followups.initial_followup_at(
            now=now, due_at=due, urgency="standard"
        ) == due

    def test_initial_followup_ignores_past_due_date(self):
        now = datetime(2026, 7, 11, 9, 0)
        due = datetime(2026, 7, 1, 12, 0)  # already past
        result = followups.initial_followup_at(now=now, due_at=due, urgency="standard")
        assert result == now + timedelta(hours=4.0)

    def test_initial_followup_no_due_date(self):
        now = datetime(2026, 7, 11, 9, 0)
        result = followups.initial_followup_at(now=now, due_at=None, urgency="standard")
        assert result == now + timedelta(hours=4.0)

    def test_next_followup_advances_by_gap(self):
        now = datetime(2026, 7, 11, 9, 0)
        result = followups.next_followup_at(now=now, urgency="high", followup_hours=4.0)
        assert result == now + timedelta(hours=1.0)  # high = 0.25 * 4h

    def test_aware_and_naive_inputs_are_normalized(self):
        """Mixing aware 'now' with a naive due date must not raise."""
        now = datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
        due = datetime(2026, 7, 14, 12, 0)  # naive
        result = followups.initial_followup_at(now=now, due_at=due, urgency="standard")
        assert result.tzinfo is None


class TestEscalation:
    def test_no_escalation_before_window(self):
        now = datetime(2026, 7, 11, 12, 0)
        created = now - timedelta(hours=2)
        assert not followups.should_escalate(
            now=now, created_at=created, urgency="standard",
            already_escalated=False, escalate_hours=24.0,
        )

    def test_escalation_after_window(self):
        now = datetime(2026, 7, 12, 13, 0)
        created = now - timedelta(hours=25)
        assert followups.should_escalate(
            now=now, created_at=created, urgency="standard",
            already_escalated=False, escalate_hours=24.0,
        )

    def test_never_escalate_twice(self):
        now = datetime(2026, 7, 12, 13, 0)
        created = now - timedelta(hours=100)
        assert not followups.should_escalate(
            now=now, created_at=created, urgency="standard",
            already_escalated=True, escalate_hours=24.0,
        )

    def test_high_urgency_escalates_much_sooner(self):
        now = datetime(2026, 7, 11, 17, 0)
        created = now - timedelta(hours=5)  # <24h but >~4h high window
        assert followups.should_escalate(
            now=now, created_at=created, urgency="high",
            already_escalated=False, escalate_hours=24.0,
        )


# ── Checklists ──────────────────────────────────────────────────────


class TestChecklists:
    def test_expected_checklists_exist(self):
        assert set(checklists.checklist_keys()) == {"listing", "buyer", "deal"}

    def test_get_checklist_case_insensitive(self):
        assert checklists.get_checklist("LISTING") is not None
        assert checklists.get_checklist("nope") is None

    def test_all_items_have_title_and_description(self):
        for key in checklists.checklist_keys():
            for item in checklists.get_checklist(key).items:
                assert item.title.strip()
                assert item.description.strip()
                assert item.urgency in ("low", "standard", "high")

    def test_deal_deposit_is_high_urgency(self):
        deal = checklists.get_checklist("deal")
        deposit = [i for i in deal.items if "deposit" in i.title.lower()]
        assert deposit and all(i.urgency == "high" for i in deposit)

    def test_buyer_starts_with_representation_agreement(self):
        buyer = checklists.get_checklist("buyer")
        assert "BRA" in buyer.items[0].title or "Representation" in buyer.items[0].title


# ── Async DB helpers (temp database) ────────────────────────────────


def _run_with_temp_db(coro_factory):
    """Point db.operations at a throwaway SQLite file, run a coroutine."""
    async def runner():
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
            factory = async_sessionmaker(engine, expire_on_commit=False)
            # Swap the module globals the helpers close over.
            orig_engine, orig_factory = ops_db._engine, ops_db._session_factory
            ops_db._engine = engine
            ops_db._session_factory = factory
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                return await coro_factory()
            finally:
                ops_db._engine, ops_db._session_factory = orig_engine, orig_factory
                await engine.dispose()

    return asyncio.run(runner())


class TestTeamAndTaskDB:
    def test_upsert_and_name_lookup(self):
        async def scenario():
            await ops_db.upsert_team_member(111, "Sarah Lee", "agent")
            await ops_db.upsert_team_member(222, "John Smith", "manager")
            by_exact = await ops_db.get_team_member_by_name("john smith")
            by_first = await ops_db.get_team_member_by_name("Sarah")
            missing = await ops_db.get_team_member_by_name("Nobody")
            members = await ops_db.list_team_members()
            return by_exact, by_first, missing, members

        by_exact, by_first, missing, members = _run_with_temp_db(scenario)
        assert by_exact.telegram_id == 222
        assert by_first.telegram_id == 111  # unambiguous first-name match
        assert missing is None
        assert len(members) == 2

    def test_due_followups_filtering(self):
        async def scenario():
            now = followups.now_utc()
            await ops_db.upsert_team_member(111, "Sarah", "agent")
            # Due now (past follow-up time)
            due = await ops_db.create_task(
                title="Overdue task", assignee_telegram_id=111,
                assigner_telegram_id=222,
                next_followup_at=now - timedelta(hours=1),
            )
            # Scheduled in the future — must NOT be returned
            await ops_db.create_task(
                title="Future task", assignee_telegram_id=111,
                assigner_telegram_id=222,
                next_followup_at=now + timedelta(hours=5),
            )
            # Done — must NOT be returned even though its follow-up is past
            done = await ops_db.create_task(
                title="Done task", assignee_telegram_id=111,
                assigner_telegram_id=222,
                next_followup_at=now - timedelta(hours=1),
            )
            await ops_db.mark_task_done(done.id)
            result = await ops_db.list_due_followups(now)
            done_reloaded = await ops_db.get_task(done.id)
            return due.id, result, done_reloaded

        due_id, result, done_reloaded = _run_with_temp_db(scenario)
        returned_ids = {t.id for t in result}
        assert due_id in returned_ids
        assert len(result) == 1  # only the overdue, non-terminal task
        assert done_reloaded.status == "done"
        assert done_reloaded.next_followup_at is None  # cleared on completion

    def test_mark_done_and_activity_log(self):
        async def scenario():
            task = await ops_db.create_task(
                title="Deliver APS", assignee_telegram_id=111, assigner_telegram_id=222,
            )
            await ops_db.append_task_note(task.id, "progress", "Sent to lawyer")
            done = await ops_db.mark_task_done(task.id, note="Confirmed received")
            return done

        done = _run_with_temp_db(scenario)
        assert done.status == "done"
        assert done.completed_at is not None
        kinds = [entry["kind"] for entry in done.activity]
        assert "created" in kinds and "progress" in kinds and "done" in kinds

    def test_open_tasks_excludes_terminal(self):
        async def scenario():
            t1 = await ops_db.create_task(
                title="Open one", assignee_telegram_id=111, assigner_telegram_id=222,
            )
            t2 = await ops_db.create_task(
                title="Cancel me", assignee_telegram_id=111, assigner_telegram_id=222,
            )
            await ops_db.update_task(t2.id, status="cancelled")
            open_tasks = await ops_db.list_open_tasks()
            assignee_open = await ops_db.list_tasks_for_assignee(111)
            return t1.id, open_tasks, assignee_open

        t1_id, open_tasks, assignee_open = _run_with_temp_db(scenario)
        assert {t.id for t in open_tasks} == {t1_id}
        assert {t.id for t in assignee_open} == {t1_id}
