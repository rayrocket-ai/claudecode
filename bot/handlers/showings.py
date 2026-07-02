"""Telegram handlers for BrokerBay showing management.

Provides:
  - /showings  — list pending and upcoming showings
  - /today     — today's showings
  - Inline buttons to confirm / decline / counter showings
  - Background polling job that notifies on new showing requests
"""

from __future__ import annotations

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.handlers.conversation import _is_authorized
from config import get_settings
from integrations.brokerbay import (
    BrokerBayClient,
    BrokerBayError,
    _md,
    format_showing,
    get_showing_address,
    get_showing_id,
    google_maps_link,
    google_maps_static_url,
)

logger = logging.getLogger(__name__)

# Track which showing IDs we've already notified about, keyed by chat_id
_notified_showings: dict[int, set[str]] = {}


# ── Helpers ──────────────────────────────────────────────────────


def _showing_action_keyboard(showing_id: str) -> InlineKeyboardMarkup:
    """Inline buttons for a showing: confirm, decline, map, counter."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Confirm", callback_data=f"showing_confirm_{showing_id}"
            ),
            InlineKeyboardButton(
                "❌ Decline", callback_data=f"showing_decline_{showing_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🗺 Map", callback_data=f"showing_map_{showing_id}"
            ),
            InlineKeyboardButton(
                "🔄 Counter", callback_data=f"showing_counter_{showing_id}"
            ),
        ],
    ])


async def _send_showing_card(
    bot,
    chat_id: int,
    showing: dict[str, Any],
    *,
    show_actions: bool = True,
) -> None:
    """Send a formatted showing message with optional action buttons."""
    text = format_showing(showing)

    address = get_showing_address(showing)
    if address:
        text += f"\n\n🗺 [Google Maps]({google_maps_link(address)})"

    sid = get_showing_id(showing)
    markup = _showing_action_keyboard(sid) if show_actions and sid else None

    status = (
        showing.get("status") or showing.get("showingStatus") or ""
    ).lower()
    is_actionable = status in ("pending", "requested")

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=markup if is_actionable else None,
        disable_web_page_preview=True,
    )


# ── Command Handlers ─────────────────────────────────────────────


async def showings_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /showings — list pending + upcoming showings."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Not authorized.")
        return

    settings = get_settings()
    if not settings.is_brokerbay_configured:
        await update.message.reply_text(
            "⚠️ BrokerBay credentials not configured in .env"
        )
        return

    await update.message.reply_text("🔄 Fetching showings from BrokerBay...")

    try:
        client = BrokerBayClient()
        try:
            pending = await client.get_pending_showings()
            upcoming = await client.get_upcoming_showings(days=7)
        finally:
            await client.close()

        # Merge, dedup by ID, pending first
        seen: set[str] = set()
        all_showings: list[dict] = []
        for s in pending + upcoming:
            sid = get_showing_id(s)
            if sid and sid not in seen:
                seen.add(sid)
                all_showings.append(s)

        if not all_showings:
            await update.message.reply_text(
                "📭 No pending or upcoming showings."
            )
            return

        await update.message.reply_text(
            f"📋 *{len(all_showings)} Showing(s) Found:*",
            parse_mode="Markdown",
        )

        for showing in all_showings[:20]:  # cap at 20 to avoid flood
            await _send_showing_card(
                context.bot, update.effective_chat.id, showing
            )

    except BrokerBayError as e:
        await update.message.reply_text(f"❌ BrokerBay error: {e}")
    except Exception as e:
        logger.exception("showings_command error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")


async def today_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /today — show today's schedule."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Not authorized.")
        return

    settings = get_settings()
    if not settings.is_brokerbay_configured:
        await update.message.reply_text(
            "⚠️ BrokerBay credentials not configured."
        )
        return

    await update.message.reply_text("🔄 Fetching today's showings...")

    try:
        client = BrokerBayClient()
        try:
            showings = await client.get_todays_showings()
        finally:
            await client.close()

        if not showings:
            await update.message.reply_text("📭 No showings scheduled for today.")
            return

        await update.message.reply_text(
            f"📅 *Today's Showings ({len(showings)}):*",
            parse_mode="Markdown",
        )

        for showing in showings:
            await _send_showing_card(
                context.bot, update.effective_chat.id, showing
            )

    except BrokerBayError as e:
        await update.message.reply_text(f"❌ BrokerBay error: {e}")
    except Exception as e:
        logger.exception("today_command error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")


async def listings_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /listings — show active listings."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return

    settings = get_settings()
    if not settings.is_brokerbay_configured:
        await update.message.reply_text(
            "⚠️ BrokerBay credentials not configured."
        )
        return

    await update.message.reply_text("🔄 Fetching listings...")

    try:
        client = BrokerBayClient()
        try:
            listings = await client.get_listings()
        finally:
            await client.close()

        if not listings:
            await update.message.reply_text("📭 No active listings found.")
            return

        lines = [f"🏠 *Active Listings ({len(listings)}):*\n"]
        for lst in listings[:15]:
            address = (
                lst.get("address")
                or lst.get("fullAddress")
                or lst.get("propertyAddress")
                or "Unknown"
            )
            mls = lst.get("mlsNumber") or lst.get("mls") or ""
            price = lst.get("price") or lst.get("listPrice") or ""
            status = lst.get("status") or ""

            line = f"• {_md(address)}"
            if mls:
                line += f" (MLS: {_md(mls)})"
            if price:
                line += f" — ${price:,}" if isinstance(price, (int, float)) else f" — {_md(price)}"
            if status:
                line += f" — {_md(status)}"
            lines.append(line)

        await update.message.reply_text(
            "\n".join(lines), parse_mode="Markdown"
        )

    except BrokerBayError as e:
        await update.message.reply_text(f"❌ BrokerBay error: {e}")
    except Exception as e:
        logger.exception("listings_command error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")


# ── Callback Query Handlers (Confirm / Decline / Map / Counter) ──


async def showing_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle inline button presses for showing actions."""
    query = update.callback_query
    if not _is_authorized(update.effective_user.id):
        await query.answer("⛔ Not authorized.")
        return
    await query.answer()
    data = query.data  # e.g. "showing_confirm_12345"

    parts = data.split("_", 2)  # ["showing", "action", "id"]
    if len(parts) < 3:
        return

    action = parts[1]
    showing_id = parts[2]

    if action == "confirm":
        await _handle_confirm(query, context, showing_id)
    elif action == "decline":
        await _handle_decline(query, context, showing_id)
    elif action == "map":
        await _handle_map(query, context, showing_id)
    elif action == "counter":
        await _handle_counter_prompt(query, context, showing_id)


