"""OAuth URL generators, token exchange, and profile fetching for each social platform."""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx

from dashboard.backend.config import settings

# Store PKCE verifiers and state tokens temporarily
_pkce_store: dict[str, str] = {}
_state_store: set[str] = set()


def _redirect_uri(platform: str) -> str:
    return f"{settings.dashboard_url}/auth/callback/{platform}"


def get_oauth_url(platform: str) -> str | None:
    generators = {
        "facebook": _facebook_oauth_url,
        "instagram": _instagram_oauth_url,
        "twitter": _twitter_oauth_url,
        "youtube": _youtube_oauth_url,
        "tiktok": _tiktok_oauth_url,
    }
    gen = generators.get(platform)
    return gen() if gen else None


def is_platform_configured(platform: str) -> bool:
    checks = {
        "facebook": bool(settings.facebook_app_id and settings.facebook_app_secret),
        "instagram": bool(settings.instagram_app_id and settings.instagram_app_secret),
        "twitter": bool(settings.twitter_client_id and settings.twitter_client_secret),
        "youtube": bool(settings.youtube_client_id and settings.youtube_client_secret),
        "tiktok": bool(settings.tiktok_client_key and settings.tiktok_client_secret),
    }
    return checks.get(platform, False)


# ── Token Exchange ──────────────────────────────────────────────────────

async def exchange_code_for_token(platform: str, code: str, state: str | None = None) -> dict:
    """Exchange an OAuth authorization code for an access token and fetch profile.
    Returns dict with: access_token, username, user_id, profile_data
    """
    exchangers = {
        "facebook": _facebook_exchange,
        "instagram": _instagram_exchange,
        "twitter": _twitter_exchange,
        "youtube": _youtube_exchange,
        "tiktok": _tiktok_exchange,
    }
    exchanger = exchangers.get(platform)
    if not exchanger:
        raise ValueError(f"Unknown platform: {platform}")
    return await exchanger(code, state)


# ── Facebook ────────────────────────────────────────────────────────────

def _facebook_oauth_url() -> str | None:
    if not settings.facebook_app_id:
        return None
    state = secrets.token_urlsafe(16)
    _state_store.add(state)
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": _redirect_uri("facebook"),
        "scope": "public_profile,email,pages_show_list,pages_read_engagement",
        "response_type": "code",
        "state": state,
    }
    return f"https://www.facebook.com/v21.0/dialog/oauth?{urlencode(params)}"


async def _facebook_exchange(code: str, state: str | None) -> dict:
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        resp = await client.get("https://graph.facebook.com/v21.0/oauth/access_token", params={
            "client_id": settings.facebook_app_id,
            "client_secret": settings.facebook_app_secret,
            "redirect_uri": _redirect_uri("facebook"),
            "code": code,
        })
        token_data = resp.json()
        access_token = token_data.get("access_token", "")

        if not access_token:
            raise ValueError(f"Facebook token exchange failed: {token_data}")

        # Fetch user profile
        resp = await client.get("https://graph.facebook.com/v21.0/me", params={
            "fields": "id,name,email",
            "access_token": access_token,
        })
        profile = resp.json()

        return {
            "access_token": access_token,
            "username": profile.get("name", "Facebook User"),
            "user_id": profile.get("id", ""),
            "profile_data": profile,
        }


# ── Instagram (via Facebook Login) ─────────────────────────────────────

def _instagram_oauth_url() -> str | None:
    if not settings.instagram_app_id:
        return None
    state = secrets.token_urlsafe(16)
    _state_store.add(state)
    params = {
        "client_id": settings.instagram_app_id,
        "redirect_uri": _redirect_uri("instagram"),
        "scope": "public_profile,instagram_basic,instagram_manage_insights",
        "response_type": "code",
        "state": state,
    }
    return f"https://www.facebook.com/v21.0/dialog/oauth?{urlencode(params)}"


