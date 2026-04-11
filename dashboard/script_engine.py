"""Multi-model script generation engine for Ray's Content Engine."""

import json
import logging
import os
from typing import List, Optional, Dict
from anthropic import Anthropic
from .prompts import (
    SYSTEM_PROMPT, DAILY_BATCH_PROMPT, HORMOZI_DENSITY_PROMPT,
    IDEA_BANK_PROMPT, HOOK_FORGE_PROMPT, SCRIPT_WRITER_PROMPT
)
from .models import (
    CreatorProfile, ClientStory, ContentIdea, HookVariation,
    VideoScript, DailyBatch, json_load
)

logger = logging.getLogger(__name__)

# Model configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "claude")  # claude, deepseek, openai
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

claude_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-6")
FAST_MODEL = os.getenv("AI_FAST_MODEL", "claude-haiku-4-5")


def _call_deepseek(prompt: str, system: str = None) -> str:
    """Call DeepSeek API (OpenAI-compatible)."""
    import httpx
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": "deepseek-chat", "messages": messages, "max_tokens": 8096}
    resp = httpx.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_openai(prompt: str, system: str = None) -> str:
    """Call OpenAI API."""
    import httpx
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    payload = {"model": model, "messages": messages, "max_tokens": 8096}
    resp = httpx.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_claude(prompt: str, system: str = None, fast: bool = False) -> str:
    """Route to the configured AI provider."""
    provider = AI_PROVIDER.lower()

    if provider == "deepseek" and DEEPSEEK_API_KEY:
        return _call_deepseek(prompt, system)
    elif provider == "openai" and OPENAI_API_KEY:
        return _call_openai(prompt, system)
    else:
        # Default: Claude
        model = FAST_MODEL if fast else MODEL
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": model, "max_tokens": 8096, "messages": messages}
        if system:
            kwargs["system"] = system
        response = claude_client.messages.create(**kwargs)
        return response.content[0].text


def _parse_json(text: str) -> any:
    """Parse JSON from Claude response, handling markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(text)


def _profile_context(profile: Optional[CreatorProfile]) -> str:
    if not profile:
        return "Ray Ahmadi, GTA real estate broker and mortgage professional, 12+ years experience."
    return f"""Name: {profile.name}
Bio: {profile.bio or 'Licensed real estate broker and mortgage professional, Greater Toronto Area.'}
Markets: {', '.join(json_load(profile.gta_markets)) or 'Brampton, Vaughan, Mississauga, Markham, Oakville, Richmond Hill'}"""


def _stories_context(stories: List[ClientStory]) -> str:
    if not stories:
        return "No client stories on file yet."
    lines = []
    for s in stories[:5]:  # Max 5 to keep prompt manageable
        lines.append(f"- {s.title} ({s.category}): {s.narrative[:200]}")
        if s.lesson:
            lines.append(f"  Lesson: {s.lesson[:100]}")
    return "\n".join(lines)


def _apply_hormozi_pass(hook: str, body: str, cta: str) -> Dict[str, str]:
    """Second Claude pass: remove filler, target 15% shorter."""
    try:
        prompt = HORMOZI_DENSITY_PROMPT.format(hook=hook, body=body, cta=cta)
        response = _call_claude(prompt, system=SYSTEM_PROMPT, fast=True)
        result = _parse_json(response)
        return {
            "hook": result.get("hook", hook),
            "body": result.get("body", body),
            "cta": result.get("cta", cta),
        }
    except Exception as e:
        logger.warning(f"Hormozi pass failed: {e} — using original")
        return {"hook": hook, "body": body, "cta": cta}


# ── Daily Batch ───────────────────────────────────────────────────────────────

def generate_daily_batch(
    profile: Optional[CreatorProfile],
    trending_items: List[Dict],
    client_stories: List[ClientStory],
    n: int = 7,
    batch_id: int = None,
) -> List[Dict]:
    """Generate n scripts for today's batch. Returns list of script data dicts."""

    from .scraper import format_trending_for_prompt
    trending_context = format_trending_for_prompt(trending_items)
    story_context = _stories_context(client_stories)

    prompt = DAILY_BATCH_PROMPT.format(
        n=n,
        trending_context=trending_context,
        client_story_context=story_context,
    )

    logger.info(f"Generating daily batch of {n} scripts...")
    response = _call_claude(prompt, system=SYSTEM_PROMPT)
    raw_scripts = _parse_json(response)

    scripts = []
    for raw in raw_scripts:
        # Skip Hormozi pass for speed — DeepSeek already writes dense
        dense = {"hook": raw.get("hook", ""), "body": raw.get("body", ""), "cta": raw.get("cta", "")}

        full_text = f"{dense['hook']} {dense['body']} {dense['cta']}"
        word_count = len(full_text.split())
        duration = max(30, min(90, int(word_count / 130 * 60)))

        scripts.append({
            "batch_id": batch_id,
            "title": raw.get("title", "Untitled"),
            "script_type": raw.get("script_type", "wildcard"),
            "hook": dense["hook"],
            "body": dense["body"],
            "cta": dense["cta"],
            "platform": raw.get("platform", "reels"),
            "caption": raw.get("caption", ""),
            "hashtags": raw.get("hashtags", ""),
            "estimated_duration_seconds": raw.get("estimated_duration_seconds", duration),
            "word_count": word_count,
        })

    logger.info(f"Generated {len(scripts)} scripts")
    return scripts


