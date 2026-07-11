"""Async database operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.attributes import flag_modified

from config import DB_PATH
from db.models import (
    Base,
    ConversationSession,
    Document,
    Party,
    Property,
    Task,
    TASK_TERMINAL_STATUSES,
    TeamMember,
    Transaction,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

_engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session() -> AsyncSession:
    return _session_factory()


# ── Conversation Sessions ──────────────────────────────────────────

async def get_or_create_conversation(chat_id: int) -> ConversationSession:
    async with get_session() as session:
        result = await session.execute(
            select(ConversationSession).where(ConversationSession.telegram_chat_id == chat_id)
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            conv = ConversationSession(telegram_chat_id=chat_id)
            session.add(conv)
            await session.commit()
            await session.refresh(conv)
        return conv


async def update_session_data(chat_id: int, data: dict[str, Any]) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(ConversationSession).where(ConversationSession.telegram_chat_id == chat_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            existing = dict(conv.collected_data or {})
            existing.update(data)
            conv.collected_data = existing
            flag_modified(conv, "collected_data")
            await session.commit()


async def append_conversation_message(chat_id: int, role: str, content: str) -> list[dict]:
    async with get_session() as session:
        result = await session.execute(
            select(ConversationSession).where(ConversationSession.telegram_chat_id == chat_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            history = list(conv.conversation_history or [])
            history.append({"role": role, "content": content})
            # Keep last 40 messages to avoid token overflow
            if len(history) > 40:
                history = history[-40:]
            conv.conversation_history = history
            flag_modified(conv, "conversation_history")
            await session.commit()
            return history
    return []


async def reset_session(chat_id: int) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(ConversationSession).where(ConversationSession.telegram_chat_id == chat_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.state = "idle"
            conv.doc_type = None
            conv.transaction_id = None
            conv.collected_data = {}
            conv.conversation_history = []
            flag_modified(conv, "collected_data")
            flag_modified(conv, "conversation_history")
            await session.commit()


async def set_session_state(chat_id: int, state: str, doc_type: str | None = None,
                            transaction_id: str | None = None) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(ConversationSession).where(ConversationSession.telegram_chat_id == chat_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.state = state
            if doc_type is not None:
                conv.doc_type = doc_type
            if transaction_id is not None:
                conv.transaction_id = transaction_id
            await session.commit()


# ── Transactions ───────────────────────────────────────────────────

async def create_transaction(chat_id: int, doc_type: str, deal_data: dict) -> Transaction:
    async with get_session() as session:
        tx = Transaction(telegram_chat_id=chat_id, doc_type=doc_type, deal_data=deal_data)
        session.add(tx)
        await session.commit()
        await session.refresh(tx)
        return tx


async def update_transaction(tx_id: str, **kwargs) -> None:
    async with get_session() as session:
        result = await session.execute(select(Transaction).where(Transaction.id == tx_id))
        tx = result.scalar_one_or_none()
        if tx:
            for k, v in kwargs.items():
                setattr(tx, k, v)
            await session.commit()


async def get_transaction(tx_id: str) -> Transaction | None:
    async with get_session() as session:
        result = await session.execute(select(Transaction).where(Transaction.id == tx_id))
        return result.scalar_one_or_none()


async def list_transactions(chat_id: int, limit: int = 20) -> list[Transaction]:
    async with get_session() as session:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.telegram_chat_id == chat_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# ── Team Members ───────────────────────────────────────────────────

async def upsert_team_member(
    telegram_id: int, name: str, role: str = "agent"
) -> TeamMember:
    """Create a team member, or reactivate/update an existing one by telegram_id."""
    async with get_session() as session:
        result = await session.execute(
            select(TeamMember).where(TeamMember.telegram_id == telegram_id)
        )
        member = result.scalar_one_or_none()
        if member is None:
            member = TeamMember(telegram_id=telegram_id, name=name, role=role)
            session.add(member)
        else:
            member.name = name
            member.role = role
            member.active = True
        await session.commit()
        await session.refresh(member)
        return member


async def get_team_member(telegram_id: int) -> TeamMember | None:
    async with get_session() as session:
        result = await session.execute(
            select(TeamMember).where(TeamMember.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_team_member_by_name(name: str) -> TeamMember | None:
    """Case-insensitive lookup by name among active members.

    Matches an exact (case-insensitive) name first, then a unique prefix so
    "Sarah" resolves "Sarah Lee" when there's no ambiguity.
    """
    members = await list_team_members(active_only=True)
    needle = name.strip().lower()
    if not needle:
        return None
    exact = [m for m in members if m.name.lower() == needle]
    if exact:
        return exact[0]
    # First-name / prefix match, only if unambiguous.
    prefix = [
        m for m in members
        if m.name.lower().startswith(needle)
        or m.name.lower().split()[0] == needle
    ]
    if len(prefix) == 1:
        return prefix[0]
    return None


async def list_team_members(active_only: bool = True) -> list[TeamMember]:
    async with get_session() as session:
        stmt = select(TeamMember)
        if active_only:
            stmt = stmt.where(TeamMember.active == True)  # noqa: E712
        stmt = stmt.order_by(TeamMember.name)
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def deactivate_team_member(telegram_id: int) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(TeamMember).where(TeamMember.telegram_id == telegram_id)
        )
        member = result.scalar_one_or_none()
        if member is None:
            return False
        member.active = False
        await session.commit()
        return True


# ── Tasks ──────────────────────────────────────────────────────────

async def create_task(
    *,
    title: str,
    assignee_telegram_id: int,
    assigner_telegram_id: int,
    description: str | None = None,
    deal_ref: str | None = None,
    urgency: str = "standard",
    due_at: datetime | None = None,
    next_followup_at: datetime | None = None,
    checklist_key: str | None = None,
    checklist_item: str | None = None,
) -> Task:
    async with get_session() as session:
        task = Task(
            title=title,
            description=description,
            assignee_telegram_id=assignee_telegram_id,
            assigner_telegram_id=assigner_telegram_id,
            deal_ref=deal_ref,
            urgency=urgency,
            due_at=due_at,
            next_followup_at=next_followup_at,
            checklist_key=checklist_key,
            checklist_item=checklist_item,
            activity=[{
                "ts": _utcnow().isoformat(),
                "kind": "created",
                "text": f"Assigned to {assignee_telegram_id}",
            }],
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def get_task(task_id: str) -> Task | None:
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()


async def update_task(task_id: str, **kwargs) -> None:
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            for k, v in kwargs.items():
                setattr(task, k, v)
            await session.commit()


async def append_task_note(task_id: str, kind: str, text: str) -> None:
    """Append an entry to the task's activity log."""
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            log = list(task.activity or [])
            log.append({"ts": _utcnow().isoformat(), "kind": kind, "text": text})
            task.activity = log
            flag_modified(task, "activity")
            await session.commit()


