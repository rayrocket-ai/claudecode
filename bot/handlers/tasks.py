"""Telegram handlers for team task management (the "Ops Manager" loop).

Manager commands:
  /assign <free text>          — AI parses & assigns task(s) to team member(s)
  /tasks                       — list open tasks (manager: all; agent: own)
  /checklist <key> [@Name] <deal ref> — fan an Ontario checklist into tasks
  /team                        — list registered team members
  /addagent <id> <name> [manager]  — register a team member
  /removeagent <id>            — deactivate a team member
  /done <task_id>              — mark a task done

Agents interact via inline buttons on each task card (Done / Blocked / Snooze /
Update) and can reply in natural language after tapping Update.

Follow-ups are DB-driven: a recurring scan (scan_task_followups) reads
`next_followup_at` from the DB, so reminders/escalations survive restarts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from dateutil import parser as date_parser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai.agent import get_ops_agent
from bot.handlers.conversation import _is_authorized, _md_escape
from config import get_settings
from db.operations import (
    append_task_note,
    create_task,
    deactivate_team_member,
    get_task,
    get_team_member,
    get_team_member_by_name,
    list_due_followups,
    list_open_tasks,
    list_tasks_for_assignee,
    list_team_members,
    mark_task_done,
    update_task,
    upsert_team_member,
)
from ops import followups
from ops.checklists import checklist_keys, get_checklist

logger = logging.getLogger(__name__)

_URGENCY_EMOJI = {"high": "🔴", "standard": "🟡", "low": "⚪"}


# ── Auth ────────────────────────────────────────────────────────────


async def _is_manager(user_id: int) -> bool:
    """Manager = in the config manager list, or a DB member with role 'manager'.

    The config list bootstraps the first manager before anyone is registered.
    """
    settings = get_settings()
    if user_id in settings.manager_user_id_list:
        return True
    member = await get_team_member(user_id)
    return bool(member and member.role == "manager" and member.active)


def _manager_ids() -> list[int]:
    """Config-declared managers to escalate to (always available)."""
    return get_settings().manager_user_id_list


# ── Formatting / delivery ───────────────────────────────────────────


def _task_keyboard(task_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Done", callback_data=f"task_done_{task_id}"),
            InlineKeyboardButton("🚧 Blocked", callback_data=f"task_blocked_{task_id}"),
        ],
        [
            InlineKeyboardButton("⏳ Snooze", callback_data=f"task_snooze_{task_id}"),
            InlineKeyboardButton("💬 Update", callback_data=f"task_update_{task_id}"),
        ],
    ])


def _format_task(task, *, prefix: str = "") -> str:
    urg = _URGENCY_EMOJI.get(task.urgency, "🟡")
    lines = [f"{prefix}{urg} *{_md_escape(task.title)}*"]
    if task.description:
        lines.append(_md_escape(task.description))
    if task.deal_ref:
        lines.append(f"🏠 {_md_escape(task.deal_ref)}")
    if task.due_at:
        lines.append(f"📅 Due: {task.due_at:%Y-%m-%d}")
    lines.append(f"🆔 `{task.id[:8]}`")
    return "\n".join(lines)


async def _deliver_task(bot, task, *, prefix: str = "📋 *New task*\n\n") -> None:
    """DM the assignee their task with action buttons."""
    try:
        await bot.send_message(
            chat_id=task.assignee_telegram_id,
            text=prefix + _format_task(task),
            parse_mode="Markdown",
            reply_markup=_task_keyboard(task.id),
        )
    except Exception as e:  # noqa: BLE001 — an unreachable agent must not crash the loop
        logger.warning("task.deliver_failed task=%s err=%s", task.id, e)


async def _notify(bot, chat_ids: list[int], text: str) -> None:
    for cid in dict.fromkeys(chat_ids):  # dedup, preserve order
        try:
            await bot.send_message(chat_id=cid, text=text, parse_mode="Markdown")
        except Exception as e:  # noqa: BLE001
            logger.warning("task.notify_failed chat=%s err=%s", cid, e)


def _parse_due(due_date: str | None) -> datetime | None:
    if not due_date:
        return None
    try:
        # Model emits YYYY-MM-DD; anchor at midday UTC (approx end-of-morning
        # Ontario) so the first reminder lands during the working day.
        d = date_parser.parse(due_date)
        return d.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)
    except (ValueError, OverflowError):
        return None


# ── Commands ────────────────────────────────────────────────────────


async def addagent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/addagent <telegram_id> <name...> [manager]"""
    user = update.effective_user
    if not await _is_manager(user.id):
        await update.message.reply_text("⛔ Only managers can register team members.")
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/addagent <telegram_id> <name> [manager]`\n"
            "The person can send /whoami to find their Telegram ID.",
            parse_mode="Markdown",
        )
        return

    try:
        telegram_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ The first argument must be a numeric Telegram ID.")
        return

    role = "agent"
    name_parts = args[1:]
    if name_parts and name_parts[-1].lower() == "manager":
        role = "manager"
        name_parts = name_parts[:-1]
    name = " ".join(name_parts).strip()
    if not name:
        await update.message.reply_text("⚠️ Please provide a name.")
        return

    member = await upsert_team_member(telegram_id, name, role)
    await update.message.reply_text(
        f"✅ Registered *{_md_escape(member.name)}* as {member.role} "
        f"(ID `{member.telegram_id}`).\n\n"
        f"⚠️ Make sure `{member.telegram_id}` is also in AUTHORIZED_USER_IDS so "
        f"they can use the bot.",
        parse_mode="Markdown",
    )


async def removeagent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/removeagent <telegram_id>"""
    user = update.effective_user
    if not await _is_manager(user.id):
        await update.message.reply_text("⛔ Only managers can remove team members.")
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/removeagent <telegram_id>`", parse_mode="Markdown")
        return
    try:
        telegram_id = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Provide a numeric Telegram ID.")
        return
    ok = await deactivate_team_member(telegram_id)
    await update.message.reply_text("✅ Removed." if ok else "⚠️ No such team member.")


