# app/config.py
"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings - flat structure."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: str = Field("development", alias="APP_ENV")
    host: str = Field("0.0.0.0", alias="APP_HOST")
    port: int = Field(8000, alias="APP_PORT", validation_alias="PORT")
    workers: int = Field(1, alias="APP_WORKERS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field("sqlite+aiosqlite:///:memory:", alias="DATABASE_URL")
    database_pool_size: int = Field(10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    database_echo: bool = False

    # Anthropic/Claude
    anthropic_api_key: str = Field("test-key", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(4096, alias="ANTHROPIC_MAX_TOKENS")
    anthropic_temperature: float = 0.1
    anthropic_timeout: int = Field(60, alias="ANTHROPIC_TIMEOUT")
    anthropic_max_retries: int = 3
    anthropic_retry_wait: int = 2

    # Auth
    api_key_prefix: str = Field("di_", alias="API_KEY_PREFIX")
    api_key_hash_rounds: int = Field(12, alias="API_KEY_HASH_ROUNDS")
    rate_limit_requests: int = Field(10, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, alias="RATE_LIMIT_WINDOW")

    # Storage
    storage_provider: str = Field("local", alias="STORAGE_PROVIDER")
    local_storage_path: str = Field("/app/data/uploads", alias="LOCAL_STORAGE_PATH")
    azure_storage_account: str | None = Field(None, alias="AZURE_STORAGE_ACCOUNT")
    azure_storage_container: str = Field("documents", alias="AZURE_STORAGE_CONTAINER")
    azure_storage_connection_string: str | None = Field(
        None, alias="AZURE_STORAGE_CONNECTION_STRING"
    )
    max_file_size_mb: int = 50

    # Azure
    azure_key_vault_url: str | None = Field(None, alias="AZURE_KEY_VAULT_URL")
    azure_monitor_connection_string: str | None = Field(
        None, alias="AZURE_MONITOR_CONNECTION_STRING"
    )

    # Processing
    ocr_language: str = Field("eng", alias="OCR_LANGUAGE")
    max_text_length: int = 100_000

    # CORS
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: list[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")

    # Telemetry
    otel_service_name: str = Field("document-intelligence-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: str | None = Field(None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def load_yaml_config(path: str = "config.yaml") -> dict[str, Any]:
    """Load additional YAML configuration."""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}
