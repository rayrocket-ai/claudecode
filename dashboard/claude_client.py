"""Shared Anthropic Claude client wrapper.

Centralizes model selection, prompt caching, and billing-error detection so
every pipeline stage uses the same cost-optimized transport.

Prompt caching: Anthropic's prompt caching feature caches the system prompt on
their side for 5 minutes. Repeat calls with the same system prompt cost ~90%
less on the cached portion. Every stage's system prompt is large (2-4K tokens)
so caching is a huge win.

Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic

from config import get_settings

logger = logging.getLogger(__name__)


class BillingError(Exception):
    """Raised when Anthropic rejects a request for insufficient credits."""

    def __init__(self, message: str = "Anthropic API credit balance is too low."):
        super().__init__(message)
        self.message = message
        self.billing_url = "https://console.anthropic.com/settings/billing"


class ClaudeClient:
    """Shared Claude client used by all pipeline stages."""

    # Model cost tiers (input / output, USD per million tokens, rough)
    MODEL_INFO = {
        "claude-haiku-4-5-20251001": {"name": "Haiku 4.5", "input": 1.00, "output": 5.00, "tier": "cheap"},
        "claude-sonnet-4-6":         {"name": "Sonnet 4.6", "input": 3.00, "output": 15.00, "tier": "balanced"},
        "claude-opus-4-6":           {"name": "Opus 4.6",  "input": 15.00, "output": 75.00, "tier": "premium"},
    }

    def __init__(self):
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.script_model or "claude-haiku-4-5-20251001"

    @property
    def model_info(self) -> dict:
        return self.MODEL_INFO.get(self.model, {"name": self.model, "input": 0, "output": 0, "tier": "unknown"})

    def messages_create(
        self,
        *,
        system: str | list,
        messages: list,
        max_tokens: int = 4096,
        enable_caching: bool = True,
        override_model: str | None = None,
    ) -> Any:
        """Create a Claude completion with automatic prompt caching + error mapping.

        If the system prompt is >1024 tokens (roughly), we cache it. Anthropic
        only caches segments >= 1024 tokens for Sonnet/Opus, >= 2048 for Haiku.
        Caching saves ~90% on repeat calls within 5 minutes.
        """
        model = override_model or self.model

        # Wrap system prompt in cache-control block if it's a string
        if enable_caching and isinstance(system, str) and len(system) > 2000:
            system_param = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        else:
            system_param = system

        try:
            return self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_param,
                messages=messages,
            )
        except anthropic.BadRequestError as e:
            msg = str(e).lower()
            if "credit balance is too low" in msg or "insufficient" in msg:
                raise BillingError(
                    "Your Anthropic API credit balance is too low. "
                    "Add credits at https://console.anthropic.com/settings/billing"
                ) from e
            raise
        except anthropic.AuthenticationError as e:
            raise BillingError(
                "Anthropic API key is invalid or missing. Check ANTHROPIC_API_KEY "
                "in Railway environment variables."
            ) from e


# Singleton
_client: ClaudeClient | None = None


def get_claude_client() -> ClaudeClient:
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
