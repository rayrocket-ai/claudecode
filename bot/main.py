"""Telegram bot entry point."""

from __future__ import annotations

import asyncio
import logging
import sys

import structlog
from telegram import BotCommand
from telegram.ext import Application

from bot.handlers.conversation import build_conversation_handler
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

    commands = [
        BotCommand("start", "Main menu"),
        BotCommand("new", "Create a new document"),
        BotCommand("tour", "Generate a house tour video"),
        BotCommand("higgsfieldtest", "Test Higgsfield API credentials"),
        BotCommand("higgsfieldlogin", "Log in to Higgsfield (browser backend)"),
        BotCommand("realmtest", "Test REALM / TransactionDesk connection"),
        BotCommand("help", "Show help"),
        BotCommand("cancel", "Cancel current operation"),
    ]
    await application.bot.set_my_commands(commands)


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

    # Add conversation handler
    conv_handler = build_conversation_handler()
    app.add_handler(conv_handler)

    # Start polling
    log.info("bot.polling", mode="polling")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
