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
    DailyBatch, ContentIdea, HookVariation, VideoScript, FBComment, Listing,
    json_dump, json_load
)
from .operations import (
    get_profile, update_profile,
    get_pillars, get_pillar, upsert_pillar,
    get_stories, get_story, create_story, delete_story,
    get_today_batch, get_batch, create_batch, complete_batch, fail_batch,
    get_scripts, get_today_scripts, get_script, create_script, update_script_status,
    rate_script,
    get_ideas, get_idea, create_idea, update_idea_status,
    get_hooks_for_idea, create_hook, choose_hook,
)
from .scraper import get_trending_items
from .script_engine import generate_daily_batch, generate_idea_bank, forge_hooks, write_script, regenerate_script, generate_shot_list
from .pipeline.stage1_idea_bank import run_stage1
from .pipeline.stage2_hook_forge import run_stage2
from .pipeline.stage3_script_writer import run_stage3
from . import facebook as fb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Ray's Content Engine", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.on_event("startup")
def on_startup():
    try:
        init_db()
    except Exception as e:
        logger.error(f"DB init failed: {e}")
    try:
        _seed_data()
    except Exception as e:
        logger.error(f"Seed data failed: {e}")


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
def generate_batch(request: Request, db: Session = Depends(get_db)):
    """Generate scripts synchronously and redirect."""
    existing = get_today_batch(db)
    if existing and existing.status == "complete":
        return RedirectResponse("/scripts", status_code=303)

    batch = create_batch(db, topic_mix={
        "market": 2, "mortgage": 1, "personal": 1,
        "client_win": 1, "trending": 1, "wildcard": 1
    })

    try:
        profile = get_profile(db)
        stories = get_stories(db, scriptable_only=True)
        trending = get_trending_items(8)
        script_dicts = generate_daily_batch(
            profile=profile,
            trending_items=trending,
            client_stories=stories,
            n=7,
            batch_id=batch.id,
        )
        for sd in script_dicts:
            sd["batch_id"] = batch.id
            create_script(db, sd)
        complete_batch(db, batch.id, len(script_dicts))
        logger.info(f"Batch {batch.id} complete with {len(script_dicts)} scripts")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        fail_batch(db, batch.id)

    return RedirectResponse("/scripts", status_code=303)


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


@app.post("/scripts/{script_id}/rate")
def script_rate(script_id: int, rating: int = Form(...), db: Session = Depends(get_db)):
    """Rate a script: rating=1 (👍) or rating=-1 (👎). Sends JSON response."""
    from fastapi.responses import JSONResponse
    script = get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    updated = rate_script(db, script_id, rating)
    return JSONResponse({"ok": True, "rating": updated.rating})


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

# ── Email digest ──────────────────────────────────────────────────────────

@app.post("/api/send-digest")
def send_digest_endpoint(db: Session = Depends(get_db)):
    """Send today's scripts as a digest email to DIGEST_EMAIL."""
    from fastapi.responses import JSONResponse
    from .digest_email import send_daily_digest

    to_email = os.getenv("DIGEST_EMAIL", "")
    if not to_email:
        return JSONResponse({"ok": False, "error": "DIGEST_EMAIL env var not set"}, status_code=400)

    profile = get_profile(db)
    scripts = get_today_scripts(db)
    if not scripts:
        scripts = get_scripts(db, limit=7)

    result = send_daily_digest(to_email, profile, scripts)
    status = 200 if result["ok"] else 500
    return JSONResponse(result, status_code=status)


# ── Shot list ────────────────────────────────────────────────────────────

@app.get("/scripts/{script_id}/shot-list")
def shot_list_endpoint(script_id: int, db: Session = Depends(get_db)):
    """Generate and return a shot list for a script."""
    from fastapi.responses import JSONResponse
    script = get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    try:
        shots = generate_shot_list(script)
        return JSONResponse({"ok": True, "shots": shots})
    except Exception as e:
        logger.error(f"Shot list generation failed: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


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

@app.get("/api/test-deepseek")
def test_deepseek():
    """Test DeepSeek connection directly."""
    try:
        import httpx
        from .script_engine import DEEPSEEK_API_KEY
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
        resp = httpx.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=30)
        return {"status": resp.status_code, "response": resp.json()}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/api/reset-batch")
