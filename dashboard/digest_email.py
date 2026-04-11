"""Daily script digest emailer for Ray's Content Engine.

Usage:
    from .digest_email import send_daily_digest
    send_daily_digest(to_email, profile, scripts)

Env vars required:
    SMTP_HOST  - e.g. smtp.gmail.com
    SMTP_PORT  - e.g. 587 (default)
    SMTP_USER  - sender email address
    SMTP_PASS  - SMTP password / app password
    DIGEST_EMAIL - recipient email (used by the /api/send-digest endpoint)
"""

import os
import smtplib
import logging
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# Dashboard public URL (shown at the bottom of the email)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8000")


def _first_n_sentences(text: str, n: int = 2) -> str:
    """Return the first n sentences from a block of text."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:n]) if sentences else text[:200]


def build_html(profile, scripts, today_str: str) -> str:
    """Build the HTML email body."""

    script_cards = ""
    for i, script in enumerate(scripts, 1):
        body_preview = _first_n_sentences(script.body, 2)
        hook_html = script.hook.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body_html = body_preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        cta_html = script.cta.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        title_html = script.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Script type badge colour (email-safe inline)
        type_colour_map = {
            "market": "#3b82f6",
            "mortgage": "#8b5cf6",
            "personal": "#ec4899",
            "client_win": "#22c55e",
            "trending": "#f59e0b",
        }
        badge_color = type_colour_map.get(getattr(script, "script_type", ""), "#6b7280")
        script_type = getattr(script, "script_type", "script").replace("_", " ").title()
        platform = getattr(script, "platform", "")
        duration = getattr(script, "estimated_duration_seconds", 0)
        script_id = getattr(script, "id", i)

        script_cards += f"""
        <tr>
          <td style="padding: 0 0 28px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#1a1a1a; border-radius:12px; overflow:hidden; border:1px solid #2a2a2a;">
              <tr>
                <td style="padding:20px 24px 16px 24px; border-bottom:1px solid #222;">
                  <!-- Meta badges -->
                  <span style="background:{badge_color}22; color:{badge_color}; font-size:11px;
                               font-weight:700; text-transform:uppercase; letter-spacing:1px;
                               padding:3px 10px; border-radius:4px; margin-right:8px;">{script_type}</span>
                  <span style="background:#1f1f1f; color:#888; font-size:11px;
                               padding:3px 10px; border-radius:4px; margin-right:8px;">{platform}</span>
                  <span style="background:#1f1f1f; color:#666; font-size:11px;
                               padding:3px 10px; border-radius:4px;">~{duration}s</span>
                </td>
              </tr>
              <tr>
                <td style="padding:20px 24px 0 24px;">
                  <!-- Title -->
                  <p style="margin:0 0 16px 0; font-size:18px; font-weight:700; color:#ffffff;
                             line-height:1.4;">{i}. {title_html}</p>
                  <!-- Hook -->
                  <p style="margin:0 0 4px 0; font-size:10px; font-weight:700; text-transform:uppercase;
                             letter-spacing:2px; color:#eab308;">HOOK</p>
                  <p style="margin:0 0 16px 0; font-size:15px; font-weight:700; color:#fde047;
                             line-height:1.5; font-style:italic;">&#8220;{hook_html}&#8221;</p>
                  <!-- Body preview -->
                  <p style="margin:0 0 4px 0; font-size:10px; font-weight:700; text-transform:uppercase;
                             letter-spacing:2px; color:#9ca3af;">BODY (preview)</p>
                  <p style="margin:0 0 16px 0; font-size:14px; color:#d1d5db; line-height:1.6;">{body_html}&#8230;</p>
                  <!-- CTA -->
                  <p style="margin:0 0 4px 0; font-size:10px; font-weight:700; text-transform:uppercase;
                             letter-spacing:2px; color:#22c55e;">CTA</p>
                  <p style="margin:0 0 20px 0; font-size:14px; color:#86efac; line-height:1.5;">{cta_html}</p>
                </td>
              </tr>
              <tr>
                <td style="padding:0 24px 20px 24px;">
                  <a href="{DASHBOARD_URL}/scripts/{script_id}/teleprompter"
                     style="display:inline-block; background:#f97316; color:#ffffff; font-size:13px;
                            font-weight:700; text-decoration:none; padding:8px 18px; border-radius:8px;">
                    🎤 Open in Teleprompter
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    profile_name = getattr(profile, "name", "Ray") if profile else "Ray"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Ray's Scripts for {today_str}</title>
</head>
<body style="margin:0; padding:0; background:#0a0a0a; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0a; min-height:100vh;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="640" cellpadding="0" cellspacing="0" border="0" style="max-width:640px; width:100%;">

          <!-- Header -->
          <tr>
            <td style="padding:0 0 32px 0; text-align:center;">
              <p style="margin:0 0 8px 0; font-size:28px; font-weight:800; color:#ffffff;">
                🎬 Ray's Scripts
              </p>
              <p style="margin:0; font-size:16px; color:#6b7280;">{today_str}</p>
              <p style="margin:8px 0 0 0; font-size:14px; color:#4b5563;">
                {len(scripts)} script{'s' if len(scripts) != 1 else ''} ready for {profile_name}
              </p>
            </td>
          </tr>

          <!-- Script cards -->
          {script_cards}

          <!-- Footer -->
          <tr>
            <td style="padding:16px 0 0 0; text-align:center; border-top:1px solid #1f1f1f;">
              <p style="margin:0 0 12px 0; font-size:13px; color:#4b5563;">
                View all scripts and generate new batches in your dashboard
              </p>
              <a href="{DASHBOARD_URL}"
                 style="display:inline-block; background:#1a1a1a; color:#f97316; font-size:13px;
                        font-weight:700; text-decoration:none; padding:10px 24px; border-radius:8px;
                        border:1px solid #f97316;">
                Open Dashboard →
              </a>
              <p style="margin:20px 0 0 0; font-size:12px; color:#374151;">
                Ray's Content Engine · Powered by DeepSeek + FastAPI
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html


def send_daily_digest(to_email: str, profile, scripts: list) -> dict:
    """Send a daily digest email with today's scripts.

    Returns a dict: {"ok": True} or {"ok": False, "error": str}
    """
    if not SMTP_USER or not SMTP_PASS:
        msg = "SMTP_USER or SMTP_PASS not configured"
        logger.error(msg)
        return {"ok": False, "error": msg}

    if not to_email:
        return {"ok": False, "error": "No recipient email provided"}

    today_str = date.today().strftime("%A, %B %d, %Y")
    subject = f"🎬 Ray's Scripts for {today_str}"

    html_body = build_html(profile, scripts, today_str)

    # Plain-text fallback
    plain_lines = [f"Ray's Scripts for {today_str}", "=" * 40]
    for i, s in enumerate(scripts, 1):
        plain_lines.append(f"\n{i}. {s.title}")
        plain_lines.append(f"HOOK: {s.hook}")
        plain_lines.append(f"CTA: {s.cta}")
    plain_lines.append(f"\nOpen dashboard: {DASHBOARD_URL}")
    plain_text = "\n".join(plain_lines)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        logger.info(f"Digest sent to {to_email} ({len(scripts)} scripts)")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Failed to send digest: {e}")
        return {"ok": False, "error": str(e)}
