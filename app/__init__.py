# app/__init__.py
"""Document Intelligence API - Production-grade AI Document Analysis."""

__version__ = "1.0.0"
__author__ = "Document Intelligence Team"

from app.config import Settings, get_settings, load_yaml_config
from app.constants import (
    DocumentStatus,
    StorageProvider,
    MimeType,
    API_VERSION,
    API_PREFIX,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    MAX_FILE_SIZE_BYTES,
    MAX_TEXT_LENGTH,
)
from app.exceptions import (
    AppException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    StorageError,
    ProcessingError,
    LLMError,
    to_http_exception,
)
from app.logging import setup_logging, get_logger
from app.telemetry import setup_telemetry, record_span_error

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "load_yaml_config",
    # Constants
    "DocumentStatus",
    "StorageProvider",
    "MimeType",
    "API_VERSION",
    "API_PREFIX",
    "DEFAULT_RATE_LIMIT_REQUESTS",
    "DEFAULT_RATE_LIMIT_WINDOW",
    "MAX_FILE_SIZE_BYTES",
    "MAX_TEXT_LENGTH",
    # Exceptions
    "AppException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "RateLimitError",
    "StorageError",
    "ProcessingError",
    "LLMError",
    "to_http_exception",
    # Logging
    "setup_logging",
    "get_logger",
    # Telemetry
    "setup_telemetry",
    "record_span_error",
]