# BrokerBay Showing Management Bot

A Discord bot that automates BrokerBay showing management tasks for real estate agents using Playwright browser automation.

## Features

- **Showing Tours** — Book optimized multi-property showing tours with route optimization
- **Listing Management** — View listings, approve/decline showing requests via buttons
- **Day Summary** — View all confirmed showings for any date
- **Session Management** — Persistent BrokerBay login sessions

## Setup

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**, give it a name
3. Go to **Bot** tab, click **Add Bot**
4. Copy the **Token** — this is your `DISCORD_BOT_TOKEN`
5. Copy the **Application ID** from the General Information tab — this is your `DISCORD_CLIENT_ID`
6. Under **Privileged Gateway Intents**, enable **Message Content Intent**
7. Go to **OAuth2 > URL Generator**, select scopes: `bot`, `applications.commands`
8. Select permissions: Send Messages, Use Slash Commands, Read Message History, Embed Links, Attach Files
9. Copy the generated URL and open it to invite the bot to your server

### 2. Get Your Discord User ID

1. Open Discord Settings > Advanced > Enable **Developer Mode**
2. Right-click your name in any chat > **Copy User ID**

### 3. Get Your Server (Guild) ID (optional, for dev)

Right-click your server name > **Copy Server ID**. Setting `DISCORD_GUILD_ID` makes slash commands appear instantly instead of taking up to 1 hour.

### 4. Get a Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Geocoding API** and **Distance Matrix API**
3. Create an API key

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```
BROKERBAY_EMAIL=your-brokerbay-email@example.com
BROKERBAY_PASSWORD=your-password
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_CLIENT_ID=your-application-id
DISCORD_ALLOWED_USER_IDS=your-discord-user-id
DISCORD_GUILD_ID=your-server-id
GOOGLE_MAPS_API_KEY=AIza...
```

### 6. Install Dependencies

```bash
npm install
npx playwright install chromium
```

### 7. Deploy Slash Commands

```bash
npm run deploy-commands
```

This registers the slash commands with Discord. If you set `DISCORD_GUILD_ID`, they appear instantly. Otherwise, global commands can take up to 1 hour.

### 8. First Login (Generate BrokerBay Session)

```bash
npm run login
```

A browser window will open. Log in through the Honeywell SSO. Once you reach the BrokerBay dashboard, the session is saved automatically.

### 9. Start the Bot

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
| `/tour` | Start booking a showing tour |
| `/book` | Alias for `/tour` |
| `/listings` | View your active listings (with buttons) |
| `/pending` | View pending showing requests (approve/decline buttons) |
| `/approve id:<id>` | Approve a showing request |
| `/decline id:<id> [reason:<reason>]` | Decline a showing request |
| `/summary [date:<date>]` | View showings for a date (default: today) |
| `/status` | Check bot and BrokerBay session status |

## Tour Booking Flow

1. `/tour` — Bot asks for addresses (one per line)
2. Enter date (e.g., "March 25")
3. Enter time window (e.g., "10am - 4pm")
4. Enter client name
5. Enter starting point (office address or "first property")
6. Choose duration (20/25/30 minutes)
7. Review optimized route, click **Book All** or **Cancel**
8. Bot books all showings in BrokerBay and posts a summary

## Architecture

```
/brokerbay-bot
  /src
    /bot          — Discord.js client, slash commands, button handlers, messenger interface
    /browser      — Playwright session & BrokerBay page objects
    /scheduler    — Route optimization & Google Maps integration
    /formatters   — Discord message formatters (markdown)
    /types        — Shared TypeScript interfaces
    config.ts     — Zod-validated environment config
    index.ts      — Entry point
```

### Key Design Decisions

- **IMessenger interface** — Discord is abstracted behind an interface for future WhatsApp/other platform support
- **p-queue (concurrency: 1)** — All browser tasks run sequentially to prevent conflicts
- **Session persistence** — BrokerBay session (cookies + localStorage) saved to disk, reused across restarts
- **User whitelist** — Only authorized Discord user IDs can interact with the bot
- **Discord slash commands** — Native Discord UX with autocomplete, options, and buttons

## Development

```bash
# Run with visible browser for debugging
HEADLESS=false npm run dev
```

## Security

- Only whitelisted Discord user IDs can use the bot
- Session files are gitignored
- Credentials are never logged
- Unauthorized users get an ephemeral "Unauthorized" response