async def _instagram_exchange(code: str, state: str | None) -> dict:
    async with httpx.AsyncClient() as client:
        # Exchange code for token via Facebook
        resp = await client.get("https://graph.facebook.com/v21.0/oauth/access_token", params={
            "client_id": settings.instagram_app_id,
            "client_secret": settings.instagram_app_secret,
            "redirect_uri": _redirect_uri("instagram"),
            "code": code,
        })
        token_data = resp.json()
        access_token = token_data.get("access_token", "")

        if not access_token:
            raise ValueError(f"Instagram token exchange failed: {token_data}")

        # Get Facebook pages, then linked Instagram accounts
        resp = await client.get("https://graph.facebook.com/v21.0/me/accounts", params={
            "access_token": access_token,
        })
        pages = resp.json().get("data", [])

        ig_username = "Instagram User"
        ig_user_id = ""

        if pages:
            page_id = pages[0].get("id")
            resp = await client.get(f"https://graph.facebook.com/v21.0/{page_id}", params={
                "fields": "instagram_business_account",
                "access_token": access_token,
            })
            ig_account = resp.json().get("instagram_business_account", {})
            if ig_account.get("id"):
                ig_user_id = ig_account["id"]
                resp = await client.get(f"https://graph.facebook.com/v21.0/{ig_user_id}", params={
                    "fields": "username,name,followers_count",
                    "access_token": access_token,
                })
                ig_profile = resp.json()
                ig_username = ig_profile.get("username", "Instagram User")

        return {
            "access_token": access_token,
            "username": ig_username,
            "user_id": ig_user_id,
            "profile_data": {"pages": len(pages)},
        }


# ── Twitter / X (OAuth 2.0 with PKCE) ──────────────────────────────────

def _twitter_oauth_url() -> str | None:
    if not settings.twitter_client_id:
        return None
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    _pkce_store[state] = code_verifier
    _state_store.add(state)
    params = {
        "response_type": "code",
        "client_id": settings.twitter_client_id,
        "redirect_uri": _redirect_uri("twitter"),
        "scope": "tweet.read users.read follows.read offline.access",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"


async def _twitter_exchange(code: str, state: str | None) -> dict:
    code_verifier = _pkce_store.pop(state or "", "")
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        resp = await client.post(
            "https://api.twitter.com/2/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _redirect_uri("twitter"),
                "client_id": settings.twitter_client_id,
                "code_verifier": code_verifier,
            },
            auth=(settings.twitter_client_id, settings.twitter_client_secret),
        )
        token_data = resp.json()
        access_token = token_data.get("access_token", "")

        if not access_token:
            raise ValueError(f"Twitter token exchange failed: {token_data}")

        # Fetch user profile
        resp = await client.get(
            "https://api.twitter.com/2/users/me",
            params={"user.fields": "public_metrics,profile_image_url,username,name"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = resp.json().get("data", {})

        return {
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "username": user_data.get("username", "X User"),
            "user_id": user_data.get("id", ""),
            "profile_data": user_data,
        }


# ── YouTube (Google OAuth 2.0) ──────────────────────────────────────────

def _youtube_oauth_url() -> str | None:
    if not settings.youtube_client_id:
        return None
    state = secrets.token_urlsafe(16)
    _state_store.add(state)
    params = {
        "client_id": settings.youtube_client_id,
        "redirect_uri": _redirect_uri("youtube"),
        "scope": "https://www.googleapis.com/auth/youtube.readonly",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def _youtube_exchange(code: str, state: str | None) -> dict:
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        resp = await client.post("https://oauth2.googleapis.com/token", data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _redirect_uri("youtube"),
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
        })
        token_data = resp.json()
        access_token = token_data.get("access_token", "")

        if not access_token:
            raise ValueError(f"YouTube token exchange failed: {token_data}")

        # Fetch channel info
        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet,statistics", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        channels = resp.json().get("items", [])
        channel = channels[0] if channels else {}
        snippet = channel.get("snippet", {})

        return {
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "username": snippet.get("title", "YouTube Channel"),
            "user_id": channel.get("id", ""),
            "profile_data": {"subscribers": channel.get("statistics", {}).get("subscriberCount")},
        }


# ── TikTok ──────────────────────────────────────────────────────────────

def _tiktok_oauth_url() -> str | None:
    if not settings.tiktok_client_key:
        return None
    state = secrets.token_urlsafe(16)
    _state_store.add(state)
    params = {
        "client_key": settings.tiktok_client_key,
        "redirect_uri": _redirect_uri("tiktok"),
        "scope": "user.info.basic,video.list",
        "response_type": "code",
        "state": state,
    }
    return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"


async def _tiktok_exchange(code: str, state: str | None) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://open.tiktokapis.com/v2/oauth/token/", data={
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": _redirect_uri("tiktok"),
        })
        token_data = resp.json()
        access_token = token_data.get("access_token", "")

        if not access_token:
            raise ValueError(f"TikTok token exchange failed: {token_data}")

        # Fetch user info
        resp = await client.get(
            "https://open.tiktokapis.com/v2/user/info/",
            params={"fields": "display_name,follower_count,username"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = resp.json().get("data", {}).get("user", {})

        return {
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "username": user_data.get("username", user_data.get("display_name", "TikTok User")),
            "user_id": token_data.get("open_id", ""),
            "profile_data": user_data,
        }
