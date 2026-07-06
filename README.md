# AI Realtor Assistant

A Telegram bot for Ontario real estate agents with three capabilities:

1. **Document generation** — collects deal information through a natural
   conversation powered by Claude, then fills the matching OREA/TRREB form in
   **TransactionDesk WebForms** via browser automation — falling back to a
   locally generated summary PDF when TransactionDesk is unavailable.
2. **Showing management** — connects to **BrokerBay** to list, approve,
   decline, and counter showing requests, notify you of new requests, and
   book route-optimized showing tours (`/tour`) using Google Maps.
3. **Listing launch** — turns one listing (`/launch`) into a full marketing
   campaign: RECO/CREA-compliant copy, a feature-sheet outline, a reel script,
   a just-listed email + SMS, and an open-house calendar invite.

## Listing launch (`/launch`)

Send `/launch` an MLS number, an address, or a few lines of detail. Claude
drafts the whole campaign under RECO/CREA advertising rules (no invented
facts, no Fair-Housing violations), you review it, and — on an explicit
**Publish** tap — the bot delivers each asset. The email blast goes out over
your existing SMTP when you set recipients; every other asset is handed back
ready to paste (Gamma/Canva for the sheet, Higgsfield for the reel) or as a
downloadable `.ics` for the open house. Nothing is sent without confirmation,
and any unconfigured channel simply degrades to "drafted" rather than failing.

Direct publishing to Boosend / Gamma / Higgsfield is stubbed behind
`BOOSEND_API_KEY` / `GAMMA_API_KEY` / `HIGGSFIELD_API_KEY` — each `run_*`
function in `integrations/campaign.py` is the single seam to wire a provider.

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
ai/             Claude agents — deal-data collection (submit_deal_data) and
                listing marketing (listing_agent.py, submit_campaign tool)
forms/          Generation orchestrator, TD field maps, ReportLab fallback
integrations/   TransactionDesk & REALM browser automation (Playwright),
                BrokerBay (HTTP API + browser client), email (SMTP),
                SkySlope upload, MLS lookup, campaign delivery (campaign.py)
scheduler/      Tour geocoding (Google Maps) + route optimization
db/             SQLAlchemy models + async SQLite (transactions, sessions)
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
