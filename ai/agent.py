"""Claude-powered conversation agent for collecting deal data."""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from ai.prompts import SYSTEM_PROMPT, COLLECTION_PROMPTS
from config import get_settings

# Tool the model calls once every required field has been collected.
# Structured output is validated by the API — no JSON-in-text parsing.
DEAL_DATA_TOOL = {
    "name": "submit_deal_data",
    "description": (
        "Submit the final collected deal data. Call this ONLY when every "
        "required field for the document has been gathered from the user. "
        "Include every field you collected, using the field names from the "
        "collection instructions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "buyer_1": {"type": "string"},
            "buyer_2": {"type": "string"},
            "buyer_1_email": {"type": "string"},
            "buyer_2_email": {"type": "string"},
            "seller_1": {"type": "string"},
            "seller_2": {"type": "string"},
            "seller_1_email": {"type": "string"},
            "seller_2_email": {"type": "string"},
            "property_street_number": {"type": "string"},
            "property_street_name": {"type": "string"},
            "property_unit": {"type": "string"},
            "property_city": {"type": "string"},
            "property_province": {"type": "string"},
            "property_postal_code": {"type": "string"},
            "mls_number": {"type": "string"},
            "legal_description": {"type": "string"},
            "purchase_price": {"type": "number"},
            "deposit": {"type": "number"},
            "deposit_holder": {"type": "string"},
            "offer_date": {"type": "string", "description": "YYYY-MM-DD"},
            "irrevocability_date": {"type": "string", "description": "YYYY-MM-DD"},
            "irrevocability_time": {"type": "string"},
            "closing_date": {"type": "string", "description": "YYYY-MM-DD"},
            "financing_condition": {"type": "boolean"},
            "home_inspection": {"type": "boolean"},
            "status_certificate": {"type": "boolean"},
            "sale_of_buyers_property": {"type": "boolean"},
            "inclusions": {"type": "string"},
            "exclusions": {"type": "string"},
            "listing_brokerage": {"type": "string"},
            "listing_agent": {"type": "string"},
            "co_op_brokerage": {"type": "string"},
        },
        "additionalProperties": True,
    },
}


class RealEstateAgent:
    """Manages the AI conversation for collecting deal data."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def continue_collection(
        self,
        user_message: str,
        history: list[dict],
        doc_type: str,
    ) -> tuple[str, list[dict], dict | None]:
        """Send a message and get the AI response.

        Returns: (ai_reply_text, updated_history, extracted_data_or_None)
        """
        collection_prompt = COLLECTION_PROMPTS.get(doc_type, COLLECTION_PROMPTS["aps"])
        system = f"{SYSTEM_PROMPT}\n\n{collection_prompt}"

        # Build messages for Claude
        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=[DEAL_DATA_TOOL],
        )

        ai_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        # Structured extraction: the model calls submit_deal_data when done
        extracted = None
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_deal_data":
                extracted = dict(block.input)
                extracted["collection_complete"] = True
                break

        # Fallback: some replies may still embed JSON in text
        if extracted is None:
            extracted = self._try_extract_json(ai_text)

        if not ai_text:
            ai_text = "✅ I have everything I need."

        # Update history
        new_history = list(history)
        new_history.append({"role": "user", "content": user_message})
        new_history.append({"role": "assistant", "content": ai_text})

        return ai_text, new_history, extracted

    def _try_extract_json(self, text: str) -> dict | None:
        """Try to extract JSON from AI response. Returns dict if complete."""
        # Look for ```json ... ``` blocks
        match = re.search(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if data.get("collection_complete"):
                    return data
            except json.JSONDecodeError:
                pass

        # Also try bare JSON at end of message
        match = re.search(r"\{[^{}]*\"collection_complete\"\s*:\s*true[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None


class DataExtractor:
    """Validates and normalizes collected deal data."""

    REQUIRED_APS_FIELDS = [
        "buyer_1", "seller_1", "purchase_price",
        "property_street_number", "property_street_name", "property_city",
    ]

    @staticmethod
    def validate_aps(data: dict) -> list[str]:
        """Return list of missing required fields."""
        missing = []
        for field in DataExtractor.REQUIRED_APS_FIELDS:
            if not data.get(field):
                missing.append(field)
        return missing

    @staticmethod
    def normalize_price(value: Any) -> float:
        """Convert price string/int to float."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = re.sub(r"[,$\s]", "", value)
            return float(cleaned)
        return 0.0


_agent: RealEstateAgent | None = None


def get_agent() -> RealEstateAgent:
    global _agent
    if _agent is None:
        _agent = RealEstateAgent()
    return _agent
