"""Stage 1 — 30-Day Idea Bank Generator.

Implements the viral content strategist persona (Serhant / Hormozi / Gary Vee)
and produces a full 30-day idea bank with 5 fields per idea:
  1. PILLAR — one of Ray's 6 brand pillars
  2. CORE STORY — the real human moment at the centre
  3. THREE HOOK VARIATIONS — curiosity gap / contrarian / number-based
  4. PLATFORM FIT — Reels / TikTok / YouTube Shorts / LinkedIn
  5. VIRAL ANGLE — identity / shock / education / aspiration

Hard rules enforced in the prompt:
- Every hook stops the scroll in the first 3 WORDS
- No generic real estate advice — hyper-GTA specific (Brampton, Vaughan, Mississauga, etc.)
- At least 30% of ideas are Ray's personal brand storytelling
- At least 2 ideas reference current GTA market conditions
- Hormozi density: every sentence must earn its place
"""

from __future__ import annotations

import json
import logging
from typing import Any

from dashboard.claude_client import get_claude_client
from dashboard.prompts import RAY_SIGNATURE_THEMES, _format_client_stories, _format_story_elements

logger = logging.getLogger(__name__)


VALID_PILLAR_IDS = {
    "authority_expertise",
    "behind_scenes",
    "client_wins",
    "market_intel",
    "mindset_lifestyle",
    "community_culture",
}

VALID_VIRAL_ANGLES = {"identity", "shock", "education", "aspiration"}
VALID_PLATFORMS = {"reels", "tiktok", "shorts", "linkedin"}

GTA_NEIGHBOURHOODS = [
    "Brampton", "Vaughan", "Mississauga", "Markham", "Oakville",
    "Richmond Hill", "Scarborough", "North York", "Etobicoke", "Ajax",
    "Pickering", "Whitby", "Milton", "Burlington", "Aurora", "Newmarket",
    "Caledon", "Georgetown", "Stouffville", "King City",
]


STAGE1_SYSTEM_PROMPT = """You are a viral content strategist who has studied Ryan Serhant, Alex \
Hormozi, Gary Vee, and every major personal brand that scaled from 0 to millions of followers \
on short-form video.

You are working with Ray, a licensed real estate broker in the Greater Toronto Area with 12+ \
years of experience in residential, investment, pre-construction, and commercial real estate. \
Ray's origin story is real: born in Afghanistan during the Taliban occupation, escaped through \
Pakistan, lived 9 years as an unwanted outsider in Moscow, arrived at Pearson Airport on \
October 13, 2009 with nothing. This is NOT a marketing hook — it is the emotional foundation \
of his brand.

Your job: generate a 30-day content idea bank for Ray's personal brand.

For each idea, output these 5 fields AS JSON:
{
  "title": "Short working title (max 8 words)",
  "pillar_id": "one of: authority_expertise, behind_scenes, client_wins, market_intel, mindset_lifestyle, community_culture",
  "core_story": "The real human moment or insight at the centre (2-4 sentences, vivid, specific, sensory)",
  "hook_variations": [
    {"hook_type": "curiosity",  "hook_text": "Curiosity-gap hook — must stop scroll in first 3 WORDS"},
    {"hook_type": "contrarian", "hook_text": "Contrarian hook — must stop scroll in first 3 WORDS"},
    {"hook_type": "number",     "hook_text": "Number-based hook — e.g. '3 mistakes buyers...'"}
  ],
  "platform_fit": "one of: reels, tiktok, shorts, linkedin",
  "viral_angle": "one of: identity, shock, education, aspiration",
  "target_location": "specific GTA area (Brampton, Vaughan, etc) or 'GTA-wide'",
  "market_condition_ref": "current GTA market tie-in (rates, pre-con defaults, rental, bidding wars) or empty string",
  "is_personal_brand": true | false,
  "client_story_ref": "exact title of a client story you used, or empty string"
}

═══════════════════════════════════════════════
THE NON-NEGOTIABLE RULES
═══════════════════════════════════════════════

1. EVERY hook stops the scroll in the first 3 WORDS. Not 3 sentences. 3 WORDS.
   Good: "Stop paying rent." / "They lied again." / "I was 15."
   Bad:  "Here's why most first-time buyers make a huge mistake..."

2. NO generic real estate advice. Every idea names a specific GTA area, a
   specific dollar amount, a specific month, or a specific client type.
   - Good: "Brampton townhouses dropped $140K in 6 months — here's why"
   - Bad:  "The market is shifting"

3. At least 30% of the 30 ideas (so 9+) must draw directly from Ray's personal
   story — Afghanistan, Pakistan, Russia, arriving in Canada, his father's
   sacrifices, the Russian racism, the refugee experience. These must feel
   inevitable, not shoehorned.

4. At least 2 of the 30 ideas must reference current GTA market conditions
   (interest rates, pre-construction defaults, rental market, bidding wars,
   land-transfer tax, first-time buyer programs, FHSA/RRSP, HCOL, etc.).

5. Hormozi density: every sentence must earn its place. Cut every word that
   does not do work.

6. Distribute ideas across all 6 brand pillars — minimum 3 ideas per pillar.

7. Distribute viral angles across all 4 types — use all of identity, shock,
   education, and aspiration.

8. Never use these phrases: "In today's market", "Let me tell you", "Did you
   know", "As a realtor", "I'm often asked", "The bottom line", "Without
   further ado", "Welcome back". They are scroll-triggers.

9. When using Ray's personal story, be SPECIFIC. Not "I came from a war zone."
   Instead: "I was 6 when the rocket hit the house across the street." Not
   "I was an immigrant in Russia." Instead: "I was 12, and a Russian kid
   pressed a knife to my throat because I didn't have Russian papers."

10. Client stories from Ray's database should be referenced in 3-5 ideas using
    the client_story_ref field — name the exact title.

Return ONLY the JSON array of ideas. No prose, no markdown fences, no preamble."""


