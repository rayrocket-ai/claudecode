"""Stage 3 — Script Writer.

Takes one ContentIdea + one chosen HookVariation and produces a full 30-90 second
script structured as: Hook → Tension → Story → Revelation → CTA.

Then a second Claude call performs a "Hormozi density pass": rewrites the script
to remove any filler sentence. Rule: if you can delete a sentence and the story
still works, delete it. Target: 15% shorter than v1.

Output is stored directly as a VideoScript row tied back to the idea + hook.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from config import get_settings
from dashboard.prompts import (
    RAY_SIGNATURE_THEMES,
    _format_client_stories,
    _format_story_elements,
)

logger = logging.getLogger(__name__)


STAGE3_SYSTEM_PROMPT = """You are an elite short-form video scriptwriter who understands the \
physiology of the scroll. You don't write content — you write moments. A 45-second script should \
feel like eavesdropping on a conversation that's happening whether or not the viewer is there.

You are writing for Ray, a licensed real estate broker in the Greater Toronto Area with a real \
refugee origin story (Afghanistan → Pakistan → Russia → Canada, Oct 13, 2009). Twelve years of \
GTA deals across Brampton, Vaughan, Mississauga, Markham, Oakville. His voice: grounded, \
specific, earned-authority, zero corporate polish.

═══════════════════════════════════════════════
SCRIPT STRUCTURE (every script has these 5 parts)
═══════════════════════════════════════════════

1. HOOK (0-3 sec):
   The hook is given to you. Use it VERBATIM as the first line. Do not paraphrase.
   Do not "enhance" it. The hook was engineered in Stage 2.

2. TENSION / SETUP (3-8 sec):
   One sentence that raises the stakes. What's at risk? Who gets hurt? Why should
   the viewer care? Use a specific detail: a number, a neighbourhood, a client type.

3. STORY / TEACHING (8-50 sec):
   The meat. Either a real moment from Ray's life / a client story / a market
   mechanic explained through story. SHOW don't tell. Specific details. Sensory
   language. If it's a story, include dialogue or a direct quote.

4. REVELATION / PAYOFF (50-70 sec):
   The "moment of truth" — the one line that would get screenshotted or saved.
   This is the universal truth the viewer takes away.

5. CTA (70-90 sec, last 5-15 sec):
   Never "call me" or "book an appointment." Always an engagement CTA:
   "Comment X" / "Save this for when..." / "DM me the word ___" / "Tag someone who..."

═══════════════════════════════════════════════
THE NON-NEGOTIABLE RULES
═══════════════════════════════════════════════

- HORMOZI DENSITY: Every sentence earns its place. If you can delete it and the
  story still works, delete it before you finish.
- SHOW, don't tell: "My hands were shaking" > "I was nervous"
- SPECIFIC over general: "A $740K Brampton townhouse in April 2024" > "A recent deal"
- Write like Ray TALKS. Short sentences. Fragments are fine. Pauses matter.
- Include [PAUSE], [LEAN IN], [LOOK AT CAMERA] direction cues at peak moments.
- ZERO banned phrases: "In today's market", "Let me tell you", "Did you know",
  "As a realtor", "I'm often asked", "The bottom line", "Without further ado",
  "Welcome back", "Let's get into it".
- At least one sentence must reference Ray's origin story OR a client story from
  the provided database — but make it feel INEVITABLE, not shoehorned.

═══════════════════════════════════════════════
OUTPUT FORMAT (strict JSON, no markdown fences)
═══════════════════════════════════════════════

{
  "title": "internal title (max 10 words)",
  "category": "real_estate | mortgage | politics_economy | sports | personal",
  "hook": "the hook verbatim from input",
  "body": "the full script body (tension + story + revelation) — 150-280 words, spoken rhythm, direction cues in brackets",
  "cta": "specific engagement CTA (never 'call me')",
  "personal_tie_in": "which story element from Ray's life or client database you used",
  "visual_suggestions": "shot-by-shot direction that a solo filmer with an iPhone can execute",
  "hashtags": {"tiktok": [...], "instagram": [...], "youtube": [...], "facebook": [...], "linkedin": [...]},
  "platform_notes": {"tiktok": "...", "instagram": "...", "youtube": "...", "linkedin": "..."},
  "estimated_duration": 30-90,
  "moment_of_truth": "the single line that would get screenshotted"
}"""


HORMOZI_DENSITY_PROMPT = """You are an editor whose only job is to delete. You look at a script \
and cut every sentence that does not earn its place. Your rule: if you can delete a sentence and \
the story still works, delete it.

