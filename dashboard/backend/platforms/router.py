from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.auth.models import User
from dashboard.backend.auth.service import get_current_user
from dashboard.backend.db.engine import get_db
from dashboard.backend.platforms.models import SocialAccount
from dashboard.backend.platforms.oauth import exchange_code_for_token, get_oauth_url, is_platform_configured
from dashboard.backend.platforms.schemas import ConnectResponse, PlatformStatus, PlatformsListResponse

router = APIRouter(prefix="/api/platforms", tags=["platforms"])

ALL_PLATFORMS = ["facebook", "instagram", "twitter", "youtube", "tiktok"]

PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "twitter": "X (Twitter)",
    "youtube": "YouTube",
    "tiktok": "TikTok",
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

    # Check if already connected
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user.id,
            SocialAccount.platform == platform,
            SocialAccount.is_active == True,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Already connected to {PLATFORM_LABELS.get(platform, platform)}")

    # If OAuth is configured, return the OAuth URL for redirect
    if is_platform_configured(platform) and not body:
        oauth_url = get_oauth_url(platform)
        if oauth_url:
            return {"oauth_url": oauth_url, "platform": platform}

    # Fallback: manual connect with username
    if body and body.username.strip():
        username = body.username.strip().lstrip("@")

        # Reactivate previously disconnected account
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
        else:
            db.add(SocialAccount(
                user_id=user.id,
                platform=platform,
                platform_user_id=f"{platform}_{username}",
                platform_username=username,
                access_token="manual",
                is_active=True,
            ))
        await db.commit()

        from dashboard.backend.demo.seed import seed_platform_data
        await seed_platform_data(db, user.id, platform)

        return ConnectResponse(message=f"Connected to {PLATFORM_LABELS.get(platform, platform)}", platform=platform, username=username)

    # No OAuth and no username provided
    raise HTTPException(status_code=400, detail="Please provide your username or configure OAuth credentials.")


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str = Query(...),
    state: str | None = Query(None),
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback: exchange code for token, fetch profile, save account."""
    if platform not in ALL_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")

    try:
        result = await exchange_code_for_token(platform, code, state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")

    # Reactivate or create account
    db_result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.platform == platform,
        )
    )
    existing = db_result.scalar_one_or_none()

    if existing:
        existing.platform_username = result["username"]
        existing.platform_user_id = result["user_id"]
        existing.access_token = result["access_token"]
        existing.refresh_token = result.get("refresh_token")
        existing.is_active = True
        existing.connected_at = datetime.now(timezone.utc)
    else:
        db.add(SocialAccount(
            user_id=user_id,
            platform=platform,
            platform_user_id=result["user_id"],
            platform_username=result["username"],
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            is_active=True,
        ))
    await db.commit()

    # Seed demo analytics for the new connection
    from dashboard.backend.demo.seed import seed_platform_data
    await seed_platform_data(db, user_id, platform)

    return {
        "success": True,
        "platform": platform,
        "username": result["username"],
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
        raise HTTPException(status_code=404, detail=f"Not connected to {PLATFORM_LABELS.get(platform, platform)}")

    account.is_active = False
    await db.commit()
    return ConnectResponse(message=f"Disconnected from {PLATFORM_LABELS.get(platform, platform)}", platform=platform)
