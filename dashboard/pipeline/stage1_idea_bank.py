"""Stage 1: Generate 30-day content idea bank."""

import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from ..models import CreatorProfile, ClientStory, ContentIdea
from ..script_engine import generate_idea_bank
from ..scraper import get_trending_items
from ..operations import (
    create_idea, get_profile, get_stories, clear_old_ideas, get_ideas
)

logger = logging.getLogger(__name__)


def run_stage1(db: Session, days: int = 30) -> List[ContentIdea]:
    """
    Full pipeline: fetch trending → generate 30 ideas → save to DB.
    Returns the list of created ContentIdea objects.
    """
    profile = get_profile(db)
    client_stories = get_stories(db, scriptable_only=True)

    logger.info("Stage 1: Fetching trending items...")
    trending = get_trending_items(10)

    logger.info(f"Stage 1: Generating {days}-day idea bank with Claude...")
    idea_dicts = generate_idea_bank(
        profile=profile,
        trending_items=trending,
        client_stories=client_stories,
        days=days,
    )

    # Clear old ideas to avoid accumulation beyond ~35 days
    clear_old_ideas(db, keep_days=35)

    ideas = []
    for idea_data in idea_dicts:
        idea = create_idea(
            db=db,
            pillar_id=idea_data["pillar_id"],
            core_story=idea_data["core_story"],
            viral_angle=idea_data.get("viral_angle", ""),
            platform_fit=idea_data.get("platform_fit", "reels,tiktok"),
            hook_seeds=idea_data.get("hook_seeds", []),
            script_type=idea_data.get("script_type", "wildcard"),
        )
        ideas.append(idea)

    logger.info(f"Stage 1 complete: {len(ideas)} ideas saved")
    return ideas
