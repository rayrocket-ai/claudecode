"""SQLAlchemy models for the real estate document generator."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=_new_id)
    telegram_chat_id = Column(Integer, index=True)
    doc_type = Column(String, nullable=False)  # aps, amendment, waiver, lease, ...
    status = Column(String, default="draft")   # draft, collecting, generating, review, signing, completed
    td_transaction_uuid = Column(String, nullable=True)  # TransactionDesk UUID
    td_form_uuid = Column(String, nullable=True)

    # Deal data (JSON blob)
    deal_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    parties = relationship("Party", back_populates="transaction", cascade="all, delete-orphan")
    property = relationship("Property", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="transaction", cascade="all, delete-orphan")


class Party(Base):
    __tablename__ = "parties"

    id = Column(String, primary_key=True, default=_new_id)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    role = Column(String, nullable=False)  # buyer, seller, buyer_agent, seller_agent
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    transaction = relationship("Transaction", back_populates="parties")


class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, default=_new_id)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    address = Column(String, nullable=False)
    street_number = Column(String, nullable=True)
    street_name = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    city = Column(String, nullable=True)
    province = Column(String, default="Ontario")
    postal_code = Column(String, nullable=True)
    mls_number = Column(String, nullable=True)
    property_type = Column(String, nullable=True)  # residential, commercial, condo
    legal_description = Column(String, nullable=True)
    list_price = Column(Float, nullable=True)

    transaction = relationship("Transaction", back_populates="property")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_new_id)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    doc_type = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    td_form_uuid = Column(String, nullable=True)
    signing_status = Column(String, default="unsigned")  # unsigned, sent, signed
    signing_envelope_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    transaction = relationship("Transaction", back_populates="documents")


class TeamMember(Base):
    """A person on the real estate team who can be assigned tasks.

    The Telegram user ID doubles as the private-chat ID, so the bot can DM a
    member directly by `telegram_id`. Managers can assign/see all tasks and
    receive escalations; agents see and act on their own tasks.
    """

    __tablename__ = "team_members"

    id = Column(String, primary_key=True, default=_new_id)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="agent")  # manager, agent
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Task(Base):
    """A single unit of work assigned to a team member.

    Follow-ups are DB-driven, not per-task timers: a recurring scan reads
    `next_followup_at`/`status` so reminders and escalations survive restarts.
    """

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=_new_id)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    assignee_telegram_id = Column(Integer, index=True, nullable=False)
    assigner_telegram_id = Column(Integer, index=True, nullable=False)

    # What deal/property this relates to (free text) and optional link to a
    # generated Transaction record.
    deal_ref = Column(String, nullable=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)

    # assigned, acknowledged, in_progress, blocked, done, cancelled
    status = Column(String, default="assigned", index=True)
    urgency = Column(String, default="standard")  # low, standard, high

    due_at = Column(DateTime, nullable=True)
    next_followup_at = Column(DateTime, nullable=True, index=True)
    followup_count = Column(Integer, default=0)
    escalated = Column(Boolean, default=False)

    # Chronological log of events/notes: [{ts, kind, text}]
    activity = Column(JSON, default=list)

    # Provenance when generated from a checklist template.
    checklist_key = Column(String, nullable=True)
    checklist_item = Column(String, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    completed_at = Column(DateTime, nullable=True)


# Terminal statuses that stop follow-ups/escalation.
TASK_TERMINAL_STATUSES = ("done", "cancelled")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(String, primary_key=True, default=_new_id)
    telegram_chat_id = Column(Integer, unique=True, index=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    state = Column(String, default="idle")
    doc_type = Column(String, nullable=True)
    collected_data = Column(JSON, default=dict)
    conversation_history = Column(JSON, default=list)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
