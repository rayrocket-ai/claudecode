"""Stage 2 — Hook Forge.

Takes an idea from Stage 1 and either:
  (a) scores its existing hook variations on 4 metrics, or
  (b) regenerates 3 fresh hook variations with tighter, more specific phrasing

Each hook is scored 1-10 on:
  - scroll_stop_score: does the first 3 words pattern-interrupt?
  - curiosity_score: does it open an information gap?
  - specificity_score: is it GTA-hyper-specific?
  - authenticity_score: does it sound like Ray, not AI?
"""

from __future__ import annotations

import json
import logging
from typing import Any

from dashboard.claude_client import get_claude_client
from dashboard.prompts import RAY_SIGNATURE_THEMES

logger = logging.getLogger(__name__)


STAGE2_SYSTEM_PROMPT = """You are a hook specialist who has reverse-engineered the first 3 seconds \
of every video that ever hit 10M views on short-form platforms. You understand that a hook is not \
a sentence — it is a physiological response. The first 3 WORDS either stop the thumb or lose the \
viewer forever.

You are working for Ray, a licensed real estate broker in the Greater Toronto Area with a real \
refugee origin story (Afghanistan → Pakistan → Russia → Canada, Oct 13, 2009).

Your job: for a given content idea, produce exactly 3 hook variations AND score each one \
ruthlessly. Always return strict JSON — no prose.

SCORING (every score 1-10, be brutal, default is 5):
  1. scroll_stop_score — Does the FIRST 3 WORDS pattern-interrupt?
      10 = "I was 15." / "They took everything." / "Stop paying rent."
       5 = Normal declarative opening
       1 = "Hey guys, welcome back" / "Today I want to talk about"
  2. curiosity_score — Does it open an information gap the viewer MUST close?
      10 = "Nobody told her this."
       5 = Vaguely interesting claim
       1 = Closed statement with no follow-up
  3. specificity_score — Is it GTA-hyper-specific?
      10 = Names a neighbourhood, dollar amount, month, client type
       5 = Generic real estate angle with some detail
       1 = Could be said by any realtor anywhere
  4. authenticity_score — Does it sound like a real person, not AI?
      10 = Raw, human, phrased like spoken English
       5 = Slightly polished but believable
       1 = Corporate, jargon-heavy, obviously AI-generated

HOOK TYPES (must produce one of each):
  - curiosity: opens an information gap
  - contrarian: challenges a common belief
  - number: leads with a specific stat or count

RULES:
- NEVER use these phrases: "In today's market", "Let me tell you", "Did you know",
  "As a realtor", "I'm often asked", "The bottom line", "Without further ado",
  "Welcome back". They trigger scrolls.
- The first 3 WORDS are sacred. If the first 3 words don't punch, score 4 or below.
- Reference specific GTA neighbourhoods when possible: Brampton, Vaughan, Mississauga,
  Markham, Oakville, Richmond Hill, Scarborough, North York.

OUTPUT FORMAT (strict JSON, no markdown fences, no prose):
{
  "hooks": [
    {
      "hook_type": "curiosity",
      "hook_text": "...",
      "scroll_stop_score": 1-10,
      "curiosity_score": 1-10,
      "specificity_score": 1-10,
      "authenticity_score": 1-10,
      "why_it_works": "one-sentence explanation"
    },
    { "hook_type": "contrarian", ... },
    { "hook_type": "number", ... }
  ]
}"""


class Stage2HookForge:
    """Regenerates + scores hook variations for a content idea."""

    def __init__(self):
        self.claude = get_claude_client()

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

    async def forge(
        self,
        idea: dict,
        creator_profile: dict,
    ) -> list[dict[str, Any]]:
        """Generate 3 fresh, scored hook variations for one idea."""
        name = creator_profile.get("name", "Ray")
        pillar = idea.get("pillar_id", "")
        viral_angle = idea.get("viral_angle", "education")
        platform = idea.get("platform_fit", "reels")
        target_location = idea.get("target_location", "GTA")
        core_story = idea.get("core_story", "")
        title = idea.get("title", "")

        user_prompt = f"""CONTENT IDEA TO FORGE HOOKS FOR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: {title}
Pillar: {pillar}
Viral Angle: {viral_angle}
Platform Fit: {platform}
Target GTA Area: {target_location}

CORE STORY:
{core_story}

{RAY_SIGNATURE_THEMES}

Produce 3 hook variations (curiosity / contrarian / number). Score each ruthlessly.
Return strict JSON in the format specified in the system prompt."""

        response = self.claude.messages_create(
            max_tokens=2000,
            system=STAGE2_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text
        parsed = self._parse_json(raw_text)
        hooks = parsed.get("hooks", [])

        normalized = []
        for h in hooks[:3]:
            hook_type = (h.get("hook_type") or "curiosity").strip().lower()
            if hook_type not in {"curiosity", "contrarian", "number"}:
                hook_type = "curiosity"
            normalized.append({
                "hook_type": hook_type,
                "hook_text": (h.get("hook_text") or "").strip(),
                "scroll_stop_score": max(1, min(10, int(h.get("scroll_stop_score") or 5))),
                "curiosity_score": max(1, min(10, int(h.get("curiosity_score") or 5))),
                "specificity_score": max(1, min(10, int(h.get("specificity_score") or 5))),
                "authenticity_score": max(1, min(10, int(h.get("authenticity_score") or 5))),
                "why_it_works": (h.get("why_it_works") or "").strip(),
            })
        return normalized


_forge: Stage2HookForge | None = None


def get_hook_forge() -> Stage2HookForge:
    global _forge
    if _forge is None:
        _forge = Stage2HookForge()
    return _forge
