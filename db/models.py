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


class Reminder(Base):
    """A scheduled deadline notification for a deal.

    All datetimes are stored as naive UTC (the SQLite dialect drops tzinfo on
    write, so naive-UTC-everywhere keeps reads and writes consistent).
    """

    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=_new_id)
    telegram_chat_id = Column(Integer, index=True, nullable=False)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    kind = Column(String, nullable=False)      # irrevocability, closing, condition
    label = Column(String, nullable=False)     # e.g. "Irrevocability — 123 Main St, Toronto"
    deadline_at = Column(DateTime, nullable=False)          # the actual deadline (UTC)
    notify_at = Column(DateTime, nullable=False, index=True)  # when to send the DM (UTC)
    sent = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=_utcnow)


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
