"""Database CRUD operations for the video script dashboard."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from db.operations import get_session, init_db
from dashboard.models import CreatorProfile, DailyBatch, VideoScript, TrendingItem


# ── Creator Profile ───────────────────────────────────────────────────

async def get_or_create_profile() -> CreatorProfile:
    """Get the single creator profile, creating one if it doesn't exist."""
    async with get_session() as session:
        result = await session.execute(select(CreatorProfile))
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = CreatorProfile()
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
        return profile


async def update_profile(data: dict[str, Any]) -> CreatorProfile:
    """Update the creator profile with new data."""
    async with get_session() as session:
        result = await session.execute(select(CreatorProfile))
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = CreatorProfile()
            session.add(profile)

        for key, value in data.items():
            if hasattr(profile, key) and key not in ("id", "created_at"):
                setattr(profile, key, value)
                if isinstance(value, (dict, list)):
                    flag_modified(profile, key)

        await session.commit()
        await session.refresh(profile)
        return profile


def profile_to_dict(profile: CreatorProfile) -> dict[str, Any]:
    """Convert a profile model to a plain dict for prompt building."""
    return {
        "name": profile.name,
        "location": profile.location,
        "profession": profile.profession,
        "bio": profile.bio,
        "brand_values": profile.brand_values or [],
        "story_elements": profile.story_elements or {},
        "tone": profile.tone,
        "platforms": profile.platforms or [],
    }


# ── Daily Batches ─────────────────────────────────────────────────────

async def get_batch_for_date(target_date: date) -> DailyBatch | None:
    """Get the batch for a specific date, with scripts loaded."""
    async with get_session() as session:
        result = await session.execute(
            select(DailyBatch)
            .options(selectinload(DailyBatch.scripts), selectinload(DailyBatch.trending_items))
            .where(DailyBatch.date == target_date)
        )
        return result.scalar_one_or_none()


async def create_batch(target_date: date, trending_data: dict) -> DailyBatch:
    """Create a new daily batch."""
    async with get_session() as session:
        batch = DailyBatch(date=target_date, trending_data=trending_data, status="generating")
        session.add(batch)
        await session.commit()
        await session.refresh(batch)
        return batch


async def update_batch_status(batch_id: str, status: str, error_message: str | None = None) -> None:
    """Update batch status."""
    async with get_session() as session:
        result = await session.execute(select(DailyBatch).where(DailyBatch.id == batch_id))
        batch = result.scalar_one_or_none()
        if batch:
            batch.status = status
            if error_message is not None:
                batch.error_message = error_message
            await session.commit()


async def list_batches(limit: int = 30) -> list[DailyBatch]:
    """List recent batches ordered by date descending."""
    async with get_session() as session:
        result = await session.execute(
            select(DailyBatch)
            .options(selectinload(DailyBatch.scripts))
            .order_by(DailyBatch.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# ── Video Scripts ─────────────────────────────────────────────────────

async def save_scripts(batch_id: str, scripts_data: list[dict[str, Any]]) -> list[VideoScript]:
    """Save generated scripts to the database."""
    async with get_session() as session:
        scripts = []
        for i, sd in enumerate(scripts_data):
            script = VideoScript(
                batch_id=batch_id,
                category=sd.get("category", ""),
                title=sd.get("title", ""),
                hook=sd.get("hook", ""),
                body=sd.get("body", ""),
                cta=sd.get("cta", ""),
                personal_tie_in=sd.get("personal_tie_in", ""),
                hashtags=sd.get("hashtags", {}),
                visual_suggestions=sd.get("visual_suggestions", ""),
                platform_notes=sd.get("platform_notes", {}),
                hook_style=sd.get("hook_style", ""),
                estimated_duration=sd.get("estimated_duration", 45),
                sort_order=i + 1,
            )
            session.add(script)
            scripts.append(script)
        await session.commit()
        for s in scripts:
            await session.refresh(s)
        return scripts


async def get_script(script_id: str) -> VideoScript | None:
    """Get a single script by ID."""
    async with get_session() as session:
        result = await session.execute(select(VideoScript).where(VideoScript.id == script_id))
        return result.scalar_one_or_none()


async def update_script(script_id: str, data: dict[str, Any]) -> VideoScript | None:
    """Update a script (user edits)."""
    async with get_session() as session:
        result = await session.execute(select(VideoScript).where(VideoScript.id == script_id))
        script = result.scalar_one_or_none()
        if script is None:
            return None

        for key, value in data.items():
            if hasattr(script, key) and key not in ("id", "batch_id", "created_at", "sort_order"):
                setattr(script, key, value)
                if isinstance(value, (dict, list)):
                    flag_modified(script, key)

        script.is_edited = True
        await session.commit()
        await session.refresh(script)
        return script


async def delete_script(script_id: str) -> bool:
    """Delete a script."""
    async with get_session() as session:
        result = await session.execute(select(VideoScript).where(VideoScript.id == script_id))
        script = result.scalar_one_or_none()
        if script:
            await session.delete(script)
            await session.commit()
            return True
        return False


# ── Trending Items ────────────────────────────────────────────────────

async def save_trending_items(batch_id: str, items: list[dict[str, Any]]) -> None:
    """Save trending items to the database."""
    async with get_session() as session:
        for item in items:
            ti = TrendingItem(
                batch_id=batch_id,
                source=item.get("source", ""),
                category=item.get("category", "general"),
                title=item.get("title", ""),
                summary=item.get("summary", ""),
                url=item.get("url", ""),
                raw_data=item.get("raw_data", {}),
            )
            session.add(ti)
        await session.commit()


async def get_trending_for_date(target_date: date) -> list[TrendingItem]:
    """Get trending items for a specific date."""
    async with get_session() as session:
        result = await session.execute(
            select(TrendingItem)
            .join(DailyBatch)
            .where(DailyBatch.date == target_date)
            .order_by(TrendingItem.category, TrendingItem.fetched_at.desc())
        )
        return list(result.scalars().all())
