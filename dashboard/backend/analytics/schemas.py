from pydantic import BaseModel


class PlatformFollowers(BaseModel):
    platform: str
    followers: int
    change_percent: float


class OverviewResponse(BaseModel):
    total_followers: int
    followers_change_percent: float
    total_views: int
    views_change_percent: float
    total_posts: int
    engagement_rate: float
    engagement_change_percent: float
    platforms: list[PlatformFollowers]


class PostPerformance(BaseModel):
    id: str
    platform: str
    post_title: str | None
    post_type: str
    published_at: str
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float

    model_config = {"from_attributes": True}


class PostsResponse(BaseModel):
    posts: list[PostPerformance]
    total: int


class GrowthPoint(BaseModel):
    date: str
    followers: int


class PlatformGrowth(BaseModel):
    platform: str
    data: list[GrowthPoint]


class GrowthResponse(BaseModel):
    platforms: list[PlatformGrowth]


class EngagementPoint(BaseModel):
    date: str
    rate: float


class PlatformEngagement(BaseModel):
    platform: str
    data: list[EngagementPoint]


class EngagementResponse(BaseModel):
    platforms: list[PlatformEngagement]
