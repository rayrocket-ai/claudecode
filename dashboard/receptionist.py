"""AI Receptionist — receives Vapi end-of-call webhook, emails recap to Ray.

Architecture
    Caller dials Vapi phone number → Vapi assistant handles voice + STT + reasoning
    (system prompt lives in the Vapi dashboard). When the call ends, Vapi POSTs an
    "end-of-call-report" message to /voice/vapi/webhook. We persist the transcript
    + recording URL, run a Claude recap if Vapi's own summary is missing, and email
    Ray at RECEPTIONIST_EMAIL.

Required env vars
    VAPI_SECRET               Shared secret set on the Vapi assistant's Server URL.
                              Vapi sends it as X-Vapi-Secret on every webhook.
    RECEPTIONIST_EMAIL        Where the recap is sent.
    SMTP_HOST/PORT/USER/PASS  Reused from digest_email.
    ANTHROPIC_API_KEY         For the Claude recap pass.
"""

from __future__ import annotations

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

VAPI_SECRET = os.getenv("VAPI_SECRET", "")
RECEPTIONIST_EMAIL = os.getenv("RECEPTIONIST_EMAIL", "")


# ── Auth ────────────────────────────────────────────────────────────────

def _authorized(request: Request) -> bool:
    """Vapi sends the configured Server URL Secret as X-Vapi-Secret."""
    if not VAPI_SECRET:
        logger.warning("VAPI_SECRET not set — webhook auth disabled")
        return True
    sent = request.headers.get("x-vapi-secret") or request.headers.get("X-Vapi-Secret") or ""
    return bool(sent) and hmac.compare_digest(sent, VAPI_SECRET)


# ── Payload helpers ───────────────────────────────────────────────────────────

def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def _extract_collected(analysis: dict) -> dict:
    """Vapi puts assistant-extracted fields under analysis.structuredData."""
    raw = analysis.get("structuredData") or analysis.get("structured_data") or {}
    if not isinstance(raw, dict):
        return {}
    collected = {}
    for k, v in raw.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            s = str(v).strip()
            if s:
                collected[k] = s
        elif isinstance(v, dict) and "value" in v:
            s = str(v["value"]).strip()
            if s:
                collected[k] = s
    return collected


def _extract_turns(artifact: dict) -> list[tuple[str, str]]:
    """Return [(role, text), ...] where role is 'ai' or 'caller'."""
    messages = artifact.get("messages") or []
    turns = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role_raw = (m.get("role") or "").lower()
        text = (m.get("message") or m.get("content") or "").strip()
        if not text or role_raw in ("system", "tool", "function"):
            continue
        role = "caller" if role_raw == "user" else "ai"
        turns.append((role, text))
    if turns:
        return turns
    # Fallback: some payloads only include a flat transcript string
    transcript = (artifact.get("transcript") or "").strip()
    if transcript:
        for line in transcript.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                who, text = line.split(":", 1)
                role = "caller" if who.strip().lower() in ("user", "customer", "caller") else "ai"
                turns.append((role, text.strip()))
    return turns


# ── Persistence ──────────────────────────────────────────────────────────────

