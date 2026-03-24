"""Main conversation handler for the Telegram bot.

FSM States:
  IDLE (0)            → User sends /start or a message
  SELECTING_DOC (1)   → User picks a document type
  COLLECTING (2)      → AI collects deal data via conversation
  CONFIRMING (3)      → User reviews and confirms data
  GENERATING (4)      → Document is being generated
  POST_GENERATE (5)   → Document ready, user picks next action
  SIGNING (6)         → User provides signer emails
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from telegram import Update, InputFile, BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ai.agent import get_agent
from bot.keyboards import (
    main_menu_keyboard,
    doc_type_keyboard,
    confirm_keyboard,
    post_generate_keyboard,
)
from config import get_settings
from db.operations import (
    append_conversation_message,
    get_or_create_conversation,
    reset_session,
    set_session_state,
    update_session_data,
)
from forms.generator import generate_document, get_last_td_result

logger = logging.getLogger(__name__)

# Conversation states
IDLE, SELECTING_DOC, COLLECTING, CONFIRMING, GENERATING, POST_GENERATE, SIGNING = range(7)

# Module-level dict for 2FA futures (avoids setting attributes on PTB ExtBot)
_pending_2fa: dict[int, asyncio.Future] = {}

DOC_TYPE_NAMES = {
    "aps": "Agreement of Purchase and Sale (Form 100)",
    "amendment": "Amendment (Form 120)",
    "waiver": "Waiver (Form 122)",
    "notice": "Notice (Form 124)",
    "commercial_aps": "Commercial APS (Form 500)",
    "lease": "Agreement to Lease",
}


# ── Helpers ───────────────────────────────────────────────────────


def _is_authorized(user_id: int) -> bool:
    """Check if a user is authorized. Empty whitelist = allow all."""
    settings = get_settings()
    allowed = settings.authorized_user_id_list
    if not allowed:
        return True
    return user_id in allowed


def _is_td_configured() -> bool:
    settings = get_settings()
    return settings.is_realm_configured


def make_two_factor_callback(chat_id: int, bot):
    """Create a 2FA callback that asks the user in Telegram and waits for reply."""

    async def callback() -> str:
        future = asyncio.get_event_loop().create_future()
        _pending_2fa[chat_id] = future

        await bot.send_message(
            chat_id=chat_id,
            text=(
                "🔐 *REALM 2FA Required*\n\n"
                "TRREB just sent an SMS code to your phone.\n"
                "Reply with the code (e.g. `123456`):"
            ),
            parse_mode="Markdown",
        )

        try:
            code = await asyncio.wait_for(future, timeout=300)  # 5 min
            return code
        except asyncio.TimeoutError:
            return ""
        finally:
            _pending_2fa.pop(chat_id, None)

    return callback


async def _send(update: Update, text: str, **kwargs) -> None:
    """Send a message, handling both message and callback_query contexts."""
    if update.callback_query:
        await update.callback_query.message.reply_text(text, **kwargs)
    elif update.message:
        await update.message.reply_text(text, **kwargs)


# ── Command Handlers ──────────────────────────────────────────────


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start — show welcome + main menu."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return ConversationHandler.END

    await reset_session(user.id)

    realm_status = "🟢 Connected" if _is_td_configured() else "🔴 Not configured"

    await update.message.reply_text(
        f"👋 Welcome to the *Real Estate Document Assistant*\n\n"
        f"I help you create, fill, and send Ontario real estate documents "
        f"(OREA/TRREB forms) through TransactionDesk WebForms.\n\n"
        f"*REALM Status:* {realm_status}\n\n"
        f"What would you like to do?",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    return IDLE


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel — reset everything."""
    user = update.effective_user
    await reset_session(user.id)
    context.user_data.clear()

    await _send(update, "✅ Cancelled. Send /start to begin again.")
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /help."""
    await _send(
        update,
        "*Available Commands:*\n\n"
        "/start — Main menu\n"
        "/new — Create a new document\n"
        "/showings — Pending & upcoming showings\n"
        "/today — Today's showing schedule\n"
        "/listings — View active listings\n"
        "/realmtest — Test REALM/TransactionDesk connection\n"
        "/cancel — Cancel current operation\n"
        "/help — This message\n\n"
        "*Supported Documents:*\n"
        "• Agreement of Purchase & Sale (Form 100)\n"
        "• Amendment (Form 120)\n"
        "• Waiver (Form 122)\n"
        "• Notice (Form 124)\n"
        "• Commercial APS (Form 500)\n"
        "• Agreement to Lease\n\n"
        "*How it works:*\n"
        "1. Choose a document type\n"
        "2. Answer questions about the deal\n"
        "3. Review the collected data\n"
        "4. Bot fills the form in TransactionDesk WebForms\n"
        "5. Optionally create an Authentisign signing session\n",
        parse_mode="Markdown",
    )
    return IDLE


async def realm_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /realmtest — test TransactionDesk connection."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return IDLE

    if not _is_td_configured():
        await _send(update, "⚠️ REALM credentials not configured in .env")
        return IDLE

    await _send(update, "🔄 Testing TransactionDesk connection...")

    try:
        from integrations.transactiondesk import TransactionDeskClient

        two_fa = make_two_factor_callback(user.id, context.bot)
        td = TransactionDeskClient(two_factor_callback=two_fa)
        result = await td.test_connection()

        if result.get("success"):
            screenshot = result.get("screenshot_path")
            msg = f"✅ TransactionDesk connected!\n📍 URL: {result.get('url', 'N/A')}"

            if screenshot:
                try:
                    with open(screenshot, "rb") as f:
                        await context.bot.send_photo(
                            chat_id=user.id,
                            photo=InputFile(f, filename="td_connection.png"),
                            caption=msg,
                        )
                except Exception:
                    await _send(update, msg)
            else:
                await _send(update, msg)
        else:
            await _send(update, f"❌ Connection failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        await _send(update, f"❌ Error: {e}")

    return IDLE


# ── Menu Callback Handler ─────────────────────────────────────────


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu button clicks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_new_doc":
        await query.edit_message_text(
            "📄 *What document would you like to create?*",
            parse_mode="Markdown",
            reply_markup=doc_type_keyboard(),
        )
        return SELECTING_DOC

    elif data == "menu_transactions":
        from db.operations import list_transactions
        txs = await list_transactions(update.effective_user.id)
        if not txs:
            await query.edit_message_text(
                "📋 No transactions yet. Create your first document!",
                reply_markup=main_menu_keyboard(),
            )
            return IDLE

        lines = []
        for tx in txs[:10]:
            doc_name = DOC_TYPE_NAMES.get(tx.doc_type, tx.doc_type)
            status = tx.status
            lines.append(f"• {doc_name} — _{status}_ ({tx.created_at.strftime('%b %d')})")

        await query.edit_message_text(
            f"📋 *Recent Transactions:*\n\n" + "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return IDLE

    elif data == "menu_realm_test":
        await query.edit_message_text("🔄 Testing TransactionDesk connection...")
        # Reuse the realm_test logic
        return await realm_test_command(update, context)

    elif data == "menu_showings":
        from bot.handlers.showings import showings_command
        await showings_command(update, context)
        return IDLE

    elif data == "menu_today":
        from bot.handlers.showings import today_command
        await today_command(update, context)
        return IDLE

    elif data == "menu_help":
        return await help_command(update, context)

    elif data == "menu_main":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\nWhat would you like to do?",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return IDLE

    return IDLE


# ── Document Type Selection ───────────────────────────────────────


async def doc_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle document type button selection."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END

    # Extract doc type from callback data (e.g., "doc_aps" → "aps")
    doc_type = data.replace("doc_", "")
    doc_name = DOC_TYPE_NAMES.get(doc_type, doc_type)

    # Save state
    context.user_data["doc_type"] = doc_type
    chat_id = update.effective_user.id
    await set_session_state(chat_id, "collecting", doc_type=doc_type)

    await query.edit_message_text(
        f"📝 *Creating: {doc_name}*\n\n"
        f"I'll ask you some questions to collect all the information needed.\n"
        f"Let's start — what is the *property address*?",
        parse_mode="Markdown",
    )
    return COLLECTING


async def doc_type_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle typed document type (instead of clicking a button)."""
    text = update.message.text.lower().strip()

    type_map = {
        "aps": "aps", "offer": "aps", "purchase": "aps", "form 100": "aps",
        "amendment": "amendment", "form 120": "amendment",
        "waiver": "waiver", "form 122": "waiver",
        "notice": "notice", "form 124": "notice",
        "commercial": "commercial_aps", "form 500": "commercial_aps",
        "lease": "lease",
    }

    doc_type = None
    for keyword, dtype in type_map.items():
        if keyword in text:
            doc_type = dtype
            break

    if not doc_type:
        await update.message.reply_text(
            "I didn't recognize that document type. Please choose from the menu:",
            reply_markup=doc_type_keyboard(),
        )
        return SELECTING_DOC

    doc_name = DOC_TYPE_NAMES.get(doc_type, doc_type)
    context.user_data["doc_type"] = doc_type
    await set_session_state(update.effective_user.id, "collecting", doc_type=doc_type)

    await update.message.reply_text(
        f"📝 *Creating: {doc_name}*\n\n"
        f"Let's start — what is the *property address*?",
        parse_mode="Markdown",
    )
    return COLLECTING


