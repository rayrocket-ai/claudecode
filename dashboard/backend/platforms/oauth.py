"""OAuth URL generators and token exchange for each social platform."""

import secrets
from urllib.parse import urlencode

from dashboard.backend.config import settings

# Store PKCE verifiers temporarily (in production, use Redis/DB)
_pkce_store: dict[str, str] = {}


def _redirect_uri(platform: str) -> str:
    return f"{settings.dashboard_url}/auth/callback/{platform}"


def get_oauth_url(platform: str) -> str | None:
    """Return the OAuth authorization URL for the given platform, or None if not configured."""
    generators = {
        "facebook": _facebook_oauth_url,
        "instagram": _instagram_oauth_url,
        "twitter": _twitter_oauth_url,
        "youtube": _youtube_oauth_url,
        "tiktok": _tiktok_oauth_url,
    }
    gen = generators.get(platform)
    if not gen:
        return None
    return gen()


def is_platform_configured(platform: str) -> bool:
    """Check if OAuth credentials are configured for a platform."""
    checks = {
        "facebook": bool(settings.facebook_app_id and settings.facebook_app_secret),
        "instagram": bool(settings.instagram_app_id and settings.instagram_app_secret),
        "twitter": bool(settings.twitter_client_id and settings.twitter_client_secret),
        "youtube": bool(settings.youtube_client_id and settings.youtube_client_secret),
        "tiktok": bool(settings.tiktok_client_key and settings.tiktok_client_secret),
    }
    return checks.get(platform, False)


def _facebook_oauth_url() -> str | None:
    if not settings.facebook_app_id:
        return None
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": _redirect_uri("facebook"),
        "scope": "pages_show_list,pages_read_engagement,pages_read_user_content",
        "response_type": "code",
        "state": secrets.token_urlsafe(16),
    }
    return f"https://www.facebook.com/v21.0/dialog/oauth?{urlencode(params)}"


def _instagram_oauth_url() -> str | None:
    if not settings.instagram_app_id:
        return None
    params = {
        "client_id": settings.instagram_app_id,
        "redirect_uri": _redirect_uri("instagram"),
        "scope": "instagram_basic,instagram_manage_insights",
        "response_type": "code",
        "state": secrets.token_urlsafe(16),
    }
    return f"https://www.facebook.com/v21.0/dialog/oauth?{urlencode(params)}"


def _twitter_oauth_url() -> str | None:
    if not settings.twitter_client_id:
        return None
    # Twitter OAuth 2.0 with PKCE
    code_verifier = secrets.token_urlsafe(64)
    import hashlib, base64
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    _pkce_store[state] = code_verifier
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


def _youtube_oauth_url() -> str | None:
    if not settings.youtube_client_id:
        return None
    params = {
        "client_id": settings.youtube_client_id,
        "redirect_uri": _redirect_uri("youtube"),
        "scope": "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/yt-analytics.readonly",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": secrets.token_urlsafe(16),
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def _tiktok_oauth_url() -> str | None:
    if not settings.tiktok_client_key:
        return None
    params = {
        "client_key": settings.tiktok_client_key,
        "redirect_uri": _redirect_uri("tiktok"),
        "scope": "user.info.basic,video.list",
        "response_type": "code",
        "state": secrets.token_urlsafe(16),
    }
    return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"
