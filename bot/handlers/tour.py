"""Tour booking conversation handler.

Flow (per spec):
  /tour or /book
    → "Paste your list of addresses"
    → "What date?"
    → "Preferred start and latest end time?"
    → "Client name?"
    → "Starting point?"
    → Geocode + optimize route
    → Show proposed schedule with [Book All] [Adjust]
    → On confirm, open BrokerBay and book each stop
    → Send full tour summary
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

from dateutil import parser as date_parser
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.formatters.tour import format_proposed_schedule, format_tour_message
from config import get_settings
from integrations.brokerbay_browser import BrokerBayBrowser, BrokerBayBrowserError
from scheduler.geocoder import Geocoder, GeocoderError, GeoPoint
from scheduler.optimizer import Tour, build_schedule

logger = logging.getLogger(__name__)

# ── FSM States ───────────────────────────────────────────────────

(
    TOUR_ADDRESSES,
    TOUR_DATE,
    TOUR_TIME_WINDOW,
    TOUR_CLIENT,
    TOUR_START,
    TOUR_CONFIRM,
) = range(6)


# ── Helpers ──────────────────────────────────────────────────────


def _is_authorized(user_id: int) -> bool:
    settings = get_settings()
    allowed = settings.authorized_user_id_list
    if not allowed:
        return True
    return user_id in allowed


def _parse_addresses(text: str) -> list[str]:
    """Split a pasted block into a list of addresses."""
    lines = [
        line.strip(" -•*\t")
        for line in re.split(r"[\r\n]+", text)
        if line.strip()
    ]
    # Filter obvious junk
    return [l for l in lines if len(l) > 5 and any(c.isdigit() for c in l)]


def _parse_time_window(text: str) -> tuple[str, str] | None:
    """Parse '10am - 4pm' or '10:00-16:00' into ('10:00 AM', '4:00 PM')."""
    cleaned = text.replace("–", "-").replace("to", "-").replace("until", "-")
    parts = [p.strip() for p in cleaned.split("-") if p.strip()]
    if len(parts) != 2:
        return None
    try:
        start = date_parser.parse(parts[0])
        end = date_parser.parse(parts[1])
        return start.strftime("%I:%M %p"), end.strftime("%I:%M %p")
    except (ValueError, TypeError):
        return None


def _combine_date_time(date: datetime, time_str: str) -> datetime:
    """Merge a date and an 'HH:MM AM/PM' time string into a datetime."""
    t = date_parser.parse(time_str).time()
    return date.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Book All", callback_data="tour_book"),
            InlineKeyboardButton("✏️ Adjust", callback_data="tour_adjust"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="tour_cancel")],
    ])


# ── Entry / Command Handlers ─────────────────────────────────────


async def tour_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /tour and /book."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Not authorized.")
        return ConversationHandler.END

    settings = get_settings()
    if not settings.is_brokerbay_configured:
        await update.message.reply_text(
            "⚠️ BrokerBay credentials not configured."
        )
        return ConversationHandler.END
    if not settings.google_maps_api_key:
        await update.message.reply_text(
            "⚠️ GOOGLE_MAPS_API_KEY not configured — route optimization disabled."
        )
        return ConversationHandler.END

    context.user_data["tour"] = {}
    await update.message.reply_text(
        "📋 *Book a Showing Tour*\n\n"
        "Paste your list of addresses (one per line).\n\n"
        "Type /cancel to abort.",
        parse_mode="Markdown",
    )
    return TOUR_ADDRESSES


async def addresses_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    addresses = _parse_addresses(update.message.text)
    if not addresses:
        await update.message.reply_text(
            "⚠️ I couldn't find any addresses. Paste them one per line, "
            "e.g.:\n\n`123 Maple Ave, Toronto`\n`456 Oak Blvd, Vaughan`",
            parse_mode="Markdown",
        )
        return TOUR_ADDRESSES

    context.user_data["tour"]["addresses"] = addresses
    await update.message.reply_text(
        f"✅ Got *{len(addresses)}* address(es).\n\n"
        f"📅 What date? (e.g. `March 25` or `2025-03-25`)",
        parse_mode="Markdown",
    )
    return TOUR_DATE


async def date_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = update.message.text.strip()
    try:
        parsed = date_parser.parse(text, fuzzy=True)
        # If year was omitted and the parsed date is in the past, bump to next year
        if parsed.date() < datetime.now().date():
            parsed = parsed.replace(year=datetime.now().year + 1)
    except (ValueError, TypeError):
        await update.message.reply_text(
            "⚠️ I couldn't parse that date. Try `March 25` or `2025-03-25`."
        )
        return TOUR_DATE

    context.user_data["tour"]["date"] = parsed.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    await update.message.reply_text(
        f"✅ Date: *{parsed.strftime('%A, %B %d, %Y')}*\n\n"
        f"⏰ Preferred start time and latest end time?\n"
        f"(e.g. `10am - 4pm`)",
        parse_mode="Markdown",
    )
    return TOUR_TIME_WINDOW


async def time_window_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    window = _parse_time_window(update.message.text)
    if not window:
        await update.message.reply_text(
            "⚠️ I couldn't parse that time window. Try `10am - 4pm`."
        )
        return TOUR_TIME_WINDOW

    context.user_data["tour"]["start_time"] = window[0]
    context.user_data["tour"]["end_time"] = window[1]
    await update.message.reply_text(
        f"✅ Window: *{window[0]} – {window[1]}*\n\n"
        f"👤 Client name for these showings?",
        parse_mode="Markdown",
    )
    return TOUR_CLIENT


async def client_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("⚠️ Please enter the client's name.")
        return TOUR_CLIENT

    context.user_data["tour"]["client_name"] = name
    await update.message.reply_text(
        f"✅ Client: *{name}*\n\n"
        f"📍 Starting point?\n"
        f"(your office address, home, or type `first property` to start from the first stop)",
        parse_mode="Markdown",
    )
    return TOUR_START


async def start_point_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    text = update.message.text.strip()
    tour_state = context.user_data["tour"]

    if text.lower() in ("first property", "first", "first stop"):
        # Use the first address as the start point
        start_addr = tour_state["addresses"][0]
        tour_state["start_from_first"] = True
    else:
        start_addr = text
        tour_state["start_from_first"] = False

    tour_state["start_address"] = start_addr

    await update.message.reply_text(
        "🔄 Geocoding addresses and calculating route...\n"
        "_This may take 10-30 seconds._",
        parse_mode="Markdown",
    )

    try:
        await _compute_and_propose(update, context)
    except GeocoderError as e:
        await update.message.reply_text(f"❌ Geocoding failed: {e}")
        return ConversationHandler.END
    except Exception as e:
        logger.exception("tour planning error: %s", e)
        await update.message.reply_text(f"❌ Planning failed: {e}")
        return ConversationHandler.END

    return TOUR_CONFIRM


async def _compute_and_propose(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Geocode, optimize, and show proposed schedule."""
    tour_state = context.user_data["tour"]
    addresses: list[str] = tour_state["addresses"]
    date: datetime = tour_state["date"]
    start_time: str = tour_state["start_time"]
    end_time: str = tour_state["end_time"]

    earliest = _combine_date_time(date, start_time)
    latest = _combine_date_time(date, end_time)
    if latest <= earliest:
        latest = latest + timedelta(days=1)

    geocoder = Geocoder()

    if tour_state.get("start_from_first"):
        # Geocode all addresses at once; first is the start
        points = await geocoder.geocode_many(addresses)
        start = points[0]
        stops = points[1:] if len(points) > 1 else []
    else:
        start = await geocoder.geocode(tour_state["start_address"])
        stops = await geocoder.geocode_many(addresses)

    # Filter out any that failed to geocode (lat/lng == 0)
    valid_stops = [p for p in stops if p.lat != 0.0 or p.lng != 0.0]
    failed = [p.address for p in stops if p.lat == 0.0 and p.lng == 0.0]

    if not valid_stops:
        await update.message.reply_text(
            "❌ No addresses could be geocoded. Check spelling and try /tour again."
        )
        return

    matrix = await geocoder.distance_matrix([start] + valid_stops)
    tour = build_schedule(
        start=start,
        stops=valid_stops,
        matrix=matrix,
        earliest=earliest,
        latest=latest,
    )

    tour_state["tour"] = tour
    tour_state["failed_addresses"] = failed

    summary = format_proposed_schedule(
        tour, tour_state["client_name"], date
    )
    if failed:
        summary += "\n\n⚠️ Could not geocode: " + ", ".join(failed)

    summary += "\n\nConfirm to book?"

    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=_confirm_keyboard(),
        disable_web_page_preview=True,
    )


