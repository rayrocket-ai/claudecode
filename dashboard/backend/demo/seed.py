import math
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.analytics.models import FollowerSnapshot, PostMetric
from dashboard.backend.demo.data import ENGAGEMENT_RATES, PLATFORM_PROFILES, SAMPLE_POSTS
from dashboard.backend.platforms.models import SocialAccount


async def seed_demo_data(db: AsyncSession, user_id: str) -> None:
    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=180)

    accounts = {}
    for platform, profile in PLATFORM_PROFILES.items():
        account = SocialAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            platform=platform,
            platform_user_id=profile["platform_user_id"],
            platform_username=profile["platform_username"],
            access_token="demo_token",
            connected_at=six_months_ago,
            is_active=True,
        )
        db.add(account)
        accounts[platform] = account

    await db.flush()

    # Generate follower snapshots (daily for 180 days)
    for platform, account in accounts.items():
        profile = PLATFORM_PROFILES[platform]
        base = profile["base_followers"]
        target = profile["target_followers"]
        growth = target - base

        for day in range(181):
            date = six_months_ago + timedelta(days=day)
            # Logistic growth curve with daily noise
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
    for platform, account in accounts.items():
        posts = SAMPLE_POSTS.get(platform, [])
        profile = PLATFORM_PROFILES[platform]
        rates = ENGAGEMENT_RATES.get(platform, {})

        for i, (title, post_type) in enumerate(posts):
            days_ago = random.randint(1, 170)
            published = now - timedelta(days=days_ago)
            base_rate = rates.get(post_type, 0.03)
            current_followers = profile["target_followers"]

            # More recent posts have fewer views (less time to accumulate)
            time_factor = min(1.0, days_ago / 30.0)
            base_views = int(current_followers * random.uniform(0.3, 1.5) * time_factor)

            # Video content gets more views
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
