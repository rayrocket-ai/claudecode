"""Claude-powered Listing Launch agent.

Given the facts of a property listing, this agent drafts a complete marketing
campaign (copy, feature sheet, reel script, email/SMS blast, open house) and
returns it as structured data via a single tool call — mirroring the pattern
in ai/agent.py so there is no JSON-in-text parsing to babysit.

The agent only *drafts*. Delivery/publishing is handled by
integrations/campaign.py, which degrades gracefully when a channel isn't
configured. That keeps the expensive, provider-specific plumbing out of the
model loop and behind a clean, testable seam.
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic

from ai.prompts import LISTING_MARKETING_PROMPT
from config import get_settings

logger = logging.getLogger(__name__)

# Structured output: the model calls this once the full campaign is ready.
# Mirrors DEAL_DATA_TOOL in ai/agent.py — validation happens at the API layer.
CAMPAIGN_TOOL = {
    "name": "submit_campaign",
    "description": (
        "Submit the finished listing marketing campaign. Call this exactly "
        "once, only when every asset you can honestly produce is ready. Omit "
        "any field you cannot populate from the provided facts — never invent "
        "property details."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "listing_copy_long": {"type": "string"},
            "listing_copy_short": {"type": "string"},
            "social_captions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "feature_sheet": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "subhead": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                },
            },
            "reel_script": {
                "type": "object",
                "properties": {
                    "hook": {"type": "string"},
                    "shots": {"type": "array", "items": {"type": "string"}},
                    "cta": {"type": "string"},
                },
            },
            "email": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "body_html": {"type": "string"},
                },
            },
            "sms": {"type": "string"},
            "open_house": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "day_of_week": {"type": "string"},
                    "time_range": {"type": "string"},
                },
            },
        },
        "additionalProperties": True,
    },
}


def format_listing_facts(listing: dict[str, Any]) -> str:
    """Render a listing dict as a clean fact sheet for the model.

    Only non-empty fields are included so the model is never tempted to fill a
    blank — the compliance prompt tells it to omit what it isn't given.
    """
    label_map = [
        ("address", "Address"),
        ("mls_number", "MLS#"),
        ("price", "List price"),
        ("property_type", "Property type"),
        ("bedrooms", "Bedrooms"),
        ("bathrooms", "Bathrooms"),
        ("square_feet", "Square feet"),
        ("lot_size", "Lot size"),
        ("year_built", "Year built"),
        ("parking", "Parking"),
        ("features", "Notable features"),
        ("neighbourhood", "Neighbourhood"),
        ("description", "Existing remarks"),
    ]
    lines = []
    for key, label in label_map:
        value = listing.get(key)
        if value not in (None, "", [], {}):
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(v) for v in value)
            lines.append(f"- {label}: {value}")
    if not lines:
        return "- (no structured details provided)"
    return "\n".join(lines)


class ListingAgent:
    """Drafts a full launch campaign for a single listing."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.brand_voice = settings.marketing_brand_voice or "professional and warm"

    async def draft_campaign(self, listing: dict[str, Any]) -> dict[str, Any]:
        """Draft the campaign for a listing.

        Returns the structured campaign dict (may be partial — only the assets
        the model could produce honestly). Raises on API errors so the caller
        can surface them, matching ai/agent.py's behaviour.
        """
        system = LISTING_MARKETING_PROMPT.format(brand_voice=self.brand_voice)
        facts = format_listing_facts(listing)
        user_message = (
            "Draft the full launch campaign for this listing. Use only these "
            f"facts:\n\n{facts}\n\n"
            "Call submit_campaign with everything you can produce honestly."
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_message}],
            tools=[CAMPAIGN_TOOL],
            tool_choice={"type": "tool", "name": "submit_campaign"},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_campaign":
                return dict(block.input)

        # tool_choice forces the call, so this is defensive only.
        logger.warning("Listing agent returned no submit_campaign tool call")
        return {}


_agent: ListingAgent | None = None


def get_listing_agent() -> ListingAgent:
    global _agent
    if _agent is None:
        _agent = ListingAgent()
    return _agent
