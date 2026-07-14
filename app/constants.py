# app/constants.py
"""Application constants - simple module-level values."""

# Document processing status
DocumentStatus = str
UPLOADED = "uploaded"
PROCESSING = "processing"
COMPLETED = "completed"
FAILED = "failed"

# MIME types
PDF = "application/pdf"
TXT = "text/plain"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PNG = "image/png"
JPEG = "image/jpeg"
TIFF = "image/tiff"

ALLOWED_MIME_TYPES = [PDF, TXT, DOCX, PNG, JPEG, TIFF]

# File processing
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MAX_TEXT_LENGTH = 100_000  # characters sent to LLM

# Rate limiting defaults
DEFAULT_RATE_LIMIT_REQUESTS = 10
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

# API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Health check
HEALTH_CHECK_TIMEOUT = 5  # seconds
