from pydantic import BaseModel


class PlatformStatus(BaseModel):
    platform: str
    connected: bool
    username: str | None = None
    connected_at: str | None = None


class PlatformsListResponse(BaseModel):
    platforms: list[PlatformStatus]


class ConnectResponse(BaseModel):
    message: str
    platform: str
    username: str | None = None