# ── Idea Bank ─────────────────────────────────────────────────────────────────

def generate_idea_bank(
    profile: Optional[CreatorProfile],
    trending_items: List[Dict],
    client_stories: List[ClientStory],
    days: int = 30,
) -> List[Dict]:
    """Generate 30 content ideas for the idea bank."""
    logger.info(f"Generating idea bank ({days} ideas)...")
    response = _call_claude(IDEA_BANK_PROMPT, system=SYSTEM_PROMPT)
    ideas = _parse_json(response)

    result = []
    for idea in ideas[:days]:
        result.append({
            "pillar_id": idea.get("pillar", "authority_expertise"),
            "core_story": idea.get("core_story", ""),
            "viral_angle": idea.get("viral_angle", ""),
            "platform_fit": idea.get("platform_fit", "reels,tiktok"),
            "hook_seeds": idea.get("hook_seeds", []),
            "script_type": idea.get("script_type", "wildcard"),
        })

    logger.info(f"Generated {len(result)} ideas")
    return result


# ── Hook Forge ────────────────────────────────────────────────────────────────

def forge_hooks(idea: ContentIdea) -> List[Dict]:
    """Generate 3 hook variations with scores for a content idea."""
    idea_context = f"""Core Story: {idea.core_story}
Viral Angle: {idea.viral_angle}
Platform: {idea.platform_fit}
Hook Seeds: {', '.join(idea.hook_seeds_list())}"""

    prompt = HOOK_FORGE_PROMPT.format(idea_context=idea_context)
    logger.info(f"Forging hooks for idea {idea.id}...")
    response = _call_claude(prompt, system=SYSTEM_PROMPT, fast=True)
    hooks = _parse_json(response)

    return [
        {
            "idea_id": idea.id,
            "hook_text": h.get("hook_text", ""),
            "hook_type": h.get("hook_type", "curiosity"),
            "scroll_stop_score": float(h.get("scroll_stop_score", 7)),
            "curiosity_score": float(h.get("curiosity_score", 7)),
            "specificity_score": float(h.get("specificity_score", 7)),
            "authenticity_score": float(h.get("authenticity_score", 7)),
        }
        for h in hooks[:3]
    ]


# ── Script Writer ─────────────────────────────────────────────────────────────

def write_script(
    idea: ContentIdea,
    chosen_hook: HookVariation,
    profile: Optional[CreatorProfile],
    client_stories: List[ClientStory],
) -> Dict:
    """Write a full script for a given idea and chosen hook."""
    idea_context = f"""Core Story: {idea.core_story}
Viral Angle: {idea.viral_angle}
Platform: {idea.platform_fit}"""

    story_context = _stories_context(client_stories)

    prompt = SCRIPT_WRITER_PROMPT.format(
        idea_context=idea_context,
        hook_text=chosen_hook.hook_text,
        hook_type=chosen_hook.hook_type,
        client_story_context=story_context,
    )

    logger.info(f"Writing script for idea {idea.id}...")
    response = _call_claude(prompt, system=SYSTEM_PROMPT)
    raw = _parse_json(response)

    # Apply Hormozi density pass
    dense = _apply_hormozi_pass(
        raw.get("hook", chosen_hook.hook_text),
        raw.get("body", ""),
        raw.get("cta", "Follow Ray Ahmadi for GTA real estate insights."),
    )

    full_text = f"{dense['hook']} {dense['body']} {dense['cta']}"
    word_count = len(full_text.split())
    duration = max(30, min(90, int(word_count / 130 * 60)))

    return {
        "idea_id": idea.id,
        "title": raw.get("title", f"Script from idea {idea.id}"),
        "hook": dense["hook"],
        "body": dense["body"],
        "cta": dense["cta"],
        "platform": raw.get("platform", idea.platform_fit.split(",")[0] if idea.platform_fit else "reels"),
        "caption": raw.get("caption", ""),
        "hashtags": raw.get("hashtags", ""),
        "script_type": getattr(idea, "script_type", "wildcard"),
        "estimated_duration_seconds": raw.get("estimated_duration_seconds", duration),
        "word_count": word_count,
    }


