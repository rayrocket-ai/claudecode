"""`/launch` — Listing Launch Agent conversation handler.

Turns one address (or MLS#) into a full marketing campaign: the agent drafts
copy, a feature sheet, a reel script, an email/SMS blast, and an open house;
the user reviews, optionally sets blast recipients, and publishes. Nothing is
sent without an explicit tap on "Publish".

FSM states:
  LAUNCH_INPUT (0)      → user provides the listing (address/MLS#/details)
  LAUNCH_REVIEW (1)     → user reviews the drafted campaign, publishes/revises
  LAUNCH_RECIPIENTS (2) → user provides email-blast recipients
"""

from __future__ import annotations

import logging
import re

from telegram import Update, InputFile
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ai.listing_agent import get_listing_agent
from bot.handlers.conversation import _is_authorized, _md_escape, _send
from bot.keyboards import launch_review_keyboard
from config import STORAGE_DIR, get_settings
from integrations.campaign import launch_campaign
from integrations.mls import lookup_mls

logger = logging.getLogger(__name__)

LAUNCH_INPUT, LAUNCH_REVIEW, LAUNCH_RECIPIENTS = range(3)

_MLS_RE = re.compile(r"^[A-Z]?\d{5,10}$")
_EMAIL_RE = re.compile(r"[^\s,;]+@[^\s,;]+\.[^\s,;]+")


# ── Listing intake ────────────────────────────────────────────────


async def _build_listing(text: str) -> dict:
    """Turn the user's input into a listing dict.

    If the input is a bare MLS number, enrich it via REALTOR.ca; otherwise
    treat the free text as the property description/facts for the agent.
    """
    token = text.strip()
    listing: dict = {}

    if _MLS_RE.match(token.upper()):
        found = await lookup_mls(token)
        if found:
            listing.update({k: v for k, v in found.items() if v})
            return listing
        # Lookup failed/blocked — still record the number and let the user's
        # later detail (if any) carry the campaign.
        listing["mls_number"] = token

    # Free-form details: hand them to the agent as remarks + a best-guess
    # address (first line that looks like a street address).
    listing.setdefault("description", token)
    for line in token.splitlines():
        if re.search(r"\d+\s+\w+", line) and "address" not in listing:
            listing["address"] = line.strip()
            break
    return listing


