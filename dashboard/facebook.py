"""Facebook Graph API + webhook handlers for the comment agent.

Endpoints (wired in app.py):
  GET  /webhook/facebook           — webhook verification handshake
  POST /webhook/facebook           — receive comment events from FB

Graph API helpers:
  send_reply(comment_id, message)         — public reply under a comment
  send_private_reply(comment_id, message) — DM the commenter (no opt-in needed)
  get_comment(comment_id)                 — fetch comment details
"""

import hmac
import hashlib
import logging
import os
from datetime import datetime
from typing import Optional

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from .models import FBComment, Listing, SessionLocal
from .fb_agent import classify_and_draft, match_listing
from .operations import get_profile

logger = logging.getLogger(__name__)


GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION", "v21.0")
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _token() -> str:
    tok = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    if not tok:
        raise RuntimeError("FB_PAGE_ACCESS_TOKEN not set")
    return tok


def _app_secret() -> str:
    return os.getenv("FB_APP_SECRET", "")


def _verify_token() -> str:
    return os.getenv("FB_VERIFY_TOKEN", "")


def _page_id() -> str:
    return os.getenv("FB_PAGE_ID", "")


# ── Graph API helpers ───────────────────────────────────────────────────────

def get_comment(comment_id: str) -> dict:
    """Fetch comment details including author, message, parent, permalink."""
    url = f"{GRAPH_BASE}/{comment_id}"
    params = {
        "access_token": _token(),
        "fields": "id,message,from,created_time,permalink_url,parent{id},"
                  "post{id,message}",
    }
    r = httpx.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def send_reply(comment_id: str, message: str) -> dict:
    """Post a public reply under the given comment. Returns {"id": "<new_comment_id>"}."""
    url = f"{GRAPH_BASE}/{comment_id}/comments"
    r = httpx.post(
        url,
        data={"message": message, "access_token": _token()},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def send_private_reply(comment_id: str, message: str) -> dict:
    """DM the commenter via the private_replies endpoint (no prior opt-in needed)."""
    url = f"{GRAPH_BASE}/{comment_id}/private_replies"
    r = httpx.post(
        url,
        data={"message": message, "access_token": _token()},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


# ── Webhook signature verification ──────────────────────────────────────────

def verify_signature(body: bytes, signature_header: str) -> bool:
    """Verify X-Hub-Signature-256 matches HMAC-SHA256(body, app_secret)."""
    secret = _app_secret()
    if not secret:
        # If no app secret is configured, accept (dev mode) but log a warning.
        logger.warning("FB_APP_SECRET not set — skipping signature check")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ── Incoming webhook processing ─────────────────────────────────────────────

def _ingest_comment(db: Session, comment_id: str, post_id: Optional[str] = None):
    """Look up a comment on Graph, classify it, and store a draft in the DB."""
    # Skip if we already have it
    existing = db.query(FBComment).filter(FBComment.comment_id == comment_id).first()
    if existing:
        return existing

    try:
        data = get_comment(comment_id)
    except Exception as e:
        logger.error(f"Failed to fetch comment {comment_id}: {e}")
        return None

    # Skip comments authored by the Page itself (our own replies)
    from_obj = data.get("from") or {}
    author_id = from_obj.get("id")
    page_id = _page_id()
    if page_id and author_id == page_id:
        logger.info(f"Skipping Page-authored comment {comment_id}")
        return None

    message = (data.get("message") or "").strip()
    if not message:
        return None

    post_obj = data.get("post") or {}
    post_context = (post_obj.get("message") or "")[:500]
    resolved_post_id = post_id or post_obj.get("id")

    # Find which listing this post is about (if any)
    listing = match_listing(db, resolved_post_id, post_context)

    profile = get_profile(db)
    draft = classify_and_draft(
        message=message,
        author=from_obj.get("name") or "Facebook user",
        post_context=post_context,
        profile=profile,
        listing=listing,
    )

    parent = data.get("parent") or {}

    row = FBComment(
        comment_id=data.get("id", comment_id),
        post_id=resolved_post_id,
        parent_id=parent.get("id"),
        author_id=author_id,
        author_name=from_obj.get("name"),
        message=message,
        permalink=data.get("permalink_url"),
        category=draft["category"],
        language=draft.get("language", "en"),
        intent=draft["intent"],
        should_engage=draft["should_engage"],
        draft_reply=draft["draft_reply"],
        draft_dm=draft["draft_dm"],
        matched_listing_id=listing.id if listing else None,
        status="drafted" if draft["should_engage"] else "skipped",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info(
        f"Ingested comment {comment_id}: category={row.category} "
        f"engage={row.should_engage} status={row.status}"
    )
    return row


def handle_webhook_payload(payload: dict):
    """Walk a page-webhook payload and ingest any comment events."""
    db: Session = SessionLocal()
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "feed":
                    continue
                value = change.get("value") or {}
                if value.get("item") != "comment":
                    continue
                verb = value.get("verb")
                if verb not in ("add", "edited"):
                    continue
                comment_id = value.get("comment_id")
                post_id = value.get("post_id")
                if not comment_id:
                    continue
                try:
                    _ingest_comment(db, comment_id, post_id)
                except Exception as e:
                    logger.error(f"Ingest failed for {comment_id}: {e}")
    finally:
        db.close()


# ── FastAPI route handlers ─────────────────────────────────────────────────

def webhook_verify(request: Request):
    """GET /webhook/facebook — Meta sends hub.mode/hub.verify_token/hub.challenge."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge", "")
    if mode == "subscribe" and token and token == _verify_token():
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="verification failed")


async def webhook_receive(request: Request):
    """POST /webhook/facebook — receive feed change events."""
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256", "")
    if not verify_signature(body, sig):
        raise HTTPException(status_code=401, detail="bad signature")

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "invalid json"}, status_code=400)

    try:
        handle_webhook_payload(payload)
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}")
        # Always 200 so FB doesn't retry indefinitely.
        return JSONResponse({"ok": False, "error": str(e)})

    return JSONResponse({"ok": True})


# ── Send drafts (used by review queue UI) ──────────────────────────────────

def send_drafted_reply(db: Session, row: FBComment) -> FBComment:
    if not row.draft_reply:
        raise ValueError("no draft_reply")
    try:
        resp = send_reply(row.comment_id, row.draft_reply)
        row.sent_reply_id = resp.get("id")
        row.reply_sent_at = datetime.utcnow()
        row.status = "both_sent" if row.dm_sent_at else "reply_sent"
        row.error = None
    except httpx.HTTPError as e:
        row.error = f"reply failed: {e}"
        row.status = "failed"
        logger.error(row.error)
    db.commit()
    db.refresh(row)
    return row


def send_drafted_dm(db: Session, row: FBComment) -> FBComment:
    if not row.draft_dm:
        raise ValueError("no draft_dm")
    try:
        send_private_reply(row.comment_id, row.draft_dm)
        row.dm_sent_at = datetime.utcnow()
        row.status = "both_sent" if row.reply_sent_at else "dm_sent"
        row.error = None
    except httpx.HTTPError as e:
        row.error = f"dm failed: {e}"
        row.status = "failed"
        logger.error(row.error)
    db.commit()
    db.refresh(row)
    return row
