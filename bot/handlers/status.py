"""Status and summary handlers: /status, /summary, /pending, /approve, /decline."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from dateutil import parser as date_parser
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.handlers.conversation import _is_authorized
from config import get_settings, STORAGE_DIR
from integrations.brokerbay import BrokerBayClient, BrokerBayError, format_showing

logger = logging.getLogger(__name__)


# ── /status ──────────────────────────────────────────────────────


async def status_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Report bot + session health and the next upcoming showing."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return

    settings = get_settings()

    lines = ["🤖 *Bot Status*\n"]

    # Core services
    lines.append(
        "• Telegram: 🟢 Connected"
        if settings.telegram_bot_token
        else "• Telegram: 🔴 Missing token"
    )
    lines.append(
        "• BrokerBay: 🟢 Configured"
        if settings.is_brokerbay_configured
        else "• BrokerBay: 🔴 Not configured"
    )
    lines.append(
        "• Google Maps: 🟢 Configured"
        if settings.google_maps_api_key
        else "• Google Maps: 🔴 Not configured"
    )

    # Session file
    sp = settings.session_path
    session_path = (
        STORAGE_DIR / sp.lstrip("./") if sp.startswith("./") else Path(sp)
    )
    if session_path.exists() and session_path.stat().st_size > 10:
        mtime = datetime.fromtimestamp(session_path.stat().st_mtime)
        age = datetime.now() - mtime
        lines.append(
            f"• BrokerBay session: 🟢 Active "
            f"(saved {age.days}d ago)"
        )
    else:
        lines.append("• BrokerBay session: 🟡 Will login on next use")

    # Next upcoming showing
    if settings.is_brokerbay_configured:
        try:
            client = BrokerBayClient()
            try:
                upcoming = await client.get_upcoming_showings(days=7)
            finally:
                await client.close()

            if upcoming:
                lines.append("\n*Next showing:*")
                lines.append(format_showing(upcoming[0]))
            else:
                lines.append("\n📭 No upcoming showings in the next 7 days.")
        except BrokerBayError as e:
            lines.append(f"\n⚠️ Couldn't fetch showings: {e}")
        except Exception as e:
            logger.warning("status.fetch_error", error=str(e))
            lines.append("\n⚠️ Couldn't fetch showings.")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ── /summary [date] ──────────────────────────────────────────────


async def summary_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show all confirmed showings for a given date (default: today)."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return

    settings = get_settings()
    if not settings.is_brokerbay_configured:
        await update.message.reply_text("⚠️ BrokerBay not configured.")
        return

    # Parse date argument if provided
    if context.args:
        arg = " ".join(context.args)
        try:
            target = date_parser.parse(arg, fuzzy=True)
        except (ValueError, TypeError):
            await update.message.reply_text(
                f"⚠️ Couldn't parse '{arg}' as a date."
            )
            return
    else:
        target = datetime.now()

    date_str = target.strftime("%Y-%m-%d")
    pretty_date = target.strftime("%A, %B %d, %Y")

    await update.message.reply_text(
        f"🔄 Fetching showings for {pretty_date}..."
    )

    try:
        client = BrokerBayClient()
        try:
            showings = await client.get_showings(
                date_from=date_str, date_to=date_str
            )
        finally:
            await client.close()

        if not showings:
            await update.message.reply_text(
                f"📭 No showings on {pretty_date}."
            )
            return

        # Filter to confirmed-ish states
        confirmed = [
            s for s in showings
            if (s.get("status") or s.get("showingStatus") or "").lower()
            in ("confirmed", "approved", "scheduled")
        ]

        lines = [f"📅 *Showings — {pretty_date}*"]
        lines.append(
            f"({len(confirmed)} confirmed of {len(showings)} total)"
        )
        lines.append("")

        for s in (confirmed or showings)[:20]:
            lines.append(format_showing(s))
            lines.append("")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except BrokerBayError as e:
        await update.message.reply_text(f"❌ BrokerBay error: {e}")
    except Exception as e:
        logger.exception("summary error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")


# ── /pending ─────────────────────────────────────────────────────


async def pending_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List all pending showing requests for our listings."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return

    settings = get_settings()
    if not settings.is_brokerbay_configured:
        await update.message.reply_text("⚠️ BrokerBay not configured.")
        return

    await update.message.reply_text("🔄 Fetching pending requests...")

    try:
        client = BrokerBayClient()
        try:
            pending = await client.get_pending_showings()
        finally:
            await client.close()

        if not pending:
            await update.message.reply_text("📭 No pending requests.")
            return

        # Use the showing handlers' card sender for consistency
        from bot.handlers.showings import _send_showing_card

        await update.message.reply_text(
            f"⏳ *{len(pending)} Pending Request(s):*",
            parse_mode="Markdown",
        )
        for showing in pending[:20]:
            await _send_showing_card(
                context.bot, update.effective_chat.id, showing
            )
    except BrokerBayError as e:
        await update.message.reply_text(f"❌ BrokerBay error: {e}")
    except Exception as e:
        logger.exception("pending error: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")


# ── /approve [id] / /decline [id] ────────────────────────────────


async def approve_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Approve a specific showing: /approve <id>."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: `/approve <showing_id>`\n"
            "Or use the buttons on a showing card.",
            parse_mode="Markdown",
        )
        return

    showing_id = context.args[0]

    try:
        client = BrokerBayClient()
        try:
            await client.confirm_showing(showing_id)
        finally:
            await client.close()
        await update.message.reply_text(f"✅ Showing {showing_id} approved.")
    except BrokerBayError as e:
        await update.message.reply_text(f"❌ Approve failed: {e}")


async def decline_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Decline a showing: /decline <id> [reason]."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: `/decline <showing_id> [reason]`",
            parse_mode="Markdown",
        )
        return

    showing_id = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else ""

    try:
        client = BrokerBayClient()
        try:
            await client.decline_showing(showing_id, reason)
        finally:
            await client.close()
        await update.message.reply_text(f"🔴 Showing {showing_id} declined.")
    except BrokerBayError as e:
        await update.message.reply_text(f"❌ Decline failed: {e}")


# ── Registration ─────────────────────────────────────────────────


def register_status_handlers(app) -> None:
    """Register /status, /summary, /pending, /approve, /decline."""
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(CommandHandler("decline", decline_command))
