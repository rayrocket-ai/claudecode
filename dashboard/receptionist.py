"""AI Receptionist — Twilio voice webhooks, ElevenLabs TTS, Claude conversation, email recap.

Flow:
    1. Inbound call hits /voice/incoming  (Twilio webhook)
       → create CallRecord, generate greeting via Claude + ElevenLabs, return TwiML
    2. Caller speaks. Twilio posts SpeechResult to /voice/turn
       → save caller turn, ask Claude for next reply, synthesize via ElevenLabs, return TwiML
    3. When Claude flags wrap_up=true OR caller hangs up, /voice/status fires
       → Claude writes summary, email recap to RECEPTIONIST_EMAIL

Required env vars:
    TWILIO_AUTH_TOKEN          (for request signature validation)
    ELEVENLABS_API_KEY
    ELEVENLABS_VOICE_ID
    PUBLIC_BASE_URL            (e.g. https://your-app.up.railway.app — used in TwiML <Play>)
    RECEPTIONIST_EMAIL         (where the recap is sent)
    SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS  (already used by digest_email)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import smtplib
import uuid
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from xml.sax.saxutils import escape as xml_escape

import httpx
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from .models import (
    CallRecord, CallTurn, ClientStory, CreatorProfile,
    SessionLocal, get_db, json_dump, json_load,
)
from .operations import get_profile, get_stories
from .script_engine import _call_claude

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["receptionist"])

# ── Config ────────────────────────────────────────────────────────────────────
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
RECEPTIONIST_EMAIL = os.getenv("RECEPTIONIST_EMAIL", "")

MAX_TURNS = 12  # safety stop on runaway calls

BASE_DIR = Path(__file__).resolve().parent
VOICE_DIR = BASE_DIR / "static" / "voice"
VOICE_DIR.mkdir(parents=True, exist_ok=True)


# ── Twilio request signature validation ──────────────────────────────────────

def _validate_twilio(request: Request, form: dict) -> bool:
    """Verify X-Twilio-Signature so only Twilio can hit our webhooks."""
    if not TWILIO_AUTH_TOKEN:
        logger.warning("TWILIO_AUTH_TOKEN not set — webhook validation disabled")
        return True
    sig = request.headers.get("X-Twilio-Signature", "")
    if not sig:
        return False
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host") or request.url.netloc
    query = f"?{request.url.query}" if request.url.query else ""
    url = f"{proto}://{host}{request.url.path}{query}"
    data = url + "".join(f"{k}{form[k]}" for k in sorted(form.keys()))
    expected = base64.b64encode(
        hmac.new(TWILIO_AUTH_TOKEN.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
    ).decode()
    return hmac.compare_digest(expected, sig)


# ── ElevenLabs TTS ────────────────────────────────────────────────────────────

def synthesize(text: str, call_sid: str, turn_index: int) -> Optional[str]:
    """Generate MP3 with ElevenLabs and save under /static/voice. Returns URL path."""
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        logger.warning("ElevenLabs not configured — falling back to Twilio <Say>")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            logger.error(f"ElevenLabs failed {resp.status_code}: {resp.text[:200]}")
            return None
        filename = f"{call_sid}_{turn_index}_{uuid.uuid4().hex[:6]}.mp3"
        out_path = VOICE_DIR / filename
        out_path.write_bytes(resp.content)
        return f"/static/voice/{filename}"
    except Exception as e:
        logger.error(f"ElevenLabs request failed: {e}")
        return None


# ── Knowledge base for Claude ─────────────────────────────────────────────────

def _knowledge_base(profile: Optional[CreatorProfile], stories: list[ClientStory]) -> str:
    """Build the context block describing what Ray does and what the AI may answer."""
    lines = []
    if profile:
        lines.append(f"Ray's name: {profile.name}")
        if profile.bio:
            lines.append(f"Bio: {profile.bio}")
        markets = json_load(profile.gta_markets)
        if markets:
            lines.append(f"GTA markets Ray serves: {', '.join(markets)}")
        themes = json_load(profile.themes)
        if themes:
            lines.append("Ray's professional themes:")
            for t in themes[:5]:
                lines.append(f"  - {t}")
    if stories:
        lines.append("\nRecent client wins (use these as social proof if relevant):")
        for s in stories[:3]:
            lines.append(f"  - {s.title}: {s.narrative[:200]}")
    if not lines:
        lines.append("Ray Ahmadi — GTA real estate broker and mortgage professional, 12+ years experience.")
    return "\n".join(lines)


SYSTEM_TEMPLATE = """You are Ray Ahmadi's AI phone receptionist. Ray is a Greater Toronto Area real estate broker and mortgage professional. You answer when Ray cannot pick up.

