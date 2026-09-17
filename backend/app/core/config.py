"""Application settings, loaded once from the environment."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_version: str = "0.1.0"
    database_url: str

    # No default: an unsigned JWT is worse than a service that refuses to boot.
    secret_key: str
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # Resume binaries live in S3-compatible object storage; PostgreSQL stores
    # only metadata and the key (DATABASE.md section 1).
    object_storage_endpoint: str
    object_storage_bucket: str
    object_storage_access_key: str
    object_storage_secret_key: str
    # MinIO and most S3-compatible servers ignore the region but the client
    # requires one to sign requests.
    object_storage_region: str = "us-east-1"

    max_resume_bytes: int = 5 * 1024 * 1024

    # Local copy of the Stapply job slice (DATASET.md section 1). Ingested by
    # `POST /api/v1/jobs/refresh` and by scripts/import_jobs.py.
    job_dataset_path: str = "data/ashby-jobs.csv"
    # Rows per commit during ingestion. Bounds memory on a large slice.
    job_ingest_batch_size: int = 1000

    ranking_config_path: str = str(Path(__file__).resolve().parents[1] / "ml" / "ranking.json")
    model_cache_path: str = str(Path(__file__).resolve().parents[2] / ".model-cache")
    model_local_files_only: bool = True
    browser_automation_enabled: bool = False
    browser_headless: bool = True
    browser_executable_path: str | None = None
    browser_timeout_seconds: int = 90
    worker_poll_seconds: float = Field(default=1.0, ge=0.05, le=60)
    worker_lease_seconds: int = Field(default=60, ge=15, le=3600)
    rate_limits_enabled: bool = True
    auth_ip_limit: int = Field(default=200, ge=1)
    auth_account_limit: int = Field(default=10, ge=1)
    work_user_limit: int = Field(default=30, ge=1)
    rate_window_seconds: int = Field(default=60, ge=1, le=3600)
    max_request_bytes: int = Field(default=6 * 1024 * 1024, ge=1024)

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.app_env == "production":
            if len(self.secret_key) < 32 or any(part in self.secret_key.lower() for part in ("replace", "insecure", "test-only")):
                raise ValueError("Production requires a strong explicitly configured SECRET_KEY.")
            if "replace_me" in self.object_storage_secret_key or len(self.object_storage_secret_key) < 16:
                raise ValueError("Production requires explicitly configured object-storage credentials.")
            if not self.rate_limits_enabled:
                raise ValueError("Rate limits must remain enabled in production.")
        return self

    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment
