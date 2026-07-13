# tests/test_exceptions.py
"""Tests for exceptions module."""

import pytest
from fastapi import HTTPException, status

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


class TestAppException:
    """Test base AppException."""

    def test_default_values(self) -> None:
        exc = AppException("Test error")
        assert exc.message == "Test error"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {}

    def test_custom_values(self) -> None:
        exc = AppException(
            "Custom error",
            code="CUSTOM_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "value"},
        )
        assert exc.message == "Custom error"
        assert exc.code == "CUSTOM_ERROR"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.details == {"field": "value"}

    def test_str_representation(self) -> None:
        exc = AppException("Test error")
        assert str(exc) == "Test error"


class TestValidationError:
    """Test ValidationError."""

    def test_defaults(self) -> None:
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_with_details(self) -> None:
        exc = ValidationError("Invalid input", details={"field": "email"})
        assert exc.details == {"field": "email"}


class TestAuthenticationError:
    """Test AuthenticationError."""

    def test_default_message(self) -> None:
        exc = AuthenticationError()
        assert exc.message == "Invalid or missing API key"
        assert exc.code == "AUTHENTICATION_ERROR"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_custom_message(self) -> None:
        exc = AuthenticationError("Custom auth error")
        assert exc.message == "Custom auth error"


class TestAuthorizationError:
    """Test AuthorizationError."""

    def test_default_message(self) -> None:
        exc = AuthorizationError()
        assert exc.message == "Insufficient permissions"
        assert exc.code == "AUTHORIZATION_ERROR"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_custom_message(self) -> None:
        exc = AuthorizationError("Custom authz error")
        assert exc.message == "Custom authz error"


class TestNotFoundError:
    """Test NotFoundError."""

    def test_constructor(self) -> None:
        exc = NotFoundError("Document", "123")
        assert exc.message == "Document not found: 123"
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.details == {"resource": "Document", "identifier": "123"}


class TestRateLimitError:
    """Test RateLimitError."""

    def test_constructor(self) -> None:
        exc = RateLimitError(60)
        assert exc.message == "Rate limit exceeded. Retry after 60 seconds."
        assert exc.code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.details == {"retry_after": 60}


class TestStorageError:
    """Test StorageError."""

    def test_constructor(self) -> None:
        exc = StorageError("Failed to upload", details={"path": "/tmp/file"})
        assert exc.message == "Failed to upload"
        assert exc.code == "STORAGE_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {"path": "/tmp/file"}


class TestProcessingError:
    """Test ProcessingError."""

    def test_constructor(self) -> None:
        exc = ProcessingError("Processing failed", details={"doc_id": "123"})
        assert exc.message == "Processing failed"
        assert exc.code == "PROCESSING_ERROR"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {"doc_id": "123"}


class TestLLMError:
    """Test LLMError."""

    def test_constructor(self) -> None:
        exc = LLMError("LLM timeout", details={"model": "claude-3"})
        assert exc.message == "LLM timeout"
        assert exc.code == "LLM_ERROR"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.details == {"model": "claude-3"}


class TestToHttpException:
    """Test to_http_exception function."""

    def test_conversion(self) -> None:
        exc = AppException(
            "Test error",
            code="TEST_CODE",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"key": "value"},
        )
        http_exc = to_http_exception(exc)

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == status.HTTP_400_BAD_REQUEST
        assert http_exc.detail == {
            "error": {
                "code": "TEST_CODE",
                "message": "Test error",
                "details": {"key": "value"},
            }
        }