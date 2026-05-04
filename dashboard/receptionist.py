"""AI Receptionist — receives ElevenLabs post-call webhook, emails recap to Ray.

Architecture
    Caller dials Twilio number → Twilio routes to ElevenLabs Agent → agent
    handles voice (TTS + STT + reasoning) using its own system prompt and Ray's
    knowledge. When the call ends, ElevenLabs POSTs the full transcript to
    /voice/elevenlabs/post-call. We persist it, ask Claude for a sharp recap,
    and email it to RECEPTIONIST_EMAIL.

Required env vars
    ELEVENLABS_WEBHOOK_SECRET  HMAC secret for signature validation
                               (ElevenLabs → Conversational AI → Settings →
                                Post-call webhook → "Webhook secret")
    RECEPTIONIST_EMAIL         where the recap is sent
    SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS  (already used by digest_email)
    ANTHROPIC_API_KEY          for the Claude recap pass
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from .models import (
    CallRecord, CallTurn, SessionLocal,
    get_db, json_dump,
)
from .script_engine import _call_claude

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["receptionist"])

ELEVENLABS_WEBHOOK_SECRET = os.getenv("ELEVENLABS_WEBHOOK_SECRET", "")
RECEPTIONIST_EMAIL = os.getenv("RECEPTIONIST_EMAIL", "")

# Tolerance for timestamp drift on the webhook signature (seconds)
WEBHOOK_TIMESTAMP_TOLERANCE = 30 * 60


# ── Signature validation ─────────────────────────────────────────────────────

def _validate_elevenlabs_signature(raw_body: bytes, header: str) -> bool:
    """Verify ElevenLabs-Signature header. Format: t=<unix>,v0=<hex>."""
    if not ELEVENLABS_WEBHOOK_SECRET:
        logger.warning("ELEVENLABS_WEBHOOK_SECRET not set — webhook validation disabled")
        return True
    if not header:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    timestamp = parts.get("t")
    received_sig = parts.get("v0")
    if not timestamp or not received_sig:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(int(datetime.utcnow().timestamp()) - ts) > WEBHOOK_TIMESTAMP_TOLERANCE:
        return False
    payload = f"{timestamp}.".encode("utf-8") + raw_body
    expected = hmac.new(
        ELEVENLABS_WEBHOOK_SECRET.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_sig)


# ── Persistence ──────────────────────────────────────────────────────────────

def _persist_call(db: Session, payload: dict) -> Optional[CallRecord]:
    data = payload.get("data") or {}
    conv_id = data.get("conversation_id") or payload.get("conversation_id")
    if not conv_id:
        logger.error("Webhook missing conversation_id; payload keys=%s", list(payload.keys()))
        return None

    existing = db.query(CallRecord).filter(CallRecord.call_sid == conv_id).first()
    if existing and existing.recap_sent:
        logger.info("Recap already sent for %s — skipping", conv_id)
        return existing

    metadata = data.get("metadata") or {}
    phone_meta = metadata.get("phone_call") or {}
    from_number = phone_meta.get("external_number") or phone_meta.get("caller_id") or ""
    to_number = phone_meta.get("agent_number") or ""

    started_at = datetime.utcnow()
    if metadata.get("start_time_unix_secs"):
        try:
            started_at = datetime.utcfromtimestamp(int(metadata["start_time_unix_secs"]))
        except (TypeError, ValueError):
            pass

    analysis = data.get("analysis") or {}
    collected = {}
    dcr = analysis.get("data_collection_results") or {}
    for key, val in dcr.items():
        if isinstance(val, dict) and val.get("value"):
            collected[key] = str(val["value"])
        elif isinstance(val, str):
            collected[key] = val

    if existing:
        call = existing
        call.collected = json_dump(collected)
        call.from_number = from_number or call.from_number
        call.to_number = to_number or call.to_number
    else:
        call = CallRecord(
            call_sid=conv_id,
            from_number=from_number,
            to_number=to_number,
            status="completed",
            collected=json_dump(collected),
            started_at=started_at,
        )
        db.add(call)
        db.flush()

    duration = metadata.get("call_duration_secs")
    if duration:
        try:
            call.ended_at = datetime.utcfromtimestamp(
                int(metadata.get("start_time_unix_secs", 0)) + int(duration)
            )
        except (TypeError, ValueError):
            call.ended_at = datetime.utcnow()
    else:
        call.ended_at = datetime.utcnow()

    db.query(CallTurn).filter(CallTurn.call_id == call.id).delete()
    transcript = data.get("transcript") or []
    for i, turn in enumerate(transcript):
        role = "ai" if turn.get("role") in ("agent", "assistant") else "caller"
        text = (turn.get("message") or "").strip()
        if not text:
            continue
        db.add(CallTurn(call_id=call.id, turn_index=i, role=role, text=text))

    eleven_summary = analysis.get("transcript_summary")
    if eleven_summary:
        call.summary = eleven_summary

    db.commit()
    db.refresh(call)
    return call


# ── Summary + email recap ────────────────────────────────────────────────────

def _summarize_call(call: CallRecord) -> str:
    transcript = "\n".join(
        f"{'AI' if t.role == 'ai' else 'CALLER'}: {t.text}" for t in call.turns
    )
    if not transcript.strip():
        return "(no conversation captured)"
    prompt = (
        "Below is a transcript of a call answered by Ray Ahmadi's AI receptionist. "
        "Write a 3–5 line recap for Ray covering: caller's name, callback number, "
        "reason for the call, anything else useful, and a recommended next step. "
        "Plain text, no markdown.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )
    try:
        return _call_claude(prompt, fast=True).strip()
    except Exception as e:
        logger.error("Claude summary failed: %s", e)
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
    name = collected.get("name") or collected.get("caller_name") or "Unknown caller"
    reason = collected.get("reason") or collected.get("topic") or "(not stated)"
    callback = (
        collected.get("callback")
        or collected.get("phone")
        or collected.get("callback_number")
        or call.from_number
        or "(unknown)"
    )

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
        logger.info("Recap emailed to %s for call %s", to_email, call.call_sid)
        return {"ok": True}
    except Exception as e:
        logger.error("Recap email failed: %s", e)
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
            f"{xml_escape(line)}</td></tr><tr><td style=\"height:6px;\"></td></tr>"
        )

    other_html = ""
    skip = {"name", "caller_name", "callback", "callback_number", "phone", "reason", "topic"}
    for k, v in collected.items():
        if k in skip or not v:
            continue
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


# ── Webhook route ────────────────────────────────────────────────────────────

@router.post("/elevenlabs/post-call")
async def elevenlabs_post_call(request: Request):
    """Receive ElevenLabs post-call webhook, persist, and email recap."""
    raw = await request.body()
    sig = request.headers.get("ElevenLabs-Signature", "") or request.headers.get("elevenlabs-signature", "")
    if not _validate_elevenlabs_signature(raw, sig):
        return PlainTextResponse("Invalid signature", status_code=403)

    try:
        payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return PlainTextResponse("Invalid JSON", status_code=400)

    event_type = payload.get("type", "")
    if event_type and event_type != "post_call_transcription":
        logger.info("Ignoring ElevenLabs event type=%s", event_type)
        return JSONResponse({"ok": True, "ignored": event_type})

    db = SessionLocal()
    try:
        call = _persist_call(db, payload)
        if not call:
            return JSONResponse({"ok": False, "error": "could not persist call"}, status_code=400)
        if call.recap_sent:
            return JSONResponse({"ok": True, "already_sent": True})

        if not call.summary:
            call.summary = _summarize_call(call)
            db.commit()

        result = _send_recap_email(call)
        call.recap_sent = bool(result.get("ok"))
        db.commit()
        return JSONResponse({"ok": True, "email": result, "conversation_id": call.call_sid})
    finally:
        db.close()


# ── Debug ────────────────────────────────────────────────────────────────────

@router.get("/calls")
def list_calls(db: Session = Depends(get_db)):
    """Return the last 25 calls as JSON for quick inspection."""
    calls = db.query(CallRecord).order_by(CallRecord.started_at.desc()).limit(25).all()
    return [
        {
            "conversation_id": c.call_sid,
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
