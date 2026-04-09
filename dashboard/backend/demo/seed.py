import math
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.analytics.models import FollowerSnapshot, PostMetric
from dashboard.backend.demo.data import ENGAGEMENT_RATES, PLATFORM_PROFILES, SAMPLE_POSTS
from dashboard.backend.platforms.models import SocialAccount


async def seed_platform_data(db: AsyncSession, user_id: str, platform: str) -> None:
    """Seed demo analytics data for a single platform when a user connects it."""
    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=180)

    # Find the user's active account for this platform
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.platform == platform,
            SocialAccount.is_active == True,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return

    # Check if data already exists for this account
    result = await db.execute(
        select(FollowerSnapshot.id)
        .where(FollowerSnapshot.social_account_id == account.id)
        .limit(1)
    )
    if result.scalar_one_or_none():
        return  # Already has data

    profile = PLATFORM_PROFILES.get(platform)
    if not profile:
        return

    base = profile["base_followers"]
    target = profile["target_followers"]
    growth = target - base

    # Generate follower snapshots (daily for 180 days)
    for day in range(181):
        date = six_months_ago + timedelta(days=day)
        t = day / 180.0
        sigmoid = 1 / (1 + math.exp(-10 * (t - 0.5)))
        followers = int(base + growth * sigmoid + random.gauss(0, growth * 0.01))
        following = profile["following"] + random.randint(-5, 10)

        snapshot = FollowerSnapshot(
            id=str(uuid.uuid4()),
            social_account_id=account.id,
            platform=platform,
            follower_count=max(base, followers),
            following_count=max(0, following),
            recorded_at=date,
        )
        db.add(snapshot)

    # Generate post metrics
    posts = SAMPLE_POSTS.get(platform, [])
    rates = ENGAGEMENT_RATES.get(platform, {})

    for title, post_type in posts:
        days_ago = random.randint(1, 170)
        published = now - timedelta(days=days_ago)
        base_rate = rates.get(post_type, 0.03)
        current_followers = target

        time_factor = min(1.0, days_ago / 30.0)
        base_views = int(current_followers * random.uniform(0.3, 1.5) * time_factor)

        if post_type in ("video", "reel"):
            base_views = int(base_views * random.uniform(1.5, 3.0))

        likes = int(base_views * base_rate * random.uniform(0.6, 1.4))
        comments = int(likes * random.uniform(0.05, 0.15))
        shares = int(likes * random.uniform(0.02, 0.08))
        engagement = (likes + comments + shares) / max(base_views, 1) * 100

        post = PostMetric(
            id=str(uuid.uuid4()),
            social_account_id=account.id,
            platform=platform,
            post_id=f"{platform}_{uuid.uuid4().hex[:8]}",
            post_title=title,
            post_url=f"https://{platform}.com/p/{uuid.uuid4().hex[:8]}",
            post_type=post_type,
            published_at=published,
            views=base_views,
            likes=likes,
            comments=comments,
            shares=shares,
            engagement_rate=round(engagement, 2),
            recorded_at=now,
        )
        db.add(post)

    await db.commit()
