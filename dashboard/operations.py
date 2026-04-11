"""CRUD operations for Ray's Content Engine."""

import json
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import (
    CreatorProfile, BrandPillar, ClientStory, DailyBatch,
    ContentIdea, HookVariation, VideoScript,
    json_dump, json_load
)


# ── Profile ──────────────────────────────────────────────────────────────────

def get_profile(db: Session) -> Optional[CreatorProfile]:
    return db.query(CreatorProfile).first()


def update_profile(db: Session, data: dict) -> CreatorProfile:
    profile = get_profile(db)
    if not profile:
        profile = CreatorProfile()
        db.add(profile)

    for key, val in data.items():
        if key in ("story_elements", "themes", "gta_markets"):
            if isinstance(val, (list, dict)):
                val = json_dump(val)
        if hasattr(profile, key):
            setattr(profile, key, val)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


# ── Brand Pillars ─────────────────────────────────────────────────────────────

def get_pillars(db: Session) -> List[BrandPillar]:
    return db.query(BrandPillar).order_by(BrandPillar.sort_order).all()


def get_pillar(db: Session, pillar_id: str) -> Optional[BrandPillar]:
    return db.query(BrandPillar).filter(BrandPillar.id == pillar_id).first()


def upsert_pillar(db: Session, id: str, name: str, description: str,
                  emoji: str = "", sort_order: int = 0) -> BrandPillar:
    pillar = get_pillar(db, id)
    if not pillar:
        pillar = BrandPillar(id=id)
        db.add(pillar)
    pillar.name = name
    pillar.description = description
    pillar.emoji = emoji
    pillar.sort_order = sort_order
    db.commit()
    db.refresh(pillar)
    return pillar


# ── Client Stories ────────────────────────────────────────────────────────────

def get_stories(db: Session, scriptable_only: bool = False) -> List[ClientStory]:
    q = db.query(ClientStory)
    if scriptable_only:
        q = q.filter(ClientStory.is_scriptable == True)
    return q.order_by(ClientStory.created_at.desc()).all()


def get_story(db: Session, story_id: int) -> Optional[ClientStory]:
    return db.query(ClientStory).filter(ClientStory.id == story_id).first()


