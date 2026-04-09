import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.auth.models import User
from dashboard.backend.auth.service import get_current_user
from dashboard.backend.config import settings
from dashboard.backend.db.engine import get_db
from dashboard.backend.platforms.models import SocialAccount
from dashboard.backend.platforms.oauth import get_oauth_url, is_platform_configured
from dashboard.backend.platforms.schemas import ConnectResponse, PlatformStatus, PlatformsListResponse

router = APIRouter(prefix="/api/platforms", tags=["platforms"])

ALL_PLATFORMS = ["facebook", "instagram", "twitter", "youtube", "tiktok"]


@router.get("", response_model=PlatformsListResponse)
async def list_platforms(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == user.id, SocialAccount.is_active == True)
    )
    connected = {a.platform: a for a in result.scalars().all()}

    platforms = []
    for p in ALL_PLATFORMS:
        if p in connected:
            account = connected[p]
            platforms.append(PlatformStatus(
                platform=p,
                connected=True,
                username=account.platform_username,
                connected_at=account.connected_at.isoformat() if account.connected_at else None,
                configured=is_platform_configured(p),
            ))
        else:
            platforms.append(PlatformStatus(
                platform=p,
                connected=False,
                configured=is_platform_configured(p),
            ))

    return PlatformsListResponse(platforms=platforms)


@router.post("/{platform}/connect")
async def connect_platform(
    platform: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if platform not in ALL_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    # Check if already connected
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user.id,
            SocialAccount.platform == platform,
            SocialAccount.is_active == True,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Already connected to {platform}")

    # Check if OAuth credentials are configured
    if is_platform_configured(platform):
        # Return the real OAuth URL - frontend will redirect there
        oauth_url = get_oauth_url(platform)
        return {"oauth_url": oauth_url, "platform": platform}

    # No credentials configured - tell the user what's needed
    credential_keys = {
        "facebook": "FACEBOOK_APP_ID and FACEBOOK_APP_SECRET",
        "instagram": "INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET",
        "twitter": "TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET",
        "youtube": "YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET",
        "tiktok": "TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET",
    }
    raise HTTPException(
        status_code=400,
        detail=f"To connect {platform}, add {credential_keys[platform]} to your .env file and restart the server.",
    )


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from social platforms.

    In a production app, this would:
    1. Exchange the authorization code for an access token
    2. Fetch the user's profile from the platform API
    3. Save the account with real tokens

    For now, this creates the account record with the auth code.
    Token exchange requires platform-specific API calls.
    """
    if platform not in ALL_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    # TODO: Exchange code for access token using platform-specific API
    # TODO: Fetch user profile (username, follower count, etc.)
    # For now, save with the code - implement token exchange per platform as needed

    return {
        "message": f"OAuth callback received for {platform}. Configure token exchange in platforms/{platform}.py",
        "platform": platform,
        "code_received": True,
    }


@router.post("/{platform}/disconnect", response_model=ConnectResponse)
async def disconnect_platform(
    platform: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user.id,
            SocialAccount.platform == platform,
            SocialAccount.is_active == True,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail=f"Not connected to {platform}")

    account.is_active = False
    await db.commit()
    return ConnectResponse(message=f"Disconnected from {platform}", platform=platform)
