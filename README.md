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

## Ray's Story

Ray Ahmadi was born in Afghanistan in the mid-1990s during Taliban occupation. His family fled through wilderness, spent 18 months in Pakistan, made an illegal bus journey to Moscow, rebuilt from a roadside table to a factory in China — then left it all behind again for Canada. He arrived at Pearson Airport on October 13, 2009, and built his real estate career from zero.

Every script Claude generates draws from this real story. No placeholders. No generic advice.
# force redeploy Sat Apr 11 04:04:57 AM UTC 2026
