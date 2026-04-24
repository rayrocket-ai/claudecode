"""Facebook comment agent: classify each comment and draft a reply + DM.

Categories:
  - price_inquiry      — asking price/cost of a home (most common on video posts)
  - real_estate_inquiry — asking about a property, the market, mortgages, how to help
  - compliment          — praise/thanks/positive
  - spam                — promo, links, scams, bots
  - other               — off-topic/trolling

Only price_inquiry and real_estate_inquiry get engagement. For price_inquiry with
a matched listing, the public reply is short ("sent! 📩" / "ارسال شد 📩") and the
DM contains the actual price + listing details. If no listing is matched, it
falls back to real_estate_inquiry behaviour and asks which property.

Language: Claude detects the comment's language and replies in the same language
(currently supports English and Dari — Ray is fluent in both).
"""

import logging
from typing import Optional

from .script_engine import _call_claude, _parse_json
from .models import CreatorProfile, Listing, json_load

logger = logging.getLogger(__name__)


RAY_VOICE = """You are drafting a public Facebook reply AND a private DM on behalf of Ray Ahmadi, a licensed GTA real estate broker and mortgage professional. Ray is fluent in English and Dari (Farsi).

VOICE RULES (strict):
- Warm, direct, confident. Plain language. No salesy fluff.
- Never sign off with a name or signature. Don't write "- Ray" or "Ray Ahmadi" at the end.
- Never refer to yourself in the third person.
- Never invent listing details, prices, addresses, or specs. Only use numbers/facts from the LISTING CONTEXT block if one is provided.
- If the comment is in Dari (or uses Farsi/Persian script or Dari romanized), reply in Dari. Otherwise reply in English.
- Keep the public reply SHORT (max ~15 words). It's a comment thread.
- DM is longer but tight (3–5 sentences, max ~80 words).
- No hashtags. No links unless present in LISTING CONTEXT.
- One friendly emoji max in the public reply, only if natural.

PRICE INQUIRIES (most common):
- If a listing is matched, the public reply should be very short and push them to DMs. Examples:
    English: "sent! 📩"  "just messaged you 📩"  "check your DMs 📩"
    Dari:    "ارسال شد 📩"  "پیام برات فرستادم 📩"
- The DM must state the price clearly, plus a one-line property summary (beds/baths/address), and invite a quick follow-up question (timeline, financing, viewing).
- If NO listing is matched, do NOT invent a price. Public reply: ask which property (short). DM: acknowledge, ask them to confirm the address/listing so you can pull the right details.

GENERAL REAL ESTATE INQUIRIES:
- Short public reply that invites them to DM. DM gives a useful first take + asks for budget/timeline/area."""


CLASSIFY_AND_DRAFT_PROMPT = """Classify this Facebook comment, detect its language, and draft a public reply + private DM.

POST CAPTION: {post_context}

LISTING CONTEXT (use these facts; if blank, no listing was matched):
{listing_context}

COMMENT AUTHOR: {author}
COMMENT: {message}

Classify category into exactly one of:
- "price_inquiry": asking price, cost, how much, "how much?", "price please", "قیمت؟" etc.
- "real_estate_inquiry": other real estate/mortgage question (market, financing, "do you have anything in Brampton", general help)
- "compliment": praise/thanks/positive reaction with no question
- "spam": links, promo for other services, bots, scams
- "other": off-topic chatter, hate, trolling, anything else

Detect language: return "en" for English or "dari" for Dari/Farsi. If mixed or unclear, prefer the language of the actual question words.

Write a short "intent" — 3–10 words, in English, describing what they want (e.g. "asking price of featured home", "wants Brampton investment condo", "asking if mortgage pre-approval still valid").

Engagement rule: set should_engage=true ONLY for price_inquiry or real_estate_inquiry.

If engaging:
  - draft_reply: short public comment (in detected language). Max ~15 words.
  - draft_dm: the DM (in detected language). Max ~80 words. If listing context exists and category is price_inquiry, state the price plainly from the context.

If not engaging, set draft_reply="" and draft_dm="".

If category is price_inquiry but listing context is blank, do NOT invent a price. Public reply should ask which property. DM should ask them to confirm the address so you can send the right details.

Return ONLY a JSON object:
{{
  "category": "...",
  "language": "en" | "dari",
  "intent": "...",
  "should_engage": true|false,
  "draft_reply": "...",
  "draft_dm": "..."
}}"""


