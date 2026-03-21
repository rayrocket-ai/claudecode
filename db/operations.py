"""Async database operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.attributes import flag_modified

from config import DB_PATH
from db.models import Base, ConversationSession, Transaction, Party, Property, Document

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
