# AI Realtor Assistant

A Telegram bot for Ontario real estate agents with three capabilities:

1. **Document generation** — collects deal information through a natural
   conversation powered by Claude, then fills the matching OREA/TRREB form in
   **TransactionDesk WebForms** via browser automation — falling back to a
   locally generated summary PDF when TransactionDesk is unavailable.
2. **Showing management** — connects to **BrokerBay** to list, approve,
   decline, and counter showing requests, notify you of new requests, and
   book route-optimized showing tours (`/tour`) using Google Maps.
3. **Team task management (Ops Manager)** — a manager assigns work in plain
   language, Claude turns it into tasks for the right agent, the bot follows up
   automatically, escalates stalled tasks to the manager, and reports back on
   completion.

## Team task commands

| Command | What it does |
|---|---|
| `/assign <plain language>` | Claude parses your request and assigns task(s) to the right team member(s). e.g. `/assign ask Sarah to book the home inspection for 123 Main St by Friday` |
| `/tasks` | Managers see all open tasks; agents see their own |
| `/checklist <type> [@Name] <deal ref>` | Fan an Ontario checklist into tasks. Types: `listing`, `buyer`, `deal` |
| `/team`, `/addagent <id> <name> [manager]`, `/removeagent <id>` | Manage the roster (a person finds their ID with `/whoami`) |
| `/done <task_id>` | Mark a task complete |

Each assigned task arrives as a DM with **✅ Done / 🚧 Blocked / ⏳ Snooze /
💬 Update** buttons; tapping *Update* lets the agent reply in natural language
("done", "waiting on the lawyer", "need another day") which Claude interprets.

**Follow-ups are DB-driven** — a recurring scan (`TASK_SCAN_INTERVAL` seconds)
reads each task's due follow-up time from the database, so reminders and
escalations survive restarts. Cadence scales with urgency from the
`TASK_FOLLOWUP_HOURS` / `TASK_ESCALATE_HOURS` "standard" baseline (high nags
sooner and escalates faster; low is gentler). Managers are set via
`MANAGER_USER_IDS` (must also be in `AUTHORIZED_USER_IDS`).

> **Roadmap — Phase B (social/email inbox):** a hybrid front-end where ManyChat
> forwards Instagram/Facebook/WhatsApp DMs and Gmail forwards email to a webhook
> on this bot; Claude triages importance, routes each lead to an agent as a
> task, drafts a suggested reply for approval, and pings the manager on the
> important ones. Designed but not yet built.

## Showing commands

| Command | What it does |
|---|---|
| `/showings` | Pending + upcoming showings with confirm/decline buttons |
| `/today`, `/summary [date]` | Schedule for today or a given date |
| `/pending`, `/approve <id>`, `/decline <id> [reason]` | Manage requests on your listings |
| `/tour` (or `/book`) | Paste addresses → geocode + optimize route → book each stop in BrokerBay |
| `/listings`, `/status`, `/whoami` | Listings, health check, your Telegram ID |

A background job polls BrokerBay every `SHOWING_POLL_INTERVAL` seconds and
pushes new showing requests to every authorized user.

## How document generation works

1. Agent messages the bot and picks a document type (APS, Amendment, Waiver,
   Notice, Commercial APS, or Lease).
2. Claude interviews the agent for the deal details (property, parties,
   price, deposit, dates, conditions) and submits the structured data via a
   typed tool call.
3. The bot shows a summary; the agent confirms or edits.
4. The bot logs into TRREB REALM (SSO + SMS 2FA relayed through Telegram),
   creates a TransactionDesk transaction, adds the OREA form, fills the
   fields, verifies each value, and saves.
5. The agent gets a link to the form, a fill report (e.g. "Filled 24 of 26
   fields"), a screenshot preview, and options to email the document or start
   an Authentisign signing session.

## Architecture

```
bot/            Telegram UI — conversation state machine, keyboards
  main.py       Entry point (polling); global 2FA code catcher
  handlers/     ConversationHandler: IDLE → SELECTING_DOC → COLLECTING
                → CONFIRMING → GENERATING → POST_GENERATE → SIGNING
ai/             Claude agent — collection prompts + submit_deal_data tool
forms/          Generation orchestrator, TD field maps, ReportLab fallback
integrations/   TransactionDesk & REALM browser automation (Playwright),
                BrokerBay (HTTP API + browser client), email (SMTP),
                SkySlope upload, MLS lookup
scheduler/      Tour geocoding (Google Maps) + route optimization
ops/            Team task layer — Ontario checklists + follow-up cadence logic
                (bot/handlers/tasks.py drives assign → follow-up → escalate)
db/             SQLAlchemy models + async SQLite (transactions, sessions, tasks)
storage/        Runtime data: DB, session cookies, PDFs, screenshots (gitignored)
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # then fill it in
python bot/main.py
```

Required `.env` values:

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `ANTHROPIC_API_KEY` | Claude API key |
| `AUTHORIZED_USER_IDS` | Comma-separated Telegram user IDs. **Empty = nobody can use the bot.** Get yours from @userinfobot |
| `REALM_USERNAME` / `REALM_PASSWORD` | TRREB REALM login (for TransactionDesk) |
| `BROKERAGE_*` | Your brokerage details, stamped on documents |

Optional: `BROKERBAY_EMAIL`/`BROKERBAY_PASSWORD` (showing management),
`GOOGLE_MAPS_API_KEY` (tour route optimization), SMTP (email delivery),
DocuSign, SkySlope. Without REALM credentials the bot still works,
generating summary PDFs locally; without BrokerBay credentials the showing
features simply stay hidden.

## Deployment

```bash
# On a fresh Ubuntu server (e.g. Hetzner):
curl -O https://raw.githubusercontent.com/rayrocket-ai/claudecode/<branch>/deploy.sh
bash deploy.sh
```

Or manually: `docker compose up -d --build`. The `storage/` directory is
volume-mounted so the database and sessions survive container rebuilds.

## Calibrating TransactionDesk field maps

`forms/field_maps.py` maps TransactionDesk's HTML input `name` attributes to
collected deal-data keys. TransactionDesk UI updates can rename fields. To
recalibrate:

1. Set `BROWSER_HEADLESS=false` in `.env`.
2. Open the target form via `python test_realm_login.py`, then inspect the
   form editor inputs in DevTools.
3. Update the `name` → data-key entries in `FORM_100_FIELDS` (etc.).
4. The bot's fill report ("Filled X of Y fields") tells you which fields
   failed verification — check the logs for the exact names.

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Security notes

- Access is deny-by-default: users not in `AUTHORIZED_USER_IDS` are rejected.
- REALM session cookies are stored unencrypted in `storage/` — keep server
  access restricted.
- The bot prepares documents under a licensed broker's supervision; it is not
  a substitute for legal review.
