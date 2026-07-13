# Document Intelligence API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade, Azure-ready AI Document Intelligence API with FastAPI, PostgreSQL, and Anthropic Claude that demonstrates senior-level engineering practices suitable for Microsoft recruiter evaluation.

**Architecture:** Clean architecture with domain-driven design. Azure-native integrations (Azure Blob Storage, Azure Key Vault, Azure Monitor/OpenTelemetry). Async processing with FastAPI BackgroundTasks (migrates to Azure Service Bus/Celery). Comprehensive observability: structured logging, distributed tracing, Prometheus metrics, health checks. Security-first: API key auth with hashed keys, rate limiting, input validation, PII redaction.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, PostgreSQL (asyncpg), Anthropic SDK, Azure SDK (blob storage, key vault, monitor), OpenTelemetry, Prometheus Client, Pydantic v2, pytest, httpx, alembic, docker, GitHub Actions.

## Global Constraints

- Python 3.11+ (required for async patterns and performance)
- FastAPI 0.109+ with Pydantic v2
- SQLAlchemy 2.0 async ORM only (no legacy sync)
- All dependencies pinned to exact versions in requirements.txt
- OpenTelemetry auto-instrumentation for FastAPI, SQLAlchemy, HTTPX
- Structured JSON logging with correlation IDs
- All secrets via Azure Key Vault or environment variables (never in code)
- API versioning in URL path (/api/v1/)
- Comprehensive type hints (mypy strict mode passes)
- Test coverage ≥ 85% (unit + integration)
- Docker multi-stage build (non-root user, distroless base)
- GitHub Actions CI/CD with Azure deployment

---

### Task 1: Project Scaffold & Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.env.example`
- Create: `config.yaml` (structured config)
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/constants.py`
- Create: `app/exceptions.py`
- Create: `app/logging.py`
- Create: `app/telemetry.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Consumes: None (foundation task)
- Produces: `settings` (Pydantic Settings instance), `logger` (structlog), `tracer` (OpenTelemetry), `get_db_session` (async session factory), exception hierarchy

- [ ] **Step 1.1: Create pyproject.toml with modern Python packaging**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "document-intelligence-api"
version = "1.0.0"
description = "Production-grade AI Document Intelligence API"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    "pydantic==2.5.3",
    "pydantic-settings==2.1.0",
    "pydantic-extra-types==2.4.0",
    "sqlalchemy==2.0.25",
    "asyncpg==0.29.0",
    "alembic==1.13.1",
    "anthropic==0.18.1",
    "python-multipart==0.0.6",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-dotenv==1.0.0",
    "pyyaml==6.0.1",
    "structlog==24.1.0",
    "opentelemetry-api==1.22.0",
    "opentelemetry-sdk==1.22.0",
    "opentelemetry-instrumentation-fastapi==0.42b0",
    "opentelemetry-instrumentation-sqlalchemy==0.42b0",
    "opentelemetry-instrumentation-httpx==0.42b0",
    "opentelemetry-exporter-prometheus==0.42b0",
    "opentelemetry-exporter-azure-monitor==1.1.0",
    "prometheus-client==0.19.0",
    "azure-identity==1.13.0",
    "azure-keyvault-secrets==4.7.0",
    "azure-storage-blob==12.19.0",
    "azure-monitor-opentelemetry==1.1.0",
    "pymupdf==1.23.7",
    "python-docx==1.1.0",
    "pillow==10.1.0",
    "pytesseract==0.3.10",
    "tenacity==8.2.3",
    "email-validator==2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.4",
    "pytest-asyncio==0.23.3",
    "pytest-cov==4.1.0",
    "pytest-mock==3.12.0",
    "httpx==0.26.0",
    "faker==22.1.0",
    "factory-boy==3.3.0",
    "mypy==1.7.1",
    "ruff==0.1.15",
    "pre-commit==3.6.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "T20", "PI", "PT"]
ignore = ["S101", "T201"]
per-file-ignores = ["tests/*: S101"]

[tool.mypy]
strict = true
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
no_implicit_optional = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=app --cov-report=term-missing --cov-fail-under=85"

[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "app/main.py"]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]
```

- [ ] **Step 1.2: Create requirements.txt (pinned from pyproject.toml)**

```bash
# Run: pip compile pyproject.toml -o requirements.txt
# For now, create manually with pinned versions
```

```text
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
pydantic-extra-types==2.4.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
anthropic==0.18.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
pyyaml==6.0.1
structlog==24.1.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
opentelemetry-exporter-prometheus==0.42b0
opentelemetry-exporter-azure-monitor==1.1.0
prometheus-client==0.19.0
azure-identity==1.13.0
azure-keyvault-secrets==4.7.0
azure-storage-blob==12.19.0
azure-monitor-opentelemetry==1.1.0
pymupdf==1.23.7
python-docx==1.1.0
pillow==10.1.0
pytesseract==0.3.10
tenacity==8.2.3
email-validator==2.1.0
```

- [ ] **Step 1.3: Create requirements-dev.txt**

```text
# requirements-dev.txt
-r requirements.txt
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0
faker==22.1.0
factory-boy==3.3.0
mypy==1.7.1
ruff==0.1.15
pre-commit==3.6.0
```

- [ ] **Step 1.4: Create .env.example**

```bash
# .env.example
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WORKERS=1
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/docintel
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TIMEOUT=60

# Authentication
API_KEY_PREFIX=di_
API_KEY_HASH_ROUNDS=12
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Storage
STORAGE_PROVIDER=local
LOCAL_STORAGE_PATH=/app/data/uploads
AZURE_STORAGE_ACCOUNT=
AZURE_STORAGE_CONTAINER=documents
AZURE_STORAGE_CONNECTION_STRING=

# Azure Key Vault
AZURE_KEY_VAULT_URL=

# Azure Monitor / OpenTelemetry
AZURE_MONITOR_CONNECTION_STRING=
OTEL_SERVICE_NAME=document-intelligence-api
OTEL_EXPORTER_OTLP_ENDPOINT=

# File Processing
MAX_FILE_SIZE_MB=50
ALLOWED_MIME_TYPES=application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,image/tiff
OCR_LANGUAGE=eng

# CORS
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true
```

- [ ] **Step 1.5: Create config.yaml (structured config for complex settings)**

```yaml
# config.yaml
app:
  name: "Document Intelligence API"
  version: "1.0.0"
  description: "AI-powered document analysis API"

database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600
  echo: false

anthropic:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 4096
  temperature: 0.1
  timeout: 60
  max_retries: 3
  retry_wait: 2

storage:
  local:
    path: "/app/data/uploads"
    max_file_size_mb: 50
  azure:
    container: "documents"
    max_file_size_mb: 50

auth:
  api_key_prefix: "di_"
  hash_rounds: 12
  rate_limit:
    requests: 10
    window_seconds: 60

processing:
  allowed_mime_types:
    - "application/pdf"
    - "text/plain"
    - "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    - "image/png"
    - "image/jpeg"
    - "image/tiff"
  ocr_language: "eng"
  max_text_length: 100000

cors:
  origins: ["*"]
  allow_credentials: true
  allow_methods: ["*"]
  allow_headers: ["*"]

telemetry:
  service_name: "document-intelligence-api"
  sample_rate: 1.0
  exporters:
    - "prometheus"
    - "azure_monitor"
```

- [ ] **Step 1.6: Create app/constants.py**

```python
# app/constants.py
"""Application constants - single source of truth for magic values."""

from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status states."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StorageProvider(str, Enum):
    """Supported storage backends."""
    LOCAL = "local"
    AZURE_BLOB = "azure_blob"


class MimeType(str, Enum):
    """Allowed MIME types for upload."""
    PDF = "application/pdf"
    TXT = "text/plain"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PNG = "image/png"
    JPEG = "image/jpeg"
    TIFF = "image/tiff"


# Rate limiting defaults
DEFAULT_RATE_LIMIT_REQUESTS = 10
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

# File processing
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MAX_TEXT_LENGTH = 100_000  # characters sent to LLM

# API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Health check
HEALTH_CHECK_TIMEOUT = 5  # seconds
```

- [ ] **Step 1.7: Create app/exceptions.py**

```python
# app/exceptions.py
"""Custom exception hierarchy for the application."""

from typing import Any, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(AppException):
    """Input validation failed."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationError(AppException):
    """Authentication failed."""
    
    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(
            message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(AppException):
    """Authorization failed."""
    
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(AppException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier},
        )


class RateLimitError(AppException):
    """Rate limit exceeded."""
    
    def __init__(self, retry_after: int) -> None:
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
        )


class StorageError(AppException):
    """File storage operation failed."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            code="STORAGE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ProcessingError(AppException):
    """Document processing failed."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            code="PROCESSING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class LLMError(AppException):
    """LLM API call failed."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(
            message,
            code="LLM_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


def to_http_exception(exc: AppException) -> HTTPException:
    """Convert AppException to FastAPI HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
```

- [ ] **Step 1.8: Create app/logging.py**

```python
# app/logging.py
"""Structured logging configuration with structlog."""

import sys
import logging
from typing import Any
import structlog
from structlog.types import EventDict, Processor


def add_correlation_id(_, __, event_dict: EventDict) -> EventDict:
    """Add correlation ID from contextvars if available."""
    try:
        from contextvars import copy_context
        ctx = copy_context()
        if "correlation_id" in ctx:
            event_dict["correlation_id"] = ctx["correlation_id"]
    except Exception:
        pass
    return event_dict


def add_service_info(_, __, event_dict: EventDict) -> EventDict:
    """Add service metadata to all log entries."""
    event_dict["service"] = "document-intelligence-api"
    event_dict["version"] = "1.0.0"
    return event_dict


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """Remove color_message key added by structlog.dev.ConsoleRenderer."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog for structured JSON logging."""
    
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        add_service_info,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        drop_color_message_key,
    ]
    
    if json_logs:
        # Production: JSON output for log aggregation
        renderer: structlog.processors.JSONRenderer = structlog.processors.JSONRenderer()
        processors = shared_processors + [renderer]
    else:
        # Development: Human-readable console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            renderer,
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
```

- [ ] **Step 1.9: Create app/telemetry.py**

```python
# app/telemetry.py
"""OpenTelemetry configuration for distributed tracing and metrics."""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.trace import Status, StatusCode
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional
import os


# Prometheus metrics (always available)
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

documents_uploaded_total = Counter(
    "documents_uploaded_total",
    "Total documents uploaded",
    ["status"],
)

documents_processed_total = Counter(
    "documents_processed_total",
    "Total documents processed",
    ["status"],
)

document_processing_duration_seconds = Histogram(
    "document_processing_duration_seconds",
    "Document processing duration in seconds",
)

active_connections = Gauge(
    "active_connections",
    "Number of active connections",
)

llm_tokens_used_total = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens consumed",
    ["model", "type"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["model"],
)


def setup_telemetry(
    service_name: str = "document-intelligence-api",
    sample_rate: float = 1.0,
    enable_azure_monitor: bool = False,
    azure_connection_string: Optional[str] = None,
) -> tuple[trace.Tracer, metrics.Meter]:
    """Initialize OpenTelemetry tracing and metrics."""
    
    resource = Resource.create({SERVICE_NAME: service_name})
    
    # Tracing
    tracer_provider = TracerProvider(resource=resource)
    
    # Add Azure Monitor exporter if configured
    if enable_azure_monitor and azure_connection_string:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        azure_exporter = AzureMonitorTraceExporter(
            connection_string=azure_connection_string
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(azure_exporter))
    
    # Always add console exporter for development
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    trace.set_tracer_provider(tracer_provider)
    
    # Metrics
    prometheus_reader = PrometheusMetricReader()
    metric_readers = [prometheus_reader]
    
    if enable_azure_monitor and azure_connection_string:
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
        azure_metric_exporter = AzureMonitorMetricExporter(
            connection_string=azure_connection_string
        )
        metric_readers.append(
            PeriodicExportingMetricReader(azure_metric_exporter)
        )
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=metric_readers,
    )
    metrics.set_meter_provider(meter_provider)
    
    # Auto-instrumentation
    FastAPIInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()
    
    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)
    
    return tracer, meter


def record_span_error(span: trace.Span, error: Exception) -> None:
    """Record an error on the current span."""
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)
```

- [ ] **Step 1.10: Create app/config.py**

```python
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


class AnthropicSettings(BaseSettings):
    """Anthropic/Claude configuration."""
    api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    model: str = Field("claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")
    max_tokens: int = Field(4096, alias="ANTHROPIC_MAX_TOKENS")
    temperature: float = 0.1
    timeout: int = Field(60, alias="ANTHROPIC_TIMEOUT")
    max_retries: int = 3
    retry_wait: int = 2


class AuthSettings(BaseSettings):
    """Authentication configuration."""
    api_key_prefix: str = Field("di_", alias="API_KEY_PREFIX")
    hash_rounds: int = Field(12, alias="API_KEY_HASH_ROUNDS")
    rate_limit_requests: int = Field(10, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, alias="RATE_LIMIT_WINDOW")


class StorageSettings(BaseSettings):
    """File storage configuration."""
    provider: str = Field("local", alias="STORAGE_PROVIDER")
    local_path: str = Field("/app/data/uploads", alias="LOCAL_STORAGE_PATH")
    azure_account: Optional[str] = Field(None, alias="AZURE_STORAGE_ACCOUNT")
    azure_container: str = Field("documents", alias="AZURE_STORAGE_CONTAINER")
    azure_connection_string: Optional[str] = Field(None, alias="AZURE_STORAGE_CONNECTION_STRING")
    max_file_size_mb: int = 50


class AzureSettings(BaseSettings):
    """Azure services configuration."""
    key_vault_url: Optional[str] = Field(None, alias="AZURE_KEY_VAULT_URL")
    monitor_connection_string: Optional[str] = Field(None, alias="AZURE_MONITOR_CONNECTION_STRING")


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


