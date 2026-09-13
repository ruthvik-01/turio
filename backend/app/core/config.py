"""Application settings, loaded once from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
