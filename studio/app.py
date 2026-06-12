"""RayRocket Studio — public storefront for GTA realtor services."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from .models import init_db, get_db, TourOrder, ReceptionistLead, WaitlistEntry, json_dump

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as e:
        logger.error(f"DB init failed: {e}")
    yield


app = FastAPI(title="RayRocket Studio", version="1.0.0", lifespan=lifespan)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

ADMIN_KEY = os.getenv("STUDIO_ADMIN_KEY", "")

# Optional Stripe payment links — set these env vars to send buyers straight to
# checkout after they submit an order. Left unset, orders are captured and you
# invoice manually from /admin.
STRIPE_LINKS = {
    "single": os.getenv("STRIPE_LINK_TOUR_SINGLE", ""),
    "starter": os.getenv("STRIPE_LINK_TOUR_STARTER", ""),
    "pro": os.getenv("STRIPE_LINK_TOUR_PRO", ""),
    "brokerage": os.getenv("STRIPE_LINK_TOUR_BROKERAGE", ""),
}

RECEPTIONIST_TASKS = {
    "answer_calls": "Answer & route calls 24/7",
    "qualify_leads": "Qualify buyer / seller leads",
    "book_showings": "Book & confirm showings",
    "follow_up": "Follow-up sequences (sign calls, open house leads)",
    "crm_updates": "Log everything to your CRM",
    "faq": "Answer listing & neighbourhood FAQs",
}

# ── Tour production ───────────────────────────────────────────────────────────
# Each paid order gets a ready-to-run kickoff prompt for the Claude + Higgsfield
# pipeline documented in studio/playbooks/house_tour_production.md.

PLAYBOOK_PATH = os.path.join(BASE_DIR, "playbooks", "house_tour_production.md")

STYLE_BRIEFS = {
    "cinematic": (
        "Cinematic & dramatic: sweeping drone moves, confident pacing, "
        "speed-ramp the room-to-room transits, slow down on the hero room."
    ),
    "luxury": (
        "Luxury & elegant: slow, gliding camera throughout, longer holds on "
        "premium finishes, gentler speed ramp, twilight hero finale."
    ),
    "social": (
        "Fast-cut social: aggressive FPV energy, whip-fast transits, punchy "
        "~22-25s runtime, optimized for Reels/TikTok hook-and-hold."
    ),
}


def build_production_prompt(order: "TourOrder") -> str:
    """The exact prompt to paste into a Claude session (with the Higgsfield
    connector + ffmpeg available) to produce this order's tour."""
    lines = [
        f"Create a cinematic house tour for **{order.address}**.",
        "Find the listing photos online. Make it one continuous drone shot — "
        "enter from above, descend, roam room to room. No visible cuts. "
        "~30 seconds. Deliver 16:9 and 9:16 versions.",
        "",
        f"Style brief: {STYLE_BRIEFS.get(order.style, STYLE_BRIEFS['cinematic'])}",
    ]
    if order.listing_url:
        lines.append(f"Listing URL (start photo search here): {order.listing_url}")
    if order.rush:
        lines.append("RUSH ORDER — 24h delivery promised. Start immediately.")
    if order.notes:
        lines.append(f"Client notes: {order.notes}")
    lines += [
        "",
        "Follow the production playbook at studio/playbooks/house_tour_production.md:",
        "photo sourcing → flight path → frame-chained segments (start frame = exact "
        "final frame of previous segment; 'already moving, never decelerating' in "
        "every prompt) → ffmpeg stitch with 0.25s micro-crossfades → one continuous "
        "speed ramp (whip the transits, slow the hero room) → Higgsfield reframe for "
        "9:16 → deliver both masters, silent.",
        "",
        f"Deliver to: {order.name} <{order.email}>"
        + (f" ({order.brokerage})" if order.brokerage else ""),
    ]
    return "\n".join(lines)


# ── Public pages ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "receptionist_tasks": RECEPTIONIST_TASKS,
    })


@app.get("/tours", response_class=HTMLResponse)
def tours(request: Request):
    return templates.TemplateResponse(request, "tours.html", {})


@app.get("/receptionist", response_class=HTMLResponse)
def receptionist(request: Request):
    return templates.TemplateResponse(request, "receptionist.html", {
        "receptionist_tasks": RECEPTIONIST_TASKS,
    })


@app.get("/assistant", response_class=HTMLResponse)
def assistant(request: Request):
    return templates.TemplateResponse(request, "assistant.html", {})


@app.get("/second-brain", response_class=HTMLResponse)
def second_brain(request: Request):
    return templates.TemplateResponse(request, "secondbrain.html", {})


