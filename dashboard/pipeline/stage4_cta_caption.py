"""Stage 4 — CTA + Caption Builder.

Takes a finished script and produces platform-specific captions + hashtags:
  - reels:    1-3 sentences, line breaks, emojis, 5-10 hashtags
  - tiktok:   short, punchy, 3-5 hashtags, no emojis
  - shorts:   SEO-optimized first line + longer description
  - linkedin: 800-1200 characters, professional tone, no hashtag stuffing

The CTA is matched to the idea's viral_angle:
  - identity    → "If this is you, comment X"
  - shock       → "Did this shock you too? DM me 'facts'"
  - education   → "Save this post so you don't forget"
  - aspiration  → "Ready to make this move? Book a call: [link]"
"""

from __future__ import annotations

import json
import logging
from typing import Any

from dashboard.claude_client import get_claude_client

logger = logging.getLogger(__name__)


STAGE4_SYSTEM_PROMPT = """You are a platform-native caption specialist. You understand that a \
caption on Instagram reads differently than a caption on TikTok, which reads differently than \
a YouTube Shorts description, which reads nothing like a LinkedIn post. One script, four captions.

You are working for Ray — a licensed GTA real estate broker with a refugee origin story \
(Afghanistan → Canada 2009). His voice: grounded, specific, earned-authority, zero corporate polish.

OUTPUT RULES PER PLATFORM:

INSTAGRAM REELS CAPTION:
- 1-3 sentences
- Line breaks between thoughts
- 1-2 relevant emojis (never more)
- 5-10 hashtags, mix of broad (#realestate #toronto) and niche (#bramptonhomes #gtamortgage)
- First line MUST hook — the feed only shows 2 lines before "more"

TIKTOK CAPTION:
- Short and punchy (1-2 sentences max)
- Zero emojis (TikTok culture)
- 3-5 hashtags, trending-aware
- No line breaks needed
- Often works as comment-bait ("fight me in the comments")

YOUTUBE SHORTS DESCRIPTION:
- SEO-optimized first line (imagine someone searching Google)
- 2-3 sentence summary of the video's value
- 3-5 hashtags at the bottom
- Can include a single link if relevant

LINKEDIN POST:
- 800-1200 characters
- Professional tone but still personal
- Line breaks every 1-2 sentences (readability)
- Start with a hook that establishes credibility
- NEVER stuff hashtags — maximum 3 at the end
- No emojis in body, optional 1 at end

CTA MATCHING (use the viral_angle to pick):
- identity:    "If this is you, comment X" / "Tag someone who..."
- shock:       "Did this shock you? DM me 'facts' for the full breakdown"
- education:   "Save this for when you're house hunting" / "Comment SAVE and I'll send the PDF"
- aspiration:  "Ready to make this move? DM me 'ready' and I'll walk you through step by step"

OUTPUT FORMAT (strict JSON only, no markdown fences):
{
  "reels_caption": "...",
  "reels_hashtags": ["#...", ...],
  "tiktok_caption": "...",
  "tiktok_hashtags": ["#...", ...],
  "shorts_caption": "...",
  "shorts_hashtags": ["#...", ...],
  "linkedin_caption": "...",
  "linkedin_hashtags": ["#...", ...]
}"""


class Stage4CTACaptionBuilder:
    """Generates platform-specific captions for a finished script."""

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

    async def build(
        self,
        script: dict,
        viral_angle: str = "education",
        target_location: str = "GTA",
    ) -> dict[str, Any]:
        """Build 4 platform-specific captions from a script dict."""
        hook = (script.get("hook") or "").strip()
        body = (script.get("body") or "").strip()
        cta = (script.get("cta") or "").strip()
        title = (script.get("title") or "").strip()

        user_prompt = f"""BUILD PLATFORM CAPTIONS FOR THIS SCRIPT.

TITLE: {title}
VIRAL ANGLE: {viral_angle}
TARGET LOCATION: {target_location}

HOOK (first 3 seconds):
{hook}

SCRIPT BODY:
{body}

ORIGINAL CTA (keep the intent, adapt the phrasing per platform):
{cta}

Return strict JSON with all 4 platform captions and their hashtag arrays. Match the
CTA to the viral angle ({viral_angle}). Reference {target_location} where relevant."""

        response = self.claude.messages_create(
            max_tokens=3000,
            system=STAGE4_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        parsed = self._parse_json(response.content[0].text)

        # Normalize into a single platform_captions dict for DB storage
        platform_captions = {
            "reels": {
                "caption": (parsed.get("reels_caption") or "").strip(),
                "hashtags": parsed.get("reels_hashtags") or [],
            },
            "tiktok": {
                "caption": (parsed.get("tiktok_caption") or "").strip(),
                "hashtags": parsed.get("tiktok_hashtags") or [],
            },
            "shorts": {
                "caption": (parsed.get("shorts_caption") or "").strip(),
                "hashtags": parsed.get("shorts_hashtags") or [],
            },
            "linkedin": {
                "caption": (parsed.get("linkedin_caption") or "").strip(),
                "hashtags": parsed.get("linkedin_hashtags") or [],
            },
        }
        return platform_captions


_builder: Stage4CTACaptionBuilder | None = None


def get_cta_caption_builder() -> Stage4CTACaptionBuilder:
    global _builder
    if _builder is None:
        _builder = Stage4CTACaptionBuilder()
    return _builder