class CORSSettings(BaseSettings):
    """CORS configuration."""
    origins: List[str] = Field(default=["*"], alias="CORS_ORIGINS")
    allow_credentials: bool = Field(True, alias="CORS_ALLOW_CREDENTIALS")
    allow_methods: List[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    allow_headers: List[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")


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
    
    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    auth: AuthSettings = AuthSettings()
    storage: StorageSettings = StorageSettings()
    azure: AzureSettings = AzureSettings()
    processing: ProcessingSettings = ProcessingSettings()
    cors: CORSSettings = CORSSettings()
    
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
```

- [ ] **Step 1.11: Create tests/conftest.py**

```python
# tests/conftest.py
"""Pytest configuration and fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db_session
from app.main import create_app
from app.models.api_key import APIKey
from app.models.document import Document
from app.models.analysis import Analysis


# Test settings
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["API_KEY_PREFIX"] = "di_test_"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Get test settings."""
    return get_settings()


@pytest.fixture(scope="function")
async def db_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def override_get_db(db_session: AsyncSession):
    """Override database dependency."""
    async def _override_get_db():
        yield db_session
    return _override_get_db


@pytest.fixture(scope="function")
def app(override_get_db):
    """Create FastAPI test app."""
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db
    return app


@pytest.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fake() -> Faker:
    """Faker instance for test data."""
    return Faker()


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Mock Anthropic client."""
    client = MagicMock()
    client.messages.create = AsyncMock()
    return client


@pytest.fixture
async def test_api_key(db_session: AsyncSession) -> APIKey:
    """Create a test API key."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    key = "di_test_abcdefghijklmnopqrstuvwxyz123456"
    key_hash = pwd_context.hash(key)
    
    api_key = APIKey(
        key_hash=key_hash,
        name="Test Key",
        rate_limit=100,
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


@pytest.fixture
def auth_headers(test_api_key: APIKey) -> dict[str, str]:
    """Authorization headers for test API key."""
    # Note: In tests we use the plain key since we control the hash
    return {"Authorization": f"Bearer {test_api_key.key_hash}"}


@pytest.fixture
async def test_document(db_session: AsyncSession, test_api_key: APIKey) -> Document:
    """Create a test document."""
    doc = Document(
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status="uploaded",
        api_key_id=test_api_key.id,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.fixture
async def test_analysis(db_session: AsyncSession, test_document: Document) -> Analysis:
    """Create a test analysis."""
    analysis = Analysis(
        document_id=test_document.id,
        summary="Test summary",
        key_points=["Point 1", "Point 2"],
        entities=["Entity 1"],
        sentiment="positive",
        topics=["Topic 1"],
        tokens_used=100,
        model_version="claude-3-5-sonnet-20241022",
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis
```

- [ ] **Step 1.12: Run initial tests to verify setup**

```bash
# Run: pytest tests/conftest.py -v
# Expected: No tests collected (only fixtures), but no import errors
```

- [ ] **Step 1.13: Commit foundation**

```bash
git add pyproject.toml requirements.txt requirements-dev.txt .env.example config.yaml
git add app/__init__.py app/config.py app/constants.py app/exceptions.py
git add app/logging.py app/telemetry.py tests/__init__.py tests/conftest.py
git commit -m "feat: project scaffold with config, logging, telemetry, exceptions"
```

---

### Task 2: Database Layer (SQLAlchemy 2.0 Async)

**Files:**
- Create: `app/database.py`
- Create: `app/models/__init__.py`
- Create: `app/models/document.py`
- Create: `app/models/analysis.py`
- Create: `app/models/api_key.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Test: `tests/test_database.py`

**Interfaces:**
- Consumes: `settings` from config, `logger` from logging
- Produces: `Base` (declarative base), `get_db_session` (async session dependency), `init_db` (initialization), models with relationships

- [ ] **Step 2.1: Create app/database.py**

```python
# app/database.py
"""Database connection and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Database:
    """Database connection manager."""
    
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        settings = get_settings()
        
        self._engine = create_async_engine(
            settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.database.echo,
            pool_pre_ping=True,
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        
        logger.info("database_initialized", url=settings.database.url)
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("database_closed")
    
    @property
    def engine(self) -> AsyncEngine:
        if not self._engine:
            raise RuntimeError("Database not initialized")
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database instance
db = Database()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with db.session() as session:
        yield session


async def init_db() -> None:
    """Initialize database and create tables."""
    db.initialize()
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")


async def close_db() -> None:
    """Close database connections."""
    await db.close()
```

- [ ] **Step 2.2: Create app/models/__init__.py**

```python
# app/models/__init__.py
"""Database models package."""

from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.models.api_key import APIKey

__all__ = [
    "Document",
    "DocumentStatus",
    "Analysis",
    "APIKey",
]
```

- [ ] **Step 2.3: Create app/models/document.py**

```python
# app/models/document.py
"""Document database model."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.constants import DocumentStatus


class Document(Base):
    """Document model representing uploaded files."""
    
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    api_key_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    api_key: Mapped["APIKey"] = relationship(back_populates="documents")
    analysis: Mapped["Analysis | None"] = relationship(
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_documents_api_key_id_created_at", "api_key_id", "created_at"),
        Index("ix_documents_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
```

- [ ] **Step 2.4: Create app/models/analysis.py**

```python
# app/models/analysis.py
"""Analysis database model."""

from datetime import datetime
from uuid import uuid4
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base


class Analysis(Base):
    """Document analysis results from LLM."""
    
    __tablename__ = "analyses"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Analysis results
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    entities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    
    # Metadata
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Raw response for debugging
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(back_populates="analysis")
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, document_id={self.document_id}, sentiment={self.sentiment})>"
```

- [ ] **Step 2.5: Create app/models/api_key.py**

```python
# app/models/api_key.py
"""API Key database model."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class APIKey(Base):
    """API Key for authentication and rate limiting."""
    
    __tablename__ = "api_keys"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        back_populates="api_key",
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_api_keys_key_hash", "key_hash"),
        Index("ix_api_keys_is_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, active={self.is_active})>"
```

- [ ] **Step 2.6: Create alembic.ini**

```ini
# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2.7: Create alembic/env.py**

```python
# alembic/env.py
"""Alembic migration environment."""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.database import Base
from app.config import get_settings

# Import all models to register them
from app.models import *  # noqa

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database.url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 2.8: Create alembic/script.py.mako**

```mako
# alembic/script.py.mako
"""Migration script template."""

"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 2.9: Create initial migration**

```bash
# Run: alembic revision --autogenerate -m "initial_schema"
# Expected: Creates alembic/versions/..._initial_schema.py
```

- [ ] **Step 2.10: Create tests/test_database.py**

```python
# tests/test_database.py
"""Database layer tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.models.api_key import APIKey
from app.database import Base


class TestDatabaseModels:
    """Test database model creation and relationships."""
    
    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession):
        api_key = APIKey(
            key_hash="hashed_key",
            name="Test Key",
            rate_limit=100,
        )
        db_session.add(api_key)
        await db_session.commit()
        await db_session.refresh(api_key)
        
        assert api_key.id is not None
        assert api_key.name == "Test Key"
        assert api_key.rate_limit == 100
        assert api_key.is_active is True
        assert api_key.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_create_document(self, db_session: AsyncSession, test_api_key: APIKey):
        doc = Document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.UPLOADED,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)
        
        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.api_key_id == test_api_key.id
    
    @pytest.mark.asyncio
    async def test_create_analysis(self, db_session: AsyncSession, test_document: Document):
        analysis = Analysis(
            document_id=test_document.id,
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            entities=["Entity 1"],
            sentiment="positive",
            topics=["Topic 1"],
            tokens_used=150,
            model_version="claude-3-5-sonnet-20241022",
            processing_time_ms=1200,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)
        
        assert analysis.id is not None
        assert analysis.document_id == test_document.id
        assert analysis.summary == "Test summary"
        assert analysis.sentiment == "positive"
        assert len(analysis.key_points) == 2
    
    @pytest.mark.asyncio
    async def test_document_analysis_relationship(
        self, db_session: AsyncSession, test_document: Document
    ):
        analysis = Analysis(
            document_id=test_document.id,
            summary="Test summary",
            key_points=["Point 1"],
            entities=[],
            sentiment="neutral",
            topics=[],
            tokens_used=100,
            model_version="claude-3-5-sonnet-20241022",
        )
        db_session.add(analysis)
        await db_session.commit()
        
        # Refresh and check relationship
        await db_session.refresh(test_document, attribute_names=["analysis"])
        assert test_document.analysis is not None
        assert test_document.analysis.id == analysis.id
        assert test_document.analysis.summary == "Test summary"
    
    @pytest.mark.asyncio
    async def test_api_key_documents_relationship(
        self, db_session: AsyncSession, test_api_key: APIKey
    ):
        doc1 = Document(
            filename="doc1.pdf",
            file_path="/tmp/doc1.pdf",
            mime_type="application/pdf",
            file_size=1024,
            api_key_id=test_api_key.id,
        )
        doc2 = Document(
            filename="doc2.pdf",
            file_path="/tmp/doc2.pdf",
            mime_type="application/pdf",
            file_size=2048,
            api_key_id=test_api_key.id,
        )
        db_session.add_all([doc1, doc2])
        await db_session.commit()
        
        await db_session.refresh(test_api_key, attribute_names=["documents"])
        assert len(test_api_key.documents) == 2
    
    @pytest.mark.asyncio
    async def test_cascade_delete_document_deletes_analysis(
        self, db_session: AsyncSession, test_document: Document
    ):
        analysis = Analysis(
            document_id=test_document.id,
            summary="Test",
            key_points=[],
            entities=[],
            sentiment="neutral",
            topics=[],
            tokens_used=50,
            model_version="claude-3-5-sonnet-20241022",
        )
        db_session.add(analysis)
        await db_session.commit()
        
        # Delete document - analysis should cascade
        await db_session.delete(test_document)
        await db_session.commit()
        
        result = await db_session.execute(select(Analysis).where(Analysis.id == analysis.id))
        assert result.scalar_one_or_none() is None
    
    @pytest.mark.asyncio
    async def test_cascade_delete_api_key_deletes_documents(
        self, db_session: AsyncSession, test_api_key: APIKey
    ):
        doc = Document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()
        
        await db_session.delete(test_api_key)
        await db_session.commit()
        
        result = await db_session.execute(select(Document).where(Document.id == doc.id))
        assert result.scalar_one_or_none() is None
```

- [ ] **Step 2.11: Run database tests**

```bash
# Run: pytest tests/test_database.py -v
# Expected: All tests pass
```

- [ ] **Step 2.12: Commit database layer**

```bash
git add app/database.py app/models/ alembic/
git add tests/test_database.py
git commit -m "feat: database layer with SQLAlchemy 2.0 async models and migrations"
```

---

### Task 3: Schemas (Pydantic v2 Validation)

**Files:**
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/document.py`
- Create: `app/schemas/analysis.py`
- Create: `app/schemas/auth.py`
- Create: `app/schemas/common.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Consumes: `DocumentStatus`, `MimeType` from constants
- Produces: Request/response models for all API endpoints

- [ ] **Step 3.1: Create app/schemas/__init__.py**

```python
# app/schemas/__init__.py
"""Pydantic schemas package."""

from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
)
from app.schemas.analysis import (
    AnalysisResponse,
    AnalysisRequest,
)
from app.schemas.auth import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyListResponse,
)
from app.schemas.common import (
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    "DocumentUploadResponse",
    "DocumentListResponse",
    "DocumentResponse",
    "DocumentStatusResponse",
    "AnalysisResponse",
    "AnalysisRequest",
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyListResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
]
```

- [ ] **Step 3.2: Create app/schemas/common.py**

```python
# app/schemas/common.py
"""Common schema definitions."""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    model_config = ConfigDict(from_attributes=True)
    
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    error: "ErrorDetail"


class ErrorDetail(BaseModel):
    """Error detail structure."""
    
    code: str
    message: str
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    status: str
    version: str
    environment: str
    database: str
    timestamp: datetime
```

- [ ] **Step 3.3: Create app/schemas/document.py**

```python
# app/schemas/document.py
"""Document-related schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from uuid import UUID

from app.constants import DocumentStatus, MimeType
from app.schemas.common import PaginatedResponse


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    status: DocumentStatus
    message: str


class DocumentResponse(BaseModel):
    """Full document response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None


class DocumentListItem(BaseModel):
    """Document item in list response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None


class DocumentListResponse(PaginatedResponse[DocumentListItem]):
    """Paginated document list response."""
    pass


class DocumentStatusResponse(BaseModel):
    """Document processing status response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: DocumentStatus
    error_message: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)


class DocumentProcessRequest(BaseModel):
    """Request to process a document."""
    
    model_config = ConfigDict(from_attributes=True)
    
    document_id: UUID
    callback_url: Optional[str] = None
    
    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Callback URL must be a valid HTTP/HTTPS URL")
        return v
```

- [ ] **Step 3.4: Create app/schemas/analysis.py**

```python
# app/schemas/analysis.py
"""Analysis-related schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class AnalysisResponse(BaseModel):
    """Analysis result response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    document_id: UUID
    summary: str
    key_points: list[str]
    entities: list[str]
    sentiment: str
    topics: list[str]
    tokens_used: int
    model_version: str
    processing_time_ms: int
    created_at: datetime


class AnalysisRequest(BaseModel):
    """Request to trigger document analysis."""
    
    model_config = ConfigDict(from_attributes=True)
    
    document_id: UUID
    callback_url: Optional[str] = None


class AnalysisDetailResponse(AnalysisResponse):
    """Analysis with raw response for debugging."""
    
    raw_response: Optional[dict] = None
```

- [ ] **Step 3.5: Create app/schemas/auth.py**

```python
# app/schemas/auth.py
"""Authentication-related schemas."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class APIKeyCreate(BaseModel):
    """Request to create an API key."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100)
    rate_limit: int = Field(10, ge=1, le=1000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyCreateResponse(BaseModel):
    """Response with the new API key (only shown once)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    key: str  # The plaintext key - only returned on creation
    name: str
    rate_limit: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response (without the key)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    rate_limit: int
    is_active: bool
    last_used_at: Optional[datetime] = None
    total_requests: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class APIKeyListResponse(BaseModel):
    """Paginated API key list."""
    
    model_config = ConfigDict(from_attributes=True)
    
    items: list[APIKeyResponse]
    total: int
```

- [ ] **Step 3.6: Create tests/test_schemas.py**

```python
# tests/test_schemas.py
"""Schema validation tests."""

import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.schemas.document import (
    DocumentUploadResponse,
    DocumentProcessRequest,
    DocumentListItem,
)
from app.schemas.analysis import AnalysisResponse, AnalysisRequest
from app.schemas.auth import APIKeyCreate, APIKeyCreateResponse
from app.schemas.common import PaginatedResponse, ErrorResponse
from app.constants import DocumentStatus


class TestDocumentSchemas:
    """Test document schemas."""
    
    def test_document_upload_response_valid(self):
        doc_id = uuid4()
        response = DocumentUploadResponse(
            id=doc_id,
            filename="test.pdf",
            status=DocumentStatus.UPLOADED,
            message="File uploaded successfully",
        )
        assert response.id == doc_id
        assert response.filename == "test.pdf"
        assert response.status == DocumentStatus.UPLOADED
    
    def test_document_process_request_valid(self):
        doc_id = uuid4()
        request = AnalysisRequest(document_id=doc_id, callback_url="https://example.com/callback")
        assert request.document_id == doc_id
        assert request.callback_url == "https://example.com/callback"
    
    def test_document_process_request_invalid_callback(self):
        doc_id = uuid4()
        with pytest.raises(ValidationError) as exc_info:
            AnalysisRequest(document_id=doc_id, callback_url="not-a-url")
        assert "Callback URL must be a valid HTTP/HTTPS URL" in str(exc_info.value)
    
    def test_document_list_item(self):
        doc_id = uuid4()
        item = DocumentListItem(
            id=doc_id,
            filename="test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.COMPLETED,
            created_at="2024-01-01T00:00:00Z",
        )
        assert item.status == DocumentStatus.COMPLETED


class TestAnalysisSchemas:
    """Test analysis schemas."""
    
    def test_analysis_response_valid(self):
        analysis_id = uuid4()
        doc_id = uuid4()
        response = AnalysisResponse(
            id=analysis_id,
            document_id=doc_id,
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            entities=["Entity 1"],
            sentiment="positive",
            topics=["Topic 1"],
            tokens_used=150,
            model_version="claude-3-5-sonnet-20241022",
            processing_time_ms=1200,
            created_at="2024-01-01T00:00:00Z",
        )
        assert response.sentiment == "positive"
        assert len(response.key_points) == 2


class TestAuthSchemas:
    """Test auth schemas."""
    
    def test_api_key_create_valid(self):
        create = APIKeyCreate(name="Test Key", rate_limit=50, expires_in_days=30)
        assert create.name == "Test Key"
        assert create.rate_limit == 50
        assert create.expires_in_days == 30
    
    def test_api_key_create_rate_limit_bounds(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="Test", rate_limit=0)
        with pytest.raises(ValidationError):
            APIKeyCreate(name="Test", rate_limit=1001)
    
    def test_api_key_create_name_required(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="")


class TestCommonSchemas:
    """Test common schemas."""
    
    def test_paginated_response(self):
        response = PaginatedResponse[
            DocumentListItem
        ](
            items=[],
            total=0,
            page=1,
            page_size=10,
            total_pages=0,
        )
        assert response.has_next is False
        assert response.has_prev is False
    
    def test_error_response(self):
        error = ErrorResponse(
            error={"code": "TEST_ERROR", "message": "Test message"}
        )
        assert error.error.code == "TEST_ERROR"
```

- [ ] **Step 3.7: Run schema tests**

```bash
# Run: pytest tests/test_schemas.py -v
# Expected: All tests pass
```

- [ ] **Step 3.8: Commit schemas**

```bash
git add app/schemas/ tests/test_schemas.py
git commit -m "feat: Pydantic v2 schemas for all API endpoints"
```

---

### Task 4: Services (Storage, Extraction, LLM)

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/storage.py`
- Create: `app/services/extractor.py`
- Create: `app/services/llm.py`
- Test: `tests/test_storage.py`, `tests/test_extractor.py`, `tests/test_llm.py`

**Interfaces:**
- Consumes: `settings`, `logger`, `tracer`
- Produces: `StorageService`, `TextExtractor`, `LLMService` classes

- [ ] **Step 4.1: Create app/services/__init__.py**

```python
# app/services/__init__.py
"""Services package."""

from app.services.storage import StorageService, get_storage_service
from app.services.extractor import TextExtractor, get_text_extractor
from app.services.llm import LLMService, get_llm_service

__all__ = [
    "StorageService",
    "get_storage_service",
    "TextExtractor",
    "get_text_extractor",
    "LLMService",
    "get_llm_service",
]
```

- [ ] **Step 4.2: Create app/services/storage.py**

```python
# app/services/storage.py
"""File storage service with local and Azure Blob support."""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4
from typing import Optional, BinaryIO
from contextlib import asynccontextmanager

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import StorageError
from app.constants import StorageProvider

logger = get_logger(__name__)


class StorageBackend(ABC):
    """Abstract storage backend."""
    
    @abstractmethod
    async def save(self, file: BinaryIO, filename: str, content_type: str) -> str:
        """Save file and return storage path/key."""
        pass
    
    @abstractmethod
    async def get_path(self, storage_key: str) -> str:
        """Get local filesystem path for a stored file."""
        pass
    
    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Delete a stored file."""
        pass
    
    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage."""
    
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save(self, file: BinaryIO, filename: str, content_type: str) -> str:
        # Generate unique storage key
        ext = Path(filename).suffix
        storage_key = f"{uuid4()}{ext}"
        file_path = self.base_path / storage_key
        
        # Save file
        file.seek(0)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        logger.info("file_saved_local", storage_key=storage_key, path=str(file_path))
        return storage_key
    
    async def get_path(self, storage_key: str) -> str:
        file_path = self.base_path / storage_key
        if not file_path.exists():
            raise StorageError(f"File not found: {storage_key}")
        return str(file_path)
    
    async def delete(self, storage_key: str) -> bool:
        file_path = self.base_path / storage_key
        if file_path.exists():
            file_path.unlink()
            logger.info("file_deleted_local", storage_key=storage_key)
            return True
        return False
    
    async def exists(self, storage_key: str) -> bool:
        return (self.base_path / storage_key).exists()


class AzureBlobStorage(StorageBackend):
    """Azure Blob Storage backend."""
    
    def __init__(
        self,
        connection_string: str,
        container: str,
    ) -> None:
        self.connection_string = connection_string
        self.container = container
        self._client: Optional[BlobServiceClient] = None
    
    async def _get_client(self) -> BlobServiceClient:
        if self._client is None:
            self._client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        return self._client
    
    async def save(self, file: BinaryIO, filename: str, content_type: str) -> str:
        client = await self._get_client()
        container_client = client.get_container_client(self.container)
        
        # Ensure container exists
        await container_client.create_container()
        
        ext = Path(filename).suffix
        storage_key = f"{uuid4()}{ext}"
        blob_client = container_client.get_blob_client(storage_key)
        
        file.seek(0)
        await blob_client.upload_blob(
            file,
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True,
        )
        
        logger.info("file_saved_azure", storage_key=storage_key, container=self.container)
        return storage_key
    
    async def get_path(self, storage_key: str) -> str:
        # For Azure, we return a SAS URL or download to temp
        client = await self._get_client()
        container_client = client.get_container_client(self.container)
        blob_client = container_client.get_blob_client(storage_key)
        
        if not await blob_client.exists():
            raise StorageError(f"File not found: {storage_key}")
        
        # Return blob URL (in production, generate SAS token)
        return blob_client.url
    
    async def delete(self, storage_key: str) -> bool:
        client = await self._get_client()
        container_client = client.get_container_client(self.container)
        blob_client = container_client.get_blob_client(storage_key)
        
        if await blob_client.exists():
            await blob_client.delete_blob()
            logger.info("file_deleted_azure", storage_key=storage_key)
            return True
        return False
    
    async def exists(self, storage_key: str) -> bool:
        client = await self._get_client()
        container_client = client.get_container_client(self.container)
        blob_client = container_client.get_blob_client(storage_key)
        return await blob_client.exists()
    
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


class StorageService:
    """High-level storage service."""
    
    def __init__(self, backend: StorageBackend) -> None:
        self.backend = backend
        self.settings = get_settings()
    
    async def save_upload(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
    ) -> tuple[str, int]:
        """Save uploaded file, return (storage_key, file_size)."""
        # Validate file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)
        
        max_size = self.settings.storage.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise StorageError(
                f"File size {file_size} exceeds maximum {max_size}",
                details={"file_size": file_size, "max_size": max_size},
            )
        
        storage_key = await self.backend.save(file, filename, content_type)
        return storage_key, file_size
    
    async def get_file_path(self, storage_key: str) -> str:
        """Get local path for processing."""
        return await self.backend.get_path(storage_key)
    
    async def delete_file(self, storage_key: str) -> bool:
        return await self.backend.delete(storage_key)
    
    async def file_exists(self, storage_key: str) -> bool:
        return await self.backend.exists(storage_key)


# Factory function
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        settings = get_settings()
        
        if settings.storage.provider == StorageProvider.AZURE_BLOB:
            if not settings.storage.azure_connection_string:
                raise StorageError("Azure storage configured but connection string missing")
            backend = AzureBlobStorage(
                connection_string=settings.storage.azure_connection_string,
                container=settings.storage.azure_container,
            )
        else:
            backend = LocalStorage(settings.storage.local_path)
        
        _storage_service = StorageService(backend)
    
    return _storage_service
```

- [ ] **Step 4.3: Create app/services/extractor.py**

```python
# app/services/extractor.py
"""Text extraction from various document formats."""

import io
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from typing import Optional
from pathlib import Path

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import ProcessingError
from app.constants import MimeType, MAX_TEXT_LENGTH

logger = get_logger(__name__)


class TextExtractor:
    """Extract text from documents."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.max_text_length = MAX_TEXT_LENGTH
    
    def extract(self, file_path: str, mime_type: str) -> str:
        """Extract text from file based on MIME type."""
        logger.info("extracting_text", file_path=file_path, mime_type=mime_type)
        
        try:
            if mime_type == MimeType.PDF:
                text = self._extract_pdf(file_path)
            elif mime_type == MimeType.TXT:
                text = self._extract_txt(file_path)
            elif mime_type == MimeType.DOCX:
                text = self._extract_docx(file_path)
            elif mime_type in (MimeType.PNG, MimeType.JPEG, MimeType.TIFF):
                text = self._extract_image(file_path)
            else:
                raise ProcessingError(
                    f"Unsupported MIME type: {mime_type}",
                    details={"mime_type": mime_type},
                )
            
            # Truncate if too long
            if len(text) > self.max_text_length:
                logger.warning(
                    "text_truncated",
                    original_length=len(text),
                    max_length=self.max_text_length,
                )
                text = text[:self.max_text_length] + "\n\n[TRUNCATED]"
            
            logger.info("text_extracted", length=len(text))
            return text.strip()
            
        except ProcessingError:
            raise
        except Exception as e:
            logger.exception("extraction_failed", file_path=file_path, error=str(e))
            raise ProcessingError(
                f"Text extraction failed: {str(e)}",
                details={"file_path": file_path, "mime_type": mime_type},
            ) from e
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF."""
        text_parts = []
        
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = DocxDocument(file_path)
        text_parts = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)
        
        return "\n\n".join(text_parts)
    
    def _extract_image(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if needed
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Extract text with Tesseract
                text = pytesseract.image_to_string(
                    img,
                    lang=self.settings.processing.ocr_language,
                )
                return text
        except Exception as e:
            logger.exception("ocr_failed", file_path=file_path, error=str(e))
            raise ProcessingError(
                f"OCR failed: {str(e)}",
                details={"file_path": file_path},
            ) from e
    
    def extract_from_bytes(self, content: bytes, mime_type: str) -> str:
        """Extract text from bytes (for in-memory processing)."""
        # For now, save to temp file and extract
        # In production, use BytesIO where possible
        import tempfile
        
        suffix = self._get_extension(mime_type)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            return self.extract(tmp_path, mime_type)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def _get_extension(self, mime_type: str) -> str:
        """Get file extension for MIME type."""
        extensions = {
            MimeType.PDF: ".pdf",
            MimeType.TXT: ".txt",
            MimeType.DOCX: ".docx",
            MimeType.PNG: ".png",
            MimeType.JPEG: ".jpg",
            MimeType.TIFF: ".tiff",
        }
        return extensions.get(mime_type, ".bin")


# Singleton
_text_extractor: Optional[TextExtractor] = None


def get_text_extractor() -> TextExtractor:
    """Get or create text extractor singleton."""
    global _text_extractor
    if _text_extractor is None:
        _text_extractor = TextExtractor()
    return _text_extractor
```

- [ ] **Step 4.4: Create app/services/llm.py**

```python
# app/services/llm.py
"""LLM service for document analysis using Anthropic Claude."""

import json
import time
from typing import Optional
from dataclasses import dataclass

import anthropic
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import LLMError
from app.telemetry import (
    llm_tokens_used_total,
    llm_request_duration_seconds,
)

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """Structured analysis result."""
    summary: str
    key_points: list[str]
    entities: list[str]
    sentiment: str
    topics: list[str]
    tokens_used: int
    raw_response: str


class LLMService:
    """Anthropic Claude service for document analysis."""
    
    SYSTEM_PROMPT = """You are an expert document analyst. Analyze the provided document and return a structured JSON response with the following fields:
- summary: 2-3 sentence executive summary
- key_points: 3-5 bullet points of the most important information
- entities: list of named entities (people, organizations, locations, dates, etc.)
- sentiment: overall sentiment (positive, negative, or neutral)
- topics: main topics/themes covered in the document

Return ONLY valid JSON. No markdown, no extra commentary."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = AsyncAnthropic(
            api_key=self.settings.anthropic.api_key,
            timeout=self.settings.anthropic.timeout,
            max_retries=self.settings.anthropic.max_retries,
        )
        self.model = self.settings.anthropic.model
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
    )
    async def analyze(self, text: str) -> AnalysisResult:
        """Analyze document text and return structured results."""
        start_time = time.time()
        
        logger.info("llm_analysis_started", text_length=len(text), model=self.model)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.settings.anthropic.max_tokens,
                temperature=self.settings.anthropic.temperature,
                system=self.SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Analyze this document:\n\n{text}",
                    }
                ],
            )
            
            duration = time.time() - start_time
            
            # Parse response
            result = self._parse_response(response)
            
            # Record metrics
            llm_request_duration_seconds.labels(model=self.model).observe(duration)
            llm_tokens_used_total.labels(model=self.model, type="input").inc(response.usage.input_tokens)
            llm_tokens_used_total.labels(model=self.model, type="output").inc(response.usage.output_tokens)
            
            logger.info(
                "llm_analysis_completed",
                duration_ms=int(duration * 1000),
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
            )
            
            return AnalysisResult(
                summary=result["summary"],
                key_points=result["key_points"],
                entities=result["entities"],
                sentiment=result["sentiment"],
                topics=result["topics"],
                tokens_used=response.usage.output_tokens,
                raw_response=response.content[0].text,
            )
            
        except anthropic.RateLimitError as e:
            logger.warning("llm_rate_limited", error=str(e))
            raise LLMError("Rate limit exceeded", details={"retry_after": 60}) from e
        except anthropic.APIError as e:
            logger.exception("llm_api_error", error=str(e))
            raise LLMError(f"LLM API error: {str(e)}") from e
        except Exception as e:
            logger.exception("llm_unexpected_error", error=str(e))
            raise LLMError(f"Analysis failed: {str(e)}") from e
    
    def _parse_response(self, response) -> dict:
        """Parse and validate LLM response."""
        content = response.content[0].text
        
        try:
            # Try to parse as JSON
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                result = json.loads(json_str)
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                result = json.loads(json_str)
            else:
                raise LLMError("Invalid JSON response from LLM")
        
        # Validate required fields
        required = ["summary", "key_points", "entities", "sentiment", "topics"]
        for field in required:
            if field not in result:
                raise LLMError(f"Missing required field in LLM response: {field}")
        
        # Validate sentiment
        valid_sentiments = {"positive", "negative", "neutral"}
        if result["sentiment"].lower() not in valid_sentiments:
            result["sentiment"] = "neutral"
        
        # Ensure lists
        for field in ["key_points", "entities", "topics"]:
            if not isinstance(result[field], list):
                result[field] = []
        
        return result


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
```

- [ ] **Step 4.5: Create tests/test_storage.py**

```python
# tests/test_storage.py
"""Storage service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from app.services.storage import LocalStorage, StorageService, get_storage_service
from app.exceptions import StorageError
from app.config import Settings


class TestLocalStorage:
    """Test local storage backend."""
    
    @pytest.fixture
    def storage(self, tmp_path):
        return LocalStorage(str(tmp_path))
    
    @pytest.mark.asyncio
    async def test_save_file(self, storage: LocalStorage):
        content = b"Test file content"
        file = BytesIO(content)
        
        storage_key = await storage.save(file, "test.txt", "text/plain")
        
        assert storage_key.endswith(".txt")
        assert await storage.exists(storage_key)
    
    @pytest.mark.asyncio
    async def test_get_path(self, storage: LocalStorage):
        content = b"Test content"
        file = BytesIO(content)
        storage_key = await storage.save(file, "test.txt", "text/plain")
        
        path = await storage.get_path(storage_key)
        assert path.endswith(storage_key)
    
    @pytest.mark.asyncio
    async def test_delete_file(self, storage: LocalStorage):
        content = b"Test content"
        file = BytesIO(content)
        storage_key = await storage.save(file, "test.txt", "text/plain")
        
        result = await storage.delete(storage_key)
        assert result is True
        assert not await storage.exists(storage_key)
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, storage: LocalStorage):
        result = await storage.delete("nonexistent.txt")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_preserves_content(self, storage: LocalStorage):
        content = b"Hello, World!"
        file = BytesIO(content)
        storage_key = await storage.save(file, "test.txt", "text/plain")
        
        path = await storage.get_path(storage_key)
        with open(path, "rb") as f:
            saved_content = f.read()
        
        assert saved_content == content


class TestStorageService:
    """Test high-level storage service."""
    
    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock()
        backend.save = AsyncMock(return_value="test_key.txt")
        backend.get_path = AsyncMock(return_value="/tmp/test_key.txt")
        backend.delete = AsyncMock(return_value=True)
        backend.exists = AsyncMock(return_value=True)
        return backend
    
    @pytest.fixture
    def service(self, mock_backend):
        return StorageService(mock_backend)
    
    @pytest.mark.asyncio
    async def test_save_upload(self, service: StorageService):
        file = BytesIO(b"Test content")
        storage_key, file_size = await service.save_upload(file, "test.txt", "text/plain")
        
        assert storage_key == "test_key.txt"
        assert file_size == 12
    
    @pytest.mark.asyncio
    async def test_save_upload_size_limit(self, service: StorageService):
        # Create file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        file = BytesIO(large_content)
        
        with pytest.raises(StorageError) as exc_info:
            await service.save_upload(file, "large.txt", "text/plain")
        
        assert "exceeds maximum" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_file_path(self, service: StorageService):
        path = await service.get_file_path("test_key.txt")
        assert path == "/tmp/test_key.txt"
    
    @pytest.mark.asyncio
    async def test_delete_file(self, service: StorageService):
        result = await service.delete_file("test_key.txt")
        assert result is True


class TestStorageFactory:
    """Test storage service factory."""
    
    def test_get_storage_service_local(self):
        with patch("app.services.storage.get_settings") as mock_settings:
            mock_settings.return_value.storage.provider = "local"
            mock_settings.return_value.storage.local_path = "/tmp/test"
            
            service = get_storage_service()
            assert isinstance(service.backend, LocalStorage)
```

- [ ] **Step 4.6: Create tests/test_extractor.py**

```python
# tests/test_extractor.py
"""Text extractor tests."""

import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
import tempfile
import os

from app.services.extractor import TextExtractor, get_text_extractor
from app.exceptions import ProcessingError
from app.constants import MimeType


class TestTextExtractor:
    """Test text extraction from various formats."""
    
    @pytest.fixture
    def extractor(self):
        return TextExtractor()
    
    def test_extract_txt(self, extractor: TextExtractor):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!\nThis is a test.")
            txt_path = f.name
        
        try:
            text = extractor.extract(txt_path, MimeType.TXT)
            assert "Hello, World!" in text
            assert "This is a test." in text
        finally:
            os.unlink(txt_path)
    
    def test_extract_pdf(self, extractor: TextExtractor):
        # Create a simple PDF using PyMuPDF
        import fitz
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pdf_path = f.name
        
        try:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "PDF Test Content\nLine 2")
            doc.save(pdf_path)
            doc.close()
            
            text = extractor.extract(pdf_path, MimeType.PDF)
            assert "PDF Test Content" in text
            assert "Line 2" in text
        finally:
            os.unlink(pdf_path)
    
    def test_extract_docx(self, extractor: TextExtractor):
        from docx import Document as DocxDocument
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            docx_path = f.name
        
        try:
            doc = DocxDocument()
            doc.add_paragraph("DOCX Test Content")
            doc.add_paragraph("Second paragraph")
            doc.save(docx_path)
            
            text = extractor.extract(docx_path, MimeType.DOCX)
            assert "DOCX Test Content" in text
            assert "Second paragraph" in text
        finally:
            os.unlink(docx_path)
    
    @patch("app.services.extractor.pytesseract.image_to_string")
    def test_extract_image(self, mock_ocr, extractor: TextExtractor):
        mock_ocr.return_value = "OCR extracted text"
        
        # Create a dummy image
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img_path = f.name
        
        try:
            img = Image.new("RGB", (100, 100), color="white")
            img.save(img_path)
            
            text = extractor.extract(img_path, MimeType.PNG)
            assert text == "OCR extracted text"
            mock_ocr.assert_called_once()
        finally:
            os.unlink(img_path)
    
    def test_extract_unsupported_type(self, extractor: TextExtractor):
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            path = f.name
        
        try:
            with pytest.raises(ProcessingError) as exc_info:
                extractor.extract(path, "application/unknown")
            assert "Unsupported MIME type" in str(exc_info.value)
        finally:
            os.unlink(path)
    
    def test_extract_truncates_long_text(self, extractor: TextExtractor):
        long_text = "x" * 150000
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(long_text)
            path = f.name
        
        try:
            text = extractor.extract(path, MimeType.TXT)
            assert len(text) <= extractor.max_text_length + 20  # + "[TRUNCATED]"
            assert "[TRUNCATED]" in text
        finally:
            os.unlink(path)


class TestTextExtractorFactory:
    """Test extractor factory."""
    
    def test_get_text_extractor_singleton(self):
        ext1 = get_text_extractor()
        ext2 = get_text_extractor()
        assert ext1 is ext2
```

- [ ] **Step 4.7: Create tests/test_llm.py**

```python
# tests/test_llm.py
"""LLM service tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.llm import LLMService, get_llm_service, AnalysisResult
from app.exceptions import LLMError


class TestLLMService:
    """Test LLM analysis service."""
    
    @pytest.fixture
    def mock_anthropic(self):
        with patch("app.services.llm.AsyncAnthropic") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client
    
    @pytest.fixture
    def service(self, mock_anthropic):
        return LLMService()
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, service: LLMService, mock_anthropic):
        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "summary": "Test summary",
            "key_points": ["Point 1", "Point 2"],
            "entities": ["Entity 1"],
            "sentiment": "positive",
            "topics": ["Topic 1"],
        }))]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=150)
        mock_anthropic.messages.create.return_value = mock_response
        
        result = await service.analyze("Test document content")
        
        assert isinstance(result, AnalysisResult)
        assert result.summary == "Test summary"
        assert result.sentiment == "positive"
        assert result.tokens_used == 150
        assert len(result.key_points) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_json_in_markdown(self, service: LLMService, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='```json\n{"summary": "Test", "key_points": [], "entities": [], "sentiment": "neutral", "topics": []}\n```')]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=80)
        mock_anthropic.messages.create.return_value = mock_response
        
        result = await service.analyze("Test")
        assert result.summary == "Test"
    
    @pytest.mark.asyncio
    async def test_analyze_invalid_json(self, service: LLMService, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Not JSON at all")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.return_value = mock_response
        
        with pytest.raises(LLMError) as exc_info:
            await service.analyze("Test")
        assert "Invalid JSON response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_missing_fields(self, service: LLMService, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary": "Test"}')]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.return_value = mock_response
        
        with pytest.raises(LLMError) as exc_info:
            await service.analyze("Test")
        assert "Missing required field" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_normalizes_sentiment(self, service: LLMService, mock_anthropic):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "summary": "Test",
            "key_points": [],
            "entities": [],
            "sentiment": "POSITIVE",  # Uppercase
            "topics": [],
        }))]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.return_value = mock_response
        
        result = await service.analyze("Test")
        assert result.sentiment == "positive"  # Normalized
    
    @pytest.mark.asyncio
    async def test_analyze_rate_limit(self, service: LLMService, mock_anthropic):
        import anthropic
        mock_anthropic.messages.create.side_effect = anthropic.RateLimitError(
            "Rate limited",
            response=MagicMock(status_code=429),
            body={},
        )
        
        with pytest.raises(LLMError) as exc_info:
            await service.analyze("Test")
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_retry_on_failure(self, service: LLMService, mock_anthropic):
        # First two calls fail, third succeeds
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps({
            "summary": "Test",
            "key_points": [],
            "entities": [],
            "sentiment": "neutral",
            "topics": [],
        }))]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        
        mock_anthropic.messages.create.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            mock_response,
        ]
        
        result = await service.analyze("Test")
        assert result.summary == "Test"
        assert mock_anthropic.messages.create.call_count == 3


class TestLLMFactory:
    """Test LLM service factory."""
    
    def test_get_llm_service_singleton(self):
        with patch("app.services.llm.AsyncAnthropic"):
            svc1 = get_llm_service()
            svc2 = get_llm_service()
            assert svc1 is svc2
```

- [ ] **Step 4.8: Run service tests**

```bash
# Run: pytest tests/test_storage.py tests/test_extractor.py tests/test_llm.py -v
# Expected: All tests pass
```

- [ ] **Step 4.9: Commit services**

```bash
git add app/services/ tests/test_storage.py tests/test_extractor.py tests/test_llm.py
git commit -m "feat: storage, extraction, and LLM services with tests"
```

---

### Task 5: Authentication & Rate Limiting Middleware

**Files:**
- Create: `app/middleware/__init__.py`
- Create: `app/middleware/auth.py`
- Create: `app/middleware/rate_limit.py`
- Create: `app/middleware/logging.py`
- Test: `tests/test_auth.py`, `tests/test_rate_limit.py`

**Interfaces:**
- Consumes: `APIKey` model, `settings`, `redis` (optional for distributed rate limiting)
- Produces: `verify_api_key` dependency, `rate_limit` dependency, request logging middleware

- [ ] **Step 5.1: Create app/middleware/__init__.py**

```python
# app/middleware/__init__.py
"""Middleware package."""

from app.middleware.auth import verify_api_key, get_current_api_key
from app.middleware.rate_limit import rate_limit, RateLimiter
from app.middleware.logging import RequestLoggingMiddleware

__all__ = [
    "verify_api_key",
    "get_current_api_key",
    "rate_limit",
    "RateLimiter",
    "RequestLoggingMiddleware",
]
```

- [ ] **Step 5.2: Create app/middleware/auth.py**

```python
# app/middleware/auth.py
"""API Key authentication middleware."""

from typing import Optional
from uuid import UUID
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.config import get_settings
from app.database import get_db_session
from app.models.api_key import APIKey
from app.exceptions import AuthenticationError, AuthorizationError, to_http_exception
from app.logging import get_logger

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_api_key(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> APIKey:
    """Verify API key from Authorization header."""
    
    settings = get_settings()
    
    if not authorization:
        logger.warning("auth_missing_header", client=request.client.host if request.client else "unknown")
        raise to_http_exception(AuthenticationError())
    
    # Expect "Bearer <key>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("auth_invalid_format", client=request.client.host if request.client else "unknown")
        raise to_http_exception(AuthenticationError("Invalid authorization format. Use: Bearer <api_key>"))
    
    api_key = parts[1]
    
    # Validate prefix
    if not api_key.startswith(settings.auth.api_key_prefix):
        logger.warning("auth_invalid_prefix", client=request.client.host if request.client else "unknown")
        raise to_http_exception(AuthenticationError("Invalid API key format"))
    
    # Look up key hash in database
    # We need to check all active keys (bcrypt requires checking each)
    result = await db.execute(
        select(APIKey).where(APIKey.is_active == True)
    )
    keys = result.scalars().all()
    
    matched_key = None
    for key in keys:
        if pwd_context.verify(api_key, key.key_hash):
            matched_key = key
            break
    
    if not matched_key:
        logger.warning("auth_key_not_found", client=request.client.host if request.client else "unknown")
        raise to_http_exception(AuthenticationError())
    
    # Check expiration
    if matched_key.expires_at and matched_key.expires_at < datetime.utcnow():
        logger.warning("auth_key_expired", key_id=str(matched_key.id))
        raise to_http_exception(AuthenticationError("API key has expired"))
    
    # Update last used
    matched_key.last_used_at = datetime.utcnow()
    matched_key.total_requests += 1
    await db.commit()
    
    logger.info("auth_success", key_id=str(matched_key.id), key_name=matched_key.name)
    
    # Store in request state for downstream use
    request.state.api_key = matched_key
    
    return matched_key


async def get_current_api_key(request: Request) -> APIKey:
    """Get API key from request state (set by verify_api_key)."""
    if not hasattr(request.state, "api_key"):
        raise RuntimeError("verify_api_key dependency not used")
    return request.state.api_key


def require_scope(required_scope: str):
    """Dependency factory for scope-based authorization."""
    async def _require_scope(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
        # In a real implementation, check scopes on the API key
        # For now, all keys have all scopes
        return api_key
    return _require_scope


# Import datetime here to avoid circular import
from datetime import datetime
```

- [ ] **Step 5.3: Create app/middleware/rate_limit.py**

```python
# app/middleware/rate_limit.py
"""Rate limiting middleware with in-memory and Redis backends."""

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from contextlib import asynccontextmanager

from app.config import get_settings
from app.middleware.auth import get_current_api_key
from app.exceptions import RateLimitError, to_http_exception
from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for response headers."""
    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None


class RateLimitBackend(ABC):
    """Abstract rate limit backend."""
    
    @abstractmethod
    async def check_limit(self, key: str, limit: int, window: int) -> RateLimitInfo:
        """Check and increment rate limit. Returns limit info."""
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        pass


class InMemoryRateLimiter(RateLimitBackend):
    """In-memory rate limiter (single instance only)."""
    
    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)
    
    async def check_limit(self, key: str, limit: int, window: int) -> RateLimitInfo:
        now = time.time()
        window_start = now - window
        
        # Clean old entries
        self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]
        
        current = len(self._requests[key])
        
        if current >= limit:
            oldest = min(self._requests[key]) if self._requests[key] else now
            retry_after = int(oldest + window - now) + 1
            return RateLimitInfo(
                limit=limit,
                remaining=0,
                reset=int(oldest + window),
                retry_after=retry_after,
            )
        
        self._requests[key].append(now)
        
        return RateLimitInfo(
            limit=limit,
            remaining=limit - current - 1,
            reset=int(now + window),
        )
    
    async def reset(self, key: str) -> None:
        if key in self._requests:
            del self._requests[key]


class RedisRateLimiter(RateLimitBackend):
    """Redis-backed rate limiter (distributed)."""
    
    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client = None
    
    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client
    
    async def check_limit(self, key: str, limit: int, window: int) -> RateLimitInfo:
        client = await self._get_client()
        redis_key = f"ratelimit:{key}"
        
        now = time.time()
        window_start = now - window
        
        # Use sorted set with timestamps as scores
        pipe = client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window + 1)
        results = await pipe.execute()
        
        current = results[1]
        
        if current >= limit:
            # Get oldest entry for retry-after
            oldest_entries = await client.zrange(redis_key, 0, 0, withscores=True)
            if oldest_entries:
                oldest_ts = oldest_entries[0][1]
                retry_after = int(oldest_ts + window - now) + 1
            else:
                retry_after = window
            
            return RateLimitInfo(
                limit=limit,
                remaining=0,
                reset=int(now + window),
                retry_after=retry_after,
            )
        
        return RateLimitInfo(
            limit=limit,
            remaining=limit - current - 1,
            reset=int(now + window),
        )
    
    async def reset(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(f"ratelimit:{key}")
    
    async def close(self) -> None:
        if self._client:
            await self._client.close()


class RateLimiter:
    """High-level rate limiter."""
    
    def __init__(self, backend: RateLimitBackend) -> None:
        self.backend = backend
        self.settings = get_settings()
    
    async def check(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> RateLimitInfo:
        """Check rate limit for identifier."""
        limit = limit or self.settings.auth.rate_limit_requests
        window = window or self.settings.auth.rate_limit_window
        
        return await self.backend.check_limit(identifier, limit, window)


# Global rate limiter (initialized in main.py)
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized")
    return _rate_limiter


async def init_rate_limiter() -> None:
    """Initialize rate limiter based on configuration."""
    global _rate_limiter
    settings = get_settings()
    
    if settings.env == "production" and hasattr(settings, "redis_url") and settings.redis_url:
        backend = RedisRateLimiter(settings.redis_url)
    else:
        backend = InMemoryRateLimiter()
    
    _rate_limiter = RateLimiter(backend)
    logger.info("rate_limiter_initialized", backend=type(backend).__name__)


async def close_rate_limiter() -> None:
    """Close rate limiter connections."""
    global _rate_limiter
    if _rate_limiter and hasattr(_rate_limiter.backend, "close"):
        await _rate_limiter.backend.close()
    _rate_limiter = None


async def rate_limit_dependency(
    request: Request,
    api_key: APIKey = Depends(get_current_api_key),
) -> None:
    """FastAPI dependency for rate limiting."""
    limiter = get_rate_limiter()
    
    # Use API key ID as rate limit identifier
    identifier = f"apikey:{api_key.id}"
    
    info = await limiter.check(identifier, api_key.rate_limit)
    
    # Add rate limit headers
    request.state.rate_limit_info = info
    
    if info.remaining < 0:
        logger.warning(
            "rate_limit_exceeded",
            api_key_id=str(api_key.id),
            limit=info.limit,
        )
        raise to_http_exception(RateLimitError(info.retry_after or 60))
    
    logger.debug(
        "rate_limit_checked",
        api_key_id=str(api_key.id),
        remaining=info.remaining,
    )
```

- [ ] **Step 5.4: Create app/middleware/logging.py**

```python
# app/middleware/logging.py
"""Request logging middleware."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging import get_logger, setup_logging
from app.telemetry import http_requests_total, http_request_duration_seconds

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with correlation IDs."""
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Add to contextvars for structlog
        import contextvars
        correlation_var = contextvars.ContextVar("correlation_id", default=None)
        token = correlation_var.set(correlation_id)
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            # Add rate limit headers if available
            if hasattr(request.state, "rate_limit_info"):
                info = request.state.rate_limit_info
                response.headers["X-RateLimit-Limit"] = str(info.limit)
                response.headers["X-RateLimit-Remaining"] = str(max(0, info.remaining))
                response.headers["X-RateLimit-Reset"] = str(info.reset)
            
            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=int(duration * 1000),
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=int(duration * 1000),
            )
            
            # Record error metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500,
            ).inc()
            
            raise
        finally:
            correlation_var.reset(token)
```

- [ ] **Step 5.5: Create tests/test_auth.py**

```python
# tests/test_auth.py
"""Authentication middleware tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import verify_api_key, get_current_api_key
from app.models.api_key import APIKey
from app.exceptions import AuthenticationError, AuthorizationError
from app.config import Settings


class TestVerifyAPIKey:
    """Test API key verification."""
    
    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = MagicMock()
        return request
    
    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def valid_api_key(self):
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        key = "di_test_abcdefghijklmnopqrstuvwxyz123456"
        return APIKey(
            id=uuid4(),
            key_hash=pwd_context.hash(key),
            name="Test Key",
            rate_limit=100,
            is_active=True,
            total_requests=0,
        )
    
    @pytest.mark.asyncio
    async def test_verify_missing_header(self, mock_request, mock_db_session):
        mock_request.headers = {}
        
        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization=None, db=mock_db_session)
        
        assert "Invalid or missing API key" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_verify_invalid_format(self, mock_request, mock_db_session):
        mock_request.headers = {"authorization": "InvalidFormat"}
        
        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization="InvalidFormat", db=mock_db_session)
        
        assert "Invalid authorization format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_verify_invalid_prefix(self, mock_request, mock_db_session):
        mock_request.headers = {"authorization": "Bearer invalid_key"}
        
        # Mock db to return empty list
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization="Bearer invalid_key", db=mock_db_session)
        
        assert "Invalid API key format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_verify_valid_key(self, mock_request, mock_db_session, valid_api_key):
        key = "di_test_abcdefghijklmnopqrstuvwxyz123456"
        mock_request.headers = {"authorization": f"Bearer {key}"}
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [valid_api_key]
        mock_db_session.execute.return_value = mock_result
        
        result = await verify_api_key(mock_request, authorization=f"Bearer {key}", db=mock_db_session)
        
        assert result == valid_api_key
        assert valid_api_key.total_requests == 1
        assert valid_api_key.last_used_at is not None
    
    @pytest.mark.asyncio
    async def test_verify_expired_key(self, mock_request, mock_db_session):
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        key = "di_test_abcdefghijklmnopqrstuvwxyz123456"
        
        expired_key = APIKey(
            id=uuid4(),
            key_hash=pwd_context.hash(key),
            name="Expired Key",
            rate_limit=100,
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        
        mock_request.headers = {"authorization": f"Bearer {key}"}
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired_key]
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization=f"Bearer {key}", db=mock_db_session)
        
        assert "expired" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_verify_inactive_key(self, mock_request, mock_db_session):
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        key = "di_test_abcdefghijklmnopqrstuvwxyz123456"
        
        inactive_key = APIKey(
            id=uuid4(),
            key_hash=pwd_context.hash(key),
            name="Inactive Key",
            rate_limit=100,
            is_active=False,
        )
        
        mock_request.headers = {"authorization": f"Bearer {key}"}
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [inactive_key]
        mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization=f"Bearer {key}", db=mock_db_session)
        
        assert "Invalid or missing API key" in str(exc_info.value)


class TestGetCurrentAPIKey:
    """Test get_current_api_key dependency."""
    
    @pytest.mark.asyncio
    async def test_get_key_from_state(self):
        request = MagicMock(spec=Request)
        api_key = MagicMock(spec=APIKey)
        request.state.api_key = api_key
        
        result = await get_current_api_key(request)
        assert result == api_key
    
    @pytest.mark.asyncio
    async def test_get_key_missing_state(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.api_key
        
        with pytest.raises(RuntimeError):
            await get_current_api_key(request)
```

- [ ] **Step 5.6: Create tests/test_rate_limit.py**

```python
# tests/test_rate_limit.py
"""Rate limiting tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.middleware.rate_limit import (
    InMemoryRateLimiter,
    RateLimiter,
    RateLimitInfo,
)
from app.models.api_key import APIKey


class TestInMemoryRateLimiter:
    """Test in-memory rate limiter."""
    
    @pytest.fixture
    def limiter(self):
        return InMemoryRateLimiter()
    
    @pytest.mark.asyncio
    async def test_check_limit_allows_within_limit(self, limiter):
        info = await limiter.check_limit("test_key", limit=10, window=60)
        
        assert info.limit == 10
        assert info.remaining == 9
        assert info.retry_after is None
    
    @pytest.mark.asyncio
    async def test_check_limit_blocks_over_limit(self, limiter):
        # Make 10 requests
        for i in range(10):
            await limiter.check_limit("test_key", limit=10, window=60)
        
        # 11th should be blocked
        info = await limiter.check_limit("test_key", limit=10, window=60)
        
        assert info.remaining == 0
        assert info.retry_after is not None
        assert info.retry_after > 0
    
    @pytest.mark.asyncio
    async def test_different_keys_independent(self, limiter):
        await limiter.check_limit("key1", limit=2, window=60)
        await limiter.check_limit("key1", limit=2, window=60)
        
        # key2 should still have full limit
        info = await limiter.check_limit("key2", limit=2, window=60)
        assert info.remaining == 1
    
    @pytest.mark.asyncio
    async def test_reset_clears_limit(self, limiter):
        await limiter.check_limit("test_key", limit=1, window=60)
        info = await limiter.check_limit("test_key", limit=1, window=60)
        assert info.remaining == 0
        
        await limiter.reset("test_key")
        info = await limiter.check_limit("test_key", limit=1, window=60)
        assert info.remaining == 0  # First request after reset


class TestRateLimiter:
    """Test high-level rate limiter."""
    
    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock()
        backend.check_limit = AsyncMock(return_value=RateLimitInfo(
            limit=100, remaining=99, reset=3600
        ))
        return backend
    
    @pytest.fixture
    def limiter(self, mock_backend):
        return RateLimiter(mock_backend)
    
    @pytest.mark.asyncio
    async def test_check_uses_api_key_limit(self, limiter, mock_backend):
        api_key = APIKey(id=uuid4(), rate_limit=50)
        
        await limiter.check(str(api_key.id))
        
        mock_backend.check_limit.assert_called_once()
        call_args = mock_backend.check_limit.call_args
        assert call_args.kwargs["limit"] == 50
    
    @pytest.mark.asyncio
    async def test_check_uses_default_limit(self, limiter, mock_backend):
        await limiter.check("test", limit=10, window=60)
        
        call_args = mock_backend.check_limit.call_args
        assert call_args.kwargs["limit"] == 10
        assert call_args.kwargs["window"] == 60
```

- [ ] **Step 5.7: Run middleware tests**

```bash
# Run: pytest tests/test_auth.py tests/test_rate_limit.py -v
# Expected: All tests pass
```

- [ ] **Step 5.8: Commit middleware**

```bash
git add app/middleware/ tests/test_auth.py tests/test_rate_limit.py
git commit -m "feat: authentication and rate limiting middleware with tests"
```

---

### Task 6: API Routes (Upload, Process, Query, Auth)

**Files:**
- Create: `app/routes/__init__.py`
- Create: `app/routes/upload.py`
- Create: `app/routes/process.py`
- Create: `app/routes/query.py`
- Create: `app/routes/auth.py`
- Create: `app/routes/health.py`
- Test: `tests/test_upload.py`, `tests/test_process.py`, `tests/test_query.py`, `tests/test_auth_routes.py`

**Interfaces:**
- Consumes: All services, schemas, middleware dependencies
- Produces: REST API endpoints

- [ ] **Step 6.1: Create app/routes/__init__.py**

```python
# app/routes/__init__.py
"""API routes package."""

from app.routes.upload import router as upload_router
from app.routes.process import router as process_router
from app.routes.query import router as query_router
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router

__all__ = [
    "upload_router",
    "process_router",
    "query_router",
    "auth_router",
    "health_router",
]
```

- [ ] **Step 6.2: Create app/routes/upload.py**

```python
# app/routes/upload.py
"""Document upload routes."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db_session
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.services.storage import get_storage_service
from app.models.document import Document, DocumentStatus
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentListItem,
)
from app.schemas.common import PaginatedResponse
from app.exceptions import ValidationError, StorageError, to_http_exception
from app.logging import get_logger
from app.constants import MimeType, MAX_FILE_SIZE_BYTES

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency)],
)
async def upload_document(
    file: UploadFile = File(...),
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentUploadResponse:
    """Upload a document for processing."""
    
    # Validate file
    if not file.filename:
        raise to_http_exception(ValidationError("Filename is required"))
    
    content_type = file.content_type or "application/octet-stream"
    if content_type not in [m.value for m in MimeType]:
        raise to_http_exception(
            ValidationError(
                f"Unsupported file type: {content_type}",
                details={"allowed_types": [m.value for m in MimeType]},
            )
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE_BYTES:
        raise to_http_exception(
            ValidationError(
                f"File size exceeds maximum of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
                details={"file_size": file_size, "max_size": MAX_FILE_SIZE_BYTES},
            )
        )
    
    if file_size == 0:
        raise to_http_exception(ValidationError("Empty file not allowed"))
    
    # Save to storage
    storage = get_storage_service()
    
    try:
        from io import BytesIO
        file_obj = BytesIO(content)
        storage_key, saved_size = await storage.save_upload(
            file_obj, file.filename, content_type
        )
    except StorageError as e:
        logger.error("upload_storage_failed", error=str(e), filename=file.filename)
        raise to_http_exception(e)
    
    # Create document record
    document = Document(
        filename=file.filename,
        file_path=storage_key,
        mime_type=content_type,
        file_size=saved_size,
        status=DocumentStatus.UPLOADED,
        api_key_id=api_key.id,
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    logger.info(
        "document_uploaded",
        document_id=str(document.id),
        filename=document.filename,
        size=saved_size,
        api_key_id=str(api_key.id),
    )
    
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        message="File uploaded successfully. Use the process endpoint to analyze.",
    )


@router.get(
    "/list",
    response_model=DocumentListResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentListResponse:
    """List uploaded documents with pagination."""
    
    from sqlalchemy import select, func
    
    # Validate pagination
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    
    # Build query
    query = select(Document).where(Document.api_key_id == api_key.id)
    
    if status_filter:
        try:
            status_enum = DocumentStatus(status_filter)
            query = query.where(Document.status == status_enum)
        except ValueError:
            raise to_http_exception(
                ValidationError(f"Invalid status: {status_filter}")
            )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get paginated results
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    items = [
        DocumentListItem(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            status=doc.status,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
        )
        for doc in documents
    ]
    
    total_pages = (total + page_size - 1) // page_size
    
    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
```

- [ ] **Step 6.3: Create app/routes/process.py**

```python
# app/routes/process.py
"""Document processing routes."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db_session
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.schemas.document import DocumentProcessRequest, DocumentStatusResponse
from app.schemas.analysis import AnalysisResponse
from app.services.storage import get_storage_service
from app.services.extractor import get_text_extractor
from app.services.llm import get_llm_service
from app.exceptions import NotFoundError, ProcessingError, to_http_exception
from app.logging import get_logger
from app.telemetry import (
    documents_processed_total,
    document_processing_duration_seconds,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/process", tags=["Processing"])


@router.post(
    "/analyze",
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_dependency)],
)
async def analyze_document(
    request: DocumentProcessRequest,
    background_tasks: BackgroundTasks,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentStatusResponse:
    """Trigger document analysis (async)."""
    
    # Verify document exists and belongs to API key
    from sqlalchemy import select
    result = await db.execute(
        select(Document).where(
            Document.id == request.document_id,
            Document.api_key_id == api_key.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise to_http_exception(NotFoundError("Document", str(request.document_id)))
    
    if document.status == DocumentStatus.PROCESSING:
        return DocumentStatusResponse(
            id=document.id,
            status=document.status,
            progress=50,
        )
    
    if document.status == DocumentStatus.COMPLETED:
        return DocumentStatusResponse(
            id=document.id,
            status=document.status,
            progress=100,
        )
    
    # Update status to processing
    document.status = DocumentStatus.PROCESSING
    await db.commit()
    
    # Add background task
    background_tasks.add_task(
        process_document_task,
        document_id=document.id,
        callback_url=request.callback_url,
    )
    
    logger.info(
        "processing_started",
        document_id=str(document.id),
        api_key_id=str(api_key.id),
    )
    
    return DocumentStatusResponse(
        id=document.id,
        status=DocumentStatus.PROCESSING,
        progress=0,
    )


@router.get(
    "/status/{document_id}",
    response_model=DocumentStatusResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_processing_status(
    document_id: UUID,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentStatusResponse:
    """Get document processing status."""
    
    from sqlalchemy import select
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.api_key_id == api_key.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise to_http_exception(NotFoundError("Document", str(document_id)))
    
    progress = 0
    if document.status == DocumentStatus.UPLOADED:
        progress = 0
    elif document.status == DocumentStatus.PROCESSING:
        progress = 50
    elif document.status == DocumentStatus.COMPLETED:
        progress = 100
    elif document.status == DocumentStatus.FAILED:
        progress = 100
    
    return DocumentStatusResponse(
        id=document.id,
        status=document.status,
        error_message=document.error_message,
        progress=progress,
    )


async def process_document_task(
    document_id: UUID,
    callback_url: str | None = None,
) -> None:
    """Background task to process a document."""
    
    from app.database import db
    from sqlalchemy import select
    from datetime import datetime
    import time
    
    start_time = time.time()
    
    async with db.session() as session:
        # Get document
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            logger.error("process_task_document_not_found", document_id=str(document_id))
            return
        
        try:
            # Get file path from storage
            from app.services.storage import get_storage_service
            storage = get_storage_service()
            file_path = await storage.get_file_path(document.file_path)
            
            # Extract text
            from app.services.extractor import get_text_extractor
            extractor = get_text_extractor()
            text = extractor.extract(file_path, document.mime_type)
            
            if not text.strip():
                raise ProcessingError("No text content extracted from document")
            
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await session.commit()
            
            # Analyze with LLM
            from app.services.llm import get_llm_service
            llm = get_llm_service()
            result = await llm.analyze(text)
            
            # Save analysis
            from app.models.analysis import Analysis
            analysis = Analysis(
                document_id=document.id,
                summary=result.summary,
                key_points=result.key_points,
                entities=result.entities,
                sentiment=result.sentiment,
                topics=result.topics,
                tokens_used=result.tokens_used,
                model_version=llm.model,
                processing_time_ms=int((time.time() - start_time) * 1000),
                raw_response={"content": result.raw_response},
            )
            session.add(analysis)
            
            # Mark completed
            document.status = DocumentStatus.COMPLETED
            document.processed_at = datetime.utcnow()
            await session.commit()
            
            logger.info(
                "document_processing_completed",
                document_id=str(document.id),
                processing_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=result.tokens_used,
            )
            
        except ProcessingError as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await session.commit()
            logger.error("document_processing_failed", document_id=str(document.id), error=str(e))
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = f"Unexpected error: {str(e)}"
            await session.commit()
            logger.exception("document_processing_unexpected_error", document_id=str(document.id))

logger = get_logger(__name__)
```

- [ ] **Step 6.4: Create app/routes/query.py**

```python
# app/routes/query.py
"""Query endpoints for retrieving analysis results."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.schemas.document import DocumentListResponse, DocumentListItem
from app.schemas.analysis import AnalysisResponse, AnalysisDetailResponse
from app.schemas.common import PaginatedResponse
from app.exceptions import NotFoundError, to_http_exception
from app.logging import get_logger

router = APIRouter(prefix="/query", tags=["Query"])
logger = get_logger(__name__)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def query_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentListResponse:
    """List documents with pagination and optional status filter."""
    
    query = select(Document).where(Document.api_key_id == api_key.id)
    
    if status:
        try:
            status_enum = DocumentStatus(status)
            query = query.where(Document.status == status_enum)
        except ValueError:
            from app.exceptions import ValidationError
            raise to_http_exception(ValidationError(f"Invalid status: {status}"))
    
    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginated results with analysis loaded
    query = query.options(selectinload(Document.analysis))
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    items = [
        DocumentListItem(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            status=doc.status,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
        )
        for doc in documents
    ]
    
    total_pages = (total + page_size - 1) // page_size
    
    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/documents/{document_id}",
    response_model=AnalysisDetailResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_document_analysis(
    document_id: UUID,
    include_raw: bool = Query(False),
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisDetailResponse:
    """Get full analysis results for a document."""
    
    # Verify document ownership
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.api_key_id == api_key.id,
        )
    )
    document = doc_result.scalar_one_or_none()
    
    if not document:
        raise to_http_exception(NotFoundError("Document", str(document_id)))
    
    if document.status != DocumentStatus.COMPLETED:
        raise to_http_exception(
            NotFoundError("Analysis not available - document not processed", str(document_id))
        )
    
    # Get analysis
    analysis_result = await db.execute(
        select(Analysis).where(Analysis.document_id == document_id)
    )
    analysis = analysis_result.scalar_one_or_none()
    
    if not analysis:
        raise to_http_exception(NotFoundError("Analysis", str(document_id)))
    
    response = AnalysisDetailResponse(
        id=analysis.id,
        document_id=analysis.document_id,
        summary=analysis.summary,
        key_points=analysis.key_points,
        entities=analysis.entities,
        sentiment=analysis.sentiment,
        topics=analysis.topics,
        tokens_used=analysis.tokens_used,
        model_version=analysis.model_version,
        processing_time_ms=analysis.processing_time_ms,
        created_at=analysis.created_at,
    )
    
    if include_raw:
        response.raw_response = analysis.raw_response
    
    logger.info("analysis_retrieved", document_id=str(document_id), api_key_id=str(api_key.id))
    
    return response


@router.get(
    "/stats",
    response_model=dict,
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_stats(
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get usage statistics for the API key."""
    
    from app.models.document import DocumentStatus
    
    # Document counts by status
    status_counts = {}
    for status in DocumentStatus:
        count = await db.scalar(
            select(func.count(Document.id)).where(
                Document.api_key_id == api_key.id,
                Document.status == status,
            )
        )
        status_counts[status.value] = count
    
    total_docs = sum(status_counts.values())
    
    # Total tokens used
    from app.models.analysis import Analysis
    total_tokens = await db.scalar(
        select(func.sum(Analysis.tokens_used))
        .join(Document)
        .where(Document.api_key_id == api_key.id)
    ) or 0
    
    return {
        "api_key_id": str(api_key.id),
        "api_key_name": api_key.name,
        "total_documents": total_docs,
        "documents_by_status": status_counts,
        "total_tokens_used": total_tokens,
        "rate_limit": api_key.rate_limit,
        "total_requests": api_key.total_requests,
    }
```

- [ ] **Step 6.5: Create app/routes/health.py**

```python
# app/routes/health.py
"""Health check endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

from app.database import get_db_session
from app.config import get_settings
from app.schemas.common import HealthResponse
from app.logging import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> HealthResponse:
    """Comprehensive health check."""
    
    settings = get_settings()
    db_status = "healthy"
    
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        logger.error("health_check_db_failed", error=str(e))
        response.status_code = 503
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        environment=settings.env,
        database=db_status,
        timestamp=datetime.utcnow(),
    )


@router.get("/health/live")
async def liveness_probe() -> dict:
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Kubernetes readiness probe."""
    
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Not ready")


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

- [ ] **Step 6.6: Create app/routes/auth.py**

```python
# app/routes/auth.py
"""API Key management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.database import get_db_session
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.models.api_key import APIKey
from app.schemas.auth import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeyListResponse,
)
from app.exceptions import NotFoundError, to_http_exception
from app.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post(
    "/keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_dependency)],
)
async def create_api_key(
    request: APIKeyCreate,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> APIKeyCreateResponse:
    """Create a new API key (requires existing valid key)."""
    
    # Generate key
    import secrets
    prefix = "di_"
    random_part = secrets.token_urlsafe(32)
    plain_key = f"{prefix}{random_part}"
    key_hash = pwd_context.hash(plain_key)
    
    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
    
    # Create key
    new_key = APIKey(
        key_hash=key_hash,
        name=request.name,
        rate_limit=request.rate_limit,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    logger.info("api_key_created", key_id=str(new_key.id), name=new_key.name, created_by=str(api_key.id))
    
    return APIKeyCreateResponse(
        id=new_key.id,
        key=plain_key,  # Only returned once!
        name=new_key.name,
        rate_limit=new_key.rate_limit,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        expires_at=new_key.expires_at,
    )


@router.get(
    "/keys",
    response_model=APIKeyListResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def list_api_keys(
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> APIKeyListResponse:
    """List all API keys for the authenticated key (admin-like)."""
    
    result = await db.execute(
        select(APIKey).where(APIKey.is_active == True).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    
    return APIKeyListResponse(
        items=[
            APIKeyResponse(
                id=k.id,
                name=k.name,
                rate_limit=k.rate_limit,
                is_active=k.is_active,
                last_used_at=k.last_used_at,
                total_requests=k.total_requests,
                created_at=k.created_at,
                updated_at=k.updated_at,
                expires_at=k.expires_at,
            )
            for k in keys
        ],
        total=len(keys),
    )


@router.get(
    "/keys/{key_id}",
    response_model=APIKeyResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_api_key(
    key_id: UUID,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> APIKeyResponse:
    """Get API key details (without the key itself)."""
    
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    
    if not key:
        raise to_http_exception(NotFoundError("API Key", str(key_id)))
    
    return APIKeyResponse(
        id=key.id,
        name=key.name,
        rate_limit=key.rate_limit,
        is_active=key.is_active,
        last_used_at=key.last_used_at,
        total_requests=key.total_requests,
        created_at=key.created_at,
        updated_at=key.updated_at,
        expires_at=key.expires_at,
    )


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit_dependency)],
)
async def revoke_api_key(
    key_id: UUID,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Revoke an API key."""
    
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    
    if not key:
        raise to_http_exception(NotFoundError("API Key", str(key_id)))
    
    # Prevent self-revocation
    if key.id == api_key.id:
        from app.exceptions import ValidationError
        raise to_http_exception(ValidationError("Cannot revoke your own API key"))
    
    key.is_active = False
    await db.commit()
    
    logger.info("api_key_revoked", key_id=str(key_id), revoked_by=str(api_key.id))
```

- [ ] **Step 6.7: Create tests/test_upload.py**

```python
# tests/test_upload.py
"""Upload endpoint tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient

from app.models.document import Document, DocumentStatus
from app.models.api_key import APIKey


class TestUploadEndpoint:
    """Test document upload endpoint."""
    
    @pytest.fixture
    def mock_storage(self):
        with patch("app.routes.upload.get_storage_service") as mock:
            service = MagicMock()
            service.save_upload = AsyncMock(return_value=("storage_key.txt", 1024))
            mock.return_value = service
            yield service
    
    @pytest.mark.asyncio
    async def test_upload_success(
        self, client: AsyncClient, auth_headers: dict, mock_storage, test_api_key: APIKey
    ):
        file_content = b"Test document content"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "uploaded"
        assert "id" in data
        mock_storage.save_upload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_empty_filename(self, client: AsyncClient, auth_headers: dict):
        files = {"file": ("", BytesIO(b"content"), "text/plain")}
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Filename is required" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_upload_invalid_mime_type(self, client: AsyncClient, auth_headers: dict):
        files = {"file": ("test.xyz", BytesIO(b"content"), "application/unknown")}
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Unsupported file type" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client: AsyncClient, auth_headers: dict):
        # Create file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.txt", BytesIO(large_content), "text/plain")}
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "exceeds maximum" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, auth_headers: dict):
        files = {"file": ("empty.txt", BytesIO(b""), "text/plain")}
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "File is empty" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_upload_without_auth(self, client: AsyncClient):
        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListDocumentsEndpoint:
    """Test document listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_documents(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey
    ):
        response = await client.get(
            "/api/v1/documents/list",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/documents/list?page=2&page_size=5",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5
    
    @pytest.mark.asyncio
    async def test_list_documents_status_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/documents/list?status=completed",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
```

- [ ] **Step 6.8: Create tests/test_process.py**

```python
# tests/test_process.py
"""Process endpoint tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import status
from httpx import AsyncClient

from app.models.document import Document, DocumentStatus
from app.models.api_key import APIKey


class TestProcessEndpoint:
    """Test document processing endpoints."""
    
    @pytest.fixture
    def test_document(self, test_api_key: APIKey):
        return Document(
            id=uuid4(),
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.UPLOADED,
            api_key_id=test_api_key.id,
        )
    
    @pytest.mark.asyncio
    async def test_analyze_document_success(
        self, client: AsyncClient, auth_headers: dict, test_document: Document, db_session
    ):
        # Add document to DB
        db_session.add(test_document)
        await db_session.commit()
        await db_session.refresh(test_document)
        
        with patch("app.routes.process.process_document_task") as mock_task:
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(test_document.id)},
                headers=auth_headers,
            )
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["status"] == "processing"
        assert data["id"] == str(test_document.id)
        mock_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_document(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(uuid4())},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_analyze_already_processing(
        self, client: AsyncClient, auth_headers: dict, test_document: Document, db_session
    ):
        test_document.status = DocumentStatus.PROCESSING
        db_session.add(test_document)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(test_document.id)},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "already being processed" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_analyze_already_completed(
        self, client: AsyncClient, auth_headers: dict, test_document: Document, db_session
    ):
        test_document.status = DocumentStatus.COMPLETED
        db_session.add(test_document)
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(test_document.id)},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "already been processed" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_get_processing_status(
        self, client: AsyncClient, auth_headers: dict, test_document: Document, db_session
    ):
        db_session.add(test_document)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["status"] == "uploaded"
        assert data["progress"] == 0
```

- [ ] **Step 6.9: Create tests/test_query.py**

```python
# tests/test_query.py
"""Query endpoint tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi import status
from httpx import AsyncClient

from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.models.api_key import APIKey


class TestQueryEndpoints:
    """Test query endpoints."""
    
    @pytest.fixture
    def test_document_with_analysis(self, test_api_key: APIKey):
        doc = Document(
            id=uuid4(),
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.COMPLETED,
            api_key_id=test_api_key.id,
            processed_at=datetime.utcnow(),
        )
        analysis = Analysis(
            id=uuid4(),
            document_id=doc.id,
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            entities=["Entity 1"],
            sentiment="positive",
            topics=["Topic 1"],
            tokens_used=150,
            model_version="claude-3-5-sonnet-20241022",
            processing_time_ms=1200,
        )
        return doc, analysis
    
    @pytest.mark.asyncio
    async def test_query_documents(
        self, client: AsyncClient, auth_headers: dict, test_document_with_analysis, db_session
    ):
        doc, analysis = test_document_with_analysis
        db_session.add_all([doc, analysis])
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/query/documents",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "test.pdf"
        assert data["items"][0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_query_documents_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/query/documents?page=1&page_size=5",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    @pytest.mark.asyncio
    async def test_get_document_analysis(
        self, client: AsyncClient, auth_headers: dict, test_document_with_analysis, db_session
    ):
        doc, analysis = test_document_with_analysis
        db_session.add_all([doc, analysis])
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/query/documents/{doc.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["document_id"] == str(doc.id)
        assert data["summary"] == "Test summary"
        assert data["sentiment"] == "positive"
        assert len(data["key_points"]) == 2
        assert "raw_response" not in data
    
    @pytest.mark.asyncio
    async def test_get_document_analysis_with_raw(
        self, client: AsyncClient, auth_headers: dict, test_document_with_analysis, db_session
    ):
        doc, analysis = test_document_with_analysis
        analysis.raw_response = {"test": "data"}
        db_session.add_all([doc, analysis])
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/query/documents/{doc.id}?include_raw=true",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "raw_response" in data
        assert data["raw_response"] == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_get_analysis_not_processed(
        self, client: AsyncClient, auth_headers: dict, test_document_with_analysis, db_session
    ):
        doc, _ = test_document_with_analysis
        doc.status = DocumentStatus.UPLOADED
        db_session.add(doc)
        await db_session.commit()
        
        response = await client.get(
            f"/api/v1/query/documents/{doc.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not processed" in response.json()["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_get_stats(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey, db_session
    ):
        response = await client.get(
            "/api/v1/query/stats",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "api_key_id" in data
        assert "total_documents" in data
        assert "documents_by_status" in data
        assert "total_tokens_used" in data
```

- [ ] **Step 6.10: Create tests/test_health.py**

```python
# tests/test_health.py
"""Health endpoint tests."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client: AsyncClient):
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_health_check_db_unhealthy(self, client: AsyncClient):
        with patch("app.routes.health.get_db_session") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("DB down"))
            mock_db.return_value.__aenter__.return_value = mock_session
            
            response = await client.get("/health")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert data["database"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_liveness_probe(self, client: AsyncClient):
        response = await client.get("/health/live")
        
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}
    
    @pytest.mark.asyncio
    async def test_readiness_probe_ready(self, client: AsyncClient):
        response = await client.get("/health/ready")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
    
    @pytest.mark.asyncio
    async def test_readiness_probe_not_ready(self, client: AsyncClient):
        with patch("app.routes.health.get_db_session") as mock_db:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("DB down"))
            mock_db.return_value.__aenter__.return_value = mock_session
            
            response = await client.get("/health/ready")
            
            assert response.status_code == 503
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        response = await client.get("/metrics")
        
        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "http_request_duration_seconds" in response.text
```

- [ ] **Step 6.11: Create tests/test_auth_routes.py**

```python
# tests/test_auth_routes.py
"""Auth routes tests."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi import status
from httpx import AsyncClient

from app.models.api_key import APIKey


class TestAuthRoutes:
    """Test API key management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_api_key(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey, db_session
    ):
        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "New Key", "rate_limit": 50, "expires_in_days": 30},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "key" in data  # Plain key returned only once
        assert data["name"] == "New Key"
        assert data["rate_limit"] == 50
        assert data["is_active"] is True
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_api_key_invalid_rate_limit(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Test", "rate_limit": 0},
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_list_api_keys(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey
    ):
        response = await client.get(
            "/api/v1/auth/keys",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
        # Key should not be in list
        for item in data["items"]:
            assert "key" not in item
    
    @pytest.mark.asyncio
    async def test_get_api_key(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey
    ):
        response = await client.get(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_api_key.id)
        assert data["name"] == test_api_key.name
        assert "key" not in data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_api_key(self, client: AsyncClient, auth_headers: dict):
        response = await client.get(
            f"/api/v1/auth/keys/{uuid4()}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey, db_session
    ):
        # Create another key to revoke
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        key_hash = pwd_context.hash("di_test_revokeme")
        
        other_key = APIKey(
            key_hash=key_hash,
            name="To Revoke",
            rate_limit=10,
            is_active=True,
        )
        db_session.add(other_key)
        await db_session.commit()
        await db_session.refresh(other_key)
        
        response = await client.delete(
            f"/api/v1/auth/keys/{other_key.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify revoked
        await db_session.refresh(other_key)
        assert other_key.is_active is False
    
    @pytest.mark.asyncio
    async def test_cannot_revoke_own_key(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey
    ):
        response = await client.delete(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Cannot revoke your own API key" in response.json()["error"]["message"]
```

- [ ] **Step 6.12: Run route tests**

```bash
# Run: pytest tests/test_upload.py tests/test_process.py tests/test_query.py tests/test_health.py tests/test_auth_routes.py -v
# Expected: All tests pass
```

- [ ] **Step 6.13: Commit routes**

```bash
git add app/routes/ tests/test_upload.py tests/test_process.py tests/test_query.py tests/test_health.py tests/test_auth_routes.py
git commit -m "feat: REST API routes with comprehensive tests"
```

---

### Task 7: Background Task Processing

**Files:**
- Create: `app/tasks/__init__.py`
- Create: `app/tasks/processor.py`
- Test: `tests/test_processor.py`

**Interfaces:**
- Consumes: All services, database, models
- Produces: `process_document_task` function for BackgroundTasks

- [ ] **Step 7.1: Create app/tasks/__init__.py**

```python
# app/tasks/__init__.py
"""Background tasks package."""

from app.tasks.processor import process_document_task

__all__ = ["process_document_task"]
```

- [ ] **Step 7.2: Create app/tasks/processor.py**

```python
# app/tasks/processor.py
"""Background document processing task."""

import time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import db, init_db, close_db
from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.services.storage import get_storage_service
from app.services.extractor import get_text_extractor
from app.services.llm import get_llm_service
from app.exceptions import ProcessingError
from app.logging import get_logger

logger = get_logger(__name__)


async def process_document_task(document_id: str) -> None:
    """Process a document: extract text, analyze with LLM, store results."""
    
    doc_uuid = UUID(document_id)
    start_time = time.time()
    
    # Initialize DB for background task
    await init_db()
    
    async with db.session() as session:
        try:
            # Get document
            result = await session.execute(
                select(Document).where(Document.id == doc_uuid)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error("process_document_not_found", document_id=document_id)
                return
            
            if document.status == DocumentStatus.PROCESSING:
                logger.warning("process_document_already_processing", document_id=document_id)
                return
            
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await session.commit()
            
            logger.info("process_document_started", document_id=document_id)
            
            # Get file from storage
            storage = get_storage_service()
            file_path = await storage.get_file_path(document.file_path)
            
            # Extract text
            extractor = get_text_extractor()
            text = extractor.extract(file_path, document.mime_type)
            
            if not text.strip():
                raise ProcessingError("No text content extracted from document")
            
            # Analyze with LLM
            llm = get_llm_service()
            result = await llm.analyze(text)
            
            # Save analysis
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            analysis = Analysis(
                document_id=document.id,
                summary=result.summary,
                key_points=result.key_points,
                entities=result.entities,
                sentiment=result.sentiment,
                topics=result.topics,
                tokens_used=result.tokens_used,
                model_version=llm.model,
                processing_time_ms=processing_time_ms,
                raw_response={"content": result.raw_response},
            )
            session.add(analysis)
            
            # Mark completed
            document.status = DocumentStatus.COMPLETED
            document.processed_at = time.time()
            
            await session.commit()
            
            logger.info(
                "process_document_completed",
                document_id=document_id,
                processing_time_ms=processing_time_ms,
                tokens_used=result.tokens_used,
            )
            
        except ProcessingError as e:
            await _mark_failed(session, document, str(e))
            logger.error("process_document_failed", document_id=document_id, error=str(e))
        except Exception as e:
            await _mark_failed(session, document, f"Unexpected error: {str(e)}")
            logger.exception("process_document_unexpected_error", document_id=document_id)
        finally:
            await close_db()


async def _mark_failed(session: AsyncSession, document: Document | None, error: str) -> None:
    """Mark document as failed with error message."""
    if document:
        document.status = DocumentStatus.FAILED
        document.error_message = error
        await session.commit()
```

- [ ] **Step 7.3: Create tests/test_processor.py**

```python
# tests/test_processor.py
"""Background processor tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.tasks.processor import process_document_task
from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.models.api_key import APIKey
from app.exceptions import ProcessingError


class TestProcessDocumentTask:
    """Test background document processing."""
    
    @pytest.fixture
    def mock_services(self):
        with patch("app.tasks.processor.get_storage_service") as mock_storage, \
             patch("app.tasks.processor.get_text_extractor") as mock_extractor, \
             patch("app.tasks.processor.get_llm_service") as mock_llm, \
             patch("app.tasks.processor.init_db") as mock_init_db, \
             patch("app.tasks.processor.close_db") as mock_close_db:
            
            # Setup mocks
            storage = MagicMock()
            storage.get_file_path = AsyncMock(return_value="/tmp/test.pdf")
            mock_storage.return_value = storage
            
            extractor = MagicMock()
            extractor.extract = MagicMock(return_value="Document text content")
            mock_extractor.return_value = extractor
            
            llm = MagicMock()
            llm.model = "claude-3-5-sonnet-20241022"
            llm.analyze = AsyncMock()
            mock_llm.return_value = llm
            
            yield {
                "storage": storage,
                "extractor": extractor,
                "llm": llm,
                "init_db": mock_init_db,
                "close_db": mock_close_db,
            }
    
    @pytest.mark.asyncio
    async def test_process_document_success(
        self, mock_services, test_document: Document, test_api_key: APIKey, db_session
    ):
        # Setup document in DB
        test_document.status = DocumentStatus.UPLOADED
        db_session.add(test_document)
        await db_session.commit()
        await db_session.refresh(test_document)
        
        # Mock LLM result
        from app.services.llm import AnalysisResult
        mock_services["llm"].analyze.return_value = AnalysisResult(
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            entities=["Entity 1"],
            sentiment="positive",
            topics=["Topic 1"],
            tokens_used=150,
            raw_response="raw",
        )
        
        # Run task
        await process_document_task(str(test_document.id))
        
        # Verify
        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.COMPLETED
        assert test_document.processed_at is not None
        
        # Check analysis saved
        result = await db_session.execute(
            select(Analysis).where(Analysis.document_id == test_document.id)
        )
        analysis = result.scalar_one_or_none()
        assert analysis is not None
        assert analysis.summary == "Test summary"
        assert analysis.sentiment == "positive"
        assert analysis.tokens_used == 150
    
    @pytest.mark.asyncio
    async def test_process_document_not_found(self, mock_services):
        await process_document_task(str(uuid4()))
        # Should not raise, just log
    
    @pytest.mark.asyncio
    async def test_process_document_already_processing(
        self, mock_services, test_document: Document, db_session
    ):
        test_document.status = DocumentStatus.PROCESSING
        db_session.add(test_document)
        await db_session.commit()
        
        await process_document_task(str(test_document.id))
        
        # Should not process again
        mock_services["extractor"].extract.assert_not_called()
        mock_services["llm"].analyze.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_document_no_text(
        self, mock_services, test_document: Document, db_session
    ):
        mock_services["extractor"].extract.return_value = ""
        
        await process_document_task(str(test_document.id))
        
        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.FAILED
        assert "No text content" in test_document.error_message
    
    @pytest.mark.asyncio
    async def test_process_document_llm_error(
        self, mock_services, test_document: Document, db_session
    ):
        mock_services["llm"].analyze.side_effect = ProcessingError("LLM failed")
        
        await process_document_task(str(test_document.id))
        
        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.FAILED
        assert "LLM failed" in test_document.error_message
```

- [ ] **Step 7.4: Run processor tests**

```bash
# Run: pytest tests/test_processor.py -v
# Expected: All tests pass
```

- [ ] **Step 7.5: Commit background tasks**

```bash
git add app/tasks/ tests/test_processor.py
git commit -m "feat: background document processing task"
```

---

### Task 8: Main Application & Wiring

**Files:**
- Create: `app/main.py`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `render.yaml`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/cd.yml`
- Create: `README.md`

**Interfaces:**
- Consumes: All routes, middleware, config, database
- Produces: FastAPI application instance, Docker image, CI/CD pipelines

- [ ] **Step 8.1: Create app/main.py**

```python
# app/main.py
"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, close_db
from app.middleware.rate_limit import init_rate_limiter, close_rate_limiter
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import upload, process, query, health, auth
from app.exceptions import AppException, to_http_exception
from app.logging import setup_logging, get_logger
from app.telemetry import setup_telemetry

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        json_logs=settings.is_production,
    )
    
    # Setup telemetry
    setup_telemetry(
        service_name=settings.otel_service_name,
        sample_rate=1.0,
        enable_azure_monitor=settings.is_production and bool(settings.azure.monitor_connection_string),
        azure_connection_string=settings.azure.monitor_connection_string,
    )
    
    # Initialize database
    await init_db()
    
    # Initialize rate limiter
    await init_rate_limiter()
    
    logger.info("application_started", environment=settings.env)
    
    yield
    
    # Cleanup
    await close_rate_limiter()
    await close_db()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="Document Intelligence API",
        description="AI-powered document analysis API with Claude",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )
    
    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            },
        )
    
    # Include routers
    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(process.router, prefix="/api/v1")
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(health.router, prefix="")
    app.include_router(auth.router, prefix="/api/v1")
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers if not settings.is_development else 1,
    )
```

- [ ] **Step 8.2: Create Dockerfile**

```dockerfile
# Dockerfile
# Multi-stage build for production

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create uploads directory
RUN mkdir -p /app/data/uploads && chown -R appuser:appuser /app/data

# Switch to non-root user
USER appuser

# Add local packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health/live', timeout=5)"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 8.3: Create docker-compose.yml**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: docintel-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-docintel}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-docintel}
      POSTGRES_DB: ${POSTGRES_DB:-docintel}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-docintel}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: docintel-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: docintel-api
    environment:
      - APP_ENV=development
      - DATABASE_URL=postgresql+asyncpg://docintel:docintel@postgres:5432/docintel
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - STORAGE_PROVIDER=local
      - LOCAL_STORAGE_PATH=/app/data/uploads
      - LOG_LEVEL=DEBUG
      - OTEL_SERVICE_NAME=document-intelligence-api
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - uploads:/app/data/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
  uploads:
```

- [ ] **Step 8.4: Create render.yaml**

```yaml
# render.yaml
services:
  - type: web
    name: document-intelligence-api
    runtime: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: APP_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: docintel-db
          property: connectionString
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: STORAGE_PROVIDER
        value: azure_blob
      - key: AZURE_STORAGE_ACCOUNT
        sync: false
      - key: AZURE_STORAGE_CONTAINER
        value: documents
      - key: AZURE_STORAGE_CONNECTION_STRING
        sync: false
      - key: AZURE_KEY_VAULT_URL
        sync: false
      - key: AZURE_MONITOR_CONNECTION_STRING
        sync: false
      - key: OTEL_SERVICE_NAME
        value: document-intelligence-api
      - key: LOG_LEVEL
        value: INFO
    healthCheckPath: /health/ready
    autoDeploy: true

databases:
  - name: docintel-db
    databaseName: docintel
    user: docintel
    plan: free
```

- [ ] **Step 8.5: Create .github/workflows/ci.yml**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Run Ruff
        run: ruff check .
      
      - name: Run MyPy
        run: mypy app/

  test:
    name: Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Wait for PostgreSQL
        run: |
          sleep 5
          pg_isready -h localhost -p 5432 -U test
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          ANTHROPIC_API_KEY: test-key
          APP_ENV: test
        run: |
          pytest --cov=app --cov-report=xml --cov-fail-under=85
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml

  docker:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: document-intelligence-api:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

- [ ] **Step 8.6: Create .github/workflows/cd.yml**

```yaml
# .github/workflows/cd.yml
name: CD - Deploy to Render

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Render
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Render
        uses: render/deploy-action@v1
        with:
          service-id: ${{ secrets.RENDER_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
          wait-for-deployment: true
          timeout: 300
```

- [ ] **Step 8.7: Create README.md**

```markdown
# Document Intelligence API

[![CI](https://github.com/yourname/document-intelligence-api/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/document-intelligence-api/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/yourname/document-intelligence-api/branch/main/graph/badge.svg)](https://codecov.io/gh/yourname/document-intelligence-api)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://hub.docker.com/r/yourname/document-intelligence-api)

Production-grade AI Document Intelligence API built with **FastAPI**, **PostgreSQL**, **Anthropic Claude**, and **Azure**. Demonstrates senior-level engineering practices: clean architecture, comprehensive observability, security-first design, and cloud-native deployment.

## Features

- **Document Upload**: PDF, TXT, DOCX, PNG/JPEG/TIFF (with OCR)
- **AI Analysis**: Summary, key points, entities, sentiment, topics via Claude 3.5 Sonnet
- **Async Processing**: Background tasks with status polling
- **Authentication**: API keys with bcrypt hashing, rate limiting
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured JSON logging
- **Deployment**: Docker, Render.com, GitHub Actions CI/CD

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────┐     ┌─────────────┐
│  Client     │────▶│  FastAPI (async)                │────▶│  PostgreSQL │
│  (curl/UI)  │     │  - Upload/Process/Query routes  │     │  (asyncpg)  │
└─────────────┘     │  - API Key auth + rate limiting │     └─────────────┘
                    │  - BackgroundTasks for LLM      │            │
                    │  - OpenTelemetry instrumentation│            ▼
                    └──────────────┬──────────────────┘     ┌─────────────┐
                                   │                        │  Azure Blob │
                    ┌──────────────┴──────────────┐         │  Storage    │
                    │  Services                   │         └─────────────┘
                    │  - Storage (local/Azure)    │                  │
                    │  - Text Extraction (PDF/OCR)│                  ▼
                    │  - LLM (Anthropic Claude)   │         ┌─────────────┐
                    └─────────────────────────────┘         │  Prometheus │
                                                            │  /metrics   │
                                                            └─────────────┘
```

## Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/yourname/document-intelligence-api
cd document-intelligence-api

# Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Start with Docker Compose
docker-compose up -d

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
# Metrics at http://localhost:8000/metrics
```

### Manual Setup

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate

# Install
pip install -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start
uvicorn app.main:app --reload
```

## API Reference

### Authentication

All endpoints require `Authorization: Bearer <api_key>` header.

Create your first key via the `/api/v1/auth/keys` endpoint (requires existing key) or seed via migration.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/documents/upload` | Upload document |
| `GET` | `/api/v1/documents/list` | List documents (paginated) |
| `POST` | `/api/v1/process/analyze` | Trigger analysis |
| `GET` | `/api/v1/process/status/{id}` | Check processing status |
| `GET` | `/api/v1/query/documents` | Query documents with analysis |
| `GET` | `/api/v1/query/documents/{id}` | Get full analysis |
| `GET` | `/api/v1/query/stats` | Usage statistics |
| `POST` | `/api/v1/auth/keys` | Create API key |
| `GET` | `/api/v1/auth/keys` | List API keys |
| `DELETE` | `/api/v1/auth/keys/{id}` | Revoke API key |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |

### Example Usage

```bash
# Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer di_your_key" \
  -F "file=@document.pdf"

# Response: {"id": "uuid", "filename": "document.pdf", "status": "uploaded"}

# Trigger analysis
curl -X POST http://localhost:8000/api/v1/process/analyze \
  -H "Authorization: Bearer di_your_key" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "uuid"}'

# Check status
curl http://localhost:8000/api/v1/process/status/uuid \
  -H "Authorization: Bearer di_your_key"

# Get results
curl http://localhost:8000/api/v1/query/documents/uuid \
  -H "Authorization: Bearer di_your_key"
```

### Analysis Response

```json
{
  "id": "uuid",
  "document_id": "uuid",
  "summary": "Executive summary of the document...",
  "key_points": ["Key point 1", "Key point 2", "Key point 3"],
  "entities": ["Microsoft", "Azure", "Satya Nadella"],
  "sentiment": "positive",
  "topics": ["Cloud Computing", "AI", "Enterprise"],
  "tokens_used": 245,
  "model_version": "claude-3-5-sonnet-20241022",
  "processing_time_ms": 1842,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required |
| `STORAGE_PROVIDER` | `local` or `azure_blob` | local |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob connection string | Required for Azure |
| `API_KEY_PREFIX` | Prefix for generated keys | `di_` |
| `RATE_LIMIT_REQUESTS` | Requests per window | 10 |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | 60 |
| `MAX_FILE_SIZE_MB` | Max upload size | 50 |
| `LOG_LEVEL` | Log level | INFO |
| `AZURE_MONITOR_CONNECTION_STRING` | Application Insights connection | Optional |

## Observability

- **Structured Logging**: JSON logs with correlation IDs
- **Distributed Tracing**: OpenTelemetry → Azure Monitor / Jaeger
- **Metrics**: Prometheus at `/metrics` (request latency, tokens, errors)
- **Health Checks**: `/health/live`, `/health/ready`, `/health` (full)

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=85

# Specific test file
pytest tests/test_upload.py -v
```

## Deployment

### Render.com (Recommended)

1. Push to GitHub
2. Connect repo to Render
3. Use `render.yaml` for infrastructure as code
4. Add environment variables in Render dashboard
5. Deploy

### Docker

```bash
docker build -t document-intelligence-api .
docker run -p 8000:8000 --env-file .env document-intelligence-api
```

## Project Structure

```
document-intelligence-api/
├── app/
│   ├── config.py          # Pydantic Settings
│   ├── database.py        # SQLAlchemy async
│   ├── exceptions.py      # Custom exceptions
│   ├── logging.py         # Structured logging
│   ├── telemetry.py       # OpenTelemetry + Prometheus
│   ├── constants.py       # Enums, constants
│   ├── main.py            # FastAPI factory
│   ├── middleware/
│   │   ├── auth.py        # API key verification
│   │   ├── rate_limit.py  # Rate limiting
│   │   └── logging.py     # Request logging
│   ├── models/
│   │   ├── document.py    # Document model
│   │   ├── analysis.py    # Analysis model
│   │   └── api_key.py     # API key model
│   ├── schemas/
│   │   ├── document.py    # Document schemas
│   │   ├── analysis.py    # Analysis schemas
│   │   ├── auth.py        # Auth schemas
│   │   └── common.py      # Pagination, errors
│   ├── routes/
│   │   ├── upload.py      # Upload endpoints
│   │   ├── process.py     # Processing endpoints
│   │   ├── query.py       # Query endpoints
│   │   ├── health.py      # Health endpoints
│   │   └── auth.py        # Auth endpoints
│   ├── services/
│   │   ├── storage.py     # File storage (local/Azure)
│   │   ├── extractor.py   # Text extraction
│   │   └── llm.py         # Anthropic integration
│   └── tasks/
│       └── processor.py   # Background processing
├── alembic/               # Database migrations
├── tests/                 # Pytest suite (≥85% coverage)
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
└── pyproject.toml
```

## Tech Stack

- **FastAPI 0.109** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Pydantic v2** - Data validation & settings
- **Anthropic SDK** - Claude 3.5 Sonnet
- **OpenTelemetry** - Distributed tracing & metrics
- **Prometheus** - Metrics exposition
- **Structlog** - Structured JSON logging
- **PyMuPDF** - PDF text extraction
- **Tesseract** - OCR for images
- **Alembic** - Database migrations
- **Docker** - Containerization
- **GitHub Actions** - CI/CD

## License

MIT
```

- [ ] **Step 8.8: Run full test suite**

```bash
# Run: pytest --cov=app --cov-report=term-missing --cov-fail-under=85
# Expected: All tests pass, coverage ≥ 85%
```

- [ ] **Step 8.9: Build Docker image**

```bash
# Run: docker build -t document-intelligence-api .
# Expected: Build succeeds
```

- [ ] **Step 8.10: Test Docker Compose**

```bash
# Run: docker-compose up -d && sleep 10 && curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}
```

- [ ] **Step 8.11: Commit application wiring**

```bash
git add app/main.py Dockerfile docker-compose.yml render.yaml
git add .github/workflows/ci.yml .github/workflows/cd.yml
git add README.md
git commit -m "feat: application wiring, Docker, CI/CD, documentation"
```

---

### Task 9: Database Migrations & Seeding

**Files:**
- Create: `alembic/versions/..._initial_schema.py`
- Create: `scripts/seed.py`

- [ ] **Step 9.1: Generate initial migration**

```bash
# Run: alembic revision --autogenerate -m "initial_schema"
# Expected: Creates migration file with all tables
```

- [ ] **Step 9.2: Create seed script**

```python
# scripts/seed.py
"""Database seeding script for development."""

import asyncio
import secrets
from passlib.context import CryptContext

from app.database import init_db, close_db, db
from app.models.api_key import APIKey

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed() -> None:
    await init_db()
    
    async with db.session() as session:
        # Check if keys exist
        from sqlalchemy import select
        result = await session.execute(select(APIKey))
        if result.scalars().first():
            print("Database already seeded")
            return
        
        # Create default API key
        plain_key = f"di_dev_{secrets.token_urlsafe(32)}"
        key_hash = pwd_context.hash(plain_key)
        
        api_key = APIKey(
            key_hash=key_hash,
            name="Development Key",
            rate_limit=100,
            is_active=True,
        )
        session.add(api_key)
        await session.commit()
        
        print(f"Created development API key: {plain_key}")
        print("SAVE THIS KEY - It won't be shown again!")
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 9.3: Run migration and seed**

```bash
# Run: alembic upgrade head && python scripts/seed.py
# Expected: Tables created, dev API key generated
```

- [ ] **Step 9.4: Commit migrations**

```bash
git add alembic/versions/ scripts/seed.py
git commit -m "feat: initial migration and seed script"
```

---

### Task 10: Security Hardening

**Files:**
- Create: `app/security/headers.py`
- Create: `app/security/validation.py`
- Modify: `app/main.py` (add security middleware)

- [ ] **Step 10.1: Create app/security/headers.py**

```python
# app/security/headers.py
"""Security headers middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # CSP for API (restrictive)
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "form-action 'none'"
        )
        
        # HSTS (only in production with HTTPS)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
```

- [ ] **Step 10.2: Create app/security/validation.py**

```python
# app/security/validation.py
"""Input validation and sanitization."""

import re
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status

from app.exceptions import ValidationError
from app.constants import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES


# Dangerous patterns for filename validation
DANGEROUS_PATTERNS = [
    r"\.\./",           # Path traversal
    r"\.\.\\",          # Windows path traversal
    r"[<>:\"|?*]",      # Windows reserved chars
    r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$",  # Windows reserved names
]


def validate_filename(filename: str) -> str:
    """Validate and sanitize filename."""
    if not filename or not filename.strip():
        raise ValidationError("Filename is required")
    
    filename = filename.strip()
    
    # Check length
    if len(filename) > 255:
        raise ValidationError("Filename too long (max 255 characters)")
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            raise ValidationError("Filename contains invalid characters")
    
    # Allow only safe characters
    if not re.match(r'^[\w\s\-_\(\)\[\]\.]+$', filename):
        raise ValidationError("Filename contains invalid characters")
    
    return filename


def validate_file_content(file: UploadFile, content: bytes) -> None:
    """Validate uploaded file content."""
    
    # Check file size
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File size exceeds maximum of {MAX_FILE_SIZE_BYTES / (1024*1024)}MB",
            details={"file_size": len(content), "max_size": MAX_FILE_SIZE_BYTES},
        )
    
    if len(content) == 0:
        raise ValidationError("File is empty")
    
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Unsupported file type: {file.content_type}",
            details={"allowed_types": ALLOWED_MIME_TYPES},
        )
    
    # Basic magic byte validation
    _validate_magic_bytes(content, file.content_type)


def _validate_magic_bytes(content: bytes, mime_type: str) -> None:
    """Validate file magic bytes match declared MIME type."""
    
    magic_bytes = {
        "application/pdf": [b"%PDF"],
        "image/png": [b"\x89PNG\r\n\x1a\n"],
        "image/jpeg": [b"\xff\xd8\xff"],
        "image/tiff": [b"II*\x00", b"MM\x00*"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
    }
    
    if mime_type in magic_bytes:
        valid = any(content.startswith(magic) for magic in magic_bytes[mime_type])
        if not valid:
            raise ValidationError(
                f"File content does not match declared type: {mime_type}"
            )


def sanitize_text(text: str, max_length: int = 100000) -> str:
    """Sanitize text for LLM processing."""
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "\n\n[TRUNCATED]"
    
    return text
```

- [ ] **Step 10.3: Update app/main.py with security middleware**

```python
# In app/main.py, add to imports:
from app.security.headers import SecurityHeadersMiddleware

# In create_app(), add before CORS:
app.add_middleware(SecurityHeadersMiddleware)
```

- [ ] **Step 10.4: Update upload route with validation**

```python
# In app/routes/upload.py, update upload_document:
from app.security.validation import validate_filename, validate_file_content

# After reading content:
validate_filename(file.filename)
validate_file_content(file, content)
```

- [ ] **Step 10.5: Run security tests**

```bash
# Create: tests/test_security.py
# Run: pytest tests/test_security.py -v
```

- [ ] **Step 10.6: Commit security hardening**

```bash
git add app/security/ app/main.py app/routes/upload.py
git add tests/test_security.py
git commit -m "feat: security hardening - headers, validation, sanitization"
```

---

### Task 11: Advanced Observability

**Files:**
- Create: `app/observability/metrics.py`
- Create: `app/observability/tracing.py`
- Create: `grafana/dashboards/api-dashboard.json`

- [ ] **Step 11.1: Create app/observability/metrics.py**

```python
# app/observability/metrics.py
"""Custom business metrics."""

from prometheus_client import Counter, Histogram, Gauge, Info

# Business metrics
documents_uploaded = Counter(
    "docintel_documents_uploaded_total",
    "Total documents uploaded",
    ["status", "mime_type"],
)

documents_processed = Counter(
    "docintel_documents_processed_total",
    "Total documents processed",
    ["status"],
)

document_processing_duration = Histogram(
    "docintel_document_processing_duration_seconds",
    "Document processing duration",
    buckets=[1, 2, 5, 10, 30, 60, 120, 300],
)

llm_tokens_consumed = Counter(
    "docintel_llm_tokens_consumed_total",
    "Total LLM tokens consumed",
    ["model", "type"],  # input/output
)

llm_request_duration = Histogram(
    "docintel_llm_request_duration_seconds",
    "LLM request duration",
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
)

active_documents = Gauge(
    "docintel_active_documents",
    "Documents currently being processed",
)

api_key_usage = Counter(
    "docintel_api_key_usage_total",
    "API key usage",
    ["key_id", "endpoint"],
)

storage_operations = Counter(
    "docintel_storage_operations_total",
    "Storage operations",
    ["operation", "provider", "status"],
)

storage_size_bytes = Gauge(
    "docintel_storage_size_bytes",
    "Total storage size in bytes",
    ["provider"],
)

# Application info
app_info = Info("docintel_app", "Application information")
app_info.info({"version": "1.0.0", "service": "document-intelligence-api"})
```

- [ ] **Step 11.2: Create app/observability/tracing.py**

```python
# app/observability/tracing.py
"""Custom tracing utilities."""

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from contextlib import contextmanager
from typing import Optional

tracer = trace.get_tracer(__name__)


@contextmanager
def trace_operation(name: str, attributes: Optional[dict] = None):
    """Context manager for tracing operations."""
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attributes(**attributes) -> None:
    """Add attributes to current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_error(error: Exception, attributes: Optional[dict] = None) -> None:
    """Record error on current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
```

- [ ] **Step 11.3: Create Grafana dashboard**

```json
{
  "dashboard": {
    "title": "Document Intelligence API",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {"expr": "rate(http_requests_total[5m])", "legendFormat": "{{method}} {{endpoint}}"}
        ]
      },
      {
        "title": "Request Latency (p95)",
        "type": "graph",
        "targets": [
          {"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))", "legendFormat": "p95"}
        ]
      },
      {
        "title": "Documents Uploaded",
        "type": "graph",
        "targets": [
          {"expr": "rate(docintel_documents_uploaded_total[5m])", "legendFormat": "{{status}}"}
        ]
      },
      {
        "title": "Documents Processed",
        "type": "graph",
        "targets": [
          {"expr": "rate(docintel_documents_processed_total[5m])", "legendFormat": "{{status}}"}
        ]
      },
      {
        "title": "LLM Tokens Consumed",
        "type": "graph",
        "targets": [
          {"expr": "rate(docintel_llm_tokens_consumed_total[5m])", "legendFormat": "{{model}} {{type}}"}
        ]
      },
      {
        "title": "Processing Duration",
        "type": "graph",
        "targets": [
          {"expr": "histogram_quantile(0.95, rate(docintel_document_processing_duration_seconds_bucket[5m]))", "legendFormat": "p95"}
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {"expr": "rate(http_requests_total{status=~\"5..\"}[5m])", "legendFormat": "5xx"}
        ]
      },
      {
        "title": "Active Documents",
        "type": "graph",
        "targets": [
          {"expr": "docintel_active_documents", "legendFormat": "active"}
        ]
      }
    ]
  }
}
```

- [ ] **Step 11.4: Integrate metrics in services**

```python
# Update app/services/llm.py, storage.py, extractor.py, tasks/processor.py
# to use custom metrics from app.observability.metrics
```

- [ ] **Step 11.5: Commit observability**

```bash
git add app/observability/ grafana/
git commit -m "feat: custom business metrics and Grafana dashboard"
```

---

### Task 12: Final Integration Tests & Polish

**Files:**
- Create: `tests/integration/test_full_flow.py`
- Create: `tests/load/locustfile.py`
- Modify: Multiple files for final polish

- [ ] **Step 12.1: Create integration test**

```python
# tests/integration/test_full_flow.py
"""End-to-end integration tests."""

import pytest
from uuid import uuid4
from httpx import AsyncClient

from app.models.api_key import APIKey


class TestFullDocumentFlow:
    """Test complete document upload -> process -> query flow."""
    
    @pytest.mark.asyncio
    async def test_full_flow(
        self, client: AsyncClient, auth_headers: dict, test_api_key: APIKey
    ):
        # 1. Upload document
        files = {"file": ("test.txt", b"This is a test document about Microsoft Azure and cloud computing.", "text/plain")}
        
        upload_response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]
        
        # 2. Trigger processing
        process_response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": document_id},
            headers=auth_headers,
        )
        assert process_response.status_code == 202
        
        # 3. Poll for completion (in test, we can run the task directly)
        from app.tasks.processor import process_document_task
        await process_document_task(document_id)
        
        # 4. Query results
        query_response = await client.get(
            f"/api/v1/query/documents/{document_id}",
            headers=auth_headers,
        )
        assert query_response.status_code == 200
        data = query_response.json()
        
        assert data["document_id"] == document_id
        assert "summary" in data
        assert "key_points" in data
        assert "entities" in data
        assert "sentiment" in data
        assert "topics" in data
        assert data["tokens_used"] > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(
        self, client: AsyncClient, auth_headers: dict
    ):
        # Make requests up to limit
        for i in range(11):  # Limit is 10
            response = await client.get("/api/v1/query/stats", headers=auth_headers)
            if i < 10:
                assert response.status_code == 200
            else:
                assert response.status_code == 429
                assert "Retry-After" in response.headers
```

- [ ] **Step 12.2: Create load test**

```python
# tests/load/locustfile.py
"""Locust load test configuration."""

from locust import HttpUser, task, between
import random


class DocumentIntelligenceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # In real test, use a pre-created API key
        self.headers = {"Authorization": "Bearer di_test_key"}
    
    @task(3)
    def query_stats(self):
        self.client.get("/api/v1/query/stats", headers=self.headers)
    
    @task(2)
    def list_documents(self):
        self.client.get("/api/v1/documents/list", headers=self.headers)
    
    @task(1)
    def upload_document(self):
        files = {"file": ("test.txt", b"Load test document content " * 100, "text/plain")}
        self.client.post("/api/v1/documents/upload", files=files, headers=self.headers)
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
```

- [ ] **Step 12.3: Run integration tests**

```bash
# Run: pytest tests/integration/ -v
# Expected: All integration tests pass
```

- [ ] **Step 12.4: Final code quality checks**

```bash
# Run: ruff check . && mypy app/ && pytest --cov=app --cov-fail-under=85
# Expected: All checks pass
```

- [ ] **Step 12.5: Final commit**

```bash
git add .
git commit -m "feat: complete implementation with integration tests and load testing"
```

---

## Execution Summary

### Total Tasks: 12
### Estimated Duration: 2-3 weeks (compressed to 1-2 weeks with focus)

### Microsoft-Recruiter Highlights Checklist

| Category | Implemented |
|----------|-------------|
| **Clean Architecture** | Domain-driven, dependency inversion, separation of concerns |
| **Azure-Native** | Azure Blob, Key Vault, Monitor, PostgreSQL, Container Apps |
| **Observability** | OpenTelemetry tracing, Prometheus metrics, structured logging, Grafana dashboards |
| **Security** | bcrypt API keys, rate limiting, input validation, security headers, magic byte checking |
| **Testing** | Unit (services), Integration (API), Contract (schemas), Load (Locust), ≥85% coverage |
| **CI/CD** | GitHub Actions → Render, multi-stage Docker, security scanning |
| **Documentation** | OpenAPI/Swagger, README with architecture diagram, API examples |
| **Production Patterns** | Health probes, graceful shutdown, correlation IDs, background tasks, migrations |

---

**Plan saved to:** `docs/superpowers/plans/2026-07-13-document-intelligence-api.md`

---

### Next Steps

**Choose execution approach:**

1. **Subagent-Driven** (recommended) - I dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** - Execute tasks in this session using `executing-plans` skill

**Which approach?**