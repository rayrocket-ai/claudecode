"""Tour summary formatter.

Builds the user-facing tour message per the spec:

    🏠 SHOWING TOUR — John & Sarah Smith
    📅 Tuesday, March 25, 2025
    🚀 Start: 123 Your Office Address
    ━━━━━━━━━━━━━━━━━━━━━━━
    1️⃣  456 Maple Ave, Richmond Hill
    🕙 10:00 AM – 10:25 AM
    💰 $1,299,000 | 📐 2,400 sqft | 🗓 Built 2008
    🔑 Access: Supra lockbox, code 1234
    👤 Agent: Jane Doe | 📞 416-555-1234
    🚗 Drive from start: 12 min
    ━━━━━━━━━━━━━━━━━━━━━━━
    ...
    ⏱ Total tour: ~2h 45min
    ✅ All showings confirmed
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from scheduler.optimizer import Tour

NUMBER_EMOJI = [
    "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣",
    "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
]
SEPARATOR = "━━━━━━━━━━━━━━━━━━━━━━━"


def number_emoji(n: int) -> str:
    """Return an emoji number (1-10) or plain number."""
    if 1 <= n <= 10:
        return NUMBER_EMOJI[n - 1]
    return f"*{n}*"


def format_price(price: Any) -> str:
    """Format price as $1,299,000."""
    if isinstance(price, (int, float)):
        return f"${int(price):,}"
    if isinstance(price, str) and price:
        return price if price.startswith("$") else f"${price}"
    return ""


def format_duration_minutes(minutes: int) -> str:
    """Format a minutes duration like '2h 45min' or '45 min'."""
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}min"


def format_tour_message(
    tour: Tour,
    client_name: str,
    date: datetime,
    confirmations: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Render a tour as a Telegram message using Markdown.

    Args:
        tour: The scheduled tour.
        client_name: Client(s) being toured.
        date: Tour date.
        confirmations: Optional dict mapping stop address → BrokerBay
                       booking confirmation details (price, sqft, agent, etc).
    """
    confirmations = confirmations or {}

    date_str = date.strftime("%A, %B %-d, %Y") if _supports_dash_format() else \
        date.strftime("%A, %B %d, %Y").replace(" 0", " ")

    lines: list[str] = [
        f"🏠 *SHOWING TOUR* — {client_name}",
        f"📅 {date_str}",
        f"🚀 Start: {tour.start_point.formatted_address or tour.start_point.address}",
        SEPARATOR,
    ]

    for stop in tour.stops:
        conf = confirmations.get(stop.address, {})
        lines.append(f"{number_emoji(stop.stop_number)}  *{stop.address}*")
        lines.append(f"🕙 {stop.time_range_str()}")

        price = format_price(conf.get("price"))
        sqft = conf.get("sqft")
        year = conf.get("yearBuilt") or conf.get("year_built")
        details = []
        if price:
            details.append(f"💰 {price}")
        if sqft:
            details.append(f"📐 {sqft:,} sqft" if isinstance(sqft, int) else f"📐 {sqft} sqft")
        if year:
            details.append(f"🗓 Built {year}")
        if details:
            lines.append(" | ".join(details))

        access = conf.get("accessInstructions") or conf.get("showingInstructions")
        if access:
            lines.append(f"🔑 Access: {access}")

        agent = conf.get("agentName")
        phone = conf.get("agentPhone")
        if agent or phone:
            agent_line = "👤 " + (agent or "")
            if phone:
                agent_line += f" | 📞 {phone}"
            lines.append(agent_line.strip())

        # Drive time
        if stop.stop_number == 1:
            lines.append(
                f"🚗 Drive from start: {stop.drive_minutes_from_previous} min"
            )
        else:
            lines.append(
                f"🚗 Drive from previous: {stop.drive_minutes_from_previous} min"
            )

        lines.append(SEPARATOR)

    if tour.stops:
        total = format_duration_minutes(tour.total_minutes + tour.stops[0].drive_minutes_from_previous)
        lines.append(f"⏱ Total tour: ~{total}")

    if tour.skipped_addresses:
        lines.append("")
        lines.append("⚠️ *Could not schedule:*")
        for addr in tour.skipped_addresses:
            lines.append(f"• {addr}")

    if confirmations and not tour.skipped_addresses:
        lines.append("✅ All showings confirmed")

    return "\n".join(lines)


def format_proposed_schedule(tour: Tour, client_name: str, date: datetime) -> str:
    """Render the tour proposal (before booking) for user confirmation."""
    date_str = date.strftime("%A, %B %-d, %Y") if _supports_dash_format() else \
        date.strftime("%A, %B %d, %Y").replace(" 0", " ")

    lines = [
        f"📋 *Proposed Tour* — {client_name}",
        f"📅 {date_str}",
        SEPARATOR,
    ]

    for stop in tour.stops:
        drive_note = (
            "from start" if stop.stop_number == 1 else "from previous"
        )
        lines.append(
            f"{number_emoji(stop.stop_number)} {stop.address}\n"
            f"   🕙 {stop.time_range_str()}  "
            f"🚗 {stop.drive_minutes_from_previous} min {drive_note}"
        )

    lines.append(SEPARATOR)
    if tour.stops:
        lines.append(f"⏱ ~{format_duration_minutes(tour.total_minutes)}")

    if tour.skipped_addresses:
        lines.append("")
        lines.append(f"⚠️ Won't fit: {', '.join(tour.skipped_addresses)}")

    return "\n".join(lines)


def _supports_dash_format() -> bool:
    """Check if platform supports %-I / %-d format specifiers."""
    try:
        datetime.now().strftime("%-d")
        return True
    except ValueError:
        return False