async def _handle_confirm(query, context, showing_id: str) -> None:
    """Confirm a showing."""
    try:
        client = BrokerBayClient()
        try:
            await client.confirm_showing(showing_id)
        finally:
            await client.close()

        # query.message.text is the already-rendered plain text — do not
        # re-parse it as Markdown (addresses may contain formatting chars)
        await query.edit_message_text(query.message.text + "\n\n✅ CONFIRMED")
    except BrokerBayError as e:
        await query.message.reply_text(f"❌ Failed to confirm: {e}")
    except Exception as e:
        logger.exception("confirm error: %s", e)
        await query.message.reply_text(f"❌ Error: {e}")


async def _handle_decline(query, context, showing_id: str) -> None:
    """Decline a showing."""
    try:
        client = BrokerBayClient()
        try:
            await client.decline_showing(showing_id)
        finally:
            await client.close()

        await query.edit_message_text(query.message.text + "\n\n🔴 DECLINED")
    except BrokerBayError as e:
        await query.message.reply_text(f"❌ Failed to decline: {e}")
    except Exception as e:
        logger.exception("decline error: %s", e)
        await query.message.reply_text(f"❌ Error: {e}")


async def _handle_map(query, context, showing_id: str) -> None:
    """Send a map image/link for the showing address."""
    settings = get_settings()

    try:
        client = BrokerBayClient()
        try:
            showing = await client.get_showing(showing_id)
        finally:
            await client.close()

        address = get_showing_address(showing)
        if not address:
            await query.message.reply_text("⚠️ No address available for this showing.")
            return

        maps_url = google_maps_link(address)

        # Send static map image if API key is available
        if settings.google_maps_api_key:
            static_url = google_maps_static_url(address, settings.google_maps_api_key)
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=static_url,
                caption=f"📍 {address}\n🗺 [Open in Google Maps]({maps_url})",
                parse_mode="Markdown",
            )
        else:
            await query.message.reply_text(
                f"📍 {address}\n🗺 [Open in Google Maps]({maps_url})",
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )

    except BrokerBayError as e:
        await query.message.reply_text(f"❌ BrokerBay error: {e}")
    except Exception as e:
        logger.exception("map error: %s", e)
        await query.message.reply_text(f"❌ Error: {e}")


async def _handle_counter_prompt(query, context, showing_id: str) -> None:
    """Prompt user to provide a counter time."""
    context.user_data["counter_showing_id"] = showing_id
    await query.message.reply_text(
        "🔄 *Counter-propose a new time*\n\n"
        "Reply with the new date and time, e.g.:\n"
        "`2026-07-15 14:00`\n\n"
        "Or reply `cancel` to cancel.",
        parse_mode="Markdown",
    )


