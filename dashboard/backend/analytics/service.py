from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.analytics.models import FollowerSnapshot, PostMetric
from dashboard.backend.analytics.schemas import (
    EngagementPoint,
    EngagementResponse,
    GrowthPoint,
    GrowthResponse,
    OverviewResponse,
    PlatformEngagement,
    PlatformFollowers,
    PlatformGrowth,
    PostPerformance,
    PostsResponse,
)
from dashboard.backend.platforms.models import SocialAccount


async def get_overview(db: AsyncSession, user_id: str) -> OverviewResponse:
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    # Get user's accounts
    result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == user_id, SocialAccount.is_active == True)
    )
    accounts = result.scalars().all()
    account_ids = [a.id for a in accounts]

    if not account_ids:
        return OverviewResponse(
            total_followers=0, followers_change_percent=0, total_views=0,
            views_change_percent=0, total_posts=0, engagement_rate=0,
            engagement_change_percent=0, platforms=[],
        )

    # Latest follower counts per platform
    platforms = []
    total_followers = 0
    total_followers_prev = 0

    for account in accounts:
        # Current followers (latest snapshot)
        result = await db.execute(
            select(FollowerSnapshot)
            .where(FollowerSnapshot.social_account_id == account.id)
            .order_by(FollowerSnapshot.recorded_at.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        # Followers 30 days ago
        result = await db.execute(
            select(FollowerSnapshot)
            .where(
                FollowerSnapshot.social_account_id == account.id,
                FollowerSnapshot.recorded_at <= thirty_days_ago,
            )
            .order_by(FollowerSnapshot.recorded_at.desc())
            .limit(1)
        )
        prev = result.scalar_one_or_none()

        current = latest.follower_count if latest else 0
        previous = prev.follower_count if prev else current
        change = ((current - previous) / max(previous, 1)) * 100

        total_followers += current
        total_followers_prev += previous

        platforms.append(PlatformFollowers(
            platform=account.platform,
            followers=current,
            change_percent=round(change, 1),
        ))

    followers_change = ((total_followers - total_followers_prev) / max(total_followers_prev, 1)) * 100

    # Total views this month
    result = await db.execute(
        select(func.sum(PostMetric.views))
        .where(
            PostMetric.social_account_id.in_(account_ids),
            PostMetric.published_at >= thirty_days_ago,
        )
    )
    current_views = result.scalar() or 0

    result = await db.execute(
        select(func.sum(PostMetric.views))
        .where(
            PostMetric.social_account_id.in_(account_ids),
            PostMetric.published_at >= sixty_days_ago,
            PostMetric.published_at < thirty_days_ago,
        )
    )
    prev_views = result.scalar() or 0
    views_change = ((current_views - prev_views) / max(prev_views, 1)) * 100

    # Total posts
    result = await db.execute(
        select(func.count(PostMetric.id))
        .where(PostMetric.social_account_id.in_(account_ids))
    )
    total_posts = result.scalar() or 0

    # Average engagement rate
    result = await db.execute(
        select(func.avg(PostMetric.engagement_rate))
        .where(
            PostMetric.social_account_id.in_(account_ids),
            PostMetric.published_at >= thirty_days_ago,
        )
    )
    current_engagement = result.scalar() or 0

    result = await db.execute(
        select(func.avg(PostMetric.engagement_rate))
        .where(
            PostMetric.social_account_id.in_(account_ids),
            PostMetric.published_at >= sixty_days_ago,
            PostMetric.published_at < thirty_days_ago,
        )
    )
    prev_engagement = result.scalar() or 0
    engagement_change = ((current_engagement - prev_engagement) / max(prev_engagement, 0.01)) * 100

    return OverviewResponse(
        total_followers=total_followers,
        followers_change_percent=round(followers_change, 1),
        total_views=current_views,
        views_change_percent=round(views_change, 1),
        total_posts=total_posts,
        engagement_rate=round(current_engagement, 2),
        engagement_change_percent=round(engagement_change, 1),
        platforms=platforms,
    )


async def get_posts(
    db: AsyncSession, user_id: str, platform: str | None = None,
    sort_by: str = "published_at", limit: int = 50, offset: int = 0,
) -> PostsResponse:
    # Get user's account ids
    q = select(SocialAccount.id).where(SocialAccount.user_id == user_id, SocialAccount.is_active == True)
    if platform:
        q = q.where(SocialAccount.platform == platform)
    result = await db.execute(q)
    account_ids = [r[0] for r in result.all()]

    if not account_ids:
        return PostsResponse(posts=[], total=0)

    # Count total
    result = await db.execute(
        select(func.count(PostMetric.id)).where(PostMetric.social_account_id.in_(account_ids))
    )
    total = result.scalar() or 0

    # Fetch posts
    sort_col = getattr(PostMetric, sort_by, PostMetric.published_at)
    result = await db.execute(
        select(PostMetric)
        .where(PostMetric.social_account_id.in_(account_ids))
        .order_by(sort_col.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = result.scalars().all()

    return PostsResponse(
        posts=[
            PostPerformance(
                id=p.id,
                platform=p.platform,
                post_title=p.post_title,
                post_type=p.post_type,
                published_at=p.published_at.isoformat(),
                views=p.views,
                likes=p.likes,
                comments=p.comments,
                shares=p.shares,
                engagement_rate=p.engagement_rate,
            )
            for p in posts
        ],
        total=total,
    )


async def get_growth(
    db: AsyncSession, user_id: str, platform: str | None = None, days: int = 30,
) -> GrowthResponse:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    q = select(SocialAccount).where(SocialAccount.user_id == user_id, SocialAccount.is_active == True)
    if platform:
        q = q.where(SocialAccount.platform == platform)
    result = await db.execute(q)
    accounts = result.scalars().all()

    platform_growths = []
    for account in accounts:
        result = await db.execute(
            select(FollowerSnapshot)
            .where(
                FollowerSnapshot.social_account_id == account.id,
                FollowerSnapshot.recorded_at >= since,
            )
            .order_by(FollowerSnapshot.recorded_at.asc())
        )
        snapshots = result.scalars().all()

        data = [
            GrowthPoint(date=s.recorded_at.strftime("%Y-%m-%d"), followers=s.follower_count)
            for s in snapshots
        ]
        platform_growths.append(PlatformGrowth(platform=account.platform, data=data))

    return GrowthResponse(platforms=platform_growths)


async def get_engagement(
    db: AsyncSession, user_id: str, platform: str | None = None, days: int = 30,
) -> EngagementResponse:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    q = select(SocialAccount).where(SocialAccount.user_id == user_id, SocialAccount.is_active == True)
    if platform:
        q = q.where(SocialAccount.platform == platform)
    result = await db.execute(q)
    accounts = result.scalars().all()

    platform_engagements = []
    for account in accounts:
        result = await db.execute(
            select(PostMetric)
            .where(
                PostMetric.social_account_id == account.id,
                PostMetric.published_at >= since,
            )
            .order_by(PostMetric.published_at.asc())
        )
        posts = result.scalars().all()

        # Group by date and average engagement
        daily: dict[str, list[float]] = {}
        for p in posts:
            d = p.published_at.strftime("%Y-%m-%d")
            daily.setdefault(d, []).append(p.engagement_rate)

        data = [
            EngagementPoint(date=d, rate=round(sum(rates) / len(rates), 2))
            for d, rates in sorted(daily.items())
        ]
        platform_engagements.append(PlatformEngagement(platform=account.platform, data=data))

    return EngagementResponse(platforms=platform_engagements)
