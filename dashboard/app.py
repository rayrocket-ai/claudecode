"""Ray's Content Engine — FastAPI main app."""

import os
import json
import logging
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from .models import (
    init_db, get_db, CreatorProfile, BrandPillar, ClientStory,
    DailyBatch, ContentIdea, HookVariation, VideoScript,
    json_dump, json_load
)
from .operations import (
    get_profile, update_profile,
    get_pillars, get_pillar, upsert_pillar,
    get_stories, get_story, create_story, delete_story,
    get_today_batch, get_batch, create_batch, complete_batch, fail_batch,
    get_scripts, get_today_scripts, get_script, create_script, update_script_status,
    get_ideas, get_idea, create_idea, update_idea_status,
    get_hooks_for_idea, create_hook, choose_hook,
)
from .scraper import get_trending_items
from .script_engine import generate_daily_batch, generate_idea_bank, forge_hooks, write_script, regenerate_script
from .pipeline.stage1_idea_bank import run_stage1
from .pipeline.stage2_hook_forge import run_stage2
from .pipeline.stage3_script_writer import run_stage3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Ray's Content Engine", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.on_event("startup")
def on_startup():
    init_db()
    _seed_data()


def _seed_data():
    """Seed initial data if DB is empty."""
    db = next(get_db())
    try:
        # Seed brand pillars
        pillars = [
            ("authority_expertise", "Authority & Expertise", "Showcase 12+ years of GTA market knowledge, negotiation wins, and professional credentials.", "🎓", 1),
            ("behind_scenes", "Behind the Scenes", "Show the real work — property tours, client calls, late-night offers, and what brokers actually do.", "🎬", 2),
            ("client_wins", "Client Wins", "Celebrate client victories: first homes secured, investment properties closed, deals that almost didn't happen.", "🏆", 3),
            ("market_intel", "Market Intel", "GTA-specific data, rate updates, neighbourhood breakdowns, and what the numbers actually mean.", "📊", 4),
            ("mindset_lifestyle", "Mindset & Lifestyle", "Ray's personal story, immigrant resilience, and what 'home' really means when you've been without one.", "💡", 5),
            ("community_culture", "Community & Culture", "Representing GTA's diverse communities — South Asian, Afghan, immigrant buyers — and their real estate journey.", "🌍", 6),
        ]
        for pid, name, desc, emoji, order in pillars:
            existing = db.query(BrandPillar).filter(BrandPillar.id == pid).first()
            if not existing:
                upsert_pillar(db, pid, name, desc, emoji, order)

        # Seed Ray's profile
        if not get_profile(db):
            update_profile(db, {
                "name": "Ray Ahmadi",
                "bio": "Licensed real estate broker + mortgage professional in the Greater Toronto Area. 12+ years experience in residential, investment, pre-construction, and commercial real estate. From hiding in cellars in Kabul to helping families find their safe place in the GTA — home means something different when you've been without one.",
                "story_elements": json_dump([
                    "Born Afghanistan mid-1990s during Taliban occupation",
                    "Hid in cellars while bombs and rockets fell on the neighbourhood",
                    "Family fled through wilderness in back of a truck across Afghan-Pakistan border",
                    "18 months in Peshawar, Pakistan — no school, no documents",
                    "Father left alone for Russia while family waited",
                    "Two-week illegal bus journey through wilderness to Moscow — fake passports, warned to stay silent",
                    "Arrived Moscow August 23, 2000 — father had lost weight from overwork",
                    "Father and uncle rebuilt from roadside table → store → factory in China → importing business",
                    "Became wealthy in Russia — house, 3 apartments, cars",
                    "Brutal racism in Russia — police bribes, 'get out of our country', denied soccer team spot",
                    "Family decided Canada was different in 2006 — waited 3 years for permission",
                    "Left everything behind — again",
                    "Arrived Pearson International Airport, Toronto, October 13, 2009",
                    "Met Canadian sponsor with tears and smiles",
                    "Built real estate and mortgage career from zero in Canada",
                ]),
                "themes": json_dump([
                    "SAFETY AS PRIVILEGE: Grew up hiding from bombs. A home means safety in a way most people will never understand.",
                    "STARTING OVER IS SURVIVABLE: Father rebuilt from zero twice. Market crashes, rejected offers, lost deals — none of it compares.",
                    "MONEY ≠ HAPPINESS: Russia gave wealth but stripped dignity. A home is more than a number.",
                    "HUSTLE FROM NOTHING: A roadside table became a factory in China. Every client journey starts small.",
                    "OUTSIDER ADVANTAGE: Knows what it's like to be told 'you don't belong.' Fights for buyers others overlook.",
                    "PATIENCE UNDER PRESSURE: Waited 3 years for Canada. Can wait out any volatile market.",
                    "FAMILY IS THE WHY: Father risked death for family's safety. Every deal carries that weight.",
                ]),
                "gta_markets": json_dump([
                    "Brampton", "Vaughan", "Mississauga", "Markham", "Oakville",
                    "Richmond Hill", "Scarborough", "North York", "Toronto"
                ]),
            })

        # Seed 3 client stories
        if db.query(ClientStory).count() == 0:
            stories = [
                {
                    "title": "Sara — Single mom, 3 rejected offers, found dream home in Brampton",
                    "category": "win",
                    "narrative": "Sara came to Ray after being rejected on 3 offers in Brampton. A single mom with two kids, pre-approved at $720K, kept losing to all-cash investors. She was ready to give up and keep renting. Ray restructured her offer strategy — 5-day closing, escalation clause, personal letter. On offer 4, a semi-detached on a quiet street in Brampton, they won. Sara cried in the driveway.",
                    "lesson": "Rejection is part of the process. Offer strategy matters as much as the number.",
                    "emotional_peak": "Sara crying in the driveway of her new home, kids running inside for the first time.",
                },
                {
                    "title": "The Khan Family — First-time buyers from Pakistan, pre-con in Vaughan",
                    "category": "first_time_buyer",
                    "narrative": "The Khans had been in Canada for 4 years, saving while renting a basement in Mississauga. They wanted to buy but were terrified of the market — felt like outsiders who didn't understand how it worked. Ray walked them through pre-construction in Vaughan: lower entry price, 5% deposit structure, occupancy timeline. They signed on a 2-bedroom condo townhouse. Closing in 2026 — building equity from day one.",
                    "lesson": "Pre-con is underused by first-time buyers who think it's only for investors.",
                    "emotional_peak": "The Khans calling Ray after they signed — Mr. Khan saying 'we finally belong somewhere.'",
                },
                {
                    "title": "Mike — Investor who missed the 2020 boom, back for 2024 pre-con",
                    "category": "turnaround",
                    "narrative": "Mike had watched Toronto prices explode in 2020-21 and did nothing. By 2022 he thought he'd missed everything. Came to Ray in 2023 frustrated and feeling left behind. Ray showed him the 2024 pre-con landscape in Markham — prices still below 2022 peak, developers offering incentives, assignment clauses still available. Mike put deposits on two units. The 2020 boom he missed funded the mindset that almost made him miss this one too.",
                    "lesson": "The best time to invest was 5 years ago. The second best time is when you stop waiting.",
                    "emotional_peak": "Mike saying 'I can't believe I almost did nothing again.'",
                },
            ]
            for s in stories:
                create_story(db, **s)

        logger.info("Seed data check complete")
    except Exception as e:
        logger.error(f"Seed error: {e}")
    finally:
        db.close()


