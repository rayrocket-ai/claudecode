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


# ── 6-Stage Content Pipeline Models ──────────────────────────────────

class BrandPillar(Base):
    """One of the 6 brand pillars every idea gets tagged with."""
    __tablename__ = "brand_pillars"

    id = Column(String, primary_key=True)  # "authority_expertise", "behind_scenes", etc.
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)

    ideas = relationship("ContentIdea", back_populates="pillar")


class ClientStory(Base):
    """Real client wins/losses that get injected into scripts as proof."""
    __tablename__ = "client_stories"

    id = Column(String, primary_key=True, default=_new_id)
    title = Column(String, default="")                 # "Sara — 3 rejected offers"
    category = Column(String, default="win")            # win, loss, turnaround, first_time_buyer, mortgage_save
    narrative = Column(Text, default="")                # Full story
    lesson = Column(Text, default="")                   # One-line takeaway
    emotional_peak = Column(Text, default="")           # The moment of truth
    is_scriptable = Column(Boolean, default=True)
    times_used = Column(Integer, default=0)             # Track repetition
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class IdeaBatch(Base):
    """A 30-day idea bank batch generated by Stage 1."""
    __tablename__ = "idea_batches"

    id = Column(String, primary_key=True, default=_new_id)
    label = Column(String, default="")                  # e.g. "November 2026 Bank"
    num_ideas = Column(Integer, default=30)
    status = Column(String, default="generating")       # generating, complete, error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    ideas = relationship("ContentIdea", back_populates="batch", cascade="all, delete-orphan",
                         order_by="ContentIdea.sort_order")


class ContentIdea(Base):
    """Stage 1 output — one content idea with pillar, story, hooks, platform, angle."""
    __tablename__ = "content_ideas"

    id = Column(String, primary_key=True, default=_new_id)
    batch_id = Column(String, ForeignKey("idea_batches.id"), nullable=True)
    pillar_id = Column(String, ForeignKey("brand_pillars.id"), nullable=True)
    title = Column(String, default="")
    core_story = Column(Text, default="")               # The real human moment at the centre
    viral_angle = Column(String, default="")            # identity, shock, education, aspiration
    platform_fit = Column(String, default="reels")      # reels, tiktok, shorts, linkedin
    target_location = Column(String, default="")        # Brampton, Vaughan, GTA-wide, etc.
    market_condition_ref = Column(Text, default="")     # Current market tie-in if any
    is_personal_brand = Column(Boolean, default=False)  # True if drawing from Ray's origin story
    client_story_id = Column(String, ForeignKey("client_stories.id"), nullable=True)
    status = Column(String, default="idea")             # idea, hook_chosen, scripted, scheduled, posted
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    batch = relationship("IdeaBatch", back_populates="ideas")
    pillar = relationship("BrandPillar", back_populates="ideas")
    hook_variations = relationship("HookVariation", back_populates="idea", cascade="all, delete-orphan")


class HookVariation(Base):
    """Stage 2 output — 3 hook variations per idea, each scored."""
    __tablename__ = "hook_variations"

    id = Column(String, primary_key=True, default=_new_id)
    idea_id = Column(String, ForeignKey("content_ideas.id"), nullable=False)
    hook_text = Column(Text, nullable=False)
    hook_type = Column(String, default="curiosity")     # curiosity, contrarian, number
    scroll_stop_score = Column(Integer, default=0)      # 1-10: stops scroll in first 3 words?
    curiosity_score = Column(Integer, default=0)        # 1-10: opens curiosity gap?
    specificity_score = Column(Integer, default=0)      # 1-10: GTA-hyper-specific?
    authenticity_score = Column(Integer, default=0)     # 1-10: sounds like Ray, not AI?
    chosen = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    idea = relationship("ContentIdea", back_populates="hook_variations")
