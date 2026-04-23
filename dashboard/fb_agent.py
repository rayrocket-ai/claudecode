"""Facebook comment agent: classify each comment and draft a reply + DM.

The agent only engages with comments that are real estate inquiries (buying/
selling/renting in the GTA, mortgage questions, questions about a specific
property or listing, asking Ray for help). Everything else — compliments,
small talk, spam, trolling — is skipped.
"""

import logging
from typing import Optional

from .script_engine import _call_claude, _parse_json
from .models import CreatorProfile, json_load

logger = logging.getLogger(__name__)


RAY_VOICE = """You are drafting a public Facebook reply AND a private DM on behalf of Ray Ahmadi, a licensed GTA real estate broker and mortgage professional.

VOICE RULES (strict):
- Warm, direct, confident. Plain English. No salesy fluff.
- Never sign off with a name, signature, emoji chain, or "- Ray". Just reply.
- Never refer to yourself in the third person. You are writing as Ray would speak.
- Never invent listing details, prices, addresses, or numbers. If the comment references specifics you don't have, ask a clarifying question or give general guidance.
- Stay Canada/GTA-focused. Mention Brampton, Vaughan, Mississauga, Markham, Oakville, Richmond Hill, Scarborough, North York, Toronto when relevant.
- Keep the public reply short (1–2 sentences, max ~25 words). It's a comment thread — brevity wins.
- The DM is longer (3–5 sentences, max ~80 words): acknowledge what they asked, give a genuinely useful first take, and invite them to share details (budget, timeline, area) so Ray can help properly.
- Do NOT mention this is automated. Do NOT ask for their phone number or email in the public reply.
- No hashtags. No links. No emojis in the DM. One friendly emoji max in the public reply, only if natural."""


CLASSIFY_AND_DRAFT_PROMPT = """Classify this Facebook comment and, if relevant, draft a public reply and a private DM.

POST CONTEXT: {post_context}
COMMENT AUTHOR: {author}
COMMENT: {message}

Classify into exactly one of:
- "real_estate_inquiry": asking about a house/condo/listing, the market, mortgages, rates, buying, selling, renting, investing, pre-construction, or asking Ray for help
- "compliment": praise, thanks, or positive reaction with no question
- "spam": links, promo for other services, obvious bots, scams
- "other": off-topic chatter, hate, trolling, anything else

Also write a short "intent" — 3–8 words describing what they actually want (e.g. "asking price of Brampton semi", "wants mortgage pre-approval", "looking for investment condo in Vaughan").

ONLY if category is "real_estate_inquiry", draft:
- draft_reply: short public comment reply (1–2 sentences, max ~25 words)
- draft_dm: private DM (3–5 sentences, max ~80 words) that acknowledges what they asked, gives a genuine first take, and invites them to share budget/timeline/area

If category is anything else, set draft_reply and draft_dm to empty strings.

Return ONLY a JSON object:
{{
  "category": "...",
  "intent": "...",
  "should_engage": true/false,
  "draft_reply": "...",
  "draft_dm": "..."
}}"""


def _profile_blurb(profile: Optional[CreatorProfile]) -> str:
    if not profile:
        return "Ray Ahmadi, GTA real estate broker and mortgage professional."
    markets = ", ".join(json_load(profile.gta_markets)) or "GTA"
    return f"{profile.name} — GTA real estate broker and mortgage professional. Active markets: {markets}."


def classify_and_draft(
    message: str,
    author: str = "Facebook user",
    post_context: str = "",
    profile: Optional[CreatorProfile] = None,
) -> dict:
    """Run Claude to classify the comment and (if relevant) draft a reply + DM.

    Returns a dict with keys: category, intent, should_engage, draft_reply, draft_dm.
    """
    system = RAY_VOICE + "\n\n" + _profile_blurb(profile)
    prompt = CLASSIFY_AND_DRAFT_PROMPT.format(
        post_context=post_context or "(no post context available)",
        author=author or "Facebook user",
        message=message.strip(),
    )

    try:
        raw = _call_claude(prompt, system=system, fast=True)
        parsed = _parse_json(raw)
    except Exception as e:
        logger.error(f"FB classify_and_draft failed: {e}")
        return {
            "category": "other",
            "intent": "",
            "should_engage": False,
            "draft_reply": "",
            "draft_dm": "",
        }

    category = (parsed.get("category") or "other").lower().strip()
    should_engage = category == "real_estate_inquiry" and bool(parsed.get("should_engage", True))

    return {
        "category": category,
        "intent": (parsed.get("intent") or "").strip(),
        "should_engage": should_engage,
        "draft_reply": (parsed.get("draft_reply") or "").strip() if should_engage else "",
        "draft_dm": (parsed.get("draft_dm") or "").strip() if should_engage else "",
    }
