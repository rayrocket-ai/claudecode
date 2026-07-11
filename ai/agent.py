"""Claude-powered conversation agent for collecting deal data."""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from ai.prompts import (
    COLLECTION_PROMPTS,
    INTERPRET_REPLY_PROMPT,
    OPS_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
)
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


# ── Team Task Management (Ops Manager) ──────────────────────────────

# Structured output: the model returns one or more tasks parsed from the
# manager's free-text request.
ASSIGN_TASK_TOOL = {
    "name": "submit_tasks",
    "description": (
        "Submit the structured task(s) parsed from the manager's request. "
        "Produce one entry per distinct task. Always call this exactly once."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "assignee_name": {
                            "type": "string",
                            "description": "Team member name as best matched to the roster.",
                        },
                        "title": {"type": "string", "description": "Short imperative title."},
                        "description": {"type": "string"},
                        "deal_ref": {
                            "type": "string",
                            "description": "Property/deal this relates to, if mentioned.",
                        },
                        "due_date": {"type": "string", "description": "YYYY-MM-DD if given/implied."},
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "standard", "high"],
                        },
                    },
                    "required": ["assignee_name", "title"],
                },
            }
        },
        "required": ["tasks"],
    },
}

# Structured output: classify a team member's reply about their task.
INTERPRET_REPLY_TOOL = {
    "name": "submit_interpretation",
    "description": "Classify the team member's reply about their assigned task.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["done", "progress", "blocked", "needs_more_time", "question", "unclear"],
            },
            "note": {
                "type": "string",
                "description": "A one-line summary of what they said, for the activity log.",
            },
        },
        "required": ["intent"],
    },
}


class OpsAgent:
    """Claude helper for the team task-management loop.

    Two jobs, both using the existing 'tool = structured output' idiom:
      - parse_task_request: manager free text -> structured task(s)
      - interpret_reply:     agent free text  -> a task-status intent
    """

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def parse_task_request(
        self, message: str, roster: list[dict]
    ) -> list[dict]:
        """Parse a manager's request into one or more task dicts.

        `roster` is a list of {"name": str, "role": str}. Returns a list of
        dicts with keys: assignee_name, title, description, deal_ref, due_date,
        urgency (missing keys default at the call site).
        """
        roster_text = "\n".join(
            f"- {m['name']} ({m.get('role', 'agent')})" for m in roster
        ) or "(no team members registered yet)"
        system = f"{OPS_SYSTEM_PROMPT}\n\nCURRENT TEAM ROSTER:\n{roster_text}"

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": message}],
            tools=[ASSIGN_TASK_TOOL],
            tool_choice={"type": "tool", "name": "submit_tasks"},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_tasks":
                return list(block.input.get("tasks", []))
        return []

    async def interpret_reply(
        self, reply: str, task_title: str, task_description: str | None = None
    ) -> dict:
        """Classify a team member's free-text reply about a task."""
        context = f"TASK: {task_title}"
        if task_description:
            context += f"\nDETAILS: {task_description}"
        system = f"{INTERPRET_REPLY_PROMPT}\n\n{context}"

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=256,
            system=system,
            messages=[{"role": "user", "content": reply}],
            tools=[INTERPRET_REPLY_TOOL],
            tool_choice={"type": "tool", "name": "submit_interpretation"},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_interpretation":
                return dict(block.input)
        return {"intent": "unclear", "note": reply[:200]}


_ops_agent: OpsAgent | None = None


def get_ops_agent() -> OpsAgent:
    global _ops_agent
    if _ops_agent is None:
        _ops_agent = OpsAgent()
    return _ops_agent