async def mark_task_done(task_id: str, note: str | None = None) -> Task | None:
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return None
        task.status = "done"
        task.completed_at = _utcnow()
        task.next_followup_at = None
        log = list(task.activity or [])
        log.append({
            "ts": _utcnow().isoformat(),
            "kind": "done",
            "text": note or "Marked done",
        })
        task.activity = log
        flag_modified(task, "activity")
        await session.commit()
        await session.refresh(task)
        return task


async def list_tasks_for_assignee(
    telegram_id: int, include_done: bool = False, limit: int = 50
) -> list[Task]:
    async with get_session() as session:
        stmt = select(Task).where(Task.assignee_telegram_id == telegram_id)
        if not include_done:
            stmt = stmt.where(Task.status.notin_(TASK_TERMINAL_STATUSES))
        stmt = stmt.order_by(Task.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def list_open_tasks(limit: int = 100) -> list[Task]:
    """All non-terminal tasks (manager view)."""
    async with get_session() as session:
        stmt = (
            select(Task)
            .where(Task.status.notin_(TASK_TERMINAL_STATUSES))
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def list_due_followups(now: datetime | None = None) -> list[Task]:
    """Non-terminal tasks whose follow-up time has arrived.

    Drives the recurring scan job. `next_followup_at is None` tasks are
    skipped (nothing scheduled), so completed/paused tasks are never nagged.
    """
    now = now or _utcnow()
    async with get_session() as session:
        stmt = (
            select(Task)
            .where(Task.status.notin_(TASK_TERMINAL_STATUSES))
            .where(Task.next_followup_at.is_not(None))
            .where(Task.next_followup_at <= now)
            .order_by(Task.next_followup_at)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
