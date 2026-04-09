import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from dashboard.backend.db.base import Base


class PostMetric(Base):
    __tablename__ = "post_metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    social_account_id: Mapped[str] = mapped_column(
        String, ForeignKey("social_accounts.id"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String, nullable=False)
    post_id: Mapped[str] = mapped_column(String, nullable=False)
    post_title: Mapped[str | None] = mapped_column(String, nullable=True)
    post_url: Mapped[str | None] = mapped_column(String, nullable=True)
    post_type: Mapped[str] = mapped_column(String, default="text")  # text, image, video, reel, story
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class FollowerSnapshot(Base):
    __tablename__ = "follower_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    social_account_id: Mapped[str] = mapped_column(
        String, ForeignKey("social_accounts.id"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String, nullable=False)
    follower_count: Mapped[int] = mapped_column(Integer, nullable=False)
    following_count: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
