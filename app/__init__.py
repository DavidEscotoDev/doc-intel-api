# app/__init__.py
"""Document Intelligence API - Production-grade AI Document Analysis."""

__version__ = "1.0.0"
__author__ = "Document Intelligence Team"

from app.config import Settings, get_settings, load_yaml_config
from app.constants import (
    API_VERSION,
    API_PREFIX,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    MAX_FILE_SIZE_BYTES,
    MAX_TEXT_LENGTH,
    UPLOADED,
    PROCESSING,
    COMPLETED,
    FAILED,
    PDF,
    TXT,
    DOCX,
    PNG,
    JPEG,
    TIFF,
    ALLOWED_MIME_TYPES,
)
from app.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    RateLimitError,
    to_http_exception,
)
from app.logging import setup_logging, get_logger

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