@app.get("/thanks", response_class=HTMLResponse)
def thanks(request: Request, type: str = "order"):
    return templates.TemplateResponse(request, "thanks.html", {"type": type})


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Order & lead capture ──────────────────────────────────────────────────────

@app.post("/order/tour")
def order_tour(
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    brokerage: str = Form(""),
    address: str = Form(...),
    listing_url: str = Form(""),
    package: str = Form("single"),
    style: str = Form("cinematic"),
    rush: bool = Form(False),
    notes: str = Form(""),
):
    order = TourOrder(
        name=name.strip(), email=email.strip(), phone=phone.strip(),
        brokerage=brokerage.strip(), address=address.strip(),
        listing_url=listing_url.strip(), package=package, style=style,
        rush=rush, notes=notes.strip(),
    )
    db.add(order)
    db.commit()
    logger.info(f"New tour order #{order.id}: {order.address} ({order.package})")

    stripe_link = STRIPE_LINKS.get(package, "")
    if stripe_link:
        return RedirectResponse(stripe_link, status_code=303)
    return RedirectResponse("/thanks?type=tour", status_code=303)


@app.post("/lead/receptionist")
async def lead_receptionist(request: Request, db: Session = Depends(get_db)):
    # Raw form read so the multi-select "tasks" checkboxes arrive as a list.
    form = await request.form()
    tasks = form.getlist("tasks")
    lead = ReceptionistLead(
        name=str(form.get("name", "")).strip(),
        email=str(form.get("email", "")).strip(),
        phone=str(form.get("phone", "")).strip(),
        brokerage=str(form.get("brokerage", "")).strip(),
        tasks=json_dump(tasks),
        call_volume=str(form.get("call_volume", "medium")),
        coverage=str(form.get("coverage", "business")),
        crm=str(form.get("crm", "")).strip(),
        notes=str(form.get("notes", "")).strip(),
        recommended_plan=str(form.get("recommended_plan", "")),
    )
    if not lead.name or not lead.email:
        raise HTTPException(status_code=422, detail="Name and email are required")
    db.add(lead)
    db.commit()
    logger.info(f"New receptionist lead #{lead.id}: {lead.email} ({lead.recommended_plan})")
    return RedirectResponse("/thanks?type=receptionist", status_code=303)


@app.post("/waitlist")
def join_waitlist(
    db: Session = Depends(get_db),
    service: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    notes: str = Form(""),
):
    entry = WaitlistEntry(service=service, name=name.strip(), email=email.strip(), notes=notes.strip())
    db.add(entry)
    db.commit()
    logger.info(f"New waitlist entry #{entry.id}: {entry.email} ({entry.service})")
    return RedirectResponse("/thanks?type=waitlist", status_code=303)


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, key: str = "", db: Session = Depends(get_db)):
    if not ADMIN_KEY or key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Set STUDIO_ADMIN_KEY and pass ?key=...")
    orders = db.query(TourOrder).order_by(TourOrder.created_at.desc()).all()
    leads = db.query(ReceptionistLead).order_by(ReceptionistLead.created_at.desc()).all()
    waitlist = db.query(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin.html", {
        "orders": orders, "leads": leads,
        "waitlist": waitlist, "key": key, "task_labels": RECEPTIONIST_TASKS,
    })


@app.get("/admin/order/{order_id}/production", response_class=HTMLResponse)
def order_production_brief(order_id: int, request: Request, key: str = "", db: Session = Depends(get_db)):
    """Per-order production brief: the kickoff prompt plus the full playbook."""
    if not ADMIN_KEY or key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Set STUDIO_ADMIN_KEY and pass ?key=...")
    order = db.query(TourOrder).filter(TourOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    try:
        with open(PLAYBOOK_PATH, encoding="utf-8") as f:
            playbook = f.read()
    except OSError:
        playbook = "(playbook file missing: studio/playbooks/house_tour_production.md)"
    return templates.TemplateResponse(request, "production.html", {
        "order": order,
        "prompt": build_production_prompt(order),
        "playbook": playbook,
        "key": key,
    })


@app.post("/admin/order/{order_id}/status")
def update_order_status(order_id: int, key: str = Form(...), status: str = Form(...), db: Session = Depends(get_db)):
    if not ADMIN_KEY or key != ADMIN_KEY:
        raise HTTPException(status_code=403)
    order = db.query(TourOrder).filter(TourOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    order.status = status
    db.commit()
    return RedirectResponse(f"/admin?key={key}", status_code=303)
