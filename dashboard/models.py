"""SQLAlchemy models for the video script dashboard."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from db.models import Base, _utcnow, _new_id


class CreatorProfile(Base):
    __tablename__ = "creator_profiles"

    id = Column(String, primary_key=True, default=_new_id)
    name = Column(String, default="")
    location = Column(String, default="Ontario, Canada")
    profession = Column(String, default="Real Estate & Mortgage Professional")
    bio = Column(Text, default="")
    brand_values = Column(JSON, default=list)
    story_elements = Column(JSON, default=lambda: {
        "family": "",
        "challenges": "",
        "victories": "",
        "travels": "",
        "background": "",
    })
    tone = Column(String, default="motivational_educational")
    platforms = Column(JSON, default=lambda: [
        "tiktok", "instagram_reels", "youtube_shorts", "facebook_reels"
    ])
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class DailyBatch(Base):
    __tablename__ = "daily_batches"

    id = Column(String, primary_key=True, default=_new_id)
    date = Column(Date, unique=True, nullable=False, index=True)
    status = Column(String, default="pending")  # pending, generating, complete, error
    trending_data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    scripts = relationship("VideoScript", back_populates="batch", cascade="all, delete-orphan",
                           order_by="VideoScript.sort_order")
    trending_items = relationship("TrendingItem", back_populates="batch", cascade="all, delete-orphan")


class VideoScript(Base):
    __tablename__ = "video_scripts"

    id = Column(String, primary_key=True, default=_new_id)
    batch_id = Column(String, ForeignKey("daily_batches.id"), nullable=False)
    category = Column(String, nullable=False)  # real_estate, mortgage, politics_economy, sports, personal
    title = Column(String, default="")
    hook = Column(Text, default="")
    body = Column(Text, default="")
    cta = Column(Text, default="")
    personal_tie_in = Column(Text, default="")
    hashtags = Column(JSON, default=dict)
    visual_suggestions = Column(Text, default="")
    platform_notes = Column(JSON, default=dict)
    hook_style = Column(String, default="")  # question, stat, controversy, story, pattern_interrupt, challenge, confession
    estimated_duration = Column(Integer, default=45)
    is_edited = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)

    batch = relationship("DailyBatch", back_populates="scripts")


class TrendingItem(Base):
    __tablename__ = "trending_items"

    id = Column(String, primary_key=True, default=_new_id)
    batch_id = Column(String, ForeignKey("daily_batches.id"), nullable=False)
    source = Column(String, nullable=False)  # google_trends, rss_news, reddit, bank_of_canada
    category = Column(String, nullable=False)  # real_estate, mortgage, politics, sports, general
    title = Column(String, nullable=False)
    summary = Column(Text, default="")
    url = Column(String, default="")
    relevance_score = Column(Float, default=0.5)
    raw_data = Column(JSON, default=dict)
    fetched_at = Column(DateTime, default=_utcnow)

    batch = relationship("DailyBatch", back_populates="trending_items")
