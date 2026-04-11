"""Stage 2: Forge 3 hooks with scores for a content idea."""

import logging
from typing import List
from sqlalchemy.orm import Session

from ..models import ContentIdea, HookVariation
from ..script_engine import forge_hooks
from ..operations import create_hook, get_hooks_for_idea, update_idea_status

logger = logging.getLogger(__name__)


def run_stage2(db: Session, idea: ContentIdea) -> List[HookVariation]:
    """
    Generate 3 hook variations for an idea, score them, save to DB.
    Returns list of HookVariation objects.
    """
    # Remove existing hooks for this idea if regenerating
    existing = get_hooks_for_idea(db, idea.id)
    for h in existing:
        db.delete(h)
    db.commit()

    logger.info(f"Stage 2: Forging hooks for idea {idea.id}...")
    hook_dicts = forge_hooks(idea)

    hooks = []
    for hook_data in hook_dicts:
        hook = create_hook(
            db=db,
            idea_id=idea.id,
            hook_text=hook_data["hook_text"],
            hook_type=hook_data["hook_type"],
            scroll_stop_score=hook_data["scroll_stop_score"],
            curiosity_score=hook_data["curiosity_score"],
            specificity_score=hook_data["specificity_score"],
            authenticity_score=hook_data["authenticity_score"],
        )
        hooks.append(hook)

    logger.info(f"Stage 2 complete: {len(hooks)} hooks saved for idea {idea.id}")
    return hooks