async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/team — list registered members."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Not authorized.")
        return
    members = await list_team_members(active_only=True)
    if not members:
        await update.message.reply_text(
            "No team members yet. A manager can add one with "
            "`/addagent <telegram_id> <name>`.",
            parse_mode="Markdown",
        )
        return
    lines = [f"👥 *Team ({len(members)}):*"]
    for m in members:
        badge = "👑" if m.role == "manager" else "•"
        lines.append(f"{badge} {_md_escape(m.name)} — `{m.telegram_id}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def assign_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/assign <natural language> — parse & assign task(s)."""
    user = update.effective_user
    if not await _is_manager(user.id):
        await update.message.reply_text("⛔ Only managers can assign tasks.")
        return

    request = " ".join(context.args or []).strip()
    if not request:
        await update.message.reply_text(
            "Usage: `/assign <what needs doing>`\n"
            "e.g. `/assign ask Sarah to book the home inspection for 123 Main St by Friday`",
            parse_mode="Markdown",
        )
        return

    members = await list_team_members(active_only=True)
    roster = [{"name": m.name, "role": m.role} for m in members]
    if not roster:
        await update.message.reply_text(
            "No team members registered. Add one first with "
            "`/addagent <telegram_id> <name>`.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text("🤔 Parsing your request...")

    try:
        parsed = await get_ops_agent().parse_task_request(request, roster)
    except Exception as e:  # noqa: BLE001
        logger.exception("assign.parse_error: %s", e)
        await update.message.reply_text(f"❌ Could not parse the request: {e}")
        return

    if not parsed:
        await update.message.reply_text(
            "⚠️ I couldn't identify a task in that. Try being explicit, e.g. "
            "`/assign have John deliver the APS to the lawyer for 55 King St`.",
            parse_mode="Markdown",
        )
        return

    created, unresolved = [], []
    now = followups.now_utc()
    settings = get_settings()
    for t in parsed:
        member = await get_team_member_by_name(t.get("assignee_name", ""))
        if member is None:
            unresolved.append(t.get("assignee_name", "?"))
            continue
        urgency = t.get("urgency") or "standard"
        due_at = _parse_due(t.get("due_date"))
        first_followup = followups.initial_followup_at(
            now=now, due_at=due_at, urgency=urgency,
            followup_hours=settings.task_followup_hours,
            escalate_hours=settings.task_escalate_hours,
        )
        task = await create_task(
            title=t.get("title", "Task"),
            description=t.get("description"),
            assignee_telegram_id=member.telegram_id,
            assigner_telegram_id=user.id,
            deal_ref=t.get("deal_ref"),
            urgency=urgency,
            due_at=due_at,
            next_followup_at=first_followup,
        )
        await _deliver_task(context.bot, task)
        created.append((task, member))

    lines = []
    if created:
        lines.append(f"✅ *Assigned {len(created)} task(s):*")
        for task, member in created:
            lines.append(f"• {_md_escape(task.title)} → {_md_escape(member.name)}")
    if unresolved:
        lines.append(
            "\n⚠️ Couldn't match: "
            + ", ".join(_md_escape(n) for n in unresolved)
            + ". Check /team or register them with /addagent."
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/tasks — manager sees all open tasks; agent sees their own."""
    user = update.effective_user
    if not _is_authorized(user.id):
        await update.message.reply_text("⛔ Not authorized.")
        return

    if await _is_manager(user.id):
        tasks = await list_open_tasks()
        header = f"📋 *Open tasks ({len(tasks)}):*"
    else:
        tasks = await list_tasks_for_assignee(user.id)
        header = f"📋 *Your open tasks ({len(tasks)}):*"

    if not tasks:
        await update.message.reply_text("📭 No open tasks. 🎉")
        return

    await update.message.reply_text(header, parse_mode="Markdown")
    for task in tasks[:25]:
        # Managers get a read-only list; assignees get action buttons.
        markup = _task_keyboard(task.id) if task.assignee_telegram_id == user.id else None
        suffix = ""
        if await _is_manager(user.id) and task.assignee_telegram_id != user.id:
            member = await get_team_member(task.assignee_telegram_id)
            who = member.name if member else str(task.assignee_telegram_id)
            suffix = f"\n👤 {_md_escape(who)} — _{task.status}_"
        await context.bot.send_message(
            chat_id=user.id,
            text=_format_task(task) + suffix,
            parse_mode="Markdown",
            reply_markup=markup,
        )


async def checklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/checklist <key> [@Name] <deal ref> — fan a template into tasks."""
    user = update.effective_user
    if not await _is_manager(user.id):
        await update.message.reply_text("⛔ Only managers can generate checklists.")
        return

    args = list(context.args or [])
    if not args:
        await update.message.reply_text(
            "Usage: `/checklist <type> [@Name] <deal ref>`\n"
            f"Types: {', '.join(checklist_keys())}\n"
            "e.g. `/checklist listing @Sarah 123 Main St`",
            parse_mode="Markdown",
        )
        return

    checklist = get_checklist(args[0])
    if checklist is None:
        await update.message.reply_text(
            f"⚠️ Unknown checklist. Available: {', '.join(checklist_keys())}."
        )
        return
    args = args[1:]

    # Optional @Name assignee; default to the manager themselves.
    assignee = await get_team_member(user.id)
    assignee_id = user.id
    assignee_name = assignee.name if assignee else "you"
    if args and args[0].startswith("@"):
        member = await get_team_member_by_name(args[0][1:])
        if member is None:
            await update.message.reply_text(f"⚠️ No team member matching {args[0]}. Check /team.")
            return
        assignee_id, assignee_name = member.telegram_id, member.name
        args = args[1:]

    deal_ref = " ".join(args).strip() or None

    now = followups.now_utc()
    settings = get_settings()
    count = 0
    for item in checklist.items:
        due_at = None
        if item.offset_days is not None:
            due_at = (now + timedelta(days=item.offset_days)).replace(
                hour=12, minute=0, second=0, microsecond=0
            )
        first_followup = followups.initial_followup_at(
            now=now, due_at=due_at, urgency=item.urgency,
            followup_hours=settings.task_followup_hours,
            escalate_hours=settings.task_escalate_hours,
        )
        task = await create_task(
            title=item.title,
            description=item.description,
            assignee_telegram_id=assignee_id,
            assigner_telegram_id=user.id,
            deal_ref=deal_ref,
            urgency=item.urgency,
            due_at=due_at,
            next_followup_at=first_followup,
            checklist_key=checklist.key,
            checklist_item=item.title,
        )
        await _deliver_task(context.bot, task, prefix="📋 *Checklist task*\n\n")
        count += 1

    await update.message.reply_text(
        f"✅ Created *{count}* '{checklist.name}' tasks"
        + (f" for {_md_escape(deal_ref)}" if deal_ref else "")
        + f", assigned to *{_md_escape(assignee_name)}*.",
        parse_mode="Markdown",
    )


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/done <task_id> — mark a task complete (assignee or manager)."""
    user = update.effective_user
    if not _is_authorized(user.id):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/done <task_id>`", parse_mode="Markdown")
        return
    await _complete_task(context.bot, args[0], user.id, update.message.reply_text)


# ── Callback buttons ────────────────────────────────────────────────


async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Done / Blocked / Snooze / Update button presses."""
    query = update.callback_query
    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await query.answer("⛔ Not authorized.")
        return
    await query.answer()

    parts = query.data.split("_", 2)  # ["task", action, id]
    if len(parts) < 3:
        return
    action, task_id = parts[1], parts[2]

    task = await get_task(task_id)
    if task is None:
        await query.edit_message_text("⚠️ This task no longer exists.")
        return

    if action == "done":
        await _complete_task(context.bot, task_id, user_id, None, query=query)
    elif action == "blocked":
        await update_task(task_id, status="blocked")
        await append_task_note(task_id, "blocked", f"Marked blocked by {user_id}")
        await query.edit_message_text(query.message.text + "\n\n🚧 BLOCKED — manager notified")
        member = await get_team_member(user_id)
        who = member.name if member else str(user_id)
        await _notify(
            context.bot, _escalation_targets(task),
            f"🚧 *{_md_escape(who)}* is blocked on: {_md_escape(task.title)}",
        )
    elif action == "snooze":
        settings = get_settings()
        nxt = followups.next_followup_at(
            now=followups.now_utc(), urgency=task.urgency,
            followup_hours=settings.task_followup_hours,
            escalate_hours=settings.task_escalate_hours,
        )
        await update_task(task_id, status="acknowledged", next_followup_at=nxt)
        await append_task_note(task_id, "snooze", "Snoozed by assignee")
        await query.edit_message_text(query.message.text + "\n\n⏳ Snoozed — I'll remind you again.")
    elif action == "update":
        context.user_data["awaiting_task_update"] = task_id
        await query.message.reply_text(
            "💬 Reply with your update (e.g. \"done\", \"waiting on the lawyer\", "
            "\"need another day\"). I'll update the task.",
        )


async def _complete_task(bot, task_id: str, user_id: int, reply, *, query=None) -> None:
    task = await get_task(task_id)
    if task is None:
        if reply:
            await reply("⚠️ No such task.")
        return
    task = await mark_task_done(task_id, note=f"Completed by {user_id}")
    member = await get_team_member(user_id)
    who = member.name if member else str(user_id)
    if query is not None:
        await query.edit_message_text(query.message.text + "\n\n✅ DONE")
    elif reply:
        await reply(f"✅ Marked done: {task.title}")
    # Report back to the manager(s) / assigner.
    targets = _escalation_targets(task)
    deal = f" ({task.deal_ref})" if task.deal_ref else ""
    await _notify(
        bot, targets,
        f"✅ *{_md_escape(who)}* completed: {_md_escape(task.title)}{_md_escape(deal)}",
    )


def _escalation_targets(task) -> list[int]:
    """Who to notify about a task: its assigner plus config managers.

    The assignee is excluded so a manager acting on their own task isn't
    pinged about their own action.
    """
    targets = [task.assigner_telegram_id, *_manager_ids()]
    return [t for t in targets if t != task.assignee_telegram_id]


# ── Natural-language update catcher ─────────────────────────────────


async def task_update_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Interpret a free-text update, but only right after the user tapped 💬 Update.

    Gated by `context.user_data["awaiting_task_update"]` (set by the Update
    button) so it never swallows messages meant for the OREA conversation flow —
    same opt-in pattern as the showings counter catcher.
    """
    task_id = context.user_data.get("awaiting_task_update")
    if not task_id:
        return  # not awaiting an update — let other handlers process this
    if not update.message or not update.message.text:
        return
    if not _is_authorized(update.effective_user.id):
        return

    context.user_data.pop("awaiting_task_update", None)
    text = update.message.text.strip()
    task = await get_task(task_id)
    if task is None:
        await update.message.reply_text("⚠️ That task no longer exists.")
        raise ApplicationHandlerStop

    try:
        result = await get_ops_agent().interpret_reply(text, task.title, task.description)
    except Exception as e:  # noqa: BLE001
        logger.warning("task.interpret_failed: %s", e)
        result = {"intent": "unclear", "note": text[:200]}

    intent = result.get("intent", "unclear")
    note = result.get("note") or text[:200]
    await append_task_note(task_id, f"update:{intent}", note)

    if intent == "done":
        await _complete_task(context.bot, task_id, update.effective_user.id, update.message.reply_text)
    elif intent == "blocked":
        await update_task(task_id, status="blocked")
        member = await get_team_member(update.effective_user.id)
        who = member.name if member else str(update.effective_user.id)
        await _notify(
            context.bot, _escalation_targets(task),
            f"🚧 *{_md_escape(who)}* is blocked on: {_md_escape(task.title)}\n_{_md_escape(note)}_",
        )
        await update.message.reply_text("🚧 Noted as blocked — manager notified.")
    else:
        # progress / needs_more_time / question / unclear → keep active, snooze one gap.
        settings = get_settings()
        nxt = followups.next_followup_at(
            now=followups.now_utc(), urgency=task.urgency,
            followup_hours=settings.task_followup_hours,
            escalate_hours=settings.task_escalate_hours,
        )
        await update_task(task_id, status="in_progress", next_followup_at=nxt)
        await update.message.reply_text("👍 Got it — I've logged your update.")

    raise ApplicationHandlerStop


# ── Recurring follow-up / escalation scan ───────────────────────────


async def scan_task_followups(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic job: nudge assignees and escalate stalled tasks.

    Reads due follow-ups from the DB (so it survives restarts), sends a reminder,
    escalates aged tasks to managers once, then reschedules the next reminder.
    """
    settings = get_settings()
    now = followups.now_utc()
    try:
        due = await list_due_followups(now)
    except Exception as e:  # noqa: BLE001
        logger.exception("task.scan_error: %s", e)
        return

    for task in due:
        try:
            assignee = await get_team_member(task.assignee_telegram_id)
            assignee_is_manager = bool(assignee and assignee.role == "manager")

            # Escalate once when aged past the window (skip if the assignee is a
            # manager — no point escalating a manager's task to themselves).
            if not assignee_is_manager and followups.should_escalate(
                now=now, created_at=task.created_at, urgency=task.urgency,
                already_escalated=bool(task.escalated),
                followup_hours=settings.task_followup_hours,
                escalate_hours=settings.task_escalate_hours,
            ):
                who = assignee.name if assignee else str(task.assignee_telegram_id)
                deal = f" ({task.deal_ref})" if task.deal_ref else ""
                await _notify(
                    context.bot, _escalation_targets(task),
                    f"⚠️ *Escalation* — still not done after "
                    f"{settings.task_escalate_hours:g}h:\n"
                    f"*{_md_escape(task.title)}*{_md_escape(deal)}\n"
                    f"👤 {_md_escape(who)} — {task.followup_count} reminder(s) sent",
                )
                await update_task(task.id, escalated=True)
                await append_task_note(task.id, "escalated", "Escalated to manager")

            # Send the reminder and reschedule.
            await _deliver_task(context.bot, task, prefix="⏰ *Reminder — still open*\n\n")
            nxt = followups.next_followup_at(
                now=now, urgency=task.urgency,
                followup_hours=settings.task_followup_hours,
                escalate_hours=settings.task_escalate_hours,
            )
            await update_task(
                task.id, next_followup_at=nxt, followup_count=(task.followup_count or 0) + 1
            )
        except Exception as e:  # noqa: BLE001 — one bad task must not stop the scan
            logger.warning("task.scan_item_failed task=%s err=%s", task.id, e)


# ── Registration ────────────────────────────────────────────────────


def register_task_handlers(app) -> None:
    """Register task-management handlers and the follow-up scan job."""
    app.add_handler(CommandHandler("assign", assign_command))
    app.add_handler(CommandHandler("tasks", tasks_command))
    app.add_handler(CommandHandler("checklist", checklist_command))
    app.add_handler(CommandHandler("team", team_command))
    app.add_handler(CommandHandler("addagent", addagent_command))
    app.add_handler(CommandHandler("removeagent", removeagent_command))
    app.add_handler(CommandHandler("done", done_command))

    app.add_handler(CallbackQueryHandler(task_callback, pattern=r"^task_"))

    # Free-text update catcher — own priority group, only consumes when the user
    # just tapped 💬 Update (ApplicationHandlerStop). Group -3 keeps it ahead of
    # the OREA conversation handler and the showings counter catcher (-2).
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, task_update_message),
        group=-3,
    )

    # Recurring follow-up / escalation scan.
    if app.job_queue is None:
        logger.error(
            "JobQueue unavailable — install python-telegram-bot[job-queue] to "
            "enable task reminders/escalation. Follow-ups disabled."
        )
        return
    interval = get_settings().task_scan_interval
    app.job_queue.run_repeating(
        scan_task_followups, interval=interval, first=30, name="task_followup_scan"
    )
    logger.info("task.followup_scan_enabled interval_seconds=%s", interval)
