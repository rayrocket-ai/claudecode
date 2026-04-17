"""SQLAlchemy models for the Off-Market Property Dashboard."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


# ── Auth ──────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_new_id)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="agent")   # admin | agent
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=True)
    tenant_id = Column(String, nullable=True, index=True)  # reserved for Phase 2
    created_at = Column(DateTime, default=_utcnow)
    last_login_at = Column(DateTime, nullable=True)


# ── Property registry (global reference data) ─────────────────────────


class CanonicalProperty(Base):
    """One row per physical property, identified by normalized address."""

    __tablename__ = "canonical_properties"

    id = Column(String, primary_key=True, default=_new_id)

    # Original + normalized address components
    address_raw = Column(String, nullable=False)
    canonical_key = Column(String, unique=True, nullable=False, index=True)
    street_number = Column(String, nullable=True)
    street_name = Column(String, nullable=True)
    street_type = Column(String, nullable=True)
    street_dir = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    province = Column(String, default="ON")
    postal_code = Column(String, nullable=True, index=True)

    # Geocoding
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # Physical attributes (last seen from any listing)
    property_type = Column(String, nullable=True, index=True)
    beds = Column(Integer, nullable=True)
    baths = Column(Float, nullable=True)
    sqft = Column(Integer, nullable=True)

    # Denormalized for fast dashboard queries.
    # One of: Active | Sold | Expired | Terminated | Suspended | Conditional | Unknown
    current_status = Column(String, default="Unknown", index=True)
    last_listing_id = Column(
        String,
        ForeignKey("listings.id", use_alter=True, name="fk_canonical_last_listing"),
        nullable=True,
    )

    first_seen_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    listings = relationship(
        "Listing",
        back_populates="canonical_property",
        cascade="all, delete-orphan",
        foreign_keys="Listing.canonical_property_id",
    )


class Listing(Base):
    """One MLS listing cycle for a property. Same property can have many."""

    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("source", "mls_number", name="uq_listings_source_mls"),
        Index("ix_listings_status", "status"),
        Index("ix_listings_expiry", "expiry_date"),
    )

    id = Column(String, primary_key=True, default=_new_id)
    canonical_property_id = Column(
        String, ForeignKey("canonical_properties.id"), nullable=False, index=True
    )

    source = Column(String, nullable=False, default="TRREB")   # TRREB, CREB, ...
    mls_number = Column(String, nullable=False, index=True)

    status = Column(String, nullable=False)
    # Active | Sold | Expired | Terminated | Suspended | Conditional

    list_price = Column(Float, nullable=True)
    sold_price = Column(Float, nullable=True)

    commencement_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    sold_date = Column(Date, nullable=True)
    terminated_date = Column(Date, nullable=True)

    listing_agent_name = Column(String, nullable=True)
    listing_agent_id = Column(String, nullable=True)
    brokerage_name = Column(String, nullable=True)
    brokerage_id = Column(String, nullable=True)

    days_on_market = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)

    # Full raw row from TRREB for debugging / later extraction
    raw_payload = Column(JSON, default=dict)

    last_seen_at = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    canonical_property = relationship(
        "CanonicalProperty",
        back_populates="listings",
        foreign_keys=[canonical_property_id],
    )


# ── Owner / contact enrichment (stubbed providers in Phase 1) ─────────


class OwnerRecord(Base):
    __tablename__ = "owner_records"

    id = Column(String, primary_key=True, default=_new_id)
    canonical_property_id = Column(
        String, ForeignKey("canonical_properties.id"), nullable=False, index=True
    )
    source = Column(String, nullable=False)   # Teranet | GeoWarehouse | manual | stub
    owner_name = Column(String, nullable=True)
    owner_type = Column(String, nullable=True)  # individual | corp
    registered_date = Column(Date, nullable=True)
    title_info = Column(JSON, default=dict)
    fetched_at = Column(DateTime, default=_utcnow)
    expires_at = Column(DateTime, nullable=True)


class ContactInfo(Base):
    __tablename__ = "contact_info"

    id = Column(String, primary_key=True, default=_new_id)
    canonical_property_id = Column(
        String, ForeignKey("canonical_properties.id"), nullable=False, index=True
    )
    owner_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    source = Column(String, nullable=False)   # skip-trace-X | manual | stub
    confidence = Column(Float, nullable=True)
    fetched_at = Column(DateTime, default=_utcnow)


# ── Leads (working layer for agents) ──────────────────────────────────


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("tenant_id", "canonical_property_id", name="uq_leads_tenant_prop"),
    )

    id = Column(String, primary_key=True, default=_new_id)
    tenant_id = Column(String, nullable=True, index=True)   # Phase 2
    canonical_property_id = Column(
        String, ForeignKey("canonical_properties.id"), nullable=False, index=True
    )
    assigned_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="NotContacted", index=True)
    # NotContacted | Contacted | Appointment | Dead | Signed
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    notes = relationship("LeadNote", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship(
        "LeadActivity", back_populates="lead", cascade="all, delete-orphan"
    )


class LeadNote(Base):
    __tablename__ = "lead_notes"

    id = Column(String, primary_key=True, default=_new_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    lead = relationship("Lead", back_populates="notes")


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    id = Column(String, primary_key=True, default=_new_id)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    activity_type = Column(String, nullable=False)   # call | email | status_change | note
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utcnow)

    lead = relationship("Lead", back_populates="activities")


# ── Operational ───────────────────────────────────────────────────────


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(String, primary_key=True, default=_new_id)
    source = Column(String, nullable=False)  # TRREB
    started_at = Column(DateTime, default=_utcnow)
    finished_at = Column(DateTime, nullable=True)
    listings_seen = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    window_from = Column(Date, nullable=True)
    window_to = Column(Date, nullable=True)


class ScraperSession(Base):
    """Persistent Playwright cookie jar so we don't re-login every run."""

    __tablename__ = "scraper_sessions"

    id = Column(String, primary_key=True, default=_new_id)
    source = Column(String, unique=True, nullable=False)   # TRREB
    cookies = Column(JSON, default=list)
    storage_state = Column(JSON, default=dict)
    expires_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_mfa_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
