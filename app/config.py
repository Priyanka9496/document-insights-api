from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "document_insights"
    redis_url: str = "redis://localhost:6379"
    max_active_jobs_per_user: int = 3
    active_job_ttl_seconds: int = 900
    summary_cache_ttl_seconds: int = 86400
    inflight_lock_ttl_seconds: int = 900

    processing_min_seconds: int = 10
    processing_max_seconds: int = 30
    processing_failure_rate: float = 0.10
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings():
    return Settings()