# ── Single Script Regeneration ────────────────────────────────────────────────

def generate_shot_list(script: VideoScript) -> List[Dict]:
    """Generate a specific shot-by-shot filming guide for a script."""
    prompt = f"""You are a social media video director. Create a practical shot list for this script.

TITLE: {script.title}
HOOK: {script.hook}
BODY: {script.body}
CTA: {script.cta}
PLATFORM: {getattr(script, 'platform', 'Instagram/TikTok')}
DURATION: ~{getattr(script, 'estimated_duration_seconds', 60)} seconds

Return a JSON array of shot objects. Each shot:
{{
  "shot": "HOOK",
  "framing": "tight selfie / medium / wide / close-up detail",
  "camera": "front / back / tripod / handheld",
  "action": "specific action and delivery instruction",
  "movement": "static / walk toward camera / step back / pan / none",
  "duration": "3 seconds",
  "notes": "optional tip for delivery or setup"
}}

Create 5-9 shots covering: hook delivery, setup/context, key points, payoff moment, CTA.
Be very specific — this is a real filming guide Ray will read on set.
Return ONLY the JSON array, no markdown."""

    response = _call_claude(prompt)
    parsed = _parse_json(response)
    if isinstance(parsed, list):
        return parsed
    # Fallback: wrap in list if single object returned
    if isinstance(parsed, dict):
        return [parsed]
    return [
        {"shot": "HOOK", "framing": "tight selfie", "camera": "front",
         "action": "Look directly at camera, deliver hook with energy",
         "movement": "static", "duration": "3-4 seconds", "notes": ""},
        {"shot": "BODY", "framing": "medium", "camera": "front/tripod",
         "action": "Walk through main points naturally",
         "movement": "slight walk toward camera", "duration": "30-40 seconds", "notes": ""},
        {"shot": "CTA", "framing": "medium", "camera": "front",
         "action": "Deliver CTA with direct eye contact",
         "movement": "static", "duration": "5 seconds", "notes": ""},
    ]


def regenerate_script(script: VideoScript, profile: Optional[CreatorProfile],
                      client_stories: List[ClientStory]) -> Dict:
    """Regenerate a single script based on its type."""
    from .scraper import get_trending_items, format_trending_for_prompt
    trending = get_trending_items(5)
    trending_context = format_trending_for_prompt(trending)
    story_context = _stories_context(client_stories)

    prompt = f"""Regenerate this script with a fresh angle. Keep the same script_type: {script.script_type}

Original title: {script.title}
Original hook: {script.hook}

TRENDING CONTEXT: {trending_context}
CLIENT STORIES: {story_context}

Return a JSON object with: title, hook, body, cta, caption, hashtags, platform, estimated_duration_seconds"""

    response = _call_claude(prompt, system=SYSTEM_PROMPT)
    raw = _parse_json(response)

    dense = _apply_hormozi_pass(
        raw.get("hook", script.hook),
        raw.get("body", script.body),
        raw.get("cta", script.cta),
    )

    full_text = f"{dense['hook']} {dense['body']} {dense['cta']}"
    word_count = len(full_text.split())

    return {
        "title": raw.get("title", script.title),
        "hook": dense["hook"],
        "body": dense["body"],
        "cta": dense["cta"],
        "platform": raw.get("platform", script.platform),
        "caption": raw.get("caption", script.caption),
        "hashtags": raw.get("hashtags", script.hashtags),
        "script_type": script.script_type,
        "estimated_duration_seconds": raw.get("estimated_duration_seconds", script.estimated_duration_seconds),
        "word_count": word_count,
    }
