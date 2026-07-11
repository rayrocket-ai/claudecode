"""Follow-up / escalation cadence — pure, testable timing logic.

Follow-ups are DB-driven: the recurring scan reads each task's
`next_followup_at`, sends a reminder, then calls these helpers to compute the
next reminder time and to decide when to escalate to a manager. Keeping the
math here (no I/O) makes it unit-testable.

Cadence is anchored on the "standard" tier (configurable via
`task_followup_hours` / `task_escalate_hours`); high/low are scaled from it:

    high     ~1/4 the follow-up gap, escalate much sooner
    standard  the configured gap
    low       much longer gap, escalate later
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Multipliers applied to the standard-tier hours to derive each urgency tier.
_FOLLOWUP_MULTIPLIER = {"high": 0.25, "standard": 1.0, "low": 6.0}
_ESCALATE_MULTIPLIER = {"high": 0.17, "standard": 1.0, "low": 3.0}

# Minimum floor so an aggressive config can't produce sub-minute nagging.
_MIN_HOURS = 1.0 / 60.0  # 1 minute


def _to_naive_utc(dt: datetime) -> datetime:
    """Normalize to naive UTC.

    SQLite returns naive datetimes while `datetime.now(timezone.utc)` is aware;
    subtracting the two raises. We collapse everything to naive UTC so the
    arithmetic is consistent regardless of source.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def now_utc() -> datetime:
    """Naive UTC 'now' — matches how datetimes come back from SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def cadence_for(
    urgency: str,
    followup_hours: float = 4.0,
    escalate_hours: float = 24.0,
) -> tuple[float, float]:
    """Return (followup_gap_hours, escalate_after_hours) for an urgency tier."""
    u = (urgency or "standard").lower()
    fu = followup_hours * _FOLLOWUP_MULTIPLIER.get(u, 1.0)
    esc = escalate_hours * _ESCALATE_MULTIPLIER.get(u, 1.0)
    return max(fu, _MIN_HOURS), max(esc, _MIN_HOURS)


def initial_followup_at(
    *,
    now: datetime,
    due_at: datetime | None,
    urgency: str,
    followup_hours: float = 4.0,
    escalate_hours: float = 24.0,
) -> datetime:
    """When to send the FIRST reminder after a task is assigned.

    If a due date is set and still in the future, nudge at the due time.
    Otherwise (no due date, or already past due) start one gap from now.
    """
    now = _to_naive_utc(now)
    gap_hours, _ = cadence_for(urgency, followup_hours, escalate_hours)
    if due_at is not None:
        due_at = _to_naive_utc(due_at)
        if due_at > now:
            return due_at
    return now + timedelta(hours=gap_hours)


def next_followup_at(
    *,
    now: datetime,
    urgency: str,
    followup_hours: float = 4.0,
    escalate_hours: float = 24.0,
) -> datetime:
    """When to send the NEXT reminder, one gap from now."""
    now = _to_naive_utc(now)
    gap_hours, _ = cadence_for(urgency, followup_hours, escalate_hours)
    return now + timedelta(hours=gap_hours)


def should_escalate(
    *,
    now: datetime,
    created_at: datetime,
    urgency: str,
    already_escalated: bool,
    followup_hours: float = 4.0,
    escalate_hours: float = 24.0,
) -> bool:
    """True when an unresolved task has aged past its escalation window.

    Escalation happens once per task (the caller sets `escalated=True`).
    """
    if already_escalated:
        return False
    now = _to_naive_utc(now)
    created_at = _to_naive_utc(created_at)
    _, escalate_after = cadence_for(urgency, followup_hours, escalate_hours)
    return now - created_at >= timedelta(hours=escalate_after)
