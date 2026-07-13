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