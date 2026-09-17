from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Financial Platform API"
    environment: str = "development"
    debug: bool = True

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/financial"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    cors_origins: list[str] = ["http://localhost:4200"]

    max_upload_bytes: int = 10 * 1024 * 1024
    storage_dir: str = "./var/documents"

    llm_provider: str = "null"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
