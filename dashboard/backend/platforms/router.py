from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.auth.models import User
from dashboard.backend.auth.service import get_current_user
from dashboard.backend.db.engine import get_db
from dashboard.backend.platforms.models import SocialAccount
from dashboard.backend.platforms.oauth import get_oauth_url, is_platform_configured
from dashboard.backend.platforms.schemas import ConnectResponse, PlatformStatus, PlatformsListResponse

router = APIRouter(prefix="/api/platforms", tags=["platforms"])

ALL_PLATFORMS = ["facebook", "instagram", "twitter", "youtube", "tiktok"]

PLATFORM_PROFILE_URLS = {
    "facebook": "https://facebook.com/",
    "instagram": "https://instagram.com/",
    "twitter": "https://x.com/",
    "youtube": "https://youtube.com/@",
    "tiktok": "https://tiktok.com/@",
}


class ManualConnectRequest(BaseModel):
    username: str


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
                profile_url=PLATFORM_PROFILE_URLS.get(p, "") + (account.platform_username or ""),
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
    body: ManualConnectRequest | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if platform not in ALL_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    # Check if already connected (active)
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user.id,
            SocialAccount.platform == platform,
            SocialAccount.is_active == True,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Already connected to {platform}")

    # If OAuth credentials are configured, return OAuth URL for redirect
    if is_platform_configured(platform) and not body:
        oauth_url = get_oauth_url(platform)
        return {"oauth_url": oauth_url, "platform": platform}

    # Manual connect: user provides their username/handle
    if body and body.username.strip():
        username = body.username.strip().lstrip("@")

        # Check if there's a previously disconnected account to reactivate
        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user.id,
                SocialAccount.platform == platform,
                SocialAccount.is_active == False,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.platform_username = username
            existing.platform_user_id = f"{platform}_{username}"
            existing.is_active = True
            existing.connected_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            account = SocialAccount(
                user_id=user.id,
                platform=platform,
                platform_user_id=f"{platform}_{username}",
                platform_username=username,
                access_token="manual",
                is_active=True,
            )
            db.add(account)
            await db.commit()

        # Seed demo analytics data for this platform
        from dashboard.backend.demo.seed import seed_platform_data
        await seed_platform_data(db, user.id, platform)

        profile_url = PLATFORM_PROFILE_URLS.get(platform, "") + username
        return ConnectResponse(
            message=f"Connected to {platform}",
            platform=platform,
            username=username,
        )

    raise HTTPException(status_code=400, detail="Please provide your username/handle for this platform.")


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
