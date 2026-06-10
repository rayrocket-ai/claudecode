"""SQLAlchemy models for RayRocket Studio — realtor services storefront."""

import json
import os
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def json_load(val):
    if val is None:
        return []
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return []


def json_dump(val):
    if val is None:
        return "[]"
    if isinstance(val, str):
        return val
    return json.dumps(val)


class TourOrder(Base):
    """A cinematic house tour order — the realtor gives us an address, we deliver a video."""

    __tablename__ = "tour_orders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=True)
    brokerage = Column(String(200), nullable=True)
    address = Column(Text, nullable=False)
    listing_url = Column(Text, nullable=True)
    package = Column(String(50), nullable=False, default="single")  # single | starter | pro | brokerage
    style = Column(String(50), nullable=False, default="cinematic")  # cinematic | luxury | social
    rush = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="new")  # new | contacted | paid | in_production | delivered
    created_at = Column(DateTime, default=datetime.utcnow)


class ReceptionistLead(Base):
    """AI receptionist intake — what the realtor needs handled and at what volume."""

    __tablename__ = "receptionist_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=True)
    brokerage = Column(String(200), nullable=True)
    tasks = Column(Text, nullable=True)            # JSON list of selected task keys
    call_volume = Column(String(50), nullable=True)   # low | medium | high
    coverage = Column(String(50), nullable=True)      # business | extended | always
    crm = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    recommended_plan = Column(String(50), nullable=True)
    status = Column(String(30), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    def tasks_list(self):
        return json_load(self.tasks)


class WaitlistEntry(Base):
    """Waitlist signups for services that aren't live yet (second brain, exec assistant, etc.)."""

    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(100), nullable=False)  # second_brain | exec_assistant | other
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Vercel's filesystem is read-only outside /tmp, so default the SQLite file
# there when running on Vercel (data is ephemeral — use a hosted DB via
# STUDIO_DATABASE_URL for production).
_default_sqlite = "sqlite:////tmp/studio.db" if os.getenv("VERCEL") else "sqlite:///./studio.db"
DATABASE_URL = os.getenv("STUDIO_DATABASE_URL", _default_sqlite)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