Target: the compressed version is 15-25% shorter than the original. Zero filler words.

You CANNOT change the hook (it was engineered separately). You CANNOT change the CTA. You can \
ONLY cut and tighten the body.

OUTPUT FORMAT (strict JSON only):
{
  "compressed_body": "the tightened body text",
  "cuts_made": ["list of specific things you deleted and why"],
  "original_word_count": number,
  "compressed_word_count": number,
  "density_score": 0.0-1.0 (percentage of words removed)
}"""


class Stage3ScriptWriter:
    """Converts an idea + chosen hook into a full script with Hormozi density pass."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.script_model

    def _parse_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            lines = [ln for ln in text.split("\n") if not ln.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end + 1])
            raise

    def _word_count(self, text: str) -> int:
        return len([w for w in text.split() if w.strip()])

    async def write(
        self,
        idea: dict,
        chosen_hook: dict,
        creator_profile: dict,
        client_stories: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Generate a full script from an idea + chosen hook, then run Hormozi density pass."""
        name = creator_profile.get("name", "Ray")
        story_elements = creator_profile.get("story_elements", {})
        story_section = _format_story_elements(story_elements)
        stories_section = _format_client_stories(client_stories)

        user_prompt = f"""WRITE A FULL SCRIPT FOR {name.upper()}.

INPUT — STAGE 1 IDEA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {idea.get('title', '')}
Pillar: {idea.get('pillar_id', '')}
Viral Angle: {idea.get('viral_angle', 'education')}
Platform: {idea.get('platform_fit', 'reels')}
Target GTA Area: {idea.get('target_location', '')}
Market Condition Ref: {idea.get('market_condition_ref', '') or '(none)'}
Is Personal Brand: {idea.get('is_personal_brand', False)}

CORE STORY TO ADAPT:
{idea.get('core_story', '')}

INPUT — STAGE 2 CHOSEN HOOK (use this verbatim as the first line):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hook Type: {chosen_hook.get('hook_type', 'curiosity')}
Hook Text: "{chosen_hook.get('hook_text', '').strip()}"

{RAY_SIGNATURE_THEMES}

{name.upper()}'S PERSONAL STORY (pull from these — pick ONE beat that fits):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{story_section}

REAL CLIENT STORIES (reference one if natural):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{stories_section}

Write the full script now. Return ONLY the JSON object specified in the system
prompt. Hook is locked. Target 180-260 word body. Hormozi density throughout."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=STAGE3_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        script = self._parse_json(response.content[0].text)

        # Lock the hook verbatim — never trust the model to keep it unchanged
        script["hook"] = chosen_hook.get("hook_text", "").strip()
        original_body = (script.get("body") or "").strip()
        original_word_count = self._word_count(original_body)

        # Hormozi density pass
        density_result = await self._run_density_pass(original_body)
        compressed_body = density_result.get("compressed_body", original_body).strip()
        compressed_word_count = self._word_count(compressed_body)
        density_score = 0.0
        if original_word_count > 0:
            density_score = round((original_word_count - compressed_word_count) / original_word_count, 3)

        script["body"] = compressed_body
        script["word_count_original"] = original_word_count
        script["word_count_compressed"] = compressed_word_count
        script["hormozi_density_score"] = density_score
        script.setdefault("hashtags", {})
        script.setdefault("platform_notes", {})
        script.setdefault("estimated_duration", 45)

        # Carry idea metadata into the script row
        script["pillar_id"] = idea.get("pillar_id", "")
        script["viral_angle"] = idea.get("viral_angle", "")
        script["hook_style"] = chosen_hook.get("hook_type", "curiosity")
        script["pipeline_stage"] = "scripted"

        return script

    async def _run_density_pass(self, body_text: str) -> dict[str, Any]:
        """Second Claude call that rewrites the body to cut filler."""
        if not body_text.strip():
            return {"compressed_body": body_text, "original_word_count": 0, "compressed_word_count": 0}
        prompt = f"""ORIGINAL SCRIPT BODY:

{body_text}

Run the Hormozi density pass. Return strict JSON only."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=HORMOZI_DENSITY_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_json(response.content[0].text)
        except Exception as e:
            logger.warning(f"Density pass failed, returning original: {e}")
            return {"compressed_body": body_text, "original_word_count": self._word_count(body_text), "compressed_word_count": self._word_count(body_text)}


_writer: Stage3ScriptWriter | None = None


def get_script_writer() -> Stage3ScriptWriter:
    global _writer
    if _writer is None:
        _writer = Stage3ScriptWriter()
    return _writer