def create_story(db: Session, title: str, category: str, narrative: str,
                 lesson: str = "", emotional_peak: str = "",
                 is_scriptable: bool = True) -> ClientStory:
    story = ClientStory(
        title=title,
        category=category,
        narrative=narrative,
        lesson=lesson,
        emotional_peak=emotional_peak,
        is_scriptable=is_scriptable,
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


def update_story(db: Session, story_id: int, data: dict) -> Optional[ClientStory]:
    story = get_story(db, story_id)
    if not story:
        return None
    for key, val in data.items():
        if hasattr(story, key):
            setattr(story, key, val)
    db.commit()
    db.refresh(story)
    return story


def delete_story(db: Session, story_id: int) -> bool:
    story = get_story(db, story_id)
    if not story:
        return False
    db.delete(story)
    db.commit()
    return True


# ── Daily Batch ───────────────────────────────────────────────────────────────

def get_today_batch(db: Session) -> Optional[DailyBatch]:
    return db.query(DailyBatch).filter(DailyBatch.date == date.today()).first()


def get_batch(db: Session, batch_id: int) -> Optional[DailyBatch]:
    return db.query(DailyBatch).filter(DailyBatch.id == batch_id).first()


def create_batch(db: Session, topic_mix: dict = None) -> DailyBatch:
    batch = DailyBatch(
        date=date.today(),
        status="generating",
        topic_mix=json_dump(topic_mix or {}),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def complete_batch(db: Session, batch_id: int, script_count: int) -> DailyBatch:
    batch = get_batch(db, batch_id)
    if batch:
        batch.status = "complete"
        batch.total_scripts = script_count
        db.commit()
        db.refresh(batch)
    return batch


def fail_batch(db: Session, batch_id: int) -> DailyBatch:
    batch = get_batch(db, batch_id)
    if batch:
        batch.status = "failed"
        db.commit()
        db.refresh(batch)
    return batch


# ── Content Ideas ─────────────────────────────────────────────────────────────

def get_ideas(db: Session, limit: int = 30) -> List[ContentIdea]:
    return db.query(ContentIdea).order_by(ContentIdea.created_at.desc()).limit(limit).all()


def get_idea(db: Session, idea_id: int) -> Optional[ContentIdea]:
    return db.query(ContentIdea).filter(ContentIdea.id == idea_id).first()


def create_idea(db: Session, pillar_id: str, core_story: str,
                viral_angle: str = "", platform_fit: str = "",
                hook_seeds: list = None, script_type: str = "wildcard",
                batch_id: int = None) -> ContentIdea:
    idea = ContentIdea(
        pillar_id=pillar_id,
        core_story=core_story,
        viral_angle=viral_angle,
        platform_fit=platform_fit,
        hook_seeds=json_dump(hook_seeds or []),
        status="idea",
        batch_id=batch_id,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def update_idea_status(db: Session, idea_id: int, status: str) -> Optional[ContentIdea]:
    idea = get_idea(db, idea_id)
    if idea:
        idea.status = status
        db.commit()
        db.refresh(idea)
    return idea


def clear_old_ideas(db: Session, keep_days: int = 35):
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=keep_days)
    db.query(ContentIdea).filter(ContentIdea.created_at < cutoff).delete()
    db.commit()


# ── Hook Variations ───────────────────────────────────────────────────────────

def get_hooks_for_idea(db: Session, idea_id: int) -> List[HookVariation]:
    return db.query(HookVariation).filter(HookVariation.idea_id == idea_id).all()


def create_hook(db: Session, idea_id: int, hook_text: str, hook_type: str,
                scroll_stop_score: float, curiosity_score: float,
                specificity_score: float, authenticity_score: float) -> HookVariation:
    hook = HookVariation(
        idea_id=idea_id,
        hook_text=hook_text,
        hook_type=hook_type,
        scroll_stop_score=scroll_stop_score,
        curiosity_score=curiosity_score,
        specificity_score=specificity_score,
        authenticity_score=authenticity_score,
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return hook


def choose_hook(db: Session, hook_id: int) -> Optional[HookVariation]:
    hook = db.query(HookVariation).filter(HookVariation.id == hook_id).first()
    if hook:
        # Deselect other hooks for this idea
        db.query(HookVariation).filter(
            HookVariation.idea_id == hook.idea_id,
            HookVariation.id != hook_id
        ).update({"chosen": False})
        hook.chosen = True
        db.commit()
        db.refresh(hook)
    return hook


# ── Video Scripts ─────────────────────────────────────────────────────────────

def get_scripts(db: Session, batch_id: int = None, limit: int = 50) -> List[VideoScript]:
    q = db.query(VideoScript)
    if batch_id:
        q = q.filter(VideoScript.batch_id == batch_id)
    return q.order_by(VideoScript.created_at.desc()).limit(limit).all()


def get_today_scripts(db: Session) -> List[VideoScript]:
    batch = get_today_batch(db)
    if not batch:
        return []
    return get_scripts(db, batch_id=batch.id)


def get_script(db: Session, script_id: int) -> Optional[VideoScript]:
    return db.query(VideoScript).filter(VideoScript.id == script_id).first()


def create_script(db: Session, data: dict) -> VideoScript:
    # Calculate word count and duration
    full_text = f"{data.get('hook', '')} {data.get('body', '')} {data.get('cta', '')}"
    word_count = len(full_text.split())
    # Average speaking pace: ~130 words/minute
    duration = max(30, min(90, int(word_count / 130 * 60)))

    script = VideoScript(
        batch_id=data.get("batch_id"),
        idea_id=data.get("idea_id"),
        client_story_id=data.get("client_story_id"),
        title=data.get("title", "Untitled"),
        hook=data.get("hook", ""),
        body=data.get("body", ""),
        cta=data.get("cta", ""),
        platform=data.get("platform", "reels"),
        caption=data.get("caption", ""),
        hashtags=data.get("hashtags", ""),
        script_type=data.get("script_type", "wildcard"),
        status="draft",
        word_count=word_count,
        estimated_duration_seconds=data.get("estimated_duration_seconds", duration),
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


def update_script_status(db: Session, script_id: int, status: str) -> Optional[VideoScript]:
    script = get_script(db, script_id)
    if script:
        script.status = status
        db.commit()
        db.refresh(script)
    return script
