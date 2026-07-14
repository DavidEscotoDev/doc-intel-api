# app/__init__.py
"""Document Intelligence API - Production-grade AI Document Analysis."""

__version__ = "1.0.0"
__author__ = "Document Intelligence Team"

from app.config import Settings, get_settings, load_yaml_config
from app.constants import (
    ALLOWED_MIME_TYPES,
    API_PREFIX,
    API_VERSION,
    COMPLETED,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    DOCX,
    FAILED,
    JPEG,
    MAX_FILE_SIZE_BYTES,
    MAX_TEXT_LENGTH,
    PDF,
    PNG,
    PROCESSING,
    TIFF,
    TXT,
    UPLOADED,
)
from app.exceptions import (
    AppException,
    NotFoundError,
    RateLimitError,
    ValidationError,
    to_http_exception,
)
from app.logging import get_logger, setup_logging

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "load_yaml_config",
    # Constants
    "API_VERSION",
    "API_PREFIX",
    "DEFAULT_RATE_LIMIT_REQUESTS",
    "DEFAULT_RATE_LIMIT_WINDOW",
    "MAX_FILE_SIZE_BYTES",
    "MAX_TEXT_LENGTH",
    "UPLOADED",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    "PDF",
    "TXT",
    "DOCX",
    "PNG",
    "JPEG",
    "TIFF",
    "ALLOWED_MIME_TYPES",
    # Exceptions
    "AppException",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "to_http_exception",
    # Logging
    "setup_logging",
    "get_logger",
]
