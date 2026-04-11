"""Claude AI script generation engine."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

import anthropic

from config import get_settings
from dashboard.prompts import (
    SCRIPT_SYSTEM_PROMPT,
    build_generation_prompt,
    build_regenerate_prompt,
)
from dashboard import operations as ops

logger = logging.getLogger(__name__)


class ScriptEngine:
    """Generates video scripts using Claude AI and trending data."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.script_model

    def _parse_scripts_json(self, text: str) -> list[dict[str, Any]]:
        """Parse the JSON array of scripts from Claude's response."""
        # Try direct parse first
        text = text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "scripts" in result:
                return result["scripts"]
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in the text
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        logger.error(f"Failed to parse scripts JSON. Response starts with: {text[:200]}")
        raise ValueError("Failed to parse script generation response as JSON")

    async def generate_daily_scripts(
        self,
        target_date: date,
        trending_data: dict[str, list[dict]],
        creator_profile: dict,
        num_scripts: int = 7,
        client_stories: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate a full daily batch of scripts."""

        prompt = build_generation_prompt(
            creator_profile,
            trending_data,
            num_scripts,
            client_stories=client_stories,
        )

        logger.info(f"Generating {num_scripts} scripts for {target_date}")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=SCRIPT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        scripts = self._parse_scripts_json(raw_text)

        # Validate and normalize
        valid_categories = {"real_estate", "mortgage", "politics_economy", "sports", "personal"}
        for script in scripts:
            if script.get("category") not in valid_categories:
                script["category"] = "personal"
            script.setdefault("estimated_duration", 45)
            script.setdefault("hashtags", {})
            script.setdefault("platform_notes", {})

        logger.info(f"Successfully generated {len(scripts)} scripts")
        return scripts

    async def regenerate_single_script(
        self,
        category: str,
        trending_data: dict[str, list[dict]],
        creator_profile: dict,
        existing_script: dict | None = None,
    ) -> dict[str, Any]:
        """Regenerate a single script for a specific category."""

        prompt = build_regenerate_prompt(creator_profile, trending_data, category, existing_script)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SCRIPT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        scripts = self._parse_scripts_json(raw_text)

        if not scripts:
            raise ValueError("No script generated")

        return scripts[0]


# Singleton
_engine: ScriptEngine | None = None


def get_engine() -> ScriptEngine:
    global _engine
    if _engine is None:
        _engine = ScriptEngine()
    return _engine
