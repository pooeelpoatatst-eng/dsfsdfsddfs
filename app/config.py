from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ADMIN_IDS is entered as a comma-separated string, not JSON. Disabling
    # automatic JSON decoding lets an empty ADMIN_IDS= remain a valid value.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", enable_decoding=False)

    control_bot_token: SecretStr
    telegram_api_id: int
    telegram_api_hash: SecretStr
    database_url: str
    session_encryption_key: SecretStr
    ai_api_key: SecretStr | None = None
    ai_base_url: str = "https://codex.sale/v1"
    ai_model: str = "gpt-5.4-mini"
    admin_ids: set[int] = Field(default_factory=set)
    log_level: str = "INFO"
    max_active_clients: int = Field(default=100, ge=1, le=1000)
    ai_max_concurrent: int = Field(default=10, ge=1, le=100)
    download_max_mb: int = Field(default=50, ge=1, le=500)
    temp_dir: Path = Path("/tmp/userbot")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> set[int]:
        if not value:
            return set()
        if isinstance(value, str):
            return {int(item.strip()) for item in value.split(",") if item.strip()}
        return set(value)  # type: ignore[arg-type]

    @field_validator("ai_base_url")
    @classmethod
    def normalize_url(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Railway provides postgresql://; SQLAlchemy async requires asyncpg.
        if value.startswith("postgres://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
