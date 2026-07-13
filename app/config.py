# app/config.py
"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(..., alias="DATABASE_URL")
    pool_size: int = Field(10, alias="DATABASE_POOL_SIZE")
    max_overflow: int = Field(20, alias="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AnthropicSettings(BaseSettings):
    """Anthropic/Claude configuration."""
    api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    model: str = Field("claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")
    max_tokens: int = Field(4096, alias="ANTHROPIC_MAX_TOKENS")
    temperature: float = 0.1
    timeout: int = Field(60, alias="ANTHROPIC_TIMEOUT")
    max_retries: int = 3
    retry_wait: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AuthSettings(BaseSettings):
    """Authentication configuration."""
    api_key_prefix: str = Field("di_", alias="API_KEY_PREFIX")
    hash_rounds: int = Field(12, alias="API_KEY_HASH_ROUNDS")
    rate_limit_requests: int = Field(10, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, alias="RATE_LIMIT_WINDOW")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class StorageSettings(BaseSettings):
    """File storage configuration."""
    provider: str = Field("local", alias="STORAGE_PROVIDER")
    local_path: str = Field("/app/data/uploads", alias="LOCAL_STORAGE_PATH")
    azure_account: Optional[str] = Field(None, alias="AZURE_STORAGE_ACCOUNT")
    azure_container: str = Field("documents", alias="AZURE_STORAGE_CONTAINER")
    azure_connection_string: Optional[str] = Field(None, alias="AZURE_STORAGE_CONNECTION_STRING")
    max_file_size_mb: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AzureSettings(BaseSettings):
    """Azure services configuration."""
    key_vault_url: Optional[str] = Field(None, alias="AZURE_KEY_VAULT_URL")
    monitor_connection_string: Optional[str] = Field(None, alias="AZURE_MONITOR_CONNECTION_STRING")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class ProcessingSettings(BaseSettings):
    """Document processing configuration."""
    allowed_mime_types: List[str] = Field(
        default=[
            "application/pdf",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/png",
            "image/jpeg",
            "image/tiff",
        ],
        alias="ALLOWED_MIME_TYPES",
    )
    ocr_language: str = Field("eng", alias="OCR_LANGUAGE")
    max_text_length: int = 100_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class CORSSettings(BaseSettings):
    """CORS configuration."""
    origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")
    allow_credentials: bool = Field(True, alias="CORS_ALLOW_CREDENTIALS")
    allow_methods: List[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    allow_headers: List[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: str = Field("development", alias="APP_ENV")
    host: str = Field("0.0.0.0", alias="APP_HOST")
    port: int = Field(8000, alias="APP_PORT")
    workers: int = Field(1, alias="APP_WORKERS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Sub-settings (lazy initialization)
    _database: DatabaseSettings | None = None
    _anthropic: AnthropicSettings | None = None
    _auth: AuthSettings | None = None
    _storage: StorageSettings | None = None
    _azure: AzureSettings | None = None
    _processing: ProcessingSettings | None = None
    _cors: CORSSettings | None = None

    @property
    def database(self) -> DatabaseSettings:
        if self._database is None:
            self._database = DatabaseSettings()
        return self._database

    @property
    def anthropic(self) -> AnthropicSettings:
        if self._anthropic is None:
            self._anthropic = AnthropicSettings()
        return self._anthropic

    @property
    def auth(self) -> AuthSettings:
        if self._auth is None:
            self._auth = AuthSettings()
        return self._auth

    @property
    def storage(self) -> StorageSettings:
        if self._storage is None:
            self._storage = StorageSettings()
        return self._storage

    @property
    def azure(self) -> AzureSettings:
        if self._azure is None:
            self._azure = AzureSettings()
        return self._azure

    @property
    def processing(self) -> ProcessingSettings:
        if self._processing is None:
            self._processing = ProcessingSettings()
        return self._processing

    @property
    def cors(self) -> CORSSettings:
        if self._cors is None:
            self._cors = CORSSettings()
        return self._cors

    # Telemetry
    otel_service_name: str = Field("document-intelligence-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_endpoint: Optional[str] = Field(None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

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


def load_yaml_config(path: str = "config.yaml") -> dict:
    """Load additional YAML configuration."""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}