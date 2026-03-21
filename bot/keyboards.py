"""Telegram inline keyboards for the bot."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu after /start."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Create New Document", callback_data="menu_new_doc")],
        [InlineKeyboardButton("📋 My Transactions", callback_data="menu_transactions")],
        [InlineKeyboardButton("🔗 Test REALM Connection", callback_data="menu_realm_test")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")],
    ])


def doc_type_keyboard() -> InlineKeyboardMarkup:
    """Document type selection."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Agreement of Purchase & Sale (Form 100)",
                              callback_data="doc_aps")],
        [InlineKeyboardButton("✏️ Amendment (Form 120)",
                              callback_data="doc_amendment")],
        [InlineKeyboardButton("✅ Waiver (Form 122)",
                              callback_data="doc_waiver")],
        [InlineKeyboardButton("📋 Notice (Form 124)",
                              callback_data="doc_notice")],
        [InlineKeyboardButton("🏢 Commercial APS (Form 500)",
                              callback_data="doc_commercial_aps")],
        [InlineKeyboardButton("🔑 Agreement to Lease",
                              callback_data="doc_lease")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm or edit collected data."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm & Generate", callback_data="confirm_generate"),
            InlineKeyboardButton("✏️ Edit", callback_data="confirm_edit"),
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ])


def post_generate_keyboard(has_transactiondesk: bool = False) -> InlineKeyboardMarkup:
    """Actions after document is generated."""
    buttons = []

    if has_transactiondesk:
        buttons.append([InlineKeyboardButton(
            "✍️ Create Signing Session (Authentisign)",
            callback_data="action_td_sign",
        )])

    buttons.extend([
        [InlineKeyboardButton("📧 Email Document", callback_data="action_email")],
        [InlineKeyboardButton("📝 Create Another Document", callback_data="menu_new_doc")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ])

    return InlineKeyboardMarkup(buttons)


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Generic yes/no keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes", callback_data=f"{prefix}_yes"),
            InlineKeyboardButton("No", callback_data=f"{prefix}_no"),
        ],
    ])
