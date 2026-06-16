"""Claude-powered conversation agent for collecting deal data."""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from ai.prompts import SYSTEM_PROMPT, COLLECTION_PROMPTS
from config import get_settings


class RealEstateAgent:
    """Manages the AI conversation for collecting deal data."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
        )

        ai_text = response.content[0].text

        # Update history
        new_history = list(history)
        new_history.append({"role": "user", "content": user_message})
        new_history.append({"role": "assistant", "content": ai_text})

        # Check if collection is complete (AI outputs JSON)
        extracted = self._try_extract_json(ai_text)

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
        """Convert price string/int to float (see forms.formatting)."""
        from forms.formatting import normalize_number
        return normalize_number(value)


_agent: RealEstateAgent | None = None


def get_agent() -> RealEstateAgent:
    global _agent
    if _agent is None:
        _agent = RealEstateAgent()
    return _agent
