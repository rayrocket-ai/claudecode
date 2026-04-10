"""FastAPI web dashboard for video script generation."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db.operations import init_db
from dashboard import operations as ops
from dashboard.scraper import collect_all_trends
from dashboard.script_engine import get_engine

logger = logging.getLogger(__name__)

# ── App Setup ─────────────────────────────────────────────────────────

DASHBOARD_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Video Script Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory=DASHBOARD_DIR / "static"), name="static")

templates = Jinja2Templates(directory=DASHBOARD_DIR / "templates")


@app.on_event("startup")
async def startup():
    await init_db()
    # Ensure dashboard models are created
    from db.operations import _engine as db_engine
    from dashboard.models import CreatorProfile, DailyBatch, VideoScript, TrendingItem
    from db.models import Base
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── Template Helpers ──────────────────────────────────────────────────

CATEGORY_COLORS = {
    "real_estate": {"bg": "bg-blue-100", "text": "text-blue-800", "border": "border-blue-300", "label": "Real Estate"},
    "mortgage": {"bg": "bg-green-100", "text": "text-green-800", "border": "border-green-300", "label": "Mortgage"},
    "politics_economy": {"bg": "bg-red-100", "text": "text-red-800", "border": "border-red-300", "label": "Politics & Economy"},
    "sports": {"bg": "bg-orange-100", "text": "text-orange-800", "border": "border-orange-300", "label": "Sports"},
    "personal": {"bg": "bg-purple-100", "text": "text-purple-800", "border": "border-purple-300", "label": "Personal"},
}

HOOK_STYLE_LABELS = {
    "question": "Question Hook",
    "stat": "Shocking Stat",
    "controversy": "Hot Take",
    "story": "Story Opener",
    "pattern_interrupt": "Pattern Interrupt",
    "challenge": "Direct Challenge",
    "confession": "Confession",
}


def _template_context(request: Request, **kwargs) -> dict:
    """Build standard template context."""
    ctx = {
        "request": request,
        "category_colors": CATEGORY_COLORS,
        "hook_style_labels": HOOK_STYLE_LABELS,
        "today": date.today(),
    }
    ctx.update(kwargs)
    return ctx


# ── Page Routes ───────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Main dashboard — today's scripts."""
    today = date.today()
    batch = await ops.get_batch_for_date(today)
    profile = await ops.get_or_create_profile()

    return templates.TemplateResponse("dashboard.html", _template_context(
        request,
        batch=batch,
        scripts=batch.scripts if batch else [],
        profile=profile,
        selected_date=today,
    ))


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Past scripts archive."""
    batches = await ops.list_batches(limit=30)
    return templates.TemplateResponse("history.html", _template_context(
        request,
        batches=batches,
    ))


@app.get("/history/{date_str}", response_class=HTMLResponse)
async def history_date_page(request: Request, date_str: str):
    """Scripts for a specific date."""
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD.")

    batch = await ops.get_batch_for_date(target_date)
    profile = await ops.get_or_create_profile()

    return templates.TemplateResponse("dashboard.html", _template_context(
        request,
        batch=batch,
        scripts=batch.scripts if batch else [],
        profile=profile,
        selected_date=target_date,
        is_history=True,
    ))


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Creator profile settings."""
    profile = await ops.get_or_create_profile()
    return templates.TemplateResponse("profile.html", _template_context(
        request,
        profile=profile,
    ))


@app.get("/trends", response_class=HTMLResponse)
async def trends_page(request: Request):
    """Today's trending data feed."""
    today = date.today()
    batch = await ops.get_batch_for_date(today)
    trending_items = []
    if batch:
        trending_items = await ops.get_trending_for_date(today)

    # Group by category
    by_category: dict[str, list] = {}
    for item in trending_items:
        by_category.setdefault(item.category, []).append(item)

    return templates.TemplateResponse("trends.html", _template_context(
        request,
        trending_items=trending_items,
        by_category=by_category,
        has_data=len(trending_items) > 0,
    ))


# ── API Routes ────────────────────────────────────────────────────────

