"""Telegram bot entry point."""

from __future__ import annotations

import asyncio
import logging
import sys

import structlog
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.handlers.conversation import build_conversation_handler
from bot.handlers.showings import register_showing_handlers
from bot.handlers.status import register_status_handlers
from bot.handlers.tour import build_tour_handler
from config import get_settings
from db.operations import init_db


def setup_logging() -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


async def post_init(application: Application) -> None:
    """Run after bot initialization — set commands and init DB."""
    await init_db()

    settings = get_settings()

    commands = [
        BotCommand("start", "Main menu"),
        BotCommand("tour", "Book a showing tour (route-optimized)"),
        BotCommand("book", "Alias for /tour"),
        BotCommand("showings", "View pending & upcoming showings"),
        BotCommand("today", "Today's showing schedule"),
        BotCommand("summary", "Showings summary for a date"),
        BotCommand("pending", "Pending requests on your listings"),
        BotCommand("approve", "Approve a showing: /approve <id>"),
        BotCommand("decline", "Decline a showing: /decline <id> [reason]"),
        BotCommand("listings", "View active listings"),
        BotCommand("status", "Bot + session health check"),
        BotCommand("whoami", "Show your Telegram user ID"),
        BotCommand("new", "Create a document (OREA forms)"),
        BotCommand("realmtest", "Test REALM / TransactionDesk connection"),
        BotCommand("help", "Show help"),
        BotCommand("cancel", "Cancel current operation"),
    ]
    await application.bot.set_my_commands(commands)

    if settings.is_brokerbay_configured:
        log = structlog.get_logger()
        log.info("brokerbay.configured", email=settings.brokerbay_email)


def main() -> None:
    """Start the Telegram bot."""
    setup_logging()
    log = structlog.get_logger()

    settings = get_settings()
    if not settings.telegram_bot_token:
        log.error("TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    if not settings.anthropic_api_key:
        log.warning("ANTHROPIC_API_KEY not set — AI features will not work")

    # Build application
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    # /whoami — always works, no auth required, so user can discover their ID
    async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        await update.message.reply_text(
            f"Your Telegram user ID is: `{user.id}`\n\n"
            f"Name: {user.full_name}\n"
            f"Username: @{user.username or 'N/A'}\n\n"
            f"Set this in your `.env` file as:\n"
            f"`AUTHORIZED_USER_IDS={user.id}`",
            parse_mode="Markdown",
        )

    app.add_handler(CommandHandler("whoami", whoami_command))

    # Tour booking conversation (must be added before the generic conv handler
    # so its /tour and /book entry points win)
    app.add_handler(build_tour_handler())

    # Add showing management handlers (commands + callback queries + polling)
    register_showing_handlers(app)

    # Add status / summary / pending / approve / decline commands
    register_status_handlers(app)

    # Add conversation handler (OREA document generation) — register last so
    # its message fallback doesn't swallow other command states
    conv_handler = build_conversation_handler()
    app.add_handler(conv_handler)

    # Start polling
    log.info("bot.polling", mode="polling")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
