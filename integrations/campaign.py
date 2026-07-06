"""Listing Launch campaign orchestrator.

Takes a drafted campaign (from ai.listing_agent) and delivers each asset
through whatever channel is configured. Every channel follows the same
defensive contract as the rest of integrations/ (see mls.py, delivery.py):
it never raises on a missing/failed provider — it returns a ChannelResult so
one broken channel can't sink the whole launch.

Delivery status vocabulary (ChannelResult.status):
  "sent"        — actually delivered to an external service
  "drafted"     — content is ready to paste; no direct provider wired/configured
  "skipped"     — nothing to do (the agent didn't produce this asset)
  "failed"      — a configured provider errored

Wiring more providers later: each `run_*` function is the single seam for its
channel. To send blasts through Boosend or generate a Gamma feature sheet
directly, implement the HTTP call inside that function guarded by the
corresponding settings flag (boosend_api_key / gamma_api_key /
higgsfield_api_key) and return status="sent". Nothing else changes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from config import get_settings
from integrations.delivery import send_email

logger = logging.getLogger(__name__)


@dataclass
class ChannelResult:
    """Outcome of a single marketing channel."""

    channel: str
    status: str  # sent | drafted | skipped | failed
    detail: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in ("sent", "drafted")


# ── Individual channels ───────────────────────────────────────────


async def run_feature_sheet(campaign: dict[str, Any]) -> ChannelResult:
    """Produce a one-page feature sheet.

    Direct Gamma generation is a future add-on (gamma_api_key); until then the
    structured sheet content is handed back ready to paste into Gamma/Canva.
    """
    sheet = campaign.get("feature_sheet")
    if not sheet:
        return ChannelResult("feature_sheet", "skipped", "No feature sheet drafted")

    settings = get_settings()
    if settings.gamma_api_key:
        # Placeholder seam for direct Gamma generation.
        logger.info("Gamma key present but direct generation not yet wired")

    highlights = sheet.get("highlights") or []
    return ChannelResult(
        "feature_sheet",
        "drafted",
        f"Feature sheet ready ({len(highlights)} highlights) — paste into Gamma/Canva",
        payload=sheet,
    )


async def run_reel(campaign: dict[str, Any]) -> ChannelResult:
    """Produce a vertical property reel script (and, later, the video)."""
    reel = campaign.get("reel_script")
    if not reel:
        return ChannelResult("reel", "skipped", "No reel script drafted")

    settings = get_settings()
    if settings.higgsfield_api_key:
        logger.info("Higgsfield key present but direct generation not yet wired")

    shots = reel.get("shots") or []
    return ChannelResult(
        "reel",
        "drafted",
        f"Reel script ready ({len(shots)} shots) — generate in Higgsfield",
        payload=reel,
    )


async def run_email_blast(
    campaign: dict[str, Any],
    recipients: list[str] | None = None,
) -> ChannelResult:
    """Send the 'just listed' email blast.

    Actually delivers via the existing SMTP path (integrations.delivery) when
    recipients + SMTP are available; otherwise returns the drafted email.
    """
    email = campaign.get("email")
    if not email or not email.get("body_html"):
        return ChannelResult("email", "skipped", "No email drafted")

    settings = get_settings()
    subject = email.get("subject") or "New Listing"
    body = email.get("body_html", "")

    if recipients and settings.is_smtp_configured:
        try:
            sent = await send_email(to=recipients, subject=subject, body=body)
        except Exception as e:  # never let a channel crash the launch
            logger.exception("Email blast failed: %s", e)
            return ChannelResult("email", "failed", str(e), payload=email)
        if sent:
            return ChannelResult(
                "email", "sent", f"Blast sent to {len(recipients)} recipient(s)",
                payload=email,
            )
        return ChannelResult("email", "failed", "SMTP send returned False", payload=email)

    reason = "no recipients given" if not recipients else "SMTP not configured"
    return ChannelResult("email", "drafted", f"Email ready ({reason})", payload=email)


async def run_sms_blast(campaign: dict[str, Any]) -> ChannelResult:
    """Prepare the 'just listed' SMS (direct send via Boosend is a future add-on)."""
    sms = campaign.get("sms")
    if not sms:
        return ChannelResult("sms", "skipped", "No SMS drafted")

    settings = get_settings()
    if settings.boosend_api_key:
        logger.info("Boosend key present but direct SMS send not yet wired")

    return ChannelResult("sms", "drafted", f"SMS ready ({len(sms)} chars)", payload={"text": sms})


def build_open_house_ics(campaign: dict[str, Any], start: datetime | None = None) -> str | None:
    """Build an .ics calendar invite for the open house, if one was drafted.

    Returns iCalendar text, or None if there's nothing to schedule. Kept pure
    (no I/O) so it's trivially testable.
    """
    oh = campaign.get("open_house")
    if not oh:
        return None

    settings = get_settings()
    start = start or (datetime.now(timezone.utc) + timedelta(days=3)).replace(
        hour=18, minute=0, second=0, microsecond=0
    )
    duration = max(15, int(settings.marketing_open_house_duration or 120))
    end = start + timedelta(minutes=duration)

    fmt = "%Y%m%dT%H%M%SZ"
    title = oh.get("title", "Open House")
    description = oh.get("description", "")
    time_hint = oh.get("time_range") or oh.get("day_of_week") or ""
    if time_hint:
        description = f"{description}\\nSuggested time: {time_hint}".strip()

    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//AI Realtor Assistant//Listing Launch//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART:{start.strftime(fmt)}\r\n"
        f"DTEND:{end.strftime(fmt)}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{description}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


async def run_open_house(campaign: dict[str, Any]) -> ChannelResult:
    """Prepare the open-house calendar invite."""
    ics = build_open_house_ics(campaign)
    if ics is None:
        return ChannelResult("open_house", "skipped", "No open house drafted")
    oh = campaign["open_house"]
    when = " ".join(x for x in (oh.get("day_of_week"), oh.get("time_range")) if x)
    return ChannelResult(
        "open_house", "drafted",
        f"Open-house invite ready{f' ({when})' if when else ''}",
        payload={"ics": ics, **oh},
    )


# ── Top-level launch ──────────────────────────────────────────────

# Order controls how results are presented back to the agent.
_CHANNELS = ("feature_sheet", "reel", "email", "sms", "open_house")


async def launch_campaign(
    campaign: dict[str, Any],
    recipients: list[str] | None = None,
    channels: list[str] | None = None,
) -> list[ChannelResult]:
    """Run every requested channel and return their results.

    Channels run independently; a failure in one is captured as a "failed"
    ChannelResult, never an exception, so the launch always completes.
    """
    selected = channels or list(_CHANNELS)
    results: list[ChannelResult] = []

    for channel in selected:
        try:
            if channel == "feature_sheet":
                results.append(await run_feature_sheet(campaign))
            elif channel == "reel":
                results.append(await run_reel(campaign))
            elif channel == "email":
                results.append(await run_email_blast(campaign, recipients))
            elif channel == "sms":
                results.append(await run_sms_blast(campaign))
            elif channel == "open_house":
                results.append(await run_open_house(campaign))
            else:
                logger.warning("Unknown campaign channel: %s", channel)
        except Exception as e:  # defense in depth — should not happen
            logger.exception("Channel %s crashed: %s", channel, e)
            results.append(ChannelResult(channel, "failed", str(e)))

    return results
