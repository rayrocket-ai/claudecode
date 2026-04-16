"""Database CRUD operations for the video script dashboard."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from db.operations import get_session, init_db
from dashboard.models import (
    CreatorProfile,
    DailyBatch,
    VideoScript,
    TrendingItem,
    BrandPillar,
    ClientStory,
    IdeaBatch,
    ContentIdea,
    HookVariation,
)


# ── Creator Profile ───────────────────────────────────────────────────

RAY_DEFAULT_PROFILE = {
    "name": "Ray",
    "location": "Greater Toronto Area, Ontario, Canada",
    "profession": "Licensed Real Estate Broker (GTA) — 12+ years residential, investment, pre-construction & commercial",
    "bio": (
        "I'm a licensed real estate broker in the Greater Toronto Area with over 12 years helping "
        "families buy, sell, and invest across Brampton, Vaughan, Mississauga, Markham, Oakville, "
        "Scarborough and North York. But my story starts a long way from Canada. I was born in "
        "Afghanistan, grew up hiding from Taliban rockets in a cellar, escaped across the Pakistani "
        "border at night in the back of a truck, spent nine years as an unwanted outsider in Moscow "
        "watching my father rebuild a life from a roadside table, and arrived at Pearson Airport on "
        "October 13, 2009 with nothing. I built everything here from zero — because I had to. "
        "When I help a family buy a home, I know exactly what 'feeling safe' is worth. I've lived "
        "the alternative."
    ),
    "brand_values": [
        "Safety is a privilege, not a given",
        "Starting over is survivable",
        "Money alone doesn't make you happy",
        "Hustle at the smallest scale works",
        "Outsider perspective is an insider advantage",
        "Patience under pressure",
        "Family is the why",
    ],
    "story_elements": {
        "origin": (
            "Born in Afghanistan in the mid-1990s, during the Taliban occupation. My earliest "
            "memories are of hiding in the cellar with my mother and sister while rockets fell "
            "on the neighbourhood. Thousands of civilians were killed. We only ever had loaves "
            "of bread my mother baked at home."
        ),
        "first_escape": (
            "My father lost his job. We sold everything we owned. One night we fled through the "
            "wilderness in the back of a truck to the Pakistani border. The military got very "
            "lucky and didn't check the back. If they had, I wouldn't be telling this story."
        ),
        "pakistan_years": (
            "We spent 18 months in Peshawar. My dad couldn't find work — he didn't speak Urdu. "
            "My sister and I couldn't attend regular school — we had no documents. Eventually my "
            "father left alone for Russia, hoping to earn enough to sponsor us."
        ),
        "journey_to_russia": (
            "Two-week illegal bus journey through the wilderness to Uzbekistan. No clean water, "
            "no fresh air, no rest. I got sick. Fake passports. A train to Moscow. Our guide "
            "warned us to stay silent — the soldiers along the road didn't like Afghans."
        ),
        "arrival_moscow": (
            "August 23, 2000. We reunited with my father at a Moscow train station. He'd lost "
            "weight from overwork. I didn't ask why. I just held him."
        ),
        "russia_years": (
            "We lived in Moscow for 9 years. My father and uncle built a business from a roadside "
            "table into a store, then a factory in China, then an import operation. We became "
            "wealthy. I always had money in my pocket. We had a house, three apartments, cars."
        ),
        "russia_racism": (
            "But Russia hated us. Bullies extorted money from my dad and threatened to kill him. "
            "Police stopped us on the street demanding bribes. I couldn't join the soccer team — "
            "'you don't have the right documents.' Classmates told me 'get out of our country.' "
            "I fought back. I lost, because I was always outnumbered. That's when I learned: "
            "money alone does not make people happy."
        ),
        "canada_decision": (
            "In 2006 we applied to immigrate to Canada. We heard Canada was equal, safe, free. "
            "We waited three years for the Canadian embassy to call us back."
        ),
        "canada_arrival": (
            "October 13, 2009. Pearson International Airport, Toronto. We met our sponsor with "
            "tears in our eyes. My father had left everything behind in Russia — his house, his "
            "business, his brother — because he had promised us he would never leave us alone "
            "again. He restarted his life twice so I could have this one."
        ),
        "real_estate_path": (
            "I became a licensed real estate broker in Ontario because I understand something "
            "most agents don't: a home isn't a price or a number on a balance sheet. A home is "
            "the feeling that nobody can tell you 'get out of our country' ever again. I've now "
            "spent 12+ years helping families across the GTA buy, sell, invest and build "
            "generational wealth through residential, investment, pre-construction and "
            "commercial real estate."
        ),
        "family": "My family is the entire point. My parents' sacrifices built my life. Everything I do is so they can see what they earned.",
        "challenges": "Taliban war. Refugee childhood. Two countries where we weren't welcome. Starting from zero in Canada at 15. Learning English. Building a real estate business from nothing with no network.",
        "victories": "Becoming a licensed GTA broker. 12+ years of closed deals. Helping newcomer families find their first Canadian home. Building the kind of trust my parents never got from anyone.",
        "background": (
            "Afghanistan → Pakistan → Russia → Canada. Arrived in Toronto October 13, 2009. "
            "Licensed real estate broker operating across the Greater Toronto Area with focus on "
            "Brampton, Vaughan, Mississauga, Markham, Oakville, Scarborough, North York."
        ),
    },
    "tone": "grounded_authoritative_personal",
    "platforms": ["tiktok", "instagram_reels", "youtube_shorts", "facebook_reels", "linkedin"],
}


async def get_or_create_profile() -> CreatorProfile:
    """Get the single creator profile, creating one seeded with Ray's real story if missing.

    If an empty default profile already exists (from earlier dashboard versions),
    backfill the name, bio, and story_elements with Ray's real story. Never
    overwrite non-empty user edits.
    """
    async with get_session() as session:
        result = await session.execute(select(CreatorProfile))
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = CreatorProfile(
                name=RAY_DEFAULT_PROFILE["name"],
                location=RAY_DEFAULT_PROFILE["location"],
                profession=RAY_DEFAULT_PROFILE["profession"],
                bio=RAY_DEFAULT_PROFILE["bio"],
                brand_values=RAY_DEFAULT_PROFILE["brand_values"],
                story_elements=RAY_DEFAULT_PROFILE["story_elements"],
                tone=RAY_DEFAULT_PROFILE["tone"],
                platforms=RAY_DEFAULT_PROFILE["platforms"],
            )
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            return profile

        # Backfill empty fields without overwriting real edits
        changed = False
        if not (profile.name or "").strip():
            profile.name = RAY_DEFAULT_PROFILE["name"]
            changed = True
        if not (profile.bio or "").strip():
            profile.bio = RAY_DEFAULT_PROFILE["bio"]
            changed = True
        if not profile.brand_values:
            profile.brand_values = RAY_DEFAULT_PROFILE["brand_values"]
            flag_modified(profile, "brand_values")
            changed = True
        # Backfill story_elements if missing the new "origin" key
        current_story = profile.story_elements or {}
        if "origin" not in current_story or not (current_story.get("origin") or "").strip():
            merged = dict(RAY_DEFAULT_PROFILE["story_elements"])
            # Preserve any existing non-empty values from the old schema
            for k, v in current_story.items():
                if v and isinstance(v, str) and v.strip():
                    merged[k] = v
            profile.story_elements = merged
            flag_modified(profile, "story_elements")
            changed = True
        if changed:
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
                platform=item.get("platform", "rss"),
                velocity_score=float(item.get("velocity_score") or 0),
                engagement=item.get("engagement", {}),
                author=item.get("author", ""),
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


# ── Brand Pillars ─────────────────────────────────────────────────────

BRAND_PILLAR_SEED = [
    ("authority_expertise", "Authority & Expertise",
     "Market knowledge, 12+ years of GTA deals, insider intel, the real numbers most people never see.", 1),
    ("behind_scenes", "Behind the Scenes",
     "The unseen hours: 11pm deal calls, driving to Brampton showings in the snow, the paperwork nobody talks about.", 2),
    ("client_wins", "Client Wins",
     "Real families, real turnarounds, real moments when a house became a home. Never generic \"happy client\" content.", 3),
    ("market_intel", "Market Intel",
     "Today's rates, today's listings, today's trends. Hyper-specific GTA neighbourhood data. Pre-con vs resale. Bidding wars.", 4),
    ("mindset_lifestyle", "Mindset & Lifestyle",
     "How Ray thinks: immigrant resilience, patience under pressure, money ≠ happiness. Daily routines, family moments.", 5),
    ("community_culture", "Community & Culture",
     "The GTA itself — Brampton, Vaughan, Mississauga, Scarborough. South Asian diaspora. Newcomer families. Multi-gen homes.", 6),
]


async def seed_brand_pillars() -> None:
    """Seed the 6 brand pillars if they don't exist."""
    async with get_session() as session:
        for pillar_id, name, description, order in BRAND_PILLAR_SEED:
            result = await session.execute(select(BrandPillar).where(BrandPillar.id == pillar_id))
            existing = result.scalar_one_or_none()
            if existing is None:
                pillar = BrandPillar(id=pillar_id, name=name, description=description, sort_order=order)
                session.add(pillar)
        await session.commit()