def reset_batch(db: Session = Depends(get_db)):
    """Reset stuck batch so generation can retry."""
    from .models import DailyBatch
    from datetime import date
    today = date.today().isoformat()
    db.query(DailyBatch).filter(DailyBatch.date == today).delete()
    db.commit()
    return {"status": "reset", "date": today}

@app.get("/scripts/{script_id}/shot-list")
def get_shot_list(script_id: int, db: Session = Depends(get_db)):
    """Generate a shot list for a script using AI."""
    from .script_engine import _call_claude
    script = get_script(db, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    prompt = f"""You are a social media video director. Generate a practical shot list for this script that Ray can film solo on his iPhone.

SCRIPT:
HOOK: {script.hook}
BODY: {script.body}
CTA: {script.cta}

Output a JSON array of shots. Each shot has:
- section: HOOK, BODY, or CTA
- framing: "tight selfie" / "medium selfie" / "wide selfie" / "walking shot"
- action: exactly what Ray should do physically
- text: the words to say in this shot
- duration: estimated seconds

Return ONLY valid JSON array, no markdown."""

    try:
        result = _call_claude(prompt)
        import json, re
        # Extract JSON array
        match = re.search(r'\[.*\]', result, re.DOTALL)
        shots = json.loads(match.group(0)) if match else []
        return {"shots": shots}
    except Exception as e:
        return {"shots": [], "error": str(e)}


@app.post("/api/send-digest")
def send_digest(db: Session = Depends(get_db)):
    """Send today's scripts to Ray's email."""
    import os
    from .digest_email import send_daily_digest
    email = os.getenv("DIGEST_EMAIL", "")
    if not email:
        return {"ok": False, "error": "DIGEST_EMAIL not set in environment variables"}
    profile = get_profile(db)
    scripts = get_today_scripts(db)
    if not scripts:
        return {"ok": False, "error": "No scripts generated today"}
    try:
        send_daily_digest(email, profile, scripts)
        return {"ok": True, "sent_to": email}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ── Listings (Google Sheets sync) ────────────────────────────────────────

@app.get("/listings", response_class=HTMLResponse)
def listings_page(request: Request, db: Session = Depends(get_db)):
    listings = db.query(Listing).order_by(Listing.synced_at.desc()).limit(200).all()
    return tmpl("listings.html", request, {
        "active_page": "listings",
        "listings": listings,
        "sheets_configured": bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("LISTINGS_SHEET_ID")),
        "sync_result": None,
    })


@app.post("/listings/sync", response_class=HTMLResponse)
def listings_sync(request: Request, db: Session = Depends(get_db)):
    from .sheets import sync_listings
    try:
        result = sync_listings(db)
        result["ok"] = True
    except Exception as e:
        logger.error(f"Sheet sync failed: {e}")
        result = {"ok": False, "error": str(e)}

    listings = db.query(Listing).order_by(Listing.synced_at.desc()).limit(200).all()
    return tmpl("listings.html", request, {
        "active_page": "listings",
        "listings": listings,
        "sheets_configured": bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and os.getenv("LISTINGS_SHEET_ID")),
        "sync_result": result,
    })


# ── Facebook comment agent ───────────────────────────────────────────────

@app.get("/webhook/facebook")
def facebook_webhook_verify(request: Request):
    return fb.webhook_verify(request)


@app.post("/webhook/facebook")
async def facebook_webhook_receive(request: Request):
    return await fb.webhook_receive(request)


