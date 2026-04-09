from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.auth.models import User
from dashboard.backend.auth.service import get_current_user
from dashboard.backend.config import settings
from dashboard.backend.db.engine import get_db
from dashboard.backend.platforms.models import SocialAccount
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
            ))
        else:
            platforms.append(PlatformStatus(platform=p, connected=False))

    return PlatformsListResponse(platforms=platforms)


@router.post("/{platform}/connect", response_model=ConnectResponse)
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

    if settings.demo_mode:
        from dashboard.backend.demo.data import PLATFORM_PROFILES
        profile = PLATFORM_PROFILES.get(platform, {})
        account = SocialAccount(
            user_id=user.id,
            platform=platform,
            platform_user_id=profile.get("platform_user_id", f"{platform}_demo"),
            platform_username=profile.get("platform_username", f"@demo_{platform}"),
            access_token="demo_token",
            is_active=True,
        )
        db.add(account)
        await db.commit()
        return ConnectResponse(
            message=f"Connected to {platform} (demo mode)",
            platform=platform,
            username=account.platform_username,
        )

    # Real OAuth would redirect to platform's auth URL
    raise HTTPException(
        status_code=501,
        detail=f"Real OAuth for {platform} not configured. Set API credentials in .env",
    )


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