# ── Template helpers ──────────────────────────────────────────────────────────

def tmpl(name: str, request: Request, ctx: dict = None):
    ctx = ctx or {}
    ctx["request"] = request
    return templates.TemplateResponse(request=request, name=name, context={k: v for k, v in ctx.items() if k != 'request'})


def redirect(url: str, flash: str = None, flash_type: str = "success"):
    response = RedirectResponse(url, status_code=303)
    return response


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    batch = get_today_batch(db)
    scripts = get_today_scripts(db) if batch else []
    pillars = get_pillars(db)
    return tmpl("dashboard.html", request, {
        "active_page": "dashboard",
        "today_date": date.today().strftime("%A, %B %d, %Y"),
        "has_today_batch": batch is not None,
        "batch": batch,
        "scripts": scripts,
        "pillars": pillars,
    })


@app.get("/generate", response_class=HTMLResponse)
def generate_page(request: Request, db: Session = Depends(get_db)):
    """Show generation page / redirect to dashboard."""
    return RedirectResponse("/", status_code=302)


def _run_generation(batch_id: str):
    """Background task: generate scripts without blocking the HTTP response."""
    from .models import SessionLocal
    db = SessionLocal()
    try:
        profile = get_profile(db)
        stories = get_stories(db, scriptable_only=True)
        trending = get_trending_items(8)
        script_dicts = generate_daily_batch(
            profile=profile,
            trending_items=trending,
            client_stories=stories,
            n=7,
            batch_id=batch_id,
        )
        for sd in script_dicts:
            sd["batch_id"] = batch_id
            create_script(db, sd)
        complete_batch(db, batch_id, len(script_dicts))
        logger.info(f"Background batch {batch_id} complete with {len(script_dicts)} scripts")
    except Exception as e:
        logger.error(f"Background batch generation failed: {e}")
        fail_batch(db, batch_id)
    finally:
        db.close()


