"""Deal deadline reminders.

Deadlines (irrevocability, closing, condition expiries) are collected during
the AI conversation but were previously never used. This module turns them
into persisted `Reminder` rows at generation time, and provides the hourly
sweep job that DMs the user when a reminder comes due.

Design notes:
- Reminders are DB-backed (not individually scheduled jobs) so they survive
  container restarts. One `run_repeating` sweep sends whatever is due.
- Deal dates are interpreted in America/Toronto and stored as naive UTC,
  matching the storage convention in `db.models.Reminder`.
- This module must stay importable without python-telegram-bot installed
  (unit tests import `build_reminders` directly), so there are no top-level
  telegram imports.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from forms.formatting import parse_date

logger = logging.getLogger(__name__)

LOCAL_TZ = ZoneInfo("America/Toronto")

# How far before each deadline to notify.
REMINDER_OFFSETS = (timedelta(hours=48), timedelta(hours=24))

# Default deadline time-of-day when the deal data has a date but no time.
# Irrevocability and conditions conventionally expire at 11:59 p.m.;
# closings happen during business hours.
DEFAULT_TIMES = {
    "irrevocability": time(23, 59),
    "closing": time(9, 0),
    "condition": time(23, 59),
}

KIND_TITLES = {
    "irrevocability": "Irrevocability",
    "closing": "Closing",
    "condition": "Condition",
}

_TIME_RE = re.compile(
    r"^\s*(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s*\.?m?\.?\s*$", re.IGNORECASE
)
_TIME_24_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*$")


def parse_time_of_day(value) -> time | None:
    """Parse '5 PM', '5:00 p.m.', '11:59pm', or '17:00' into a time.

    Returns None when the value can't be understood.
    """
    if isinstance(value, time):
        return value
    if not isinstance(value, str) or not value.strip():
        return None

    m = _TIME_RE.match(value)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        meridiem = m.group(3).lower()
        if not (1 <= hour <= 12 and 0 <= minute <= 59):
            return None
        if meridiem == "p" and hour != 12:
            hour += 12
        elif meridiem == "a" and hour == 12:
            hour = 0
        return time(hour, minute)

    m = _TIME_24_RE.match(value)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)

    return None


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_naive_utc(local_dt: datetime) -> datetime:
    """Convert a naive local (America/Toronto) datetime to naive UTC."""
    return (
        local_dt.replace(tzinfo=LOCAL_TZ).astimezone(timezone.utc).replace(tzinfo=None)
    )


def property_label(deal_data: dict) -> str:
    """Short human label for the property, e.g. '123 Main St, Toronto'."""
    addr = " ".join(
        str(deal_data.get(k) or "").strip()
        for k in ("property_street_number", "property_street_name")
    ).strip()
    city = str(deal_data.get("property_city") or "").strip()
    if addr and city:
        return f"{addr}, {city}"
    return addr or city or "your deal"


def _collect_deadlines(deal_data: dict) -> list[tuple[str, str, datetime]]:
    """Extract (kind, title, local naive deadline datetime) from deal data."""
    deadlines: list[tuple[str, str, datetime]] = []

    # Irrevocability — date plus optional explicit time.
    irrev = parse_date(deal_data.get("irrevocability_date"))
    if irrev:
        tod = parse_time_of_day(deal_data.get("irrevocability_time")) or DEFAULT_TIMES["irrevocability"]
        deadlines.append(
            ("irrevocability", KIND_TITLES["irrevocability"], datetime.combine(irrev.date(), tod))
        )

    # Closing.
    closing = parse_date(deal_data.get("closing_date"))
    if closing:
        deadlines.append(
            ("closing", KIND_TITLES["closing"], datetime.combine(closing.date(), DEFAULT_TIMES["closing"]))
        )

    # Condition expiry dates: any key like 'financing_condition_date'.
    for key, value in deal_data.items():
        m = re.match(r"^(.+)_condition_date$", key)
        if not m:
            continue
        dt = parse_date(value)
        if not dt:
            continue
        name = m.group(1).replace("_", " ").title()
        deadlines.append(
            ("condition", f"{name} condition", datetime.combine(dt.date(), DEFAULT_TIMES["condition"]))
        )

    return deadlines


def build_reminders(
    deal_data: dict,
    tx_id: str | None,
    chat_id: int,
    now: datetime | None = None,
) -> list[dict]:
    """Build reminder rows (dicts matching db.models.Reminder columns).

    For each deadline found in the deal data, emits one row per offset in
    REMINDER_OFFSETS whose notify time is still in the future. Deadlines that
    are entirely in the past produce nothing.
    """
    now = now or _utcnow_naive()
    prop = property_label(deal_data)

    rows: list[dict] = []
    for kind, title, local_deadline in _collect_deadlines(deal_data):
        deadline_utc = _to_naive_utc(local_deadline)
        if deadline_utc <= now:
            continue
        for offset in REMINDER_OFFSETS:
            notify_at = deadline_utc - offset
            if notify_at <= now:
                continue
            rows.append({
                "telegram_chat_id": chat_id,
                "transaction_id": tx_id,
                "kind": kind,
                "label": f"{title} — {prop}",
                "deadline_at": deadline_utc,
                "notify_at": notify_at,
            })
    return rows


def format_deadline_local(deadline_utc: datetime) -> str:
    """Render a naive-UTC deadline as a friendly America/Toronto string."""
    local = deadline_utc.replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
    return local.strftime("%b %d, %Y at %I:%M %p").replace(" 0", " ")


def _hours_remaining(deadline_utc: datetime, now: datetime) -> int:
    return max(0, round((deadline_utc - now).total_seconds() / 3600))


async def reminder_sweep(context) -> None:
    """JobQueue callback: send every due reminder, then mark it sent.

    Each reminder is handled independently — one failed send (e.g. a blocked
    bot) must not stall the rest of the sweep.
    """
    from db.operations import get_due_reminders, mark_reminder_sent

    now = _utcnow_naive()
    due = await get_due_reminders(now)
    if not due:
        return

    logger.info("reminder_sweep: %d reminder(s) due", len(due))
    for reminder in due:
        try:
            hours = _hours_remaining(reminder.deadline_at, now)
            when = format_deadline_local(reminder.deadline_at)
            if hours > 0:
                text = f"⏰ *Deadline reminder*\n\n{reminder.label}\nExpires in ~{hours}h — {when}"
            else:
                text = f"⏰ *Deadline reminder*\n\n{reminder.label}\nDeadline: {when}"
            await context.bot.send_message(
                chat_id=reminder.telegram_chat_id,
                text=text,
                parse_mode="Markdown",
            )
            await mark_reminder_sent(reminder.id)
        except Exception:
            logger.exception("Failed to send reminder %s", reminder.id)
