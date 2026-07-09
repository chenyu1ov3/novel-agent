from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment or .env."""

    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: SecretStr | None = None
    novel_agent_model: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