@app.post("/generate")
def generate_batch(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Kick off background generation and redirect immediately."""
    existing = get_today_batch(db)
    if existing and existing.status == "complete":
        return RedirectResponse("/scripts", status_code=303)

    batch = create_batch(db, topic_mix={
        "market": 2, "mortgage": 1, "personal": 1,
        "client_win": 1, "trending": 1, "wildcard": 1
    })
    background_tasks.add_task(_run_generation, batch.id)
    return RedirectResponse("/?generating=1", status_code=303)


@app.get("/scripts", response_class=HTMLResponse)
def scripts_list(request: Request, db: Session = Depends(get_db)):
    scripts = get_scripts(db, limit=50)
    return tmpl("scripts.html", request, {
        "active_page": "scripts",
        "scripts": scripts,
    })


@app.get("/scripts/{script_id}", response_class=HTMLResponse)
def script_detail(script_id: int, request: Request, db: Session = Depends(get_db)):
    script = get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return tmpl("scripts.html", request, {
        "active_page": "scripts",
        "scripts": [script],
        "highlighted_id": script_id,
    })


@app.get("/scripts/{script_id}/teleprompter", response_class=HTMLResponse)
def teleprompter(script_id: int, request: Request, db: Session = Depends(get_db)):
    script = get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return tmpl("teleprompter.html", request, {
        "script": script,
    })


@app.post("/scripts/{script_id}/regenerate")
def script_regenerate(script_id: int, db: Session = Depends(get_db)):
    script = get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    try:
        profile = get_profile(db)
        stories = get_stories(db, scriptable_only=True)
        new_data = regenerate_script(script, profile, stories)

        script.title = new_data["title"]
        script.hook = new_data["hook"]
        script.body = new_data["body"]
        script.cta = new_data["cta"]
        script.caption = new_data.get("caption", script.caption)
        script.hashtags = new_data.get("hashtags", script.hashtags)
        script.platform = new_data.get("platform", script.platform)
        script.estimated_duration_seconds = new_data.get("estimated_duration_seconds", script.estimated_duration_seconds)
        script.word_count = new_data.get("word_count", script.word_count)
        db.commit()

    except Exception as e:
        logger.error(f"Regeneration failed: {e}")

    return RedirectResponse("/scripts", status_code=303)


# ── Idea Bank ─────────────────────────────────────────────────────────────────

@app.get("/idea-bank", response_class=HTMLResponse)
def idea_bank(request: Request, db: Session = Depends(get_db)):
    ideas = get_ideas(db, limit=30)
    pillars = get_pillars(db)
    # Attach pillar info
    pillar_map = {p.id: p for p in pillars}
    for idea in ideas:
        idea._pillar_obj = pillar_map.get(idea.pillar_id)
    return tmpl("idea_bank.html", request, {
        "active_page": "ideas",
        "ideas": ideas,
        "pillars": pillars,
    })


@app.post("/idea-bank/generate")
def generate_idea_bank_route(db: Session = Depends(get_db)):
    """Generate 30-day idea bank."""
    try:
        run_stage1(db, days=30)
    except Exception as e:
        logger.error(f"Idea bank generation failed: {e}")
    return RedirectResponse("/idea-bank", status_code=303)


@app.get("/idea-bank/{idea_id}/hooks", response_class=HTMLResponse)
def idea_hooks(idea_id: int, request: Request, db: Session = Depends(get_db)):
    idea = get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    hooks = get_hooks_for_idea(db, idea_id)
    return tmpl("hooks.html", request, {
        "active_page": "ideas",
        "idea": idea,
        "hooks": hooks,
    })


@app.post("/idea-bank/{idea_id}/hooks")
def idea_hooks_action(
    idea_id: int,
    action: str = Form(...),
    hook_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    idea = get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")

    if action == "forge":
        # Generate hooks via stage 2
        run_stage2(db, idea)
        return RedirectResponse(f"/idea-bank/{idea_id}/hooks", status_code=303)

    elif action == "write_script" and hook_id:
        # Choose hook and write script via stage 3
        hook = db.query(HookVariation).filter(HookVariation.id == hook_id).first()
        if not hook:
            raise HTTPException(status_code=404, detail="Hook not found")
        run_stage3(db, idea, hook)
        return RedirectResponse("/scripts", status_code=303)

    return RedirectResponse(f"/idea-bank/{idea_id}/hooks", status_code=303)


# ── Stories ───────────────────────────────────────────────────────────────────

@app.get("/stories", response_class=HTMLResponse)
def stories_page(request: Request, db: Session = Depends(get_db)):
    stories = get_stories(db)
    return tmpl("stories.html", request, {
        "active_page": "stories",
        "stories": stories,
    })


@app.post("/stories")
def add_story(
    title: str = Form(...),
    category: str = Form(...),
    narrative: str = Form(...),
    lesson: str = Form(""),
    emotional_peak: str = Form(""),
    is_scriptable: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    create_story(
        db,
        title=title,
        category=category,
        narrative=narrative,
        lesson=lesson,
        emotional_peak=emotional_peak,
        is_scriptable=bool(is_scriptable),
    )
    return RedirectResponse("/stories", status_code=303)


@app.post("/stories/{story_id}/delete")
def delete_story_route(story_id: int, db: Session = Depends(get_db)):
    story = get_story(db, story_id)
    if story:
        db.delete(story)
        db.commit()
    return RedirectResponse("/stories", status_code=303)


# ── Profile ───────────────────────────────────────────────────────────────────

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    profile = get_profile(db)
    return tmpl("profile.html", request, {
        "active_page": "profile",
        "profile": profile,
    })


@app.post("/profile")
def update_profile_route(
    name: str = Form(...),
    bio: str = Form(""),
    instagram: str = Form(""),
    tiktok: str = Form(""),
    youtube: str = Form(""),
    linkedin: str = Form(""),
    gta_markets: str = Form(""),
    story_elements: str = Form(""),
    themes: str = Form(""),
    db: Session = Depends(get_db),
):
    # Parse markets as list
    markets_list = [m.strip() for m in gta_markets.split(",") if m.strip()]
    # Parse story elements as list (one per line)
    elements_list = [s.strip() for s in story_elements.splitlines() if s.strip()]
    # Parse themes as list (one per line)
    themes_list = [t.strip() for t in themes.splitlines() if t.strip()]

    update_profile(db, {
        "name": name,
        "bio": bio,
        "instagram": instagram,
        "tiktok": tiktok,
        "youtube": youtube,
        "linkedin": linkedin,
        "gta_markets": json_dump(markets_list),
        "story_elements": json_dump(elements_list),
        "themes": json_dump(themes_list),
    })
    return RedirectResponse("/profile", status_code=303)


# ── Trends ────────────────────────────────────────────────────────────────────

@app.get("/trends", response_class=HTMLResponse)
def trends_page(request: Request):
    items = get_trending_items(15)
    return tmpl("trends.html", request, {
        "active_page": "trends",
        "items": items,
    })


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "content-engine"}

@app.get("/api/status")
def api_status(db: Session = Depends(get_db)):
    """Debug endpoint — check generation status."""
    from .script_engine import AI_PROVIDER, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY
    batch = get_today_batch(db)
    scripts = get_today_scripts(db)
    return {
        "provider": AI_PROVIDER,
        "has_deepseek_key": bool(DEEPSEEK_API_KEY),
        "has_anthropic_key": bool(ANTHROPIC_API_KEY),
        "batch": {"id": batch.id, "status": batch.status} if batch else None,
        "script_count": len(scripts),
    }