# ── Data Collection (AI Conversation) ─────────────────────────────


async def collecting_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle messages during AI data collection."""
    text = update.message.text
    chat_id = update.effective_user.id
    doc_type = context.user_data.get("doc_type", "aps")

    # Check if this is a 2FA code response
    if chat_id in _pending_2fa and re.match(r"^\d{4,8}$", text.strip()):
        future = _pending_2fa.get(chat_id)
        if future and not future.done():
            future.set_result(text.strip())
            await update.message.reply_text("✅ Code received, submitting...")
            return COLLECTING

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Get conversation history
    conv = await get_or_create_conversation(chat_id)
    history = list(conv.conversation_history or [])

    try:
        agent = get_agent()
        ai_reply, new_history, extracted = await agent.continue_collection(
            text, history, doc_type
        )
    except Exception as e:
        logger.exception("AI error: %s", e)
        await update.message.reply_text(
            f"⚠️ AI error: {e}\n\nPlease try again or type /cancel to start over."
        )
        return COLLECTING

    # Save conversation history
    await append_conversation_message(chat_id, "user", text)
    await append_conversation_message(chat_id, "assistant", ai_reply)

    # Check if data collection is complete
    if extracted and extracted.get("collection_complete"):
        # Remove the flag
        extracted.pop("collection_complete", None)
        context.user_data["deal_data"] = extracted
        await update_session_data(chat_id, extracted)

        # Show summary for confirmation
        summary = _format_deal_summary(extracted, doc_type)
        await update.message.reply_text(
            f"✅ *Data Collection Complete!*\n\n{summary}\n\n"
            f"Please review and confirm:",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard(),
        )
        return CONFIRMING

    # Send AI response (trim if too long for Telegram)
    if len(ai_reply) > 4000:
        ai_reply = ai_reply[:4000] + "..."

    await update.message.reply_text(ai_reply)
    return COLLECTING


def _format_deal_summary(data: dict, doc_type: str) -> str:
    """Format deal data as a readable summary."""
    lines = []

    # Property
    addr_parts = [
        data.get("property_street_number", ""),
        data.get("property_street_name", ""),
    ]
    addr = " ".join(p for p in addr_parts if p).strip()
    unit = data.get("property_unit")
    if unit:
        addr += f", Unit {unit}"
    city = data.get("property_city", "")
    if addr or city:
        lines.append(f"🏠 *Property:* {addr}, {city}")

    # Parties
    buyer = data.get("buyer_1", "")
    buyer2 = data.get("buyer_2", "")
    if buyer:
        b = buyer
        if buyer2:
            b += f" & {buyer2}"
        lines.append(f"👤 *Buyer(s):* {b}")

    seller = data.get("seller_1", "")
    seller2 = data.get("seller_2", "")
    if seller:
        s = seller
        if seller2:
            s += f" & {seller2}"
        lines.append(f"👤 *Seller(s):* {s}")

    # Financial
    price = data.get("purchase_price")
    if price:
        lines.append(f"💰 *Price:* ${price:,}" if isinstance(price, (int, float)) else f"💰 *Price:* {price}")

    deposit = data.get("deposit")
    if deposit:
        lines.append(f"💵 *Deposit:* ${deposit:,}" if isinstance(deposit, (int, float)) else f"💵 *Deposit:* {deposit}")

    holder = data.get("deposit_holder")
    if holder:
        lines.append(f"🏦 *Deposit Holder:* {holder}")

    # Dates
    for label, key in [("Offer Date", "offer_date"), ("Closing Date", "closing_date"),
                       ("Irrevocability", "irrevocability_date")]:
        val = data.get(key)
        if val:
            lines.append(f"📅 *{label}:* {val}")

    # Conditions
    conditions = []
    if data.get("financing_condition"):
        conditions.append("Financing")
    if data.get("home_inspection"):
        conditions.append("Home Inspection")
    if data.get("status_certificate"):
        conditions.append("Status Certificate")
    if data.get("sale_of_buyers_property"):
        conditions.append("Sale of Buyer's Property")
    if conditions:
        lines.append(f"📋 *Conditions:* {', '.join(conditions)}")

    return "\n".join(lines) if lines else "_No data collected_"


# ── Confirmation ──────────────────────────────────────────────────


async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirm/edit button clicks."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "confirm_generate":
        return await _start_generation(update, context)

    elif data == "confirm_edit":
        await query.edit_message_text(
            "✏️ What would you like to change? Just tell me "
            "(e.g., \"change the price to 800000\" or \"buyer name is John Smith\")."
        )
        return COLLECTING

    elif data == "cancel":
        return await cancel_command(update, context)

    return CONFIRMING


async def _start_generation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start document generation."""
    query = update.callback_query
    chat_id = update.effective_user.id
    doc_type = context.user_data.get("doc_type", "aps")
    deal_data = context.user_data.get("deal_data", {})

    await query.edit_message_text("⏳ Generating document... This may take a moment.")
    await set_session_state(chat_id, "generating")

    try:
        two_fa = make_two_factor_callback(chat_id, context.bot)
        pdf_path = await generate_document(doc_type, deal_data, two_factor_callback=two_fa)

        # Store result
        td_result = get_last_td_result()
        context.user_data["last_pdf_path"] = pdf_path
        context.user_data["last_td_tx_uuid"] = td_result.get("transaction_uuid")

        # Send the PDF
        with open(pdf_path, "rb") as f:
            doc_name = DOC_TYPE_NAMES.get(doc_type, doc_type)
            caption = f"✅ *{doc_name}* generated successfully!"

            if td_result.get("success"):
                form_url = td_result.get("form_url", "")
                caption += f"\n\n🔗 [Open in TransactionDesk]({form_url})"

            await context.bot.send_document(
                chat_id=chat_id,
                document=InputFile(f, filename=f"{doc_type}_document.pdf"),
                caption=caption,
                parse_mode="Markdown",
            )

        # Send screenshot if available
        screenshot = td_result.get("screenshot_path")
        if screenshot:
            try:
                with open(screenshot, "rb") as f:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=InputFile(f, filename="form_preview.png"),
                        caption="📸 Form preview from TransactionDesk",
                    )
            except Exception:
                pass

        # Save transaction to DB
        from db.operations import create_transaction, update_transaction
        tx = await create_transaction(chat_id, doc_type, deal_data)
        if td_result.get("transaction_uuid"):
            await update_transaction(
                tx.id,
                td_transaction_uuid=td_result["transaction_uuid"],
                td_form_uuid=td_result.get("form_uuid"),
                status="generated",
            )
        context.user_data["transaction_id"] = tx.id

        # Show next actions
        await context.bot.send_message(
            chat_id=chat_id,
            text="What would you like to do next?",
            reply_markup=post_generate_keyboard(has_transactiondesk=_is_td_configured()),
        )
        return POST_GENERATE

    except Exception as e:
        logger.exception("Document generation failed: %s", e)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Generation failed: {e}\n\nType /start to try again.",
        )
        return ConversationHandler.END