@app.get("/facebook", response_class=HTMLResponse)
def facebook_queue(request: Request, status_filter: str = "drafted", db: Session = Depends(get_db)):
    """Review queue for Facebook comments."""
    q = db.query(FBComment)
    if status_filter == "pending":
        q = q.filter(FBComment.status.in_(["drafted"]))
    elif status_filter == "sent":
        q = q.filter(FBComment.status.in_(["reply_sent", "dm_sent", "both_sent"]))
    elif status_filter == "skipped":
        q = q.filter(FBComment.status == "skipped")
    elif status_filter == "failed":
        q = q.filter(FBComment.status == "failed")
    # "all" → no filter
    comments = q.order_by(FBComment.received_at.desc()).limit(100).all()

    counts = {
        "drafted": db.query(FBComment).filter(FBComment.status == "drafted").count(),
        "sent": db.query(FBComment).filter(FBComment.status.in_(["reply_sent", "dm_sent", "both_sent"])).count(),
        "skipped": db.query(FBComment).filter(FBComment.status == "skipped").count(),
        "failed": db.query(FBComment).filter(FBComment.status == "failed").count(),
    }
    listing_ids = {c.matched_listing_id for c in comments if c.matched_listing_id}
    listings_by_id = {
        l.id: l for l in db.query(Listing).filter(Listing.id.in_(listing_ids)).all()
    } if listing_ids else {}
    return tmpl("facebook.html", request, {
        "active_page": "facebook",
        "comments": comments,
        "status_filter": status_filter,
        "counts": counts,
        "listings_by_id": listings_by_id,
        "fb_configured": bool(os.getenv("FB_PAGE_ACCESS_TOKEN")),
    })


@app.post("/facebook/{row_id}/edit")
def facebook_edit_draft(
    row_id: int,
    draft_reply: str = Form(""),
    draft_dm: str = Form(""),
    db: Session = Depends(get_db),
):
    row = db.query(FBComment).filter(FBComment.id == row_id).first()
    if not row:
        raise HTTPException(404, "comment not found")
    row.draft_reply = draft_reply.strip()
    row.draft_dm = draft_dm.strip()
    db.commit()
    return RedirectResponse("/facebook", status_code=303)


@app.post("/facebook/{row_id}/send")
def facebook_send(
    row_id: int,
    action: str = Form(...),  # "reply" | "dm" | "both" | "skip"
    draft_reply: str = Form(""),
    draft_dm: str = Form(""),
    db: Session = Depends(get_db),
):
    row = db.query(FBComment).filter(FBComment.id == row_id).first()
    if not row:
        raise HTTPException(404, "comment not found")

    # Apply any inline edits before sending
    if draft_reply.strip():
        row.draft_reply = draft_reply.strip()
    if draft_dm.strip():
        row.draft_dm = draft_dm.strip()
    db.commit()

    if action == "skip":
        row.status = "skipped"
        db.commit()
    elif action == "reply" and row.draft_reply:
        fb.send_drafted_reply(db, row)
    elif action == "dm" and row.draft_dm:
        fb.send_drafted_dm(db, row)
    elif action == "both":
        if row.draft_reply:
            fb.send_drafted_reply(db, row)
        if row.draft_dm:
            fb.send_drafted_dm(db, row)

    return RedirectResponse("/facebook", status_code=303)


@app.post("/facebook/{row_id}/redraft")
def facebook_redraft(row_id: int, db: Session = Depends(get_db)):
    """Re-run Claude to regenerate the reply + DM drafts for this comment."""
    from .fb_agent import classify_and_draft, match_listing
    row = db.query(FBComment).filter(FBComment.id == row_id).first()
    if not row:
        raise HTTPException(404, "comment not found")
    profile = get_profile(db)
    # Try to rematch the listing using the latest listings data
    listing = None
    if row.matched_listing_id:
        listing = db.query(Listing).filter(Listing.id == row.matched_listing_id).first()
    if not listing:
        listing = match_listing(db, row.post_id, "")
    draft = classify_and_draft(
        message=row.message,
        author=row.author_name or "Facebook user",
        profile=profile,
        listing=listing,
    )
    row.category = draft["category"]
    row.language = draft.get("language", "en")
    row.intent = draft["intent"]
    row.should_engage = draft["should_engage"]
    row.draft_reply = draft["draft_reply"]
    row.draft_dm = draft["draft_dm"]
    row.matched_listing_id = listing.id if listing else None
    row.status = "drafted" if draft["should_engage"] else "skipped"
    db.commit()
    return RedirectResponse("/facebook", status_code=303)


