"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All application settings. Loaded from .env, then env vars."""

    model_config = {
        "env_file": str(Path(__file__).resolve().parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_ignore_empty": True,  # empty env vars don't override .env
    }

    # Telegram
    telegram_bot_token: str = ""
    authorized_user_ids: str = ""

    # AI
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # REALM / TRREB
    realm_username: str = ""
    realm_password: str = ""
    realm_url: str = "https://torontomls.net"
    realm_sso_url: str = (
        "https://sso.ampre.ca/realms/trreb/protocol/openid-connect/auth"
    )

    # Brokerage
    brokerage_name: str = ""
    brokerage_phone: str = ""
    brokerage_fax: str = ""
    brokerage_email: str = ""
    brokerage_address: str = ""

    # Browser
    browser_headless: bool = True
    browser_slowmo: int = 100

    # DocuSign
    docusign_account_id: str = ""
    docusign_integration_key: str = ""
    docusign_user_id: str = ""
    docusign_private_key_path: str = ""
    docusign_base_url: str = "https://demo.docusign.net/restapi"

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Higgsfield (tour video generation)
    higgsfield_api_key: str = ""
    higgsfield_model: str = "standard"  # standard or soul_cinema
    tour_max_photos: int = 10
    tour_clip_duration: int = 5  # seconds per clip (3-5)

    # SkySlope
    skyslope_api_key: str = ""
    skyslope_api_url: str = "https://api.skyslope.com"

    # Derived
    @property
    def authorized_user_id_list(self) -> list[int]:
        if not self.authorized_user_ids.strip():
            return []
        return [int(x.strip()) for x in self.authorized_user_ids.split(",") if x.strip()]

    @property
    def is_realm_configured(self) -> bool:
        return bool(self.realm_username and self.realm_password)

    @property
    def is_docusign_configured(self) -> bool:
        return bool(self.docusign_account_id and self.docusign_integration_key)

    @property
    def is_smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user)

    @property
    def is_higgsfield_configured(self) -> bool:
        return bool(self.higgsfield_api_key)


# Paths
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "realtor.db"
STORAGE_DIR.mkdir(exist_ok=True)


def get_settings() -> Settings:
    return Settings()
