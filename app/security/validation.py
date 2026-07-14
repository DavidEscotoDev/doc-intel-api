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
    r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..+)?$",  # Windows reserved names (with or without extension)
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

    # Cross-check: reject content that matches a different known type
    for known_type, magics in magic_bytes.items():
        if known_type == mime_type:
            continue
        if any(content.startswith(magic) for magic in magics):
            raise ValidationError(
                f"File content appears to be {known_type}, not {mime_type}"
            )


def sanitize_text(text: str, max_length: int = 100000) -> str:
    """Sanitize text for LLM processing."""
    # Remove null bytes
    text = text.replace("\x00", "")

    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "\n\n[TRUNCATED]"

    return text