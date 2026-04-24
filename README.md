# Ray Ahmadi — Content Engine 🎬

A FastAPI-powered content creation dashboard built for Ray Ahmadi, GTA real estate broker and mortgage professional.

## What it does

- **Generate 7 scripts in one click** — daily batch with GTA market, mortgage, personal story, client wins, trending, and wildcard
- **30-day idea bank** — with viral angles, hook seeds, and platform recommendations
- **3-hook forging** — scored on scroll-stop power, curiosity, specificity, and authenticity
- **Teleprompter view** — full-screen filming tool with speed control, section colours, pause markers
- **Client story management** — add wins, losses, turnarounds, first-time buyers
- **Ray's full story baked in** — every prompt references real events (Afghanistan → Russia → Toronto)

## Quick Start

```bash
# 1. Clone/copy project
cd content-engine

# 2. Set your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
uvicorn dashboard.app:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

## Deploy to Railway

1. Push to GitHub
2. Connect repo in Railway
3. Add environment variable: `ANTHROPIC_API_KEY=your_key`
4. Deploy — Railway auto-detects the Dockerfile

## Project Structure

```
content-engine/
├── dashboard/
│   ├── app.py              # FastAPI routes
│   ├── models.py           # SQLAlchemy models
│   ├── operations.py       # CRUD
│   ├── script_engine.py    # Claude AI layer
│   ├── prompts.py          # All prompts (Ray's story baked in)
│   ├── scraper.py          # RSS trending feed
│   ├── pipeline/           # 3-stage generation pipeline
│   ├── templates/          # Jinja2 HTML templates
│   └── static/             # CSS
├── requirements.txt
├── Dockerfile
└── railway.toml
```

## Pipeline Stages

1. **Stage 1 — Idea Bank**: 30 content ideas with viral angles and hook seeds
2. **Stage 2 — Hook Forge**: 3 hook variations with scores (scroll-stop, curiosity, specificity, authenticity)
3. **Stage 3 — Script Writer**: Full 5-part script + Hormozi density pass (15% shorter)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `DATABASE_URL` | No | Defaults to `sqlite:///./content.db` |
| `FB_PAGE_ID` | FB agent | Numeric ID of Ray's Facebook Page |
| `FB_PAGE_ACCESS_TOKEN` | FB agent | Long-lived Page Access Token |
| `FB_APP_SECRET` | FB agent | App Secret (used to verify webhook signatures) |
| `FB_VERIFY_TOKEN` | FB agent | Any random string — you pick it, then paste the same string into the Meta webhook UI |
| `FB_GRAPH_VERSION` | No | Defaults to `v21.0` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Listings | Full service-account JSON (single-line) |
| `LISTINGS_SHEET_ID` | Listings | The sheet ID (from the URL between `/d/` and `/edit`) |
| `LISTINGS_SHEET_TAB` | No | Worksheet/tab name. Defaults to the first tab |

## Facebook Comment Agent

Claude drafts a public reply + private DM for every Facebook comment that looks like a real estate inquiry. Compliments and spam are auto-skipped. Drafts land in a review queue at **`/facebook`** — nothing is sent until you click Send.

### One-time setup (Meta side)

1. **Create a Meta App** at https://developers.facebook.com/apps → "Business" type.
2. **Add products:** "Facebook Login for Business", "Webhooks", "Messenger".
3. **Link Ray's Page** to the app (App Dashboard → Messenger → Settings → Add Page).
4. **Generate a Page Access Token** and exchange it for a long-lived token:
   ```bash
   curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN"
   ```
   Put the result in `FB_PAGE_ACCESS_TOKEN`.
5. **Required permissions/scopes on the token:** `pages_show_list`, `pages_read_engagement`, `pages_manage_engagement`, `pages_messaging`. Submit for App Review if you're going live beyond testers.
6. **Configure the webhook** (App Dashboard → Webhooks → Page):
   - Callback URL: `https://your-app.up.railway.app/webhook/facebook`
   - Verify token: same random string you put in `FB_VERIFY_TOKEN`
   - Subscribe to field: **`feed`** (this is the one that delivers comment events)
7. **Subscribe the Page to the app's webhook** (one-time API call):
   ```bash
   curl -X POST "https://graph.facebook.com/v21.0/PAGE_ID/subscribed_apps?subscribed_fields=feed&access_token=PAGE_ACCESS_TOKEN"
   ```

### Local testing without a public URL

Use the manual ingest endpoint to pull a single comment by ID and watch Claude draft a response:

```bash
curl -X POST http://localhost:8000/api/facebook/ingest -d "comment_id=123_456"
```

Then visit `/facebook` to review and send.

## Google Sheets Integration (master listings)

The agent looks up price questions against a master Google Sheet of Ray's active listings. Once synced, `/listings` shows every row the app knows about, and the Facebook agent matches each video post to the correct listing so it can DM the real price.

### One-time setup

1. **Create a Google Cloud project** at https://console.cloud.google.com.
2. **Enable APIs:** "Google Sheets API" and "Google Drive API" (APIs & Services → Library).
3. **Create a service account:** IAM & Admin → Service Accounts → Create. Give it any name (e.g. `ray-listings-bot`). No roles needed.
4. **Create a JSON key** for that service account (Keys → Add key → JSON). Download it.
5. **Copy the service account's email** (looks like `ray-listings-bot@yourproject.iam.gserviceaccount.com`) and **share your master sheet with that email as Viewer**.
6. **Grab the sheet ID** from the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`.
7. Set env vars on Railway:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` = the entire JSON file content (single line). Railway handles multi-line env vars fine if you paste it as-is.
   - `LISTINGS_SHEET_ID` = the sheet ID from step 6.
   - `LISTINGS_SHEET_TAB` = worksheet name, optional. Defaults to the first tab.
8. Visit `/listings` and click **Sync from Google Sheet**.

### Supported column headers

The importer is header-tolerant — any of these work (case- and spacing-insensitive):

| Canonical | Accepted aliases |
|---|---|
| `address` | address, street, street_address, property_address, property |
| `city` | city, municipality, town |
| `price` | price, list_price, listing_price, asking_price, sale_price |
| `bedrooms` | bedrooms, beds, bed, br |
| `bathrooms` | bathrooms, baths, bath, ba |
| `sqft` | sqft, square_feet, sq_ft, size, floor_area |
| `property_type` | property_type, type, home_type, style |
| `listing_type` | listing_type, transaction_type, sale_type |
| `status` | status, state, listing_status |
| `mls` | mls, mls_number, mls_id |
| `fb_post_id` | fb_post_id, facebook_post_id, post_id |
| `fb_post_url` | fb_post_url, facebook_url, facebook_post_url, fb_link, video_url, reel_url |
| `listing_url` | listing_url, mls_url, link, url, realtor_url |
| `notes` | notes, description, comments, remarks |

Setting `fb_post_id` or `fb_post_url` on a row is optional — it makes matching instant and exact. If you leave them blank, Claude matches comments to listings by reading the FB post caption against the address + city of each active listing.

## Ray's Story

Ray Ahmadi was born in Afghanistan in the mid-1990s during Taliban occupation. His family fled through wilderness, spent 18 months in Pakistan, made an illegal bus journey to Moscow, rebuilt from a roadside table to a factory in China — then left it all behind again for Canada. He arrived at Pearson Airport on October 13, 2009, and built his real estate career from zero.

Every script Claude generates draws from this real story. No placeholders. No generic advice.
# force redeploy Sat Apr 11 04:04:57 AM UTC 2026