def _profile_blurb(profile: Optional[CreatorProfile]) -> str:
    if not profile:
        return "Ray Ahmadi, GTA real estate broker and mortgage professional."
    markets = ", ".join(json_load(profile.gta_markets)) or "GTA"
    return f"{profile.name} — GTA real estate broker and mortgage professional. Active markets: {markets}."


def _listing_block(listing: Optional[Listing]) -> str:
    if not listing:
        return "(no listing matched — do not invent any numbers)"
    lines = []
    if listing.address:
        addr = listing.address
        if listing.city:
            addr += f", {listing.city}"
        lines.append(f"Address: {addr}")
    if listing.price_label:
        lines.append(f"Price: {listing.price_label}")
    elif listing.price:
        lines.append(f"Price: ${listing.price:,}")
    if listing.bedrooms:
        lines.append(f"Bedrooms: {listing.bedrooms}")
    if listing.bathrooms:
        lines.append(f"Bathrooms: {listing.bathrooms}")
    if listing.sqft:
        lines.append(f"Size: {listing.sqft:,} sqft")
    if listing.property_type:
        lines.append(f"Type: {listing.property_type}")
    if listing.status:
        lines.append(f"Status: {listing.status}")
    if listing.mls:
        lines.append(f"MLS: {listing.mls}")
    if listing.notes:
        lines.append(f"Notes: {listing.notes[:200]}")
    return "\n".join(lines) if lines else "(no listing matched — do not invent any numbers)"


def classify_and_draft(
    message: str,
    author: str = "Facebook user",
    post_context: str = "",
    profile: Optional[CreatorProfile] = None,
    listing: Optional[Listing] = None,
) -> dict:
    """Classify + draft reply/DM. Returns dict with category, language, intent,
    should_engage, draft_reply, draft_dm.
    """
    system = RAY_VOICE + "\n\n" + _profile_blurb(profile)
    prompt = CLASSIFY_AND_DRAFT_PROMPT.format(
        post_context=post_context or "(no post context available)",
        listing_context=_listing_block(listing),
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
            "language": "en",
            "intent": "",
            "should_engage": False,
            "draft_reply": "",
            "draft_dm": "",
        }

    category = (parsed.get("category") or "other").lower().strip()
    language = (parsed.get("language") or "en").lower().strip()
    if language not in ("en", "dari"):
        language = "en"
    engageable = category in ("price_inquiry", "real_estate_inquiry")
    should_engage = engageable and bool(parsed.get("should_engage", True))

    return {
        "category": category,
        "language": language,
        "intent": (parsed.get("intent") or "").strip(),
        "should_engage": should_engage,
        "draft_reply": (parsed.get("draft_reply") or "").strip() if should_engage else "",
        "draft_dm": (parsed.get("draft_dm") or "").strip() if should_engage else "",
    }


# ── Listing matcher ───────────────────────────────────────────────────────

def match_listing(db, post_id: Optional[str], post_caption: Optional[str]) -> Optional[Listing]:
    """Find the listing referenced by this post.
    Priority: exact fb_post_id match → Claude fuzzy-match against caption.
    """
    if post_id:
        row = db.query(Listing).filter(Listing.fb_post_id == str(post_id)).first()
        if row:
            return row

    if not post_caption or not post_caption.strip():
        return None

    # Candidate set: all active listings (capped to keep the prompt small)
    candidates = (
        db.query(Listing)
        .filter(Listing.status.in_(["active", "new", "coming_soon", "", None]))
        .order_by(Listing.synced_at.desc())
        .limit(80)
        .all()
    )
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    rows = []
    for c in candidates:
        bits = []
        if c.address:
            bits.append(c.address)
        if c.city:
            bits.append(c.city)
        if c.mls:
            bits.append(f"MLS {c.mls}")
        rows.append(f"{c.id}: {' | '.join(bits) or '(no address)'}")
    roster = "\n".join(rows)

    prompt = f"""Match this Facebook post caption to the correct listing, if any.

POST CAPTION:
{post_caption[:1000]}

CANDIDATE LISTINGS (id: address | city | mls):
{roster}

Return ONLY a JSON object: {{"id": <listing_id or null>, "confidence": "high"|"medium"|"low"|"none"}}.
Return null id if none of the candidates clearly match the caption."""

    try:
        raw = _call_claude(prompt, fast=True)
        parsed = _parse_json(raw)
        listing_id = parsed.get("id")
        confidence = (parsed.get("confidence") or "").lower()
        if listing_id and confidence in ("high", "medium"):
            return db.query(Listing).filter(Listing.id == int(listing_id)).first()
    except Exception as e:
        logger.warning(f"Listing match failed: {e}")

    return None
