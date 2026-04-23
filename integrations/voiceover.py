"""Voiceover script generation (Claude) and TTS synthesis (ElevenLabs).

The script is produced as a list of `ScriptSegment`s, one per scene detected
in the source video. Each segment carries a target duration in seconds, and
Claude is instructed to write narration that, read at a natural pace, fits
inside that window.

TTS audio is rendered per-segment so we can align each line to its scene's
start timestamp in the final mix.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import anthropic
import httpx

from config import get_settings
from integrations.property_lookup import PropertyInfo

logger = logging.getLogger(__name__)


ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


@dataclass
class ScriptSegment:
    """One narration line tied to one scene of the video."""

    index: int
    start_seconds: float
    duration_seconds: float
    room_guess: str
    text: str
    audio_path: Path | None = None

    @property
    def end_seconds(self) -> float:
        return self.start_seconds + self.duration_seconds


# ----------------------------------------------------------------------
# Script generation
# ----------------------------------------------------------------------
ROOM_GUESS_ORDER = [
    "exterior",
    "foyer",
    "living room",
    "kitchen",
    "dining room",
    "primary bedroom",
    "bedroom",
    "bathroom",
    "basement",
    "backyard",
]


def _default_room_guess(index: int, total: int) -> str:
    """Heuristic room progression for when Claude doesn't label a segment."""
    if total <= 0:
        return "home"
    if index == 0:
        return "exterior"
    if index == total - 1:
        return "backyard"
    # Map interior scenes across the typical walkthrough order
    mid = ROOM_GUESS_ORDER[1:-1]
    slot = min(len(mid) - 1, int((index - 1) * len(mid) / max(1, total - 2)))
    return mid[slot]


SYSTEM_PROMPT = (
    "You are a senior real-estate listing copywriter who writes short, "
    "warm voiceover scripts for luxury home tour videos. Your narration is "
    "tight, specific, and evocative — never generic. You match each line "
    "to the room being shown on screen."
)


def _build_user_prompt(
    property_info: PropertyInfo,
    scenes: list[tuple[float, float, str]],
    words_per_second: float,
) -> str:
    """Construct the Claude prompt that asks for per-scene narration.

    `scenes` is a list of (start, duration, room_guess) tuples.
    """
    scene_lines = []
    for i, (start, dur, room) in enumerate(scenes):
        words = max(4, int(round(dur * words_per_second)))
        scene_lines.append(
            f"  scene {i}: starts at {start:.2f}s, lasts {dur:.2f}s "
            f"(~{words} words), likely shows: {room}"
        )
    scenes_block = "\n".join(scene_lines)

    features = "; ".join(property_info.features) if property_info.features else "(none)"
    description = property_info.description or "(no listing description available)"

    return f"""Write a voiceover script for this house tour video.

PROPERTY
  Address: {property_info.address}
  Bedrooms: {property_info.bedrooms or "unknown"}
  Bathrooms: {property_info.bathrooms or "unknown"}
  Sq ft: {property_info.square_footage or "unknown"}
  Type: {property_info.property_type or "residential home"}
  Features: {features}
  Listing description:
  \"\"\"{description}\"\"\"

VIDEO SCENES (one per room transition detected in the footage)
{scenes_block}

RULES
- Produce exactly one narration line per scene above (same order, same count).
- Each line's spoken length MUST fit within that scene's duration at a natural
  pace. The approximate word budget per scene is given — stay at or under it.
- Open on the exterior with the address or a hook. Close on the backyard /
  last scene with a warm invitation ("Welcome home.", etc.) — do NOT mention
  a price, agent name, or call-to-action.
- Ground the lines in real details from the listing (materials, finishes,
  room counts) when the scene's likely room matches. Never invent specifics.
- If a scene's room guess feels wrong based on timing, use a neutral line that
  works for any interior shot.

OUTPUT
Return ONLY a JSON array, no prose, no markdown fences. Each element:
  {{"scene": <int>, "room": "<short room name>", "line": "<narration>"}}
Example:
  [{{"scene": 0, "room": "exterior", "line": "Welcome to 123 Main."}}, ...]
"""