async def counter_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle a counter-proposal time input.

    Registered in a priority group before the conversation handler; when
    not in counter mode it returns without consuming the update.
    """
    from telegram.ext import ApplicationHandlerStop

    showing_id = context.user_data.get("counter_showing_id")
    if not showing_id:
        return  # Not in counter mode — let other handlers process this
    if not update.message or not update.message.text:
        return
    if not _is_authorized(update.effective_user.id):
        return

    text = update.message.text.strip()

    if text.lower() in ("cancel", "/cancel"):
        context.user_data.pop("counter_showing_id", None)
        await update.message.reply_text("❌ Counter cancelled.")
        raise ApplicationHandlerStop

    # Parse date and time
    parts = text.split(None, 1)
    if len(parts) < 2:
        await update.message.reply_text(
            "⚠️ Please provide both date and time, e.g.: `2026-07-15 14:00`\n"
            "Or reply `cancel` to cancel.",
            parse_mode="Markdown",
        )
        raise ApplicationHandlerStop

    new_date, new_time = parts[0], parts[1]

    try:
        client = BrokerBayClient()
        try:
            await client.counter_showing(showing_id, new_date, new_time)
        finally:
            await client.close()

        await update.message.reply_text(
            f"🔄 Counter-proposal sent: {new_date} at {new_time}"
        )
    except BrokerBayError as e:
        await update.message.reply_text(f"❌ Counter failed: {e}")
    except Exception as e:
        logger.exception("counter error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        context.user_data.pop("counter_showing_id", None)

    raise ApplicationHandlerStop


# ── Background Polling Job ───────────────────────────────────────


async def poll_new_showings(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Background job: check BrokerBay for new pending showings and notify.

    Runs on a configurable interval via JobQueue.
    """
    settings = get_settings()
    if not settings.is_brokerbay_configured:
        return

    allowed_ids = settings.authorized_user_id_list
    if not allowed_ids:
        return  # Don't spam if no users configured

    try:
        client = BrokerBayClient()
        try:
            pending = await client.get_pending_showings()
        finally:
            await client.close()

        for chat_id in allowed_ids:
            if chat_id not in _notified_showings:
                _notified_showings[chat_id] = set()

            already_notified = _notified_showings[chat_id]

            for showing in pending:
                sid = get_showing_id(showing)
                if not sid or sid in already_notified:
                    continue

                # New showing — notify!
                already_notified.add(sid)
                logger.info(
                    "brokerbay.new_showing_notification",
                    showing_id=sid,
                    chat_id=chat_id,
                )

                text = "🔔 *New Showing Request!*\n\n" + format_showing(showing)
                address = get_showing_address(showing)
                if address:
                    text += f"\n\n🗺 [Google Maps]({google_maps_link(address)})"

                status = (
                    showing.get("status")
                    or showing.get("showingStatus")
                    or ""
                ).lower()
                is_actionable = status in ("pending", "requested")

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=(
                        _showing_action_keyboard(sid) if is_actionable else None
                    ),
                    disable_web_page_preview=True,
                )

            # Prune old IDs to prevent memory leak (keep last 500)
            if len(already_notified) > 500:
                excess = len(already_notified) - 500
                for _ in range(excess):
                    already_notified.pop()

    except BrokerBayError as e:
        logger.warning("brokerbay.poll_error", error=str(e))
    except Exception as e:
        logger.exception("brokerbay.poll_error: %s", e)


# ── Registration ─────────────────────────────────────────────────


def register_showing_handlers(app) -> None:
    """Register all showing-related handlers on the Application."""
    # Commands (these work outside the ConversationHandler)
    app.add_handler(CommandHandler("showings", showings_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("listings", listings_command))

    # Callback queries for showing actions
    app.add_handler(
        CallbackQueryHandler(showing_callback, pattern=r"^showing_")
    )

    # Counter-proposal reply catcher — own priority group so it runs
    # before the document conversation handler; it only consumes the
    # message when a counter is actually pending (ApplicationHandlerStop)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, counter_message),
        group=-2,
    )

    # Start the background polling job
    settings = get_settings()
    if settings.is_brokerbay_configured:
        interval = settings.showing_poll_interval
        app.job_queue.run_repeating(
            poll_new_showings,
            interval=interval,
            first=10,  # start 10s after boot
            name="brokerbay_poll",
        )
        logger.info(
            "brokerbay.polling_enabled",
            interval_seconds=interval,
        )
