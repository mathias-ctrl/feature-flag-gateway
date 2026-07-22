from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "feature-flag-gateway"
    environment: str = "local"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/flags"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = Field(
        default="local-development-secret-change-me-123456",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    cache_ttl_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