@app.post("/api/generate")
async def api_generate_scripts(request: Request):
    """Generate today's scripts."""
    today = date.today()

    # Check if batch already exists
    existing = await ops.get_batch_for_date(today)
    if existing and existing.status == "complete":
        return JSONResponse({"status": "already_exists", "batch_id": existing.id})

    # Get creator profile
    profile = await ops.get_or_create_profile()
    profile_dict = ops.profile_to_dict(profile)

    # Collect trending data
    try:
        trending_data = await collect_all_trends()
    except Exception as e:
        logger.error(f"Failed to collect trends: {e}")
        trending_data = {"real_estate": [], "mortgage": [], "politics": [], "sports": [], "general": []}

    # Create or reuse batch
    if existing:
        batch = existing
        await ops.update_batch_status(batch.id, "generating")
    else:
        batch = await ops.create_batch(today, trending_data)

    # Flatten trending items for DB storage
    all_trend_items = []
    for category_items in trending_data.values():
        all_trend_items.extend(category_items)
    await ops.save_trending_items(batch.id, all_trend_items)

    # Generate scripts via Claude
    try:
        engine = get_engine()
        scripts_data = await engine.generate_daily_scripts(
            target_date=today,
            trending_data=trending_data,
            creator_profile=profile_dict,
        )
        await ops.save_scripts(batch.id, scripts_data)
        await ops.update_batch_status(batch.id, "complete")

        return JSONResponse({"status": "success", "batch_id": batch.id, "script_count": len(scripts_data)})

    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        await ops.update_batch_status(batch.id, "error", str(e))
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/api/regenerate/{script_id}")
async def api_regenerate_script(script_id: str):
    """Regenerate a single script."""
    script = await ops.get_script(script_id)
    if not script:
        raise HTTPException(404, "Script not found")

    # Get batch trending data
    async with ops.get_session() as session:
        from sqlalchemy import select
        from dashboard.models import DailyBatch
        result = await session.execute(select(DailyBatch).where(DailyBatch.id == script.batch_id))
        batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(404, "Batch not found")

    profile = await ops.get_or_create_profile()
    profile_dict = ops.profile_to_dict(profile)

    existing_data = {
        "hook_style": script.hook_style,
        "title": script.title,
    }

    try:
        engine = get_engine()
        new_script_data = await engine.regenerate_single_script(
            category=script.category,
            trending_data=batch.trending_data or {},
            creator_profile=profile_dict,
            existing_script=existing_data,
        )

        # Update the script in-place
        await ops.update_script(script_id, new_script_data)
        updated = await ops.get_script(script_id)

        return JSONResponse({"status": "success", "script_id": script_id})

    except Exception as e:
        logger.error(f"Script regeneration failed: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.put("/api/scripts/{script_id}")
async def api_update_script(script_id: str, request: Request):
    """Update/edit a script."""
    data = await request.json()
    script = await ops.update_script(script_id, data)
    if not script:
        raise HTTPException(404, "Script not found")
    return JSONResponse({"status": "success"})


@app.get("/api/scripts/{script_id}/copy")
async def api_copy_script(script_id: str):
    """Get script as copyable plain text."""
    script = await ops.get_script(script_id)
    if not script:
        raise HTTPException(404, "Script not found")

    text = f"""📹 {script.title}
Category: {script.category.replace('_', ' ').title()}

🎣 HOOK:
{script.hook}

📝 SCRIPT:
{script.body}

📢 CTA:
{script.cta}

💡 PERSONAL TIE-IN:
{script.personal_tie_in}

🎬 VISUAL SUGGESTIONS:
{script.visual_suggestions}

#️⃣ HASHTAGS:
"""
    if script.hashtags:
        for platform, tags in script.hashtags.items():
            if tags:
                text += f"\n{platform}: {' '.join(tags)}"

    return PlainTextResponse(text)


@app.put("/api/profile")
async def api_update_profile(request: Request):
    """Update creator profile."""
    data = await request.json()
    profile = await ops.update_profile(data)
    return JSONResponse({"status": "success"})


@app.post("/api/trends/refresh")
async def api_refresh_trends():
    """Re-fetch trending data for today."""
    today = date.today()
    batch = await ops.get_batch_for_date(today)
    if not batch:
        return JSONResponse({"status": "error", "message": "Generate scripts first to create a batch."}, status_code=400)

    try:
        trending_data = await collect_all_trends()
        all_items = []
        for items in trending_data.values():
            all_items.extend(items)
        await ops.save_trending_items(batch.id, all_items)
        return JSONResponse({"status": "success", "item_count": len(all_items)})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/export/{batch_id}")
async def api_export_batch(batch_id: str):
    """Export all scripts from a batch as plain text."""
    async with ops.get_session() as session:
        from sqlalchemy import select
        from dashboard.models import DailyBatch, VideoScript
        result = await session.execute(
            select(DailyBatch).where(DailyBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if not batch:
            raise HTTPException(404, "Batch not found")

        result = await session.execute(
            select(VideoScript)
            .where(VideoScript.batch_id == batch_id)
            .order_by(VideoScript.sort_order)
        )
        scripts = list(result.scalars().all())

    text = f"VIDEO SCRIPTS — {batch.date.isoformat()}\n"
    text += "=" * 50 + "\n\n"

    for i, script in enumerate(scripts, 1):
        text += f"SCRIPT #{i}: {script.title}\n"
        text += f"Category: {script.category.replace('_', ' ').title()}\n"
        text += f"Hook Style: {script.hook_style}\n"
        text += f"Duration: ~{script.estimated_duration}s\n"
        text += "-" * 40 + "\n\n"
        text += f"HOOK:\n{script.hook}\n\n"
        text += f"SCRIPT:\n{script.body}\n\n"
        text += f"CTA:\n{script.cta}\n\n"
        text += f"PERSONAL TIE-IN:\n{script.personal_tie_in}\n\n"
        text += f"VISUALS:\n{script.visual_suggestions}\n\n"
        if script.hashtags:
            text += "HASHTAGS:\n"
            for platform, tags in script.hashtags.items():
                if tags:
                    text += f"  {platform}: {' '.join(tags)}\n"
        text += "\n" + "=" * 50 + "\n\n"

    return PlainTextResponse(text, headers={
        "Content-Disposition": f'attachment; filename="scripts-{batch.date.isoformat()}.txt"'
    })