# ── Lightweight SQLite migrations (ADD COLUMN idempotent) ─────────────

TRENDING_ITEM_MIGRATIONS = [
    ("velocity_score", "FLOAT DEFAULT 0.0"),
    ("platform", "VARCHAR DEFAULT 'rss'"),
    ("engagement", "JSON DEFAULT '{}'"),
    ("author", "VARCHAR DEFAULT ''"),
    ("posted_at", "DATETIME"),
]

VIDEO_SCRIPT_MIGRATIONS = [
    ("idea_id", "VARCHAR"),
    ("chosen_hook_id", "VARCHAR"),
    ("pillar_id", "VARCHAR"),
    ("viral_angle", "VARCHAR DEFAULT ''"),
    ("platform_captions", "JSON DEFAULT '{}'"),
    ("hormozi_density_score", "FLOAT DEFAULT 0.0"),
    ("word_count_original", "INTEGER DEFAULT 0"),
    ("word_count_compressed", "INTEGER DEFAULT 0"),
    ("pipeline_stage", "VARCHAR DEFAULT 'scripted'"),
]


async def run_light_migrations() -> None:
    """Add new columns to existing tables without losing data.

    SQLAlchemy's create_all never ALTERs existing tables. This runs idempotent
    ADD COLUMN statements so the new pipeline columns appear on live deployments.
    """
    from sqlalchemy import text
    from db.operations import _engine as db_engine
    async with db_engine.begin() as conn:
        # Check which columns already exist on video_scripts
        result = await conn.execute(text("PRAGMA table_info(video_scripts)"))
        existing_cols = {row[1] for row in result.fetchall()}
        for col_name, col_type in VIDEO_SCRIPT_MIGRATIONS:
            if col_name not in existing_cols:
                try:
                    await conn.execute(text(f"ALTER TABLE video_scripts ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass

        # TrendingItem columns
        result2 = await conn.execute(text("PRAGMA table_info(trending_items)"))
        existing_ti_cols = {row[1] for row in result2.fetchall()}
        for col_name, col_type in TRENDING_ITEM_MIGRATIONS:
            if col_name not in existing_ti_cols:
                try:
                    await conn.execute(text(f"ALTER TABLE trending_items ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass


async def list_brand_pillars() -> list[BrandPillar]:
    """Get all brand pillars ordered by sort_order."""
    async with get_session() as session:
        result = await session.execute(select(BrandPillar).order_by(BrandPillar.sort_order))
        return list(result.scalars().all())


# ── Client Stories ────────────────────────────────────────────────────

async def list_client_stories(scriptable_only: bool = False) -> list[ClientStory]:
    """Get all client stories ordered by times_used ascending (prefer unused stories)."""
    async with get_session() as session:
        stmt = select(ClientStory)
        if scriptable_only:
            stmt = stmt.where(ClientStory.is_scriptable == True)
        stmt = stmt.order_by(ClientStory.times_used.asc(), ClientStory.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_client_story(story_id: str) -> ClientStory | None:
    """Get one client story by ID."""
    async with get_session() as session:
        result = await session.execute(select(ClientStory).where(ClientStory.id == story_id))
        return result.scalar_one_or_none()


async def create_client_story(data: dict[str, Any]) -> ClientStory:
    """Create a new client story."""
    async with get_session() as session:
        story = ClientStory(
            title=data.get("title", ""),
            category=data.get("category", "win"),
            narrative=data.get("narrative", ""),
            lesson=data.get("lesson", ""),
            emotional_peak=data.get("emotional_peak", ""),
            is_scriptable=data.get("is_scriptable", True),
            tags=data.get("tags", []),
        )
        session.add(story)
        await session.commit()
        await session.refresh(story)
        return story


async def update_client_story(story_id: str, data: dict[str, Any]) -> ClientStory | None:
    """Update an existing client story."""
    async with get_session() as session:
        result = await session.execute(select(ClientStory).where(ClientStory.id == story_id))
        story = result.scalar_one_or_none()
        if story is None:
            return None
        for key, value in data.items():
            if hasattr(story, key) and key not in ("id", "created_at", "times_used"):
                setattr(story, key, value)
                if isinstance(value, (dict, list)):
                    flag_modified(story, key)
        await session.commit()
        await session.refresh(story)
        return story


async def delete_client_story(story_id: str) -> bool:
    """Delete a client story."""
    async with get_session() as session:
        result = await session.execute(select(ClientStory).where(ClientStory.id == story_id))
        story = result.scalar_one_or_none()
        if story is None:
            return False
        await session.delete(story)
        await session.commit()
        return True


async def increment_story_usage(story_ids: list[str]) -> None:
    """Bump times_used for stories that were injected into a generation."""
    if not story_ids:
        return
    async with get_session() as session:
        result = await session.execute(select(ClientStory).where(ClientStory.id.in_(story_ids)))
        for story in result.scalars():
            story.times_used = (story.times_used or 0) + 1
        await session.commit()


def client_story_to_dict(story: ClientStory) -> dict[str, Any]:
    return {
        "id": story.id,
        "title": story.title,
        "category": story.category,
        "narrative": story.narrative,
        "lesson": story.lesson,
        "emotional_peak": story.emotional_peak,
        "tags": story.tags or [],
    }


# ── Idea Batches + Content Ideas ──────────────────────────────────────

async def create_idea_batch(label: str, num_ideas: int = 30) -> IdeaBatch:
    """Create a new 30-day idea bank batch."""
    async with get_session() as session:
        batch = IdeaBatch(label=label, num_ideas=num_ideas, status="generating")
        session.add(batch)
        await session.commit()
        await session.refresh(batch)
        return batch


async def update_idea_batch_status(batch_id: str, status: str, error_message: str | None = None) -> None:
    async with get_session() as session:
        result = await session.execute(select(IdeaBatch).where(IdeaBatch.id == batch_id))
        batch = result.scalar_one_or_none()
        if batch:
            batch.status = status
            if error_message is not None:
                batch.error_message = error_message
            await session.commit()


async def list_idea_batches(limit: int = 20) -> list[IdeaBatch]:
    async with get_session() as session:
        result = await session.execute(
            select(IdeaBatch)
            .options(selectinload(IdeaBatch.ideas))
            .order_by(IdeaBatch.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_idea_batch(batch_id: str) -> IdeaBatch | None:
    async with get_session() as session:
        result = await session.execute(
            select(IdeaBatch)
            .options(selectinload(IdeaBatch.ideas).selectinload(ContentIdea.pillar))
            .options(selectinload(IdeaBatch.ideas).selectinload(ContentIdea.hook_variations))
            .where(IdeaBatch.id == batch_id)
        )
        return result.scalar_one_or_none()


async def get_latest_idea_batch() -> IdeaBatch | None:
    """Return the most recent idea batch, with ideas loaded."""
    async with get_session() as session:
        result = await session.execute(
            select(IdeaBatch)
            .options(selectinload(IdeaBatch.ideas).selectinload(ContentIdea.pillar))
            .options(selectinload(IdeaBatch.ideas).selectinload(ContentIdea.hook_variations))
            .order_by(IdeaBatch.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def save_content_ideas(batch_id: str, ideas_data: list[dict[str, Any]]) -> list[ContentIdea]:
    """Persist a list of generated ideas (with optional hook variations) to an idea batch."""
    async with get_session() as session:
        ideas: list[ContentIdea] = []
        for i, data in enumerate(ideas_data):
            idea = ContentIdea(
                batch_id=batch_id,
                pillar_id=data.get("pillar_id"),
                title=data.get("title", ""),
                core_story=data.get("core_story", ""),
                viral_angle=data.get("viral_angle", "education"),
                platform_fit=data.get("platform_fit", "reels"),
                target_location=data.get("target_location", ""),
                market_condition_ref=data.get("market_condition_ref", ""),
                is_personal_brand=bool(data.get("is_personal_brand", False)),
                client_story_id=data.get("client_story_id"),
                sort_order=i + 1,
            )
            session.add(idea)
            await session.flush()

            for h in data.get("hook_variations", []) or []:
                hv = HookVariation(
                    idea_id=idea.id,
                    hook_text=h.get("hook_text", ""),
                    hook_type=h.get("hook_type", "curiosity"),
                    scroll_stop_score=int(h.get("scroll_stop_score") or 0),
                    curiosity_score=int(h.get("curiosity_score") or 0),
                    specificity_score=int(h.get("specificity_score") or 0),
                    authenticity_score=int(h.get("authenticity_score") or 0),
                )
                session.add(hv)

            ideas.append(idea)
        await session.commit()
        return ideas


async def get_content_idea(idea_id: str) -> ContentIdea | None:
    async with get_session() as session:
        result = await session.execute(
            select(ContentIdea)
            .options(
                selectinload(ContentIdea.hook_variations),
                selectinload(ContentIdea.pillar),
            )
            .where(ContentIdea.id == idea_id)
        )
        return result.scalar_one_or_none()


def content_idea_to_dict(idea: ContentIdea) -> dict[str, Any]:
    return {
        "id": idea.id,
        "title": idea.title,
        "pillar_id": idea.pillar_id,
        "core_story": idea.core_story,
        "viral_angle": idea.viral_angle,
        "platform_fit": idea.platform_fit,
        "target_location": idea.target_location,
        "market_condition_ref": idea.market_condition_ref,
        "is_personal_brand": idea.is_personal_brand,
        "status": idea.status,
    }


async def update_idea_status(idea_id: str, status: str) -> None:
    async with get_session() as session:
        result = await session.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
        idea = result.scalar_one_or_none()
        if idea:
            idea.status = status
            await session.commit()


async def replace_hook_variations(idea_id: str, hooks: list[dict[str, Any]]) -> list[HookVariation]:
    """Delete existing hook variations for an idea and insert fresh ones."""
    async with get_session() as session:
        # Delete existing
        result = await session.execute(
            select(HookVariation).where(HookVariation.idea_id == idea_id)
        )
        for h in result.scalars():
            await session.delete(h)
        await session.flush()

        # Insert new
        new_hooks = []
        for h in hooks[:3]:
            hv = HookVariation(
                idea_id=idea_id,
                hook_text=h.get("hook_text", ""),
                hook_type=h.get("hook_type", "curiosity"),
                scroll_stop_score=int(h.get("scroll_stop_score") or 0),
                curiosity_score=int(h.get("curiosity_score") or 0),
                specificity_score=int(h.get("specificity_score") or 0),
                authenticity_score=int(h.get("authenticity_score") or 0),
            )
            session.add(hv)
            new_hooks.append(hv)
        await session.commit()
        for h in new_hooks:
            await session.refresh(h)
        return new_hooks


async def get_hook_variation(hook_id: str) -> HookVariation | None:
    async with get_session() as session:
        result = await session.execute(select(HookVariation).where(HookVariation.id == hook_id))
        return result.scalar_one_or_none()


async def get_best_hook_for_idea(idea_id: str) -> HookVariation | None:
    """Return the hook with the highest total score for an idea."""
    async with get_session() as session:
        result = await session.execute(
            select(HookVariation).where(HookVariation.idea_id == idea_id)
        )
        hooks = list(result.scalars().all())
        if not hooks:
            return None
        def total(h: HookVariation) -> int:
            return (h.scroll_stop_score or 0) + (h.curiosity_score or 0) + (h.specificity_score or 0) + (h.authenticity_score or 0)
        return max(hooks, key=total)


async def create_script_from_idea(
    idea_id: str,
    hook_id: str | None,
    script_data: dict[str, Any],
) -> VideoScript:
    """Persist a Stage 3 script tied back to an idea + chosen hook."""
    async with get_session() as session:
        script = VideoScript(
            batch_id=None,
            idea_id=idea_id,
            chosen_hook_id=hook_id,
            category=script_data.get("category") or "personal",
            pillar_id=script_data.get("pillar_id"),
            viral_angle=script_data.get("viral_angle", ""),
            title=script_data.get("title", ""),
            hook=script_data.get("hook", ""),
            body=script_data.get("body", ""),
            cta=script_data.get("cta", ""),
            personal_tie_in=script_data.get("personal_tie_in", ""),
            hashtags=script_data.get("hashtags", {}),
            visual_suggestions=script_data.get("visual_suggestions", ""),
            platform_notes=script_data.get("platform_notes", {}),
            platform_captions=script_data.get("platform_captions", {}),
            hook_style=script_data.get("hook_style", ""),
            estimated_duration=script_data.get("estimated_duration", 45),
            hormozi_density_score=script_data.get("hormozi_density_score", 0.0),
            word_count_original=script_data.get("word_count_original", 0),
            word_count_compressed=script_data.get("word_count_compressed", 0),
            pipeline_stage=script_data.get("pipeline_stage", "scripted"),
        )
        session.add(script)

        # Mark the chosen hook + update idea status
        if hook_id:
            hook_res = await session.execute(select(HookVariation).where(HookVariation.id == hook_id))
            hook = hook_res.scalar_one_or_none()
            if hook:
                # Unselect other hooks for this idea
                others_res = await session.execute(
                    select(HookVariation).where(HookVariation.idea_id == idea_id)
                )
                for h in others_res.scalars():
                    h.chosen = (h.id == hook_id)

        idea_res = await session.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
        idea = idea_res.scalar_one_or_none()
        if idea:
            idea.status = "scripted"

        await session.commit()
        await session.refresh(script)
        return script


async def list_scripts_for_idea(idea_id: str) -> list[VideoScript]:
    async with get_session() as session:
        result = await session.execute(
            select(VideoScript).where(VideoScript.idea_id == idea_id)
            .order_by(VideoScript.created_at.desc())
        )
        return list(result.scalars().all())


async def update_script_platform_captions(script_id: str, platform_captions: dict) -> VideoScript | None:
    async with get_session() as session:
        result = await session.execute(select(VideoScript).where(VideoScript.id == script_id))
        script = result.scalar_one_or_none()
        if script is None:
            return None
        script.platform_captions = platform_captions
        script.pipeline_stage = "captioned"
        flag_modified(script, "platform_captions")
        await session.commit()
        await session.refresh(script)
        return script


async def list_ideas_with_pipeline_status() -> dict[str, list]:
    """Return all ideas from the latest batch grouped by pipeline stage for the Kanban."""
    async with get_session() as session:
        result = await session.execute(
            select(IdeaBatch).order_by(IdeaBatch.created_at.desc()).limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest is None:
            return {"idea": [], "scripted": [], "captioned": [], "scheduled": [], "posted": []}

        ideas_res = await session.execute(
            select(ContentIdea)
            .options(selectinload(ContentIdea.pillar), selectinload(ContentIdea.hook_variations))
            .where(ContentIdea.batch_id == latest.id)
            .order_by(ContentIdea.sort_order)
        )
        ideas = list(ideas_res.scalars().all())

        # Collect script counts per idea
        idea_ids = [i.id for i in ideas]
        scripts_by_idea: dict[str, list[VideoScript]] = {i.id: [] for i in ideas}
        if idea_ids:
            scripts_res = await session.execute(
                select(VideoScript).where(VideoScript.idea_id.in_(idea_ids))
            )
            for s in scripts_res.scalars():
                scripts_by_idea.setdefault(s.idea_id, []).append(s)

        buckets = {"idea": [], "scripted": [], "captioned": [], "scheduled": [], "posted": []}
        for idea in ideas:
            scripts = scripts_by_idea.get(idea.id, [])
            status = idea.status or "idea"
            # Upgrade status based on latest script's pipeline_stage
            if scripts:
                latest_script = max(scripts, key=lambda s: s.created_at)
                status = latest_script.pipeline_stage or "scripted"
            bucket = buckets.setdefault(status, [])
            bucket.append({"idea": idea, "scripts": scripts})

        return buckets
