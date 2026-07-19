"""Multi-campaign ads dashboard for Ray Homes.

Runs as its own docker-compose service on the same server as the bot.
The ADMAX daily loop pushes results through the /api endpoints; humans
read the HTML pages. Data lives in storage/dashboard.json (the same
volume-mounted storage/ directory the bot uses), seeded from seed.json
on first run.
"""

import json
import os
import secrets
import tempfile
import threading
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

_lock = threading.Lock()

app = FastAPI(title="Ray Homes Campaign Dashboard", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _store_path() -> Path:
    return Path(os.environ.get("DASHBOARD_STORE", "storage/dashboard.json"))


def _load() -> dict[str, Any]:
    path = _store_path()
    if path.exists():
        return json.loads(path.read_text())
    seed = json.loads((BASE_DIR / "seed.json").read_text())
    _save(seed)
    return seed


def _save(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)


def _check_key(key: str | None) -> None:
    expected = os.environ.get("DASHBOARD_KEY", "")
    if not expected:
        raise HTTPException(503, "DASHBOARD_KEY is not set on the server; writes are disabled")
    if not key or not secrets.compare_digest(key, expected):
        raise HTTPException(401, "Bad or missing X-Dashboard-Key header")


def _campaign_or_404(data: dict[str, Any], slug: str) -> dict[str, Any]:
    campaign = data.get("campaigns", {}).get(slug)
    if campaign is None:
        raise HTTPException(404, f"No campaign named {slug!r}")
    return campaign


def kpis(campaign: dict[str, Any]) -> dict[str, Any]:
    """Blended headline numbers across the campaign's daily rows."""
    daily = campaign.get("daily", [])
    spend = round(sum(row.get("spend", 0) for row in daily), 2)
    leads = sum(row.get("leads", 0) for row in daily)
    ctrs = [row["ctr_pct"] for row in daily if row.get("ctr_pct") is not None]
    return {
        "spend": spend,
        "leads": leads,
        "cpl": round(spend / leads, 2) if leads else None,
        "ctr_pct": ctrs[-1] if ctrs else None,
        "views": sum(row.get("views") or 0 for row in daily),
        "days": len(daily),
    }


class DailyResult(BaseModel):
    date: date
    spend: float = Field(ge=0)
    leads: int = Field(default=0, ge=0)
    ctr_pct: float | None = None
    impressions: int | None = None
    views: int | None = None
    notes: str = ""


class LogEntry(BaseModel):
    date: date
    title: str
    entry: str


class CampaignMeta(BaseModel):
    name: str
    subtitle: str = ""
    status: str = "pre-launch"  # pre-launch | live | paused | ended
    playbook: str = ""
    targets: dict[str, Any] = Field(default_factory=dict)
    config: list[list[str]] = Field(default_factory=list)
    rules: list[dict[str, str]] = Field(default_factory=list)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    with _lock:
        data = _load()
    order = {"live": 0, "pre-launch": 1, "paused": 2, "ended": 3}
    cards = sorted(
        (
            {"slug": slug, "campaign": c, "kpis": kpis(c)}
            for slug, c in data.get("campaigns", {}).items()
        ),
        key=lambda card: order.get(card["campaign"].get("status"), 9),
    )
    return templates.TemplateResponse(request, "index.html", {"cards": cards})


@app.get("/c/{slug}", response_class=HTMLResponse)
def campaign_page(request: Request, slug: str) -> HTMLResponse:
    with _lock:
        data = _load()
    campaign = _campaign_or_404(data, slug)
    return templates.TemplateResponse(
        request,
        "campaign.html",
        {
            "slug": slug,
            "c": campaign,
            "kpis": kpis(campaign),
            "daily": sorted(campaign.get("daily", []), key=lambda r: r["date"], reverse=True),
            "log": sorted(campaign.get("log", []), key=lambda e: e["date"], reverse=True),
        },
    )


@app.get("/api/campaigns")
def api_campaigns() -> dict[str, Any]:
    with _lock:
        data = _load()
    return {
        slug: {"name": c.get("name"), "status": c.get("status"), **kpis(c)}
        for slug, c in data.get("campaigns", {}).items()
    }


@app.get("/api/campaigns/{slug}")
def api_campaign(slug: str) -> dict[str, Any]:
    with _lock:
        data = _load()
    return _campaign_or_404(data, slug)


@app.put("/api/campaigns/{slug}")
def upsert_campaign(
    slug: str, meta: CampaignMeta, x_dashboard_key: str | None = Header(default=None)
) -> dict[str, str]:
    _check_key(x_dashboard_key)
    with _lock:
        data = _load()
        existing = data.setdefault("campaigns", {}).get(slug, {})
        merged = {**existing, **meta.model_dump()}
        merged.setdefault("daily", existing.get("daily", []))
        merged.setdefault("log", existing.get("log", []))
        data["campaigns"][slug] = merged
        _save(data)
    return {"status": "ok", "slug": slug}


@app.post("/api/campaigns/{slug}/daily")
def add_daily(
    slug: str, row: DailyResult, x_dashboard_key: str | None = Header(default=None)
) -> dict[str, Any]:
    _check_key(x_dashboard_key)
    with _lock:
        data = _load()
        campaign = _campaign_or_404(data, slug)
        daily = campaign.setdefault("daily", [])
        new_row = json.loads(row.model_dump_json())
        # Same date reported twice = correction, not a duplicate day.
        daily[:] = [r for r in daily if r["date"] != new_row["date"]]
        daily.append(new_row)
        daily.sort(key=lambda r: r["date"])
        _save(data)
        return {"status": "ok", **kpis(campaign)}


@app.post("/api/campaigns/{slug}/log")
def add_log(
    slug: str, entry: LogEntry, x_dashboard_key: str | None = Header(default=None)
) -> dict[str, str]:
    _check_key(x_dashboard_key)
    with _lock:
        data = _load()
        campaign = _campaign_or_404(data, slug)
        campaign.setdefault("log", []).append(json.loads(entry.model_dump_json()))
        _save(data)
    return {"status": "ok", "slug": slug}