Your job, in order of priority:
1. Get the caller's NAME.
2. Get the REASON they're calling.
3. Gather any other useful details naturally (callback number if it's not their caller-ID, urgency, neighbourhood/property of interest, budget, timeline).
4. Answer simple factual questions about Ray ONLY using the knowledge below. If you don't know, say so honestly and tell the caller Ray will follow up.

Voice & style:
- Warm, human, concise. ONE short sentence per turn — this is a phone call, not a chat.
- Never invent prices, mortgage rates, listings, appointment times, or commitments on Ray's behalf.
- If the caller asks something Ray needs to handle (showings, offers, mortgage pre-approval specifics, legal/tax advice), say Ray will personally call them back.
- If the caller is hostile, a robocall, or clearly not a real prospect, politely end the call.

When you have BOTH the name AND the reason (and any natural follow-ups feel covered), set wrap_up=true and say a friendly goodbye that confirms Ray will be in touch.

KNOWLEDGE ABOUT RAY:
{knowledge}

You will receive the conversation so far and the info already collected. Respond ONLY as a JSON object, no markdown:
{{
  "say": "<the single sentence to speak>",
  "collected": {{ "name": "...", "callback": "...", "reason": "...", "other": "..." }},
  "wrap_up": false
}}
Only include keys in "collected" once you actually know the value. Keep "other" short."""


def _build_messages(call: CallRecord) -> list[dict]:
    msgs = []
    for t in call.turns:
        role = "assistant" if t.role == "ai" else "user"
        msgs.append({"role": role, "content": t.text})
    return msgs


def _ai_turn(call: CallRecord, profile, stories) -> dict:
    """Ask Claude for the next line. Returns dict with say/collected/wrap_up."""
    system = SYSTEM_TEMPLATE.format(knowledge=_knowledge_base(profile, stories))
    history = _build_messages(call)
    collected = call.collected_dict()

    state_note = (
        f"Info collected so far: {json.dumps(collected) if collected else '{}'}\n"
        f"Turn number: {len([t for t in call.turns if t.role == 'ai']) + 1} of max {MAX_TURNS}.\n"
        "Reply with the JSON object now."
    )

    if history:
        # Append the state note as a system-like user message
        prompt = state_note
        # Use the existing _call_claude wrapper but inject conversation via prompt
        rendered = "\n".join(
            f"{'AI' if m['role'] == 'assistant' else 'CALLER'}: {m['content']}"
            for m in history
        )
        full_prompt = f"Conversation so far:\n{rendered}\n\n{state_note}"
    else:
        full_prompt = "This is the very start of the call — no audio yet. Greet the caller as Ray's AI receptionist and ask for their name. " + state_note

    try:
        raw = _call_claude(full_prompt, system=system, fast=True)
        return _parse_ai_json(raw)
    except Exception as e:
        logger.error(f"Claude turn failed: {e}")
        return {
            "say": "Sorry, I'm having a technical issue. Please leave your name and number after the tone and Ray will call you back.",
            "collected": collected,
            "wrap_up": True,
        }


def _parse_ai_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in: {text[:200]}")
    data = json.loads(match.group(0))
    data.setdefault("say", "Got it — Ray will call you back shortly.")
    data.setdefault("collected", {})
    data.setdefault("wrap_up", False)
    return data


# ── TwiML helpers ─────────────────────────────────────────────────────────────

def _public_url(path: str) -> str:
    if PUBLIC_BASE_URL:
        return f"{PUBLIC_BASE_URL}{path}"
    return path  # Twilio requires absolute; will fail without PUBLIC_BASE_URL


def _twiml_say(text: str) -> str:
    return f'<Say voice="Polly.Joanna">{xml_escape(text)}</Say>'


def _twiml_play_or_say(audio_path: Optional[str], fallback_text: str) -> str:
    if audio_path and PUBLIC_BASE_URL:
        return f"<Play>{xml_escape(_public_url(audio_path))}</Play>"
    return _twiml_say(fallback_text)


def _twiml_gather(action_url: str, prompt_xml: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Gather input="speech" action="{xml_escape(action_url)}" '
        'method="POST" speechTimeout="auto" speechModel="phone_call" '
        'language="en-US" actionOnEmptyResult="true">'
        f"{prompt_xml}"
        "</Gather>"
        "</Response>"
    )


def _twiml_hangup(prompt_xml: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response>{prompt_xml}<Hangup/></Response>"
    )


# ── Persistence helpers ───────────────────────────────────────────────────────

def _get_or_create_call(db: Session, call_sid: str, from_number: str, to_number: str) -> CallRecord:
    call = db.query(CallRecord).filter(CallRecord.call_sid == call_sid).first()
    if call:
        return call
    call = CallRecord(
        call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        status="in_progress",
        collected=json_dump({}),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def _add_turn(db: Session, call: CallRecord, role: str, text: str,
              audio_path: Optional[str] = None, confidence: Optional[float] = None) -> None:
    next_index = len(call.turns)
    db.add(CallTurn(
        call_id=call.id,
        turn_index=next_index,
        role=role,
        text=text,
        audio_path=audio_path,
        confidence=confidence,
    ))
    db.commit()
    db.refresh(call)


def _update_collected(db: Session, call: CallRecord, new_collected: dict) -> None:
    if not isinstance(new_collected, dict) or not new_collected:
        return
    merged = call.collected_dict()
    for k, v in new_collected.items():
        if v and isinstance(v, str) and v.strip():
            merged[k] = v.strip()
    call.collected = json_dump(merged)
    db.commit()


# ── Webhook routes ────────────────────────────────────────────────────────────

@router.post("/incoming")
async def incoming_call(request: Request, db: Session = Depends(get_db)):
    """Twilio hits this URL when a call comes in."""
    form = dict(await request.form())
    if not _validate_twilio(request, form):
        return PlainTextResponse("Forbidden", status_code=403)
    call_sid = form.get("CallSid", "")
    from_number = form.get("From", "")
    to_number = form.get("To", "")
    logger.info(f"Incoming call {call_sid} from {from_number}")

    call = _get_or_create_call(db, call_sid, from_number, to_number)

    profile = get_profile(db)
    stories = get_stories(db)

    ai = _ai_turn(call, profile, stories)
    say_text = ai["say"]
    audio_path = synthesize(say_text, call_sid, turn_index=len(call.turns))
    _add_turn(db, call, role="ai", text=say_text, audio_path=audio_path)
    _update_collected(db, call, ai.get("collected", {}))

    prompt_xml = _twiml_play_or_say(audio_path, say_text)
    if ai.get("wrap_up"):
        return PlainTextResponse(_twiml_hangup(prompt_xml), media_type="application/xml")

    return PlainTextResponse(
        _twiml_gather(action_url="/voice/turn", prompt_xml=prompt_xml),
        media_type="application/xml",
    )


@router.post("/turn")
async def caller_turn(request: Request, db: Session = Depends(get_db)):
    """Twilio posts here after each <Gather> captures speech."""
    form = dict(await request.form())
    if not _validate_twilio(request, form):
        return PlainTextResponse("Forbidden", status_code=403)
    call_sid = form.get("CallSid", "")
    speech = (form.get("SpeechResult") or "").strip()
    confidence = form.get("Confidence")
    try:
        conf_val = float(confidence) if confidence else None
    except ValueError:
        conf_val = None

    call = db.query(CallRecord).filter(CallRecord.call_sid == call_sid).first()
    if not call:
        # Should not happen, but recover gracefully
        from_number = form.get("From", "")
        to_number = form.get("To", "")
        call = _get_or_create_call(db, call_sid, from_number, to_number)

    if not speech:
        # Caller said nothing — give them one more chance, then end
        ai_count = len([t for t in call.turns if t.role == "ai"])
        if ai_count >= 2:
            say = "I didn't catch that. I'll let Ray know you called and he'll reach out. Take care."
            audio_path = synthesize(say, call_sid, len(call.turns))
            _add_turn(db, call, "ai", say, audio_path=audio_path)
            return PlainTextResponse(
                _twiml_hangup(_twiml_play_or_say(audio_path, say)),
                media_type="application/xml",
            )
        say = "Sorry, I didn't hear you — could you say that again?"
        audio_path = synthesize(say, call_sid, len(call.turns))
        _add_turn(db, call, "ai", say, audio_path=audio_path)
        return PlainTextResponse(
            _twiml_gather("/voice/turn", _twiml_play_or_say(audio_path, say)),
            media_type="application/xml",
        )

    _add_turn(db, call, role="caller", text=speech, confidence=conf_val)

    profile = get_profile(db)
    stories = get_stories(db)

    ai_turns = len([t for t in call.turns if t.role == "ai"])
    if ai_turns >= MAX_TURNS:
        say = "Thanks — I have everything I need. Ray will call you back shortly. Have a great day."
        audio_path = synthesize(say, call_sid, len(call.turns))
        _add_turn(db, call, "ai", say, audio_path=audio_path)
        return PlainTextResponse(
            _twiml_hangup(_twiml_play_or_say(audio_path, say)),
            media_type="application/xml",
        )

    ai = _ai_turn(call, profile, stories)
    _update_collected(db, call, ai.get("collected", {}))
    say_text = ai["say"]
    audio_path = synthesize(say_text, call_sid, len(call.turns))
    _add_turn(db, call, "ai", say_text, audio_path=audio_path)

    prompt_xml = _twiml_play_or_say(audio_path, say_text)
    if ai.get("wrap_up"):
        return PlainTextResponse(_twiml_hangup(prompt_xml), media_type="application/xml")
    return PlainTextResponse(
        _twiml_gather("/voice/turn", prompt_xml),
        media_type="application/xml",
    )


@router.post("/status")
async def call_status(request: Request):
    """Twilio posts call lifecycle events here. We only act on completion."""
    form = dict(await request.form())
    if not _validate_twilio(request, form):
        return PlainTextResponse("Forbidden", status_code=403)
    call_sid = form.get("CallSid", "")
    call_status = form.get("CallStatus", "")
    logger.info(f"Call status {call_sid}: {call_status}")

    if call_status not in ("completed", "failed", "busy", "no-answer", "canceled"):
        return JSONResponse({"ok": True, "ignored": call_status})

    db = SessionLocal()
    try:
        call = db.query(CallRecord).filter(CallRecord.call_sid == call_sid).first()
        if not call:
            return JSONResponse({"ok": False, "error": "call not found"})
        if call.recap_sent:
            return JSONResponse({"ok": True, "already_sent": True})

        call.status = call_status
        call.ended_at = datetime.utcnow()
        db.commit()

        summary = _summarize_call(call)
        call.summary = summary
        db.commit()

        sent = _send_recap_email(call)
        call.recap_sent = bool(sent.get("ok"))
        db.commit()
        return JSONResponse({"ok": True, "email": sent})
    finally:
        db.close()


# ── Summary + email recap ─────────────────────────────────────────────────────

def _summarize_call(call: CallRecord) -> str:
    transcript = "\n".join(
        f"{'AI' if t.role == 'ai' else 'CALLER'}: {t.text}" for t in call.turns
    )
    if not transcript.strip():
        return "(no conversation captured)"
    prompt = (
        "Below is a transcript of a call answered by Ray Ahmadi's AI receptionist. "
        "Write a 3-5 line recap for Ray covering: caller's name, callback number, reason for the call, "
        "anything else useful, and a recommended next step. Plain text, no markdown.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )
    try:
        return _call_claude(prompt, fast=True).strip()
    except Exception as e:
        logger.error(f"Summary failed: {e}")
        return f"(summary failed: {e})\n\nTranscript:\n{transcript}"


def _send_recap_email(call: CallRecord) -> dict:
    to_email = RECEPTIONIST_EMAIL
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not to_email:
        return {"ok": False, "error": "RECEPTIONIST_EMAIL not set"}
    if not smtp_user or not smtp_pass:
        return {"ok": False, "error": "SMTP_USER/SMTP_PASS not set"}

    collected = call.collected_dict()
    name = collected.get("name", "Unknown caller")
    reason = collected.get("reason", "(not stated)")
    callback = collected.get("callback") or call.from_number or "(unknown)"

    transcript_lines = [
        f"{'AI ' if t.role == 'ai' else 'You'}: {t.text}" for t in call.turns
    ]
    transcript = "\n".join(transcript_lines)

    subject = f"📞 Missed call recap — {name} ({reason[:40]})"

    plain = (
        f"Caller: {name}\n"
        f"Callback: {callback}\n"
        f"Reason: {reason}\n"
        f"Other: {collected.get('other', '')}\n"
        f"Started: {call.started_at:%Y-%m-%d %H:%M UTC}\n"
        f"Status: {call.status}\n\n"
        f"--- Recap ---\n{call.summary or '(none)'}\n\n"
        f"--- Full transcript ---\n{transcript}\n"
    )

    html = _build_recap_html(call, name, callback, reason, collected, transcript_lines)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
        logger.info(f"Recap emailed to {to_email} for call {call.call_sid}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Recap email failed: {e}")
        return {"ok": False, "error": str(e)}


def _build_recap_html(call, name, callback, reason, collected, transcript_lines) -> str:
    rows = ""
    for line in transcript_lines:
        is_ai = line.startswith("AI ")
        bg = "#1f2937" if is_ai else "#0f172a"
        color = "#fde047" if is_ai else "#e5e7eb"
        rows += (
            f'<tr><td style="padding:8px 12px;background:{bg};color:{color};'
            f'border-radius:6px;font-size:14px;line-height:1.5;">'
            f'{xml_escape(line)}</td></tr><tr><td style="height:6px;"></td></tr>'
        )

    other_html = ""
    for k, v in collected.items():
        if k in ("name", "callback", "reason"):
            continue
        if v:
            other_html += (
                f'<tr><td style="padding:4px 0;color:#9ca3af;font-size:13px;">'
                f'<strong>{xml_escape(k.title())}:</strong> {xml_escape(str(v))}</td></tr>'
            )

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;">
  <tr><td align="center" style="padding:32px 16px;">
    <table width="640" style="max-width:640px;width:100%;">
      <tr><td style="padding:0 0 24px 0;">
        <p style="margin:0;font-size:24px;font-weight:800;color:#fff;">📞 Missed Call Recap</p>
        <p style="margin:6px 0 0 0;color:#6b7280;font-size:13px;">{xml_escape(call.started_at.strftime('%A, %B %d, %Y · %H:%M UTC'))}</p>
      </td></tr>
      <tr><td style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:20px 24px;">
        <table width="100%">
          <tr><td style="padding:6px 0;color:#fff;font-size:15px;"><strong>Caller:</strong> {xml_escape(name)}</td></tr>
          <tr><td style="padding:6px 0;color:#fff;font-size:15px;"><strong>Callback:</strong> {xml_escape(callback)}</td></tr>
          <tr><td style="padding:6px 0;color:#fff;font-size:15px;"><strong>Reason:</strong> {xml_escape(reason)}</td></tr>
          {other_html}
        </table>
      </td></tr>
      <tr><td style="padding:24px 0 12px 0;">
        <p style="margin:0 0 8px 0;color:#f97316;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;">AI Recap</p>
        <p style="margin:0;background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:16px;color:#d1d5db;font-size:14px;line-height:1.6;white-space:pre-wrap;">{xml_escape(call.summary or '(no summary)')}</p>
      </td></tr>
      <tr><td style="padding:16px 0 0 0;">
        <p style="margin:0 0 8px 0;color:#f97316;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;">Transcript</p>
        <table width="100%">{rows}</table>
      </td></tr>
    </table>
  </td></tr>
</table></body></html>"""


# ── Debug helper ──────────────────────────────────────────────────────────────

@router.get("/calls")
def list_calls(db: Session = Depends(get_db)):
    """Return the last 25 calls as JSON for quick inspection."""
    calls = db.query(CallRecord).order_by(CallRecord.started_at.desc()).limit(25).all()
    return [
        {
            "call_sid": c.call_sid,
            "from": c.from_number,
            "status": c.status,
            "collected": c.collected_dict(),
            "summary": c.summary,
            "recap_sent": c.recap_sent,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "turns": [{"role": t.role, "text": t.text} for t in c.turns],
        }
        for c in calls
    ]