# ── Post-Generation Actions ───────────────────────────────────────


async def post_generate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle post-generation action buttons."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "action_td_sign":
        await query.edit_message_text(
            "✍️ *Create Signing Session*\n\n"
            "Please provide the signer emails, one per line:\n"
            "```\nbuyer@email.com\nseller@email.com\n```",
            parse_mode="Markdown",
        )
        return SIGNING

    elif data == "action_email":
        await query.edit_message_text(
            "📧 Enter the recipient email address(es), separated by commas:"
        )
        context.user_data["pending_action"] = "email"
        return SIGNING

    elif data == "menu_new_doc":
        await query.edit_message_text(
            "📄 *What document would you like to create?*",
            parse_mode="Markdown",
            reply_markup=doc_type_keyboard(),
        )
        return SELECTING_DOC

    elif data == "menu_main":
        await query.edit_message_text(
            "🏠 *Main Menu*",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return IDLE

    return POST_GENERATE


# ── Signing ───────────────────────────────────────────────────────


async def signing_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle signer email input."""
    text = update.message.text.strip()
    chat_id = update.effective_user.id

    # Check for 2FA code
    if chat_id in _pending_2fa and re.match(r"^\d{4,8}$", text):
        future = _pending_2fa.get(chat_id)
        if future and not future.done():
            future.set_result(text)
            await update.message.reply_text("✅ Code received.")
            return SIGNING

    pending = context.user_data.get("pending_action")

    if pending == "email":
        # Email delivery
        emails = [e.strip() for e in text.replace("\n", ",").split(",") if "@" in e]
        if not emails:
            await update.message.reply_text("⚠️ No valid emails found. Try again:")
            return SIGNING

        from integrations.delivery import send_email
        pdf_path = context.user_data.get("last_pdf_path")
        if pdf_path:
            success = await send_email(
                to=emails,
                subject="Real Estate Document",
                body="Please find the attached document.",
                attachment_path=pdf_path,
            )
            if success:
                await update.message.reply_text(f"✅ Email sent to {', '.join(emails)}")
            else:
                await update.message.reply_text("❌ Email sending failed. Check SMTP configuration.")
        else:
            await update.message.reply_text("⚠️ No document to send.")

        context.user_data.pop("pending_action", None)
        await update.message.reply_text(
            "What's next?",
            reply_markup=post_generate_keyboard(has_transactiondesk=_is_td_configured()),
        )
        return POST_GENERATE

    # Authentisign signing
    emails = [e.strip() for e in text.replace("\n", ",").split(",") if "@" in e]
    if not emails:
        await update.message.reply_text("⚠️ No valid emails found. Please provide emails:")
        return SIGNING

    tx_uuid = context.user_data.get("last_td_tx_uuid")
    if not tx_uuid:
        await update.message.reply_text("⚠️ No TransactionDesk transaction found for signing.")
        return POST_GENERATE

    await update.message.reply_text("✍️ Creating Authentisign session...")

    try:
        from integrations.transactiondesk import TransactionDeskClient

        two_fa = make_two_factor_callback(chat_id, context.bot)
        td = TransactionDeskClient(two_factor_callback=two_fa)

        signers = [{"name": f"Signer {i+1}", "email": email} for i, email in enumerate(emails)]
        result = await td.create_signing_session(tx_uuid, signers)

        if result.get("success"):
            await update.message.reply_text(
                f"✅ Signing session created!\n"
                f"📧 Emails sent to: {', '.join(emails)}\n"
                f"🔗 {result.get('url', '')}"
            )
        else:
            await update.message.reply_text(f"❌ Signing failed: {result.get('error', 'Unknown')}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

    await update.message.reply_text(
        "What's next?",
        reply_markup=post_generate_keyboard(has_transactiondesk=_is_td_configured()),
    )
    return POST_GENERATE


# ── Idle Message Handler ──────────────────────────────────────────


async def idle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle messages in IDLE state — route to appropriate action."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return IDLE

    text = update.message.text.strip().lower()

    # Check for TransactionDesk / REALM URLs
    full_text = update.message.text.strip()
    if any(domain in full_text for domain in ["transactiondesk.com", "torontomls.net", "ampre.ca"]):
        await update.message.reply_text(
            "🔗 I see a portal URL. Use /realmtest to test the connection, "
            "or choose *Create New Document* to start filling a form.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return IDLE

    # Check for intent to create a document
    doc_keywords = {
        "offer": "aps", "aps": "aps", "purchase": "aps", "buy": "aps",
        "amendment": "amendment", "amend": "amendment",
        "waiver": "waiver", "waive": "waiver",
        "lease": "lease", "rent": "lease",
        "commercial": "commercial_aps",
        "notice": "notice",
    }

    for keyword, doc_type in doc_keywords.items():
        if keyword in text:
            doc_name = DOC_TYPE_NAMES.get(doc_type, doc_type)
            context.user_data["doc_type"] = doc_type
            await set_session_state(user.id, "collecting", doc_type=doc_type)

            await update.message.reply_text(
                f"📝 *Creating: {doc_name}*\n\n"
                f"Let's start — what is the *property address*?",
                parse_mode="Markdown",
            )
            return COLLECTING

    # Default: show menu
    await update.message.reply_text(
        "I can help you create real estate documents. "
        "What would you like to do?",
        reply_markup=main_menu_keyboard(),
    )
    return IDLE


# ── Build Conversation Handler ────────────────────────────────────


def build_conversation_handler() -> ConversationHandler:
    """Build and return the main ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CommandHandler("new", lambda u, c: menu_callback.__wrapped__(u, c) if False else _new_doc_entry(u, c)),
            CommandHandler("realmtest", realm_test_command),
            CommandHandler("help", help_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, idle_message),
        ],
        states={
            IDLE: [
                CallbackQueryHandler(menu_callback, pattern="^menu_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, idle_message),
            ],
            SELECTING_DOC: [
                CallbackQueryHandler(doc_type_callback, pattern="^doc_|^cancel"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, doc_type_text),
            ],
            COLLECTING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collecting_message),
                CallbackQueryHandler(cancel_command, pattern="^cancel"),
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirm_callback, pattern="^confirm_|^cancel"),
            ],
            POST_GENERATE: [
                CallbackQueryHandler(post_generate_callback, pattern="^action_|^menu_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, signing_message),
            ],
            SIGNING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, signing_message),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
        ],
        allow_reentry=False,
        per_message=False,
    )


async def _new_doc_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /new command."""
    await update.message.reply_text(
        "📄 *What document would you like to create?*",
        parse_mode="Markdown",
        reply_markup=doc_type_keyboard(),
    )
    return SELECTING_DOC