async def generate_voiceover_script(
    property_info: PropertyInfo,
    scene_starts_durations: list[tuple[float, float]],
    *,
    words_per_second: float | None = None,
) -> list[ScriptSegment]:
    """Ask Claude for a room-aligned voiceover script."""
    settings = get_settings()
    wps = words_per_second if words_per_second is not None else settings.voiceover_words_per_second

    total = len(scene_starts_durations)
    if total == 0:
        return []

    scenes_with_rooms = [
        (start, dur, _default_room_guess(i, total))
        for i, (start, dur) in enumerate(scene_starts_durations)
    ]
    user_prompt = _build_user_prompt(property_info, scenes_with_rooms, wps)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    logger.info("Asking Claude for a %d-segment script for %s", total, property_info.address)
    response = await asyncio.to_thread(
        client.messages.create,
        model=settings.claude_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text if response.content else ""
    lines = _parse_script_json(text, expected=total)

    segments: list[ScriptSegment] = []
    for i, (start, dur) in enumerate(scene_starts_durations):
        room_guess = scenes_with_rooms[i][2]
        entry = lines[i] if i < len(lines) else {}
        line_text = (entry.get("line") or "").strip()
        room = (entry.get("room") or room_guess).strip() or room_guess
        if not line_text:
            line_text = _fallback_line(room, i, total)
        segments.append(
            ScriptSegment(
                index=i,
                start_seconds=start,
                duration_seconds=dur,
                room_guess=room,
                text=_trim_to_word_budget(line_text, dur, wps),
            )
        )
    return segments


def _parse_script_json(text: str, *, expected: int) -> list[dict]:
    """Pull the JSON array out of Claude's response, tolerating extra text."""
    # Fast path: whole response is JSON
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except json.JSONDecodeError:
        pass

    # Strip common code fences
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        # Greedy capture of the largest array in the message
        match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
        candidate = match.group(0) if match else None

    if candidate:
        try:
            data = json.loads(candidate)
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict)]
        except json.JSONDecodeError:
            logger.warning("Failed to parse Claude JSON; using fallbacks for %d segments", expected)

    return []


def _fallback_line(room: str, index: int, total: int) -> str:
    if index == 0:
        return "Welcome home."
    if index == total - 1:
        return "Your next chapter starts here."
    return f"Step into the {room}."


def _trim_to_word_budget(text: str, duration: float, wps: float) -> str:
    """Hard-cap the line to its word budget so TTS never overflows a scene."""
    budget = max(3, int(round(duration * wps)))
    words = text.split()
    if len(words) <= budget:
        return text
    trimmed = " ".join(words[:budget])
    # Keep a period so TTS doesn't dangle
    if not trimmed.endswith((".", "!", "?")):
        trimmed += "."
    return trimmed


# ----------------------------------------------------------------------
# ElevenLabs TTS
# ----------------------------------------------------------------------
class ElevenLabsTTS:
    """Thin async wrapper around the ElevenLabs text-to-speech REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        model_id: str | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.elevenlabs_api_key
        self.voice_id = voice_id or settings.elevenlabs_voice_id
        self.model_id = model_id or settings.elevenlabs_model_id
        if not self.api_key:
            raise ValueError(
                "ELEVENLABS_API_KEY not set. Add it to .env to enable TTS."
            )

    async def synthesize(self, text: str, output_path: Path) -> Path:
        """Render `text` to an mp3 at `output_path` and return the path."""
        url = ELEVENLABS_TTS_URL.format(voice_id=self.voice_id)
        body = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }
        headers = {
            "xi-api-key": self.api_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"ElevenLabs TTS failed ({resp.status_code}): {resp.text[:300]}"
                )
            output_path.write_bytes(resp.content)
        logger.info("Rendered TTS (%d chars) -> %s", len(text), output_path)
        return output_path


async def synthesize_segments(
    segments: list[ScriptSegment],
    output_dir: Path,
    *,
    tts: ElevenLabsTTS | None = None,
) -> list[ScriptSegment]:
    """Render one mp3 per segment and attach the path to each segment."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tts = tts or ElevenLabsTTS()

    for seg in segments:
        if not seg.text.strip():
            continue
        path = output_dir / f"seg_{seg.index:02d}.mp3"
        await tts.synthesize(seg.text, path)
        seg.audio_path = path
    return segments
