"""Read-only web dashboard for deals and deadlines.

Runs as a second container on the same host as the bot (see the `dashboard`
service in docker-compose.yml), sharing the SQLite storage volume read-only.

Security model: single shared token, required on every request. The first
visit uses `?token=...`; a cookie is then set so in-page links work bare.
With no DASHBOARD_TOKEN configured the dashboard refuses to serve anything.

Run: uvicorn web.app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

from bot.reminders import format_deadline_local, property_label
from config import get_settings
from db.operations import (
    get_transaction,
    list_all_transactions,
    list_all_upcoming_reminders,
    list_upcoming_reminders,
)
from forms.formatting import format_currency, parse_date

app = FastAPI(title="Deal Dashboard", docs_url=None, redoc_url=None, openapi_url=None)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Mirrors integrations.transactiondesk.TD_BASE (not imported — that module
# pulls in Playwright, which this container doesn't need).
TD_BASE = "https://pr.transactiondesk.com"

DOC_TYPE_NAMES = {
    "aps": "Agreement of Purchase & Sale (Form 100)",
    "amendment": "Amendment (Form 120)",
    "waiver": "Waiver (Form 122)",
    "notice": "Notice (Form 124)",
    "lease": "Agreement to Lease (Form 400)",
    "commercial_aps": "Commercial APS (Form 500)",
}

_COOKIE = "dash_token"


@app.middleware("http")
async def require_token(request: Request, call_next):
    expected = get_settings().dashboard_token
    if not expected:
        return PlainTextResponse(
            "Dashboard disabled: set DASHBOARD_TOKEN in .env and restart.",
            status_code=503,
        )

    supplied = (
        request.query_params.get("token")
        or request.cookies.get(_COOKIE)
        or request.headers.get("x-dashboard-token")
        or ""
    )
    if not secrets.compare_digest(supplied, expected):
        return PlainTextResponse(
            "Unauthorized. Open the dashboard with ?token=<DASHBOARD_TOKEN>.",
            status_code=401,
        )

    response = await call_next(request)
    if request.query_params.get("token"):
        # Token arrived via URL — persist it so in-page links work bare.
        response.set_cookie(_COOKIE, expected, httponly=True, max_age=30 * 24 * 3600)
    return response


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _next_deadline(deal_data: dict) -> tuple[str, str] | None:
    """Nearest future (label, YYYY-MM-DD) deadline from the deal's dates."""
    now = datetime.now()
    candidates = []
    for label, key in (
        ("Irrevocability", "irrevocability_date"),
        ("Closing", "closing_date"),
        ("Lease start", "lease_start_date"),
    ):
        dt = parse_date(deal_data.get(key))
        if dt and dt >= now.replace(hour=0, minute=0, second=0, microsecond=0):
            candidates.append((dt, label))
    if not candidates:
        return None
    dt, label = min(candidates)
    return (label, dt.strftime("%Y-%m-%d"))


def _deal_view(tx) -> dict:
    """Shape a Transaction row for the templates."""
    data = tx.deal_data or {}
    price = data.get("purchase_price") or data.get("monthly_rent")
    return {
        "id": tx.id,
        "doc_type": DOC_TYPE_NAMES.get(tx.doc_type, tx.doc_type),
        "status": tx.status or "draft",
        "address": property_label(data),
        "buyer": " & ".join(filter(None, [data.get("buyer_1"), data.get("buyer_2")])),
        "seller": " & ".join(filter(None, [data.get("seller_1"), data.get("seller_2")])),
        "price": f"${format_currency(price)}" if price else "",
        "next_deadline": _next_deadline(data),
        "created": tx.created_at.strftime("%b %d, %Y") if tx.created_at else "",
        "td_transaction_url": (
            f"{TD_BASE}/transaction/detail/{tx.td_transaction_uuid}/overview"
            if tx.td_transaction_uuid else None
        ),
        "td_form_url": (
            f"{TD_BASE}/form/{tx.td_form_uuid}/false" if tx.td_form_uuid else None
        ),
    }


@app.get("/")
async def deals_list(request: Request):
    transactions = await list_all_transactions()
    deals = [_deal_view(tx) for tx in transactions]
    return templates.TemplateResponse(
        request, "list.html", {"deals": deals, "active": "deals"}
    )


@app.get("/deadlines")
async def deadlines(request: Request):
    reminders = await list_all_upcoming_reminders(_utcnow_naive())
    seen: set[tuple] = set()
    rows = []
    for r in reminders:
        key = (r.label, r.deadline_at)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "label": r.label,
            "kind": r.kind,
            "when": format_deadline_local(r.deadline_at),
            "transaction_id": r.transaction_id,
        })
    return templates.TemplateResponse(
        request, "deadlines.html", {"rows": rows, "active": "deadlines"}
    )


@app.get("/deal/{tx_id}")
async def deal_detail(request: Request, tx_id: str):
    tx = await get_transaction(tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal = _deal_view(tx)
    data = tx.deal_data or {}
    fields = [
        (key.replace("_", " ").title(), value)
        for key, value in sorted(data.items())
        if key != "collection_complete" and value not in (None, "")
    ]

    reminders = await list_upcoming_reminders(tx.telegram_chat_id, _utcnow_naive(), limit=50)
    seen: set[tuple] = set()
    deal_reminders = []
    for r in reminders:
        if r.transaction_id != tx.id:
            continue
        key = (r.label, r.deadline_at)
        if key in seen:
            continue
        seen.add(key)
        deal_reminders.append({
            "label": r.label,
            "when": format_deadline_local(r.deadline_at),
        })

    return templates.TemplateResponse(
        request,
        "detail.html",
        {"deal": deal, "fields": fields, "reminders": deal_reminders, "active": "deals"},
    )
