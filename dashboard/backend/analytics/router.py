from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.analytics.schemas import (
    EngagementResponse,
    GrowthResponse,
    OverviewResponse,
    PostsResponse,
)
from dashboard.backend.analytics.service import get_engagement, get_growth, get_overview, get_posts
from dashboard.backend.auth.models import User
from dashboard.backend.auth.service import get_current_user
from dashboard.backend.db.engine import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_overview(db, user.id)


@router.get("/posts", response_model=PostsResponse)
async def posts(
    platform: str | None = Query(None),
    sort_by: str = Query("published_at"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_posts(db, user.id, platform=platform, sort_by=sort_by, limit=limit, offset=offset)


@router.get("/growth", response_model=GrowthResponse)
async def growth(
    platform: str | None = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_growth(db, user.id, platform=platform, days=days)


@router.get("/engagement", response_model=EngagementResponse)
async def engagement(
    platform: str | None = Query(None),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_engagement(db, user.id, platform=platform, days=days)
