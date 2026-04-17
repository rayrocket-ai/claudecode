"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """All application settings. Loaded from .env, then env vars."""

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_ignore_empty": True,
    }

    # Database
    database_url: str = f"sqlite+aiosqlite:///{STORAGE_DIR / 'dashboard.db'}"

    # Web / auth
    jwt_secret: str = "dev-insecure-change-me"
    session_secret: str = "dev-insecure-change-me"
    web_base_url: str = "http://localhost:8000"

    # REALM / TRREB
    realm_username: str = ""
    realm_password: str = ""
    realm_url: str = "https://torontomls.net"
    realm_sso_url: str = (
        "https://sso.ampre.ca/realms/trreb/protocol/openid-connect/auth"
    )

    # GHL (SMS relay for REALM 2FA)
    ghl_api_key: str = ""
    ghl_location_id: str = ""
    ghl_phone_number: str = ""
    ghl_api_base: str = "https://services.leadconnectorhq.com"
    ghl_mfa_poll_seconds: int = 90

    # Google Maps
    google_maps_api_key: str = ""

    # AI (optional)
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # Browser
    browser_headless: bool = True
    browser_slowmo: int = 50

    # Ingestion
    backfill_days: int = 180
    scraper_timezone: str = "America/Toronto"

    @property
    def is_realm_configured(self) -> bool:
        return bool(self.realm_username and self.realm_password)

    @property
    def is_ghl_configured(self) -> bool:
        return bool(self.ghl_api_key and self.ghl_phone_number)


def get_settings() -> Settings:
    return Settings()
