from pydantic_settings import BaseSettings


class DashboardSettings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    # Dashboard
    dashboard_secret_key: str = "change-me-in-production-use-a-random-string"
    dashboard_db_path: str = "storage/dashboard.db"
    demo_mode: bool = True

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Social platform OAuth credentials (empty = not configured)
    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    instagram_app_id: str = ""
    instagram_app_secret: str = ""
    twitter_client_id: str = ""
    twitter_client_secret: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""


settings = DashboardSettings()
