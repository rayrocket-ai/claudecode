"""BrokerBay showing management client.

Authenticates via the BrokerBay web portal and provides methods
to fetch, confirm, and decline showing requests.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from config import get_settings, STORAGE_DIR

logger = logging.getLogger(__name__)

# BrokerBay API endpoints (reverse-engineered from web app)
_API_V1 = "/api/v1"
_LOGIN_PATH = f"{_API_V1}/auth/login"
_SHOWINGS_PATH = f"{_API_V1}/showings"
_SHOWING_DETAIL_PATH = f"{_API_V1}/showings/{{showing_id}}"
_SHOWING_CONFIRM_PATH = f"{_API_V1}/showings/{{showing_id}}/confirm"
_SHOWING_DECLINE_PATH = f"{_API_V1}/showings/{{showing_id}}/decline"
_SHOWING_COUNTER_PATH = f"{_API_V1}/showings/{{showing_id}}/counter"
_LISTINGS_PATH = f"{_API_V1}/listings"
_PROFILE_PATH = f"{_API_V1}/users/me"


class BrokerBayError(Exception):
    """Raised when a BrokerBay API call fails."""


class BrokerBayClient:
    """HTTP-based BrokerBay API client with session persistence."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.brokerbay_base_url.rstrip("/")
        self.email = settings.brokerbay_email
        self.password = settings.brokerbay_password

        session_path = settings.session_path
        if session_path.startswith("./"):
            self.session_file = STORAGE_DIR / session_path.lstrip("./")
        else:
            self.session_file = Path(session_path)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        self._token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _load_session(self) -> bool:
        """Load saved auth token from disk."""
        if not self.session_file.exists():
            return False
        try:
            data = json.loads(self.session_file.read_text())
            token = data.get("token")
            expires = data.get("expires")
            if token and expires:
                exp_dt = datetime.fromisoformat(expires)
                if exp_dt > datetime.now():
                    self._token = token
                    logger.info("brokerbay.session_loaded", expires=expires)
                    return True
            logger.info("brokerbay.session_expired")
        except Exception as e:
            logger.warning("brokerbay.session_load_error", error=str(e))
        return False

    def _save_session(self, token: str, expires: str | None = None) -> None:
        """Persist auth token to disk."""
        data = {"token": token, "expires": expires or ""}
        self.session_file.write_text(json.dumps(data))
        logger.info("brokerbay.session_saved")

    async def _auth_headers(self) -> dict[str, str]:
        """Get headers with auth token, logging in if needed."""
        if not self._token:
            if not self._load_session():
                await self.login()
        return {"Authorization": f"Bearer {self._token}"}

    async def login(self) -> dict[str, Any]:
        """Authenticate with BrokerBay and obtain a session token."""
        if not self.email or not self.password:
            raise BrokerBayError("BrokerBay credentials not configured")

        client = await self._get_client()
        logger.info("brokerbay.login", email=self.email)

        resp = await client.post(
            _LOGIN_PATH,
            json={"email": self.email, "password": self.password},
        )

        if resp.status_code == 401:
            raise BrokerBayError("Invalid BrokerBay credentials")
        if resp.status_code != 200:
            raise BrokerBayError(
                f"BrokerBay login failed (HTTP {resp.status_code}): {resp.text[:200]}"
            )

        body = resp.json()
        self._token = body.get("token") or body.get("access_token") or body.get("accessToken")
        if not self._token:
            # Try cookie-based auth fallback
            for cookie in resp.cookies.jar:
                if cookie.name in ("token", "session", "auth"):
                    self._token = cookie.value
                    break

        if not self._token:
            raise BrokerBayError("No auth token in BrokerBay login response")

        expires = body.get("expires") or body.get("expiresAt")
        self._save_session(self._token, expires)
        logger.info("brokerbay.login_success")
        return body

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict | None = None,
        params: dict | None = None,
        retry_auth: bool = True,
    ) -> dict[str, Any]:
        """Make an authenticated API request with auto-retry on 401."""
        client = await self._get_client()
        headers = await self._auth_headers()

        resp = await client.request(
            method, path, headers=headers, json=json_data, params=params
        )

        # Retry once on 401 with fresh login
        if resp.status_code == 401 and retry_auth:
            self._token = None
            await self.login()
            headers = await self._auth_headers()
            resp = await client.request(
                method, path, headers=headers, json=json_data, params=params
            )

        if resp.status_code >= 400:
            raise BrokerBayError(
                f"BrokerBay API error {resp.status_code} on {method} {path}: "
                f"{resp.text[:300]}"
            )

        if resp.status_code == 204:
            return {"success": True}

        return resp.json()

    # ── Showings API ─────────────────────────────────────────────────

    async def get_showings(
        self,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch showings list.

        Args:
            status: Filter by status (pending, confirmed, declined, completed, cancelled).
            date_from: Start date filter (YYYY-MM-DD).
            date_to: End date filter (YYYY-MM-DD).
            page: Page number.
            per_page: Results per page.

        Returns:
            List of showing dicts.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        result = await self._request("GET", _SHOWINGS_PATH, params=params)

        # API may return {"data": [...]} or [...] directly
        if isinstance(result, list):
            return result
        return result.get("data") or result.get("showings") or result.get("results") or []

    async def get_showing(self, showing_id: str) -> dict[str, Any]:
        """Get a single showing's full details."""
        path = _SHOWING_DETAIL_PATH.format(showing_id=showing_id)
        result = await self._request("GET", path)
        return result.get("data", result) if isinstance(result, dict) else result

    async def confirm_showing(self, showing_id: str) -> dict[str, Any]:
        """Confirm/approve a showing request."""
        path = _SHOWING_CONFIRM_PATH.format(showing_id=showing_id)
        return await self._request("POST", path)

    async def decline_showing(
        self, showing_id: str, reason: str = ""
    ) -> dict[str, Any]:
        """Decline a showing request."""
        path = _SHOWING_DECLINE_PATH.format(showing_id=showing_id)
        payload = {"reason": reason} if reason else None
        return await self._request("POST", path, json_data=payload)

    async def counter_showing(
        self, showing_id: str, new_date: str, new_time: str, message: str = ""
    ) -> dict[str, Any]:
        """Counter-propose a different time for a showing."""
        path = _SHOWING_COUNTER_PATH.format(showing_id=showing_id)
        return await self._request(
            "POST",
            path,
            json_data={
                "date": new_date,
                "time": new_time,
                "message": message,
            },
        )

    async def get_pending_showings(self) -> list[dict[str, Any]]:
        """Convenience: get only pending/requested showings."""
        return await self.get_showings(status="pending")

    async def get_todays_showings(self) -> list[dict[str, Any]]:
        """Convenience: get today's showings."""
        today = datetime.now().strftime("%Y-%m-%d")
        return await self.get_showings(date_from=today, date_to=today)

    async def get_upcoming_showings(self, days: int = 7) -> list[dict[str, Any]]:
        """Convenience: get showings for the next N days."""
        from datetime import timedelta

        today = datetime.now()
        end = today + timedelta(days=days)
        return await self.get_showings(
            date_from=today.strftime("%Y-%m-%d"),
            date_to=end.strftime("%Y-%m-%d"),
        )

    # ── Listings API ─────────────────────────────────────────────────

    async def get_listings(self) -> list[dict[str, Any]]:
        """Fetch the user's active listings."""
        result = await self._request("GET", _LISTINGS_PATH)
        if isinstance(result, list):
            return result
        return result.get("data") or result.get("listings") or []

    # ── Profile ──────────────────────────────────────────────────────

    async def get_profile(self) -> dict[str, Any]:
        """Get the authenticated user's profile."""
        return await self._request("GET", _PROFILE_PATH)

    # ── Cleanup ──────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def format_showing(showing: dict[str, Any]) -> str:
    """Format a showing dict into a human-readable Telegram message.

    Handles various field naming conventions across BrokerBay API versions.
    """
    sid = showing.get("id") or showing.get("showingId") or "?"
    status = (
        showing.get("status") or showing.get("showingStatus") or "unknown"
    ).upper()

    # Property address
    prop = showing.get("property") or showing.get("listing") or {}
    address = (
        prop.get("address")
        or prop.get("fullAddress")
        or showing.get("address")
        or showing.get("propertyAddress")
        or "Unknown address"
    )

    mls = (
        prop.get("mlsNumber")
        or prop.get("mls")
        or showing.get("mlsNumber")
        or ""
    )

    # Date and time
    date_str = showing.get("date") or showing.get("showingDate") or ""
    start = showing.get("startTime") or showing.get("start") or ""
    end = showing.get("endTime") or showing.get("end") or ""
    time_range = f"{start} - {end}" if start and end else start or ""

    # Requesting agent
    agent = showing.get("buyerAgent") or showing.get("requestingAgent") or {}
    agent_name = agent.get("name") or agent.get("fullName") or ""
    agent_brokerage = agent.get("brokerage") or agent.get("officeName") or ""
    agent_phone = agent.get("phone") or agent.get("mobile") or ""

    # Notes
    notes = showing.get("notes") or showing.get("instructions") or showing.get("message") or ""

    # Build message
    status_emoji = {
        "PENDING": "🟡",
        "REQUESTED": "🟡",
        "CONFIRMED": "🟢",
        "APPROVED": "🟢",
        "DECLINED": "🔴",
        "CANCELLED": "⚫",
        "COMPLETED": "✅",
    }.get(status, "⚪")

    lines = [
        f"{status_emoji} *Showing #{sid}* — {status}",
        f"🏠 {address}",
    ]

    if mls:
        lines.append(f"📋 MLS: {mls}")
    if date_str:
        lines.append(f"📅 {date_str}")
    if time_range:
        lines.append(f"🕐 {time_range}")
    if agent_name:
        agent_line = f"👤 {agent_name}"
        if agent_brokerage:
            agent_line += f" ({agent_brokerage})"
        lines.append(agent_line)
    if agent_phone:
        lines.append(f"📞 {agent_phone}")
    if notes:
        lines.append(f"📝 _{notes}_")

    return "\n".join(lines)


def get_showing_address(showing: dict[str, Any]) -> str:
    """Extract the best available address string from a showing."""
    prop = showing.get("property") or showing.get("listing") or {}
    return (
        prop.get("address")
        or prop.get("fullAddress")
        or showing.get("address")
        or showing.get("propertyAddress")
        or ""
    )


def get_showing_id(showing: dict[str, Any]) -> str:
    """Extract the showing ID."""
    return str(showing.get("id") or showing.get("showingId") or "")


def google_maps_link(address: str) -> str:
    """Generate a Google Maps search URL for an address."""
    from urllib.parse import quote
    return f"https://www.google.com/maps/search/?api=1&query={quote(address)}"


def google_maps_static_url(address: str, api_key: str) -> str:
    """Generate a Google Static Maps image URL."""
    from urllib.parse import quote
    return (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={quote(address)}"
        f"&zoom=15&size=400x300&markers=color:red|{quote(address)}"
        f"&key={api_key}"
    )
