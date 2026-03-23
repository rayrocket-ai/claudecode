# BrokerBay Showing Management Bot

A Telegram bot that automates BrokerBay showing management tasks for real estate agents using Playwright browser automation.

## Features

- **Showing Tours** — Book optimized multi-property showing tours with route optimization
- **Listing Management** — View listings, approve/decline showing requests
- **Day Summary** — View all confirmed showings for any date
- **Session Management** — Persistent BrokerBay login sessions

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token

### 2. Get Your Telegram User ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID

### 3. Get a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Geocoding API** and **Distance Matrix API**
3. Create an API key

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
BROKERBAY_EMAIL=your@email.com
BROKERBAY_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ALLOWED_USER_IDS=123456789
GOOGLE_MAPS_API_KEY=AIza...
```

### 5. Install Dependencies

```bash
npm install
npx playwright install chromium
```

### 6. First Login (Generate Session)

Run the manual login script to authenticate with BrokerBay and save the session:

```bash
npm run login
```

A browser window will open. Log in to BrokerBay through the Honeywell SSO. Once you reach the dashboard, the session is saved automatically.

### 7. Start the Bot

```bash
# Development (with hot reload)
npm run dev

# Production
npm run build
npm start

# Docker
docker-compose up -d
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and command list |
| `/help` | Detailed help |
| `/tour` or `/book` | Start booking a showing tour |
| `/listings` | View your active listings |
| `/pending` | View pending showing requests |
| `/approve <id>` | Approve a showing request |
| `/decline <id> [reason]` | Decline a showing request |
| `/summary [date]` | View showings for a date (default: today) |
| `/status` | Check bot and BrokerBay session status |

## Tour Booking Flow

1. `/tour` — Bot asks for addresses (one per line)
2. Enter date (e.g., "March 25")
3. Enter time window (e.g., "10am - 4pm")
4. Enter client name
5. Enter starting point (office address or "first property")
6. Choose duration (20/25/30 minutes)
7. Review optimized route and confirm
8. Bot books all showings in BrokerBay and sends a summary

## Architecture

```
/brokerbay-bot
  /src
    /bot          — Grammy bot, commands, messenger interface
    /browser      — Playwright session & BrokerBay page objects
    /scheduler    — Route optimization & Google Maps integration
    /formatters   — Telegram message formatters (MarkdownV2)
    /types        — Shared TypeScript interfaces
    config.ts     — Zod-validated environment config
    index.ts      — Entry point
```

### Key Design Decisions

- **IMessenger interface** — Telegram is abstracted behind an interface for future WhatsApp/Discord support
- **p-queue (concurrency: 1)** — All browser tasks run sequentially to prevent conflicts
- **Session persistence** — BrokerBay session (cookies + localStorage) saved to disk, reused across restarts
- **User whitelist** — Only authorized Telegram user IDs can interact with the bot

## Development

```bash
# Run with visible browser for debugging
HEADLESS=false npm run dev
```

## Security

- Only whitelisted Telegram user IDs can use the bot
- Session files are gitignored
- Credentials are never logged
- Unauthorized users get a generic "Unauthorized" response
