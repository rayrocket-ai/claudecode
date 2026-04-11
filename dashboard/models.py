"""SQLAlchemy models for Ray's Content Engine."""

import json
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, Date,
    ForeignKey, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

Base = declarative_base()


class JSONColumn(Text):
    """Store JSON as text."""
    pass


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


class CreatorProfile(Base):
    __tablename__ = "creator_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, default="Ray Ahmadi")
    bio = Column(Text, nullable=True)
    story_elements = Column(Text, nullable=True)   # JSON list of story bullets
    themes = Column(Text, nullable=True)            # JSON list of theme dicts
    gta_markets = Column(Text, nullable=True)       # JSON list of market names
    instagram = Column(String(200), nullable=True)
    tiktok = Column(String(200), nullable=True)
    youtube = Column(String(200), nullable=True)
    linkedin = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def story_elements_list(self):
        return json_load(self.story_elements)

    def themes_list(self):
        return json_load(self.themes)

    def markets_list(self):
        return json_load(self.gta_markets)


class BrandPillar(Base):
    __tablename__ = "brand_pillars"

    id = Column(String(50), primary_key=True)   # slug like "authority_expertise"
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    emoji = Column(String(10), nullable=True)
    sort_order = Column(Integer, default=0)

    ideas = relationship("ContentIdea", back_populates="pillar")


class ClientStory(Base):
    __tablename__ = "client_stories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    category = Column(String(50), nullable=False)  # win/loss/turnaround/first_time_buyer
    narrative = Column(Text, nullable=False)
    lesson = Column(Text, nullable=True)
    emotional_peak = Column(Text, nullable=True)
    is_scriptable = Column(Boolean, default=True)
    times_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    scripts = relationship("VideoScript", back_populates="client_story")


class DailyBatch(Base):
    __tablename__ = "daily_batches"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, default=date.today)
    status = Column(String(50), default="generating")  # generating/complete/failed
    total_scripts = Column(Integer, default=0)
    topic_mix = Column(Text, nullable=True)  # JSON dict
    created_at = Column(DateTime, default=datetime.utcnow)

    scripts = relationship("VideoScript", back_populates="batch")

    def topic_mix_dict(self):
        return json_load(self.topic_mix)


class ContentIdea(Base):
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True, index=True)
    pillar_id = Column(String(50), ForeignKey("brand_pillars.id"), nullable=True)
    core_story = Column(Text, nullable=False)
    viral_angle = Column(Text, nullable=True)
    platform_fit = Column(String(200), nullable=True)   # comma-separated platforms
    hook_seeds = Column(Text, nullable=True)             # JSON list of 3 seeds
    status = Column(String(50), default="idea")  # idea/hook_chosen/scripted/scheduled/posted
    batch_id = Column(Integer, ForeignKey("daily_batches.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pillar = relationship("BrandPillar", back_populates="ideas")
    hooks = relationship("HookVariation", back_populates="idea", cascade="all, delete-orphan")
    scripts = relationship("VideoScript", back_populates="idea")

    def hook_seeds_list(self):
        return json_load(self.hook_seeds)


class HookVariation(Base):
    __tablename__ = "hook_variations"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("content_ideas.id"), nullable=False)
    hook_text = Column(Text, nullable=False)
    hook_type = Column(String(50), nullable=False)  # curiosity/contrarian/number
    scroll_stop_score = Column(Float, default=0)
    curiosity_score = Column(Float, default=0)
    specificity_score = Column(Float, default=0)
    authenticity_score = Column(Float, default=0)
    chosen = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    idea = relationship("ContentIdea", back_populates="hooks")

    def composite_score(self):
        return round(
            (self.scroll_stop_score * 0.35 +
             self.curiosity_score * 0.25 +
             self.specificity_score * 0.20 +
             self.authenticity_score * 0.20), 1
        )


class VideoScript(Base):
    __tablename__ = "video_scripts"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("daily_batches.id"), nullable=True)
    idea_id = Column(Integer, ForeignKey("content_ideas.id"), nullable=True)
    client_story_id = Column(Integer, ForeignKey("client_stories.id"), nullable=True)
    title = Column(String(300), nullable=False)
    hook = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    cta = Column(Text, nullable=False)
    platform = Column(String(50), default="reels")  # reels/tiktok/shorts/linkedin
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    script_type = Column(String(50), nullable=True)  # market/mortgage/personal/client_win/trending/wildcard
    status = Column(String(50), default="draft")  # draft/approved/posted
    word_count = Column(Integer, default=0)
    estimated_duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("DailyBatch", back_populates="scripts")
    idea = relationship("ContentIdea", back_populates="scripts")
    client_story = relationship("ClientStory", back_populates="scripts")

    def full_script(self):
        return f"{self.hook}\n\n{self.body}\n\n{self.cta}"

    def hashtags_list(self):
        if not self.hashtags:
            return []
        return [h.strip() for h in self.hashtags.split() if h.startswith("#")]


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./content.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