@app.post("/api/facebook/ingest")
def facebook_ingest_manual(comment_id: str = Form(...), db: Session = Depends(get_db)):
    """Manually ingest a comment by ID (useful for testing without webhooks)."""
    from fastapi.responses import JSONResponse
    row = fb._ingest_comment(db, comment_id.strip())
    if not row:
        return JSONResponse({"ok": False, "error": "could not ingest"}, status_code=400)
    return JSONResponse({"ok": True, "id": row.id, "status": row.status, "category": row.category})


@app.post("/api/update-story")
def update_story_timeline(db: Session = Depends(get_db)):
    """Update Ray's story timeline elements."""
    story_elements = [
        {"period": "Afghanistan, mid-1990s", "event": "Born during Taliban occupation. Hid in cellars while bombs fell. Witnessed violence and civilian casualties."},
        {"period": "Peshawar, Pakistan", "event": "18 months. No school. No documents. Father left alone for Russia to earn money and sponsor the family later."},
        {"period": "Moscow, Aug 23, 2000", "event": "Illegal bus journey through wilderness. Fake passports. Warned to stay silent — soldiers would hurt Afghans. Father had lost weight from overwork."},
        {"period": "Russia → Wealth → Racism", "event": "Father rebuilt from roadside table → store → factory in China. Became wealthy. But police bribes, racism, classmates saying 'get out of our country.' Money without dignity."},
        {"period": "Toronto, Oct 13, 2009", "event": "Waited 3 years for Canada. Arrived Pearson Airport with tears and smiles. No English. Started from zero."},
        {"period": "Seneca College", "event": "Learned English from scratch. Studied hard. Built his foundation in Canada."},
        {"period": "Real Estate — The Climb", "event": "Solo agent at RE/MAX. Grinded from nothing. No connections, no shortcuts. Built to first million by 2016."},
        {"period": "2017-18 — Lost Everything", "event": "Real estate downturn + crypto crash wiped him out completely. Zero again. Second time starting over in his life."},
        {"period": "2019-20 — The Rebuild", "event": "Slow grind back up. No shortcuts. Pure hustle. Third time building from nothing."},
        {"period": "COVID 2020 — Lost Again", "event": "Market chaos. Deals collapsed. Lost it all again. But this time he knew he'd survived worse."},
        {"period": "2022-25 — Built Different", "event": "Named Top 30 Under 30 in Canada. Built eXp organization with 200+ agents. Broker-owner. Investor in Canada and USA. Sold 1,000+ homes."},
        {"period": "Today", "event": "Father of 3. Travelled 25+ countries. Fluent in Dari, Russian, English. Sponsors Afghan refugees, settles families. Board of charity. Community leader. Client first — always. 'I would rather not make money than have my client lose.'"},
    ]

    victories = [
        "First million in Canadian real estate by 2016",
        "Top 30 Under 30 in Canada — real estate",
        "Built 200+ agent organization at eXp Realty",
        "Sold 1,000+ homes across GTA",
        "Broker-owner and mortgage professional",
        "Investor in Canada and USA",
        "Travelled to 25+ countries",
        "Fluent in 3 languages: Dari, Russian, English",
        "Speaker, team leader, mastermind group member",
    ]

    challenges = [
        "Fled Afghanistan as a child — bombs, Taliban, refugee camps",
        "18 months in Peshawar with no school and no documents",
        "2-week illegal journey to Moscow — fake passports, armed soldiers",
        "9 years of racism in Russia — bribes, threats, 'get out of our country'",
        "Arrived Canada with no English",
        "Lost everything in 2017-18 real estate + crypto crash",
        "Lost again in COVID — rebuilt from zero a third time",
    ]

    profile = get_profile(db)
    if profile:
        from .models import json_dump
        profile.story_elements = json_dump(story_elements)
        profile.victories = json_dump(victories)
        profile.challenges = json_dump(challenges)
        db.commit()
        return {"ok": True, "message": "Story updated"}
    return {"ok": False, "error": "No profile found"}