def _persist_call(db: Session, message: dict) -> Optional[CallRecord]:
    call_obj = message.get("call") or {}
    conv_id = call_obj.get("id") or message.get("callId")
    if not conv_id:
        logger.error("Vapi webhook missing call.id; message keys=%s", list(message.keys()))
        return None

    existing = db.query(CallRecord).filter(CallRecord.call_sid == conv_id).first()
    if existing and existing.recap_sent:
        logger.info("Recap already sent for %s — skipping", conv_id)
        return existing

    customer = call_obj.get("customer") or {}
    phone_meta = call_obj.get("phoneNumber") or {}
    from_number = customer.get("number") or ""
    to_number = phone_meta.get("number") or ""

    started_at = (
        _parse_iso(message.get("startedAt"))
        or _parse_iso(call_obj.get("startedAt"))
        or _parse_iso(call_obj.get("createdAt"))
        or datetime.utcnow()
    )
    ended_at = _parse_iso(message.get("endedAt")) or datetime.utcnow()

    artifact = message.get("artifact") or {}
    analysis = message.get("analysis") or {}
    collected = _extract_collected(analysis)
    recording_url = artifact.get("recordingUrl") or artifact.get("stereoRecordingUrl")
    ended_reason = message.get("endedReason") or "completed"

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
            status=ended_reason,
            collected=json_dump(collected),
            started_at=started_at,
        )
        db.add(call)
        db.flush()

    call.status = ended_reason
    call.ended_at = ended_at
    call.recording_url = recording_url

    db.query(CallTurn).filter(CallTurn.call_id == call.id).delete()
    for i, (role, text) in enumerate(_extract_turns(artifact)):
        db.add(CallTurn(call_id=call.id, turn_index=i, role=role, text=text))

    vapi_summary = analysis.get("summary")
    if vapi_summary:
        call.summary = vapi_summary

    db.commit()
    db.refresh(call)
    return call


# ── Summary + email recap ───────────────────────────────────────────────────────

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
        or collected.get("callback_number")
        or collected.get("phone")
        or call.from_number
        or "(unknown)"
    )

    transcript_lines = [
        f"{'AI ' if t.role == 'ai' else 'You'}: {t.text}" for t in call.turns
    ]
    transcript = "\n".join(transcript_lines)

    subject = f"📞 Missed call recap — {name} ({reason[:40]})"

    plain_parts = [
        f"Caller: {name}",
        f"Callback: {callback}",
        f"Reason: {reason}",
        f"Other: {collected.get('other', '')}",
        f"Started: {call.started_at:%Y-%m-%d %H:%M UTC}",
        f"Status: {call.status}",
    ]
    if call.recording_url:
        plain_parts.append(f"Recording: {call.recording_url}")
    plain_parts.extend([
        "",
        "--- Recap ---",
        call.summary or "(none)",
        "",
        "--- Full transcript ---",
        transcript,
    ])
    plain = "\n".join(plain_parts) + "\n"

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

    recording_html = ""
    if call.recording_url:
        recording_html = (
            f'<tr><td style="padding:16px 0 0 0;">'
            f'<a href="{xml_escape(call.recording_url)}" '
            f'style="display:inline-block;background:#1a1a1a;color:#f97316;font-size:13px;'
            f'font-weight:700;text-decoration:none;padding:10px 18px;border-radius:8px;'
            f'border:1px solid #f97316;">▶ Play call recording</a></td></tr>'
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
      {recording_html}
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


# ── Webhook route ─────────────────────────────────────────────────────────────

@router.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """Receive Vapi server messages. We only act on end-of-call-report."""
    if not _authorized(request):
        return PlainTextResponse("Forbidden", status_code=403)

    try:
        payload: dict[str, Any] = await request.json()
    except json.JSONDecodeError:
        return PlainTextResponse("Invalid JSON", status_code=400)

    message = payload.get("message") or {}
    msg_type = message.get("type", "")
    if msg_type != "end-of-call-report":
        logger.info("Ignoring Vapi event type=%s", msg_type)
        return JSONResponse({"ok": True, "ignored": msg_type})

    db = SessionLocal()
    try:
        call = _persist_call(db, message)
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
        return JSONResponse({"ok": True, "email": result, "call_id": call.call_sid})
    finally:
        db.close()


# ── Debug ─────────────────────────────────────────────────────────────────────

@router.get("/calls")
def list_calls(db: Session = Depends(get_db)):
    """Return the last 25 calls as JSON for quick inspection."""
    calls = db.query(CallRecord).order_by(CallRecord.started_at.desc()).limit(25).all()
    return [
        {
            "call_id": c.call_sid,
            "from": c.from_number,
            "status": c.status,
            "collected": c.collected_dict(),
            "summary": c.summary,
            "recording_url": c.recording_url,
            "recap_sent": c.recap_sent,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "turns": [{"role": t.role, "text": t.text} for t in c.turns],
        }
        for c in calls
    ]