async def launch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for /launch [address or MLS#]."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return ConversationHandler.END

    settings = get_settings()
    if not settings.is_marketing_configured:
        await update.message.reply_text(
            "⚠️ Marketing needs ANTHROPIC_API_KEY set to draft campaigns."
        )
        return ConversationHandler.END

    context.user_data.pop("campaign", None)
    context.user_data.pop("recipients", None)

    arg = " ".join(context.args) if context.args else ""
    if arg.strip():
        return await _draft_and_review(update, context, arg)

    await update.message.reply_text(
        "🚀 *Listing Launch*\n\n"
        "Send me the listing to launch — an *MLS number*, an *address*, or a "
        "few lines of detail (price, beds/baths, standout features).\n\n"
        "I'll draft the full campaign: copy, feature sheet, a reel script, a "
        "just-listed email + SMS, and an open house.",
        parse_mode="Markdown",
    )
    return LAUNCH_INPUT


async def launch_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the listing details message."""
    return await _draft_and_review(update, context, update.message.text)


async def _draft_and_review(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> int:
    """Draft the campaign with Claude and present it for review."""
    chat_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    await _send(update, "🧠 Drafting your launch campaign...")

    listing = await _build_listing(text)
    context.user_data["listing"] = listing

    try:
        agent = get_listing_agent()
        campaign = await agent.draft_campaign(listing)
    except Exception as e:
        logger.exception("Campaign drafting failed: %s", e)
        await _send(update, f"⚠️ Drafting failed: {e}\n\nTry again or /cancel.")
        return LAUNCH_INPUT

    if not campaign:
        await _send(
            update,
            "I couldn't draft a campaign from that. Add a bit more detail "
            "(address, price, a few features) and try again.",
        )
        return LAUNCH_INPUT

    context.user_data["campaign"] = campaign
    await _send_campaign_preview(update, context, campaign)
    return LAUNCH_REVIEW


def _format_campaign_preview(campaign: dict) -> str:
    """Readable summary of the drafted assets for Telegram."""
    lines = ["✅ *Campaign drafted!*\n"]

    short = campaign.get("listing_copy_short")
    if short:
        lines.append(f"📝 *Hook:* {_md_escape(short)}")

    sheet = campaign.get("feature_sheet") or {}
    if sheet.get("headline"):
        n = len(sheet.get("highlights") or [])
        lines.append(f"📄 *Feature sheet:* {_md_escape(sheet['headline'])} ({n} highlights)")

    reel = campaign.get("reel_script") or {}
    if reel.get("hook"):
        n = len(reel.get("shots") or [])
        lines.append(f"🎬 *Reel:* {n}-shot script ready")

    email = campaign.get("email") or {}
    if email.get("subject"):
        lines.append(f"📧 *Email:* \"{_md_escape(email['subject'])}\"")

    if campaign.get("sms"):
        lines.append("💬 *SMS:* ready")

    oh = campaign.get("open_house") or {}
    if oh.get("title"):
        when = " ".join(x for x in (oh.get("day_of_week"), oh.get("time_range")) if x)
        lines.append(f"📅 *Open house:* {_md_escape(oh['title'])}{f' — {_md_escape(when)}' if when else ''}")

    captions = campaign.get("social_captions") or []
    if captions:
        lines.append(f"📱 *Social captions:* {len(captions)} ready")

    lines.append("\nReview below, then publish. Set blast recipients to actually email it.")
    return "\n".join(lines)


async def _send_campaign_preview(
    update: Update, context: ContextTypes.DEFAULT_TYPE, campaign: dict
) -> None:
    has_recipients = bool(context.user_data.get("recipients"))
    text = _format_campaign_preview(campaign)
    try:
        await _send(update, text, parse_mode="Markdown",
                    reply_markup=launch_review_keyboard(has_recipients))
    except Exception:
        await _send(update, text.replace("*", ""),
                    reply_markup=launch_review_keyboard(has_recipients))


# ── Review actions ────────────────────────────────────────────────


async def launch_review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle publish / recipients / revise buttons."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "launch_publish":
        return await _publish(update, context)

    if data == "launch_recipients":
        await query.edit_message_text(
            "📧 Send the recipient email(s) for the just-listed blast, "
            "separated by commas.\n\n(Requires SMTP configured to actually send.)"
        )
        return LAUNCH_RECIPIENTS

    if data == "launch_revise":
        await query.edit_message_text(
            "✏️ Send updated or additional listing details and I'll redraft."
        )
        return LAUNCH_INPUT

    if data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Launch cancelled.")
        return ConversationHandler.END

    return LAUNCH_REVIEW


async def launch_recipients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collect email-blast recipients, then return to review."""
    emails = _EMAIL_RE.findall(update.message.text or "")
    if not emails:
        await update.message.reply_text("⚠️ No valid emails found. Try again, or /cancel.")
        return LAUNCH_RECIPIENTS

    context.user_data["recipients"] = emails
    await update.message.reply_text(f"✅ Blast will go to: {', '.join(emails)}")
    campaign = context.user_data.get("campaign") or {}
    await _send_campaign_preview(update, context, campaign)
    return LAUNCH_REVIEW


async def _publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Run every channel and report results."""
    query = update.callback_query
    chat_id = update.effective_user.id
    campaign = context.user_data.get("campaign")
    if not campaign:
        await query.edit_message_text("⚠️ Lost the drafted campaign. Start over with /launch.")
        return ConversationHandler.END

    recipients = context.user_data.get("recipients")
    await query.edit_message_text("🚀 Publishing campaign...")

    results = await launch_campaign(campaign, recipients=recipients)

    icon = {"sent": "✅", "drafted": "📝", "skipped": "⏭️", "failed": "❌"}
    lines = ["*Launch results:*\n"]
    for r in results:
        lines.append(f"{icon.get(r.status, '•')} *{r.channel.replace('_', ' ').title()}* — {r.detail}")
    await context.bot.send_message(
        chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown"
    )

    # Deliver the pasteable assets so the user can act immediately.
    await _deliver_assets(context, chat_id, campaign, results)

    context.user_data.clear()
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎉 Campaign ready. Run /launch again for the next listing.",
    )
    return ConversationHandler.END


async def _deliver_assets(context, chat_id: int, campaign: dict, results) -> None:
    """Send the full copy and any generated files back to the user."""
    long_copy = campaign.get("listing_copy_long")
    if long_copy:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📝 *Listing copy:*\n\n{_md_escape(long_copy)}"[:4000],
            parse_mode="Markdown",
        )

    captions = campaign.get("social_captions") or []
    if captions:
        body = "\n\n".join(f"• {c}" for c in captions)
        await context.bot.send_message(chat_id=chat_id, text=f"📱 Social captions:\n\n{body}"[:4000])

    reel = campaign.get("reel_script") or {}
    if reel.get("shots"):
        shots = "\n".join(f"{i+1}. {s}" for i, s in enumerate(reel["shots"]))
        text = f"🎬 Reel script\nHook: {reel.get('hook','')}\n\n{shots}\n\nCTA: {reel.get('cta','')}"
        await context.bot.send_message(chat_id=chat_id, text=text[:4000])

    sms = campaign.get("sms")
    if sms:
        await context.bot.send_message(chat_id=chat_id, text=f"💬 SMS:\n{sms}")

    # Open-house calendar invite as a real .ics file.
    for r in results:
        if r.channel == "open_house" and r.payload.get("ics"):
            path = STORAGE_DIR / f"open_house_{chat_id}.ics"
            try:
                path.write_text(r.payload["ics"], encoding="utf-8")
                with open(path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=InputFile(f, filename="open_house.ics"),
                        caption="📅 Add this open house to your calendar.",
                    )
            except Exception:
                logger.exception("Failed to send open-house .ics")


async def launch_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await _send(update, "❌ Launch cancelled.")
    return ConversationHandler.END


# ── Build handler ─────────────────────────────────────────────────


def build_listing_handler() -> ConversationHandler:
    """ConversationHandler for the /launch flow."""
    return ConversationHandler(
        entry_points=[CommandHandler("launch", launch_command)],
        states={
            LAUNCH_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, launch_input),
            ],
            LAUNCH_REVIEW: [
                CallbackQueryHandler(launch_review_callback, pattern="^launch_|^cancel"),
            ],
            LAUNCH_RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, launch_recipients),
            ],
        },
        fallbacks=[CommandHandler("cancel", launch_cancel)],
        allow_reentry=True,
        per_message=False,
    )
