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

# Allowed MIME types for upload
ALLOWED_MIME_TYPES = [m.value for m in MimeType]

# API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Health check
HEALTH_CHECK_TIMEOUT = 5  # seconds