"""Stage 3: Write full script from idea + chosen hook, with Hormozi density pass."""

import logging
from sqlalchemy.orm import Session

from ..models import ContentIdea, HookVariation, VideoScript
from ..script_engine import write_script
from ..operations import (
    get_profile, get_stories, create_script, update_idea_status,
    choose_hook
)

logger = logging.getLogger(__name__)


def run_stage3(
    db: Session,
    idea: ContentIdea,
    hook: HookVariation,
    batch_id: int = None,
) -> VideoScript:
    """
    Write a full script for the given idea and chosen hook.
    Saves and returns a VideoScript object.
    """
    profile = get_profile(db)
    client_stories = get_stories(db, scriptable_only=True)

    logger.info(f"Stage 3: Writing script for idea {idea.id}, hook {hook.id}...")

    # Mark the hook as chosen
    choose_hook(db, hook.id)

    script_data = write_script(
        idea=idea,
        chosen_hook=hook,
        profile=profile,
        client_stories=client_stories,
    )

    script_data["batch_id"] = batch_id

    script = create_script(db, script_data)

    # Update idea status
    update_idea_status(db, idea.id, "scripted")

    logger.info(f"Stage 3 complete: script {script.id} created")
    return script
