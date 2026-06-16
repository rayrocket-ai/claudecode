"""Shared formatting / normalization helpers for deal data.

These were previously duplicated inside ``integrations.transactiondesk`` and
``ai.agent``. They are pure functions with no heavy dependencies (stdlib +
python-dateutil), so they can be imported and unit-tested without pulling in
Playwright, the Anthropic SDK, or Telegram.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

__all__ = [
    "normalize_number",
    "format_currency",
    "num_to_words",
    "dollars_to_words",
    "parse_date",
    "date_parts",
]


def normalize_number(value: Any) -> float:
    """Convert a price/number (string, int, or float) to a float.

    Strips ``$``, commas, and whitespace. Returns ``0.0`` for anything that
    cannot be parsed (never raises) so callers can validate the result.
    """
    if isinstance(value, bool):  # bool is an int subclass — reject explicitly
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[,$\s]", "", value)
        if cleaned in ("", "-", "."):
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def format_currency(value: Any) -> str:
    """Format a number as a currency string with thousands separators.

    e.g. ``800000`` -> ``"800,000.00"``. The ``$`` is intentionally omitted so
    callers can place it where the form/template expects.
    """
    return f"{normalize_number(value):,.2f}"


_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
    "Eighty", "Ninety",
]
_SCALES = [(1_000_000_000, "Billion"), (1_000_000, "Million"), (1_000, "Thousand")]


def _chunk_to_words(num: int) -> str:
    """Convert an integer 0-999 to English words."""
    if num == 0:
        return ""
    if num < 20:
        return _ONES[num]
    if num < 100:
        return _TENS[num // 10] + (" " + _ONES[num % 10] if num % 10 else "")
    return _ONES[num // 100] + " Hundred" + (
        " " + _chunk_to_words(num % 100) if num % 100 else ""
    )


def num_to_words(n: int) -> str:
    """Convert a non-negative integer to English words (Title Case).

    Examples::

        num_to_words(0)       -> "Zero"
        num_to_words(800000)  -> "Eight Hundred Thousand"
        num_to_words(1250000) -> "One Million Two Hundred Fifty Thousand"
    """
    n = int(n)
    if n < 0:
        return "Negative " + num_to_words(-n)
    if n == 0:
        return "Zero"

    parts: list[str] = []
    for scale, name in _SCALES:
        if n >= scale:
            parts.append(_chunk_to_words(n // scale) + " " + name)
            n %= scale
    if n > 0:
        parts.append(_chunk_to_words(n))
    return " ".join(parts)


def dollars_to_words(value: Any) -> str:
    """Render a currency amount as the words used on OREA forms.

    Whole dollars are spelled out; any cents are appended as
    ``"... and 50/100"`` which matches the convention used in the price/deposit
    word fields. ``$800,000`` -> ``"Eight Hundred Thousand"``;
    ``1250.50`` -> ``"One Thousand Two Hundred Fifty and 50/100"``.
    """
    amount = normalize_number(value)
    dollars = int(amount)
    cents = int(round((amount - dollars) * 100))
    # Guard against floating point rounding pushing cents to 100.
    if cents >= 100:
        dollars += 1
        cents -= 100
    words = num_to_words(dollars)
    if cents:
        words += f" and {cents:02d}/100"
    return words


_DATE_FORMATS = (
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y",
    "%B %d %Y", "%b %d %Y", "%Y/%m/%d",
)


def parse_date(date_str: Any) -> Optional[datetime]:
    """Parse a date string into a ``datetime``. Returns ``None`` if unparseable.

    Tries a set of common explicit formats first, then falls back to
    ``dateutil`` (day-first disabled so ``03/04/2026`` is March 4, matching the
    North-American convention used throughout these forms).
    """
    if isinstance(date_str, datetime):
        return date_str
    if not isinstance(date_str, str):
        return None
    s = date_str.strip()
    if not s:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    try:
        from dateutil.parser import parse as _parse
        return _parse(s, dayfirst=False)
    except Exception:
        return None


def date_parts(date_str: Any) -> tuple[str, str, str]:
    """Return ``(day, month_name, year)`` for a date string.

    Falls back to ``(original_string, "", "")`` when the date cannot be parsed,
    preserving the previous behaviour of the form-filling code.
    """
    dt = parse_date(date_str)
    if dt is None:
        return (str(date_str).strip() if date_str else "", "", "")
    return (str(dt.day), dt.strftime("%B"), str(dt.year))
