"""The standalone editor agent: the brain, without Claude Code.

Inside Claude Code, ``/reels`` hands the transcript to the **editor** subagent
and ``/vlog`` to the **producer**. This module does the same job by calling
the Claude API directly, so a video can be edited from a cron job, the inbox
watcher, a phone over SSH, or anything else -- no interactive session needed.

It is deliberately the *same* brain, not a second one:

- The system prompts **are** ``agents/editor.md`` and ``agents/producer.md``.
  Improve the editorial judgment there and both paths improve; there is no
  copy to drift.
- The output is forced through a tool whose input schema **is**
  ``highlights.HIGHLIGHTS_SCHEMA`` / ``vlog.EPISODE_SCHEMA`` -- the exact JSON
  the subagents return -- and it is saved to disk before anything else
  happens. Every decision the model made is a file you can read, edit, and
  feed back through ``reelforge compose`` without paying for another call.
- The model still only decides **what is worth keeping**. Cutting, framing,
  captions and pacing stay in the composer and the playbook, where they can be
  learned and diffed -- the division the whole system is built on.

Configured with ``ANTHROPIC_API_KEY`` and, optionally, ``REELFORGE_MODEL``.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .analyze import Signals
from .highlights import HIGHLIGHTS_SCHEMA, Clip, parse
from .playbook import Playbook
from .transcribe import Transcript
from .vlog import EPISODE_SCHEMA

#: The most capable current model by default. Editorial judgment -- which take
#: was the good one, whether a clip stands alone -- is exactly where a stronger
#: model earns its cost, and one call per video is cheap against a human edit.
DEFAULT_MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"

#: A new transcript line starts after a pause this long, or after this many
#: words. Lines that follow the speaker's own phrasing are what let the model
#: read the transcript the way an editor would.
LINE_PAUSE = 0.6
LINE_WORDS = 14


class AgentError(RuntimeError):
    """The brain could not produce a usable decision. Says why and how to fix it."""


# --------------------------------------------------------------------------
# prompt material
# --------------------------------------------------------------------------

_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.S)


def agent_prompt(name: str, style_profile: str | None = None) -> str:
    """An agent's markdown body as a system prompt, plus the user's style profile.

    The style profile is appended last and labelled as outranking everything
    above it, which is exactly the instruction the agent files already give.
    """
    text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    body = _FRONTMATTER.sub("", text, count=1).strip()
    body = body.replace("Call `StructuredOutput`", "Call the submit tool")
    if style_profile and style_profile.strip():
        body += ("\n\n## This user's style profile\n\n"
                 "It outranks every default above.\n\n" + style_profile.strip())
    return body


def _stamp(seconds: float) -> str:
    minutes, secs = divmod(max(0.0, seconds), 60)
    return f"{int(minutes):02d}:{secs:04.1f}"


def transcript_text(transcript: Transcript) -> str:
    """The transcript as ``[mm:ss.s] text`` lines, broken where the speaker breaks.

    Tenths of a second rather than whole seconds: the model returns source
    seconds, and a whole-second grid would make it guess at every boundary.
    Downstream snaps to word edges anyway, but a closer guess means less
    snapping and fewer clipped first words.
    """
    lines: list[str] = []
    current: list[str] = []
    start = 0.0
    last_end: float | None = None
    for word in transcript.words:
        if current and (word.start - (last_end or word.start) > LINE_PAUSE
                        or len(current) >= LINE_WORDS):
            lines.append(f"[{_stamp(start)}] {' '.join(current)}")
            current = []
        if not current:
            start = word.start
        current.append(word.text.strip())
        last_end = word.end
    if current:
        lines.append(f"[{_stamp(start)}] {' '.join(current)}")
    return "\n".join(lines)


def signals_summary(signals: Signals | None, *, peaks: int = 20) -> str:
    """The non-verbal evidence, compact enough to be worth its tokens."""
    if signals is None:
        return "No visual or audio signals available."
    parts = [f"Duration: {signals.duration:.1f}s"]
    if signals.silence:
        longest = sorted(signals.silence, key=lambda s: s[1] - s[0], reverse=True)[:8]
        parts.append("Longest silences: " + ", ".join(
            f"{_stamp(a)}-{_stamp(b)} ({b - a:.1f}s)" for a, b in sorted(longest)))
    if signals.scenes:
        shown = signals.scenes[:40]
        parts.append(f"Scene cuts ({len(signals.scenes)}): "
                     + ", ".join(_stamp(t) for t in shown)
                     + (" ..." if len(signals.scenes) > len(shown) else ""))
    if signals.energy:
        mean = sum(signals.energy) / len(signals.energy)
        loud = sorted(range(len(signals.energy)), key=lambda i: signals.energy[i],
                      reverse=True)[:peaks]
        parts.append(f"Energy peaks (mean {mean:.2f}): " + ", ".join(
            f"{_stamp(i)}={signals.energy[i]:.2f}" for i in sorted(loud)))
    return "\n".join(parts)


def reels_request(transcript: Transcript, signals: Signals | None, *,
                  count: int, book: Playbook) -> str:
    low, high = book.target_seconds
    return (
        f"Find clips for {count} reel{'s' if count != 1 else ''}. Return roughly "
        f"{count * 3} candidates so downstream ranking has a real choice. Each clip "
        f"should run about {low:.0f}-{high:.0f} seconds after its internal drops.\n\n"
        "Timestamps below are [mm:ss.s]. Return source seconds as plain numbers "
        "(1:23.4 is 83.4).\n\n"
        f"## Signals\n\n{signals_summary(signals)}\n\n"
        f"## Transcript\n\n{transcript_text(transcript)}\n"
    )


def episode_request(transcript: Transcript, signals: Signals | None) -> str:
    return (
        "Shape this footage into a YouTube episode.\n\n"
        "Timestamps below are [mm:ss.s]. Return source seconds as plain numbers "
        "(1:23.4 is 83.4).\n\n"
        f"## Signals\n\n{signals_summary(signals)}\n\n"
        f"## Transcript\n\n{transcript_text(transcript)}\n"
    )


# --------------------------------------------------------------------------
# the call
# --------------------------------------------------------------------------

@dataclass
class Decision:
    """What the brain returned, plus what it cost."""

    payload: dict[str, Any]
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    clips: list[Clip] = field(default_factory=list)

    def usage(self) -> dict[str, Any]:
        return {"model": self.model, "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens}


def default_client():
    """An Anthropic client, or an error that says exactly what is missing."""
    try:
        import anthropic
    except ImportError as exc:
        raise AgentError("the Anthropic SDK is not installed: pip install anthropic") from exc
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise AgentError(
            "ANTHROPIC_API_KEY is not set. Create a key at console.anthropic.com "
            "and export it (on the box, put it in ~/.reelforge/env, never in chat).")
    return anthropic.Anthropic()


class Brain:
    """Calls Claude with one forced tool and returns its input as the decision."""

    def __init__(self, client=None, model: str | None = None,
                 max_tokens: int = MAX_TOKENS):
        self._client = client
        self.model = model or os.environ.get("REELFORGE_MODEL") or DEFAULT_MODEL
        self.max_tokens = max_tokens

    @property
    def client(self):
        if self._client is None:
            self._client = default_client()
        return self._client

    def _ask(self, *, system: str, request: str, tool: str, schema: dict,
             description: str) -> Decision:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            # The system prompt is identical on every call, so it is cached:
            # a batch of videos pays for it once.
            system=[{"type": "text", "text": system,
                     "cache_control": {"type": "ephemeral"}}],
            tools=[{"name": tool, "description": description, "input_schema": schema}],
            # Forcing the tool is what makes the answer machine-readable every
            # time -- no prose to parse, no "here are the clips:" preamble.
            tool_choice={"type": "tool", "name": tool},
            messages=[{"role": "user", "content": request}],
        )
        if getattr(response, "stop_reason", None) == "max_tokens":
            raise AgentError(
                f"the model ran out of output tokens ({self.max_tokens}) before "
                "finishing its decision; raise max_tokens or shorten the source")
        block = next((b for b in getattr(response, "content", [])
                      if getattr(b, "type", None) == "tool_use"
                      and getattr(b, "name", None) == tool), None)
        if block is None:
            raise AgentError("the model did not return a decision through the tool")
        payload = block.input if isinstance(block.input, dict) else json.loads(block.input)
        usage = getattr(response, "usage", None)
        return Decision(
            payload=payload,
            model=self.model,
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )

    def find_clips(self, transcript: Transcript, signals: Signals | None, *,
                   count: int, book: Playbook, style_profile: str | None = None) -> Decision:
        """Pick reel candidates. Raises if none survive parsing."""
        decision = self._ask(
            system=agent_prompt("editor", style_profile),
            request=reels_request(transcript, signals, count=count, book=book),
            tool="submit_highlights",
            schema=HIGHLIGHTS_SCHEMA,
            description="Submit the candidate clips, scored honestly.",
        )
        decision.clips = parse(decision.payload)
        if not decision.clips:
            raise AgentError("the model returned no usable clips "
                             f"(raw: {json.dumps(decision.payload)[:300]})")
        return decision

    def shape_episode(self, transcript: Transcript, signals: Signals | None, *,
                      style_profile: str | None = None) -> Decision:
        """Decide body, cold open, drops, chapters, b-roll and metadata."""
        return self._ask(
            system=agent_prompt("producer", style_profile),
            request=episode_request(transcript, signals),
            tool="submit_episode",
            schema=EPISODE_SCHEMA,
            description="Submit the episode plan.",
        )