# ── Confirm & Book ───────────────────────────────────────────────


async def confirm_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "tour_cancel":
        await query.edit_message_text("❌ Tour cancelled.")
        context.user_data.pop("tour", None)
        return ConversationHandler.END

    if data == "tour_adjust":
        await query.edit_message_text(
            "✏️ Start over with /tour to adjust addresses or times."
        )
        context.user_data.pop("tour", None)
        return ConversationHandler.END

    if data == "tour_book":
        await query.edit_message_text("⏳ Booking showings in BrokerBay...")
        await _book_all_stops(update, context)
        return ConversationHandler.END

    return TOUR_CONFIRM


async def _book_all_stops(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Sequentially book each stop in the tour via BrokerBay browser."""
    tour_state = context.user_data["tour"]
    tour: Tour = tour_state["tour"]
    client_name: str = tour_state["client_name"]
    date: datetime = tour_state["date"]
    chat_id = update.effective_chat.id

    confirmations: dict[str, dict[str, Any]] = {}
    failed: list[str] = []

    try:
        async with BrokerBayBrowser() as bb:
            for stop in tour.stops:
                address = stop.address
                booked = False

                # Try ±30min fallback per spec
                time_offsets = [0, 30, -30, 60]
                for offset in time_offsets:
                    attempt_time = stop.arrival_time + timedelta(minutes=offset)
                    try:
                        listing = await bb.search_listing(address)
                        if not listing:
                            failed.append(f"{address} (not found)")
                            break

                        details = await bb.get_listing_details(listing["id"])
                        conf = await bb.book_showing(
                            listing_id=listing["id"],
                            date_time=attempt_time,
                            client_name=client_name,
                            duration_minutes=stop.showing_minutes,
                        )

                        # Merge details into confirmation for the summary
                        confirmations[address] = {**details, **conf}
                        if offset != 0:
                            confirmations[address]["time_adjusted"] = offset
                        booked = True
                        break
                    except BrokerBayBrowserError as e:
                        logger.info(
                            "book.retry",
                            address=address,
                            offset=offset,
                            error=str(e),
                        )
                        continue

                if not booked:
                    failed.append(f"{address} (no time available)")

                # Brief update per stop
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ Booked: {address}" if booked
                        else f"⚠️ Skipped: {address}"
                    ),
                )
    except BrokerBayBrowserError as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ BrokerBay error: {e}",
        )
        return

    # Final summary
    summary = format_tour_message(
        tour, client_name, date, confirmations=confirmations
    )
    if failed:
        summary += "\n\n⚠️ *Not booked:*\n" + "\n".join(f"• {f}" for f in failed)

    await context.bot.send_message(
        chat_id=chat_id,
        text=summary,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )

    context.user_data.pop("tour", None)


async def cancel_tour(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.pop("tour", None)
    await update.message.reply_text("❌ Tour cancelled.")
    return ConversationHandler.END


# ── Registration ─────────────────────────────────────────────────


def build_tour_handler() -> ConversationHandler:
    """Build the tour booking ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("tour", tour_command),
            CommandHandler("book", tour_command),
        ],
        states={
            TOUR_ADDRESSES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, addresses_handler),
            ],
            TOUR_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, date_handler),
            ],
            TOUR_TIME_WINDOW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, time_window_handler),
            ],
            TOUR_CLIENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, client_handler),
            ],
            TOUR_START: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, start_point_handler),
            ],
            TOUR_CONFIRM: [
                CallbackQueryHandler(confirm_callback, pattern=r"^tour_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_tour)],
        allow_reentry=True,
    )
