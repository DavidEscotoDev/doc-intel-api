# tests/test_config.py
"""Tests for configuration module."""

import os
from app.config import (
    Settings,
    DatabaseSettings,
    AnthropicSettings,
    AuthSettings,
    StorageSettings,
    AzureSettings,
    ProcessingSettings,
    CORSSettings,
    get_settings,
    load_yaml_config,
)


class TestDatabaseSettings:
    """Test DatabaseSettings."""

    def test_defaults(self) -> None:
        settings = DatabaseSettings()
        assert settings.url == "sqlite+aiosqlite:///:memory:"
        assert settings.pool_size == 10
        assert settings.max_overflow == 20
        assert settings.pool_timeout == 30
        assert settings.pool_recycle == 3600
        assert settings.echo is False

    def test_env_override(self, monkeypatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("DATABASE_POOL_SIZE", "20")
        settings = DatabaseSettings()
        assert settings.url == "postgresql://user:pass@localhost/db"
        assert settings.pool_size == 20


class TestAnthropicSettings:
    """Test AnthropicSettings."""

    def test_defaults(self) -> None:
        settings = AnthropicSettings()
        assert settings.api_key == "test-key"
        assert settings.model == "claude-3-5-sonnet-20241022"
        assert settings.max_tokens == 4096
        assert settings.temperature == 0.1
        assert settings.timeout == 60
        assert settings.max_retries == 3
        assert settings.retry_wait == 2


class TestAuthSettings:
    """Test AuthSettings."""

    def test_defaults(self, monkeypatch) -> None:
        # Remove env var that might be set by conftest
        monkeypatch.delenv("API_KEY_PREFIX", raising=False)
        settings = AuthSettings()
        assert settings.api_key_prefix == "di_"
        assert settings.hash_rounds == 12
        assert settings.rate_limit_requests == 10
        assert settings.rate_limit_window == 60


class TestStorageSettings:
    """Test StorageSettings."""

    def test_defaults(self) -> None:
        settings = StorageSettings()
        assert settings.provider == "local"
        assert settings.local_path == "/app/data/uploads"
        assert settings.azure_account is None
        assert settings.azure_container == "documents"
        assert settings.azure_connection_string is None
        assert settings.max_file_size_mb == 50


class TestAzureSettings:
    """Test AzureSettings."""

    def test_defaults(self) -> None:
        settings = AzureSettings()
        assert settings.key_vault_url is None
        assert settings.monitor_connection_string is None


class TestProcessingSettings:
    """Test ProcessingSettings."""

    def test_defaults(self) -> None:
        settings = ProcessingSettings()
        assert "application/pdf" in settings.allowed_mime_types
        assert settings.ocr_language == "eng"
        assert settings.max_text_length == 100_000


class TestCORSSettings:
    """Test CORSSettings."""

    def test_defaults(self) -> None:
        settings = CORSSettings()
        assert settings.origins == ["*"]
        assert settings.allow_credentials is True
        assert settings.allow_methods == ["*"]
        assert settings.allow_headers == ["*"]


class TestSettings:
    """Test main Settings class."""

    def test_defaults(self, monkeypatch) -> None:
        monkeypatch.delenv("APP_ENV", raising=False)
        settings = Settings()
        assert settings.env == "development"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.workers == 1
        assert settings.log_level == "INFO"
        assert settings.otel_service_name == "document-intelligence-api"
        assert settings.otel_exporter_endpoint is None

    def test_is_production(self) -> None:
        settings = Settings(env="production")
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_development(self) -> None:
        settings = Settings(env="development")
        assert settings.is_development is True
        assert settings.is_production is False

    def test_sub_settings_lazy_init(self) -> None:
        settings = Settings()
        # Access each sub-setting to trigger lazy initialization
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.anthropic, AnthropicSettings)
        assert isinstance(settings.auth, AuthSettings)
        assert isinstance(settings.storage, StorageSettings)
        assert isinstance(settings.azure, AzureSettings)
        assert isinstance(settings.processing, ProcessingSettings)
        assert isinstance(settings.cors, CORSSettings)

    def test_sub_settings_cached(self) -> None:
        settings = Settings()
        db1 = settings.database
        db2 = settings.database
        assert db1 is db2


class TestGetSettings:
    """Test get_settings function."""

    def test_returns_settings(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_cached(self) -> None:
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestLoadYamlConfig:
    """Test load_yaml_config function."""

    def test_nonexistent_file(self, tmp_path) -> None:
        config = load_yaml_config(str(tmp_path / "nonexistent.yaml"))
        assert config == {}

    def test_existing_file(self, tmp_path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value\nnumber: 42")
        config = load_yaml_config(str(config_file))
        assert config == {"key": "value", "number": 42}

    def test_empty_file(self, tmp_path) -> None:
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        config = load_yaml_config(str(config_file))
        assert config == {}