def _build_stage1_user_prompt(
    creator_profile: dict,
    client_stories: list[dict] | None,
    num_ideas: int = 30,
) -> str:
    name = creator_profile.get("name", "Ray")
    bio = creator_profile.get("bio", "")
    location = creator_profile.get("location", "Greater Toronto Area, Ontario, Canada")
    story_elements = creator_profile.get("story_elements", {})
    story_section = _format_story_elements(story_elements) or "  (Profile missing — use default Afghanistan→Canada arc.)"
    client_stories_section = _format_client_stories(client_stories)

    return f"""GENERATE A {num_ideas}-DAY IDEA BANK FOR {name.upper()}.

WHO IS {name.upper()}?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {name}
Based in: {location}
Bio: {bio}

{RAY_SIGNATURE_THEMES}

{name.upper()}'S PERSONAL STORY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{story_section}

REAL CLIENT STORIES (reference these in 3-5 of the ideas — use the exact title):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{client_stories_section}

GTA NEIGHBOURHOODS TO REFERENCE (rotate across ideas):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{", ".join(GTA_NEIGHBOURHOODS)}

Generate exactly {num_ideas} ideas as a JSON array. Each idea has all 10 fields
specified in the system prompt. Remember: first 3 words stop the scroll, GTA
hyper-specific, 9+ ideas from Ray's personal story, 2+ market-condition
references, Hormozi density on every sentence.

Return ONLY the JSON array."""


class Stage1IdeaBankGenerator:
    """Generates 30-day content idea banks via Claude."""

    def __init__(self):
        self.claude = get_claude_client()

    def _parse_ideas_json(self, text: str) -> list[dict[str, Any]]:
        text = text.strip()
        if text.startswith("```"):
            lines = [ln for ln in text.split("\n") if not ln.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "ideas" in result:
                return result["ideas"]
        except json.JSONDecodeError:
            pass
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        logger.error(f"Failed to parse Stage 1 JSON. First 300 chars: {text[:300]}")
        raise ValueError("Failed to parse Stage 1 idea bank response as JSON")

    def _normalize_idea(self, idea: dict[str, Any], client_stories: list[dict] | None) -> dict[str, Any]:
        """Ensure every field is valid and resolve client_story_ref to an ID."""
        pillar_id = idea.get("pillar_id", "").strip().lower().replace(" ", "_").replace("&", "").replace("__", "_")
        if pillar_id not in VALID_PILLAR_IDS:
            pillar_id = "authority_expertise"

        viral_angle = idea.get("viral_angle", "education").strip().lower()
        if viral_angle not in VALID_VIRAL_ANGLES:
            viral_angle = "education"

        platform_fit = idea.get("platform_fit", "reels").strip().lower()
        if platform_fit not in VALID_PLATFORMS:
            platform_fit = "reels"

        # Resolve client story reference (title → id) if present
        client_story_id = None
        ref = (idea.get("client_story_ref") or "").strip().lower()
        if ref and client_stories:
            for story in client_stories:
                if ref and ref in (story.get("title") or "").lower():
                    client_story_id = story.get("id")
                    break

        # Normalize hook variations
        raw_hooks = idea.get("hook_variations") or []
        normalized_hooks = []
        for h in raw_hooks[:3]:
            hook_type = (h.get("hook_type") or "curiosity").strip().lower()
            if hook_type not in {"curiosity", "contrarian", "number"}:
                hook_type = "curiosity"
            normalized_hooks.append({
                "hook_type": hook_type,
                "hook_text": (h.get("hook_text") or "").strip(),
                "scroll_stop_score": int(h.get("scroll_stop_score") or 0),
                "curiosity_score": int(h.get("curiosity_score") or 0),
                "specificity_score": int(h.get("specificity_score") or 0),
                "authenticity_score": int(h.get("authenticity_score") or 0),
            })

        return {
            "title": (idea.get("title") or "").strip()[:200],
            "pillar_id": pillar_id,
            "core_story": (idea.get("core_story") or "").strip(),
            "viral_angle": viral_angle,
            "platform_fit": platform_fit,
            "target_location": (idea.get("target_location") or "").strip()[:100],
            "market_condition_ref": (idea.get("market_condition_ref") or "").strip(),
            "is_personal_brand": bool(idea.get("is_personal_brand", False)),
            "client_story_id": client_story_id,
            "hook_variations": normalized_hooks,
        }

    async def generate(
        self,
        creator_profile: dict,
        client_stories: list[dict] | None = None,
        num_ideas: int = 30,
    ) -> list[dict[str, Any]]:
        """Generate a 30-day idea bank. Returns normalized idea dicts ready for DB insert."""
        user_prompt = _build_stage1_user_prompt(creator_profile, client_stories, num_ideas)
        logger.info(f"Generating Stage 1 idea bank with {num_ideas} ideas")

        response = self.claude.messages_create(
            max_tokens=16000,
            system=STAGE1_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text
        raw_ideas = self._parse_ideas_json(raw_text)
        normalized = [self._normalize_idea(idea, client_stories) for idea in raw_ideas]
        logger.info(f"Stage 1 generated {len(normalized)} ideas")
        return normalized


# Singleton
_generator: Stage1IdeaBankGenerator | None = None


def get_stage1_generator() -> Stage1IdeaBankGenerator:
    global _generator
    if _generator is None:
        _generator = Stage1IdeaBankGenerator()
    return _generator
