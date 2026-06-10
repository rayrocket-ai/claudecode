# Ray Ahmadi — Content Engine 🎬 + RayRocket Studio 🚀

This repo now ships two FastAPI apps:

1. **Content Engine** (`dashboard/`) — Ray's private content creation dashboard (below)
2. **RayRocket Studio** (`studio/`) — the public landing page selling services to GTA realtors

## RayRocket Studio — services storefront

A dark, cinematic landing page where GTA realtors can browse and buy:

- **Cinematic House Tours** — order with just an address; one-time ($249, $349 rush) or subscriptions (Starter $399/mo, Pro $899/mo, Brokerage $1,999/mo). Orders are captured to the database and shown in `/admin`; set the `STRIPE_LINK_TOUR_*` env vars to send buyers straight to Stripe checkout instead.
- **AI Receptionist** (early access) — interactive scope builder: realtors pick the tasks they need handled (answering, lead qualification, showing bookings, CRM logging, follow-ups), call volume and coverage hours, and see a live plan recommendation (Core $299 / Plus $499 / Concierge $899) with a setup-effort estimate before submitting.
- **Executive Assistant** (early access) — Essentials $450/mo and Operator $950/mo packages, waitlist signup.
- **Second Brain** (waitlist) — email capture.

All pricing lives in `studio/templates/index.html` (display) and `studio/static/studio.js` (receptionist estimator) — edit there to change numbers.

### Run the storefront locally

```bash
uvicorn studio.app:app --reload --port 8001
```

### Storefront environment variables

| Variable | Required | Description |
|---|---|---|
| `STUDIO_DATABASE_URL` | No | Defaults to `sqlite:///./studio.db` |
| `STUDIO_ADMIN_KEY` | Yes for `/admin` | Visit `/admin?key=<value>` to see orders, leads & waitlist |
| `STRIPE_LINK_TOUR_SINGLE/STARTER/PRO/BROKERAGE` | No | Stripe payment links; when set, order submissions redirect to checkout |

### Deploy the storefront on Railway

The Dockerfile starts whichever app `APP_MODULE` points at. Create a **second Railway service** from this same repo and set:

```
APP_MODULE=studio.app:app
STUDIO_ADMIN_KEY=<your secret>
```

The existing service keeps running the content engine (no `APP_MODULE` needed — it defaults to `dashboard.app:app`).

---

# Content Engine

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

## Ray's Story

Ray Ahmadi was born in Afghanistan in the mid-1990s during Taliban occupation. His family fled through wilderness, spent 18 months in Pakistan, made an illegal bus journey to Moscow, rebuilt from a roadside table to a factory in China — then left it all behind again for Canada. He arrived at Pearson Airport on October 13, 2009, and built his real estate career from zero.

Every script Claude generates draws from this real story. No placeholders. No generic advice.
# force redeploy Sat Apr 11 04:04:57 AM UTC 2026
