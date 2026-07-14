"""API Key authentication middleware."""
from datetime import UTC, datetime

from fastapi import Depends, Header, Request
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.exceptions import ValidationError, to_http_exception
from app.logging import get_logger
from app.models.api_key import APIKey

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_api_key(
    request: Request,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> APIKey:
    """Verify API key from Authorization header."""

    settings = get_settings()

    if not authorization:
        logger.warning(
            "auth_missing_header", client=request.client.host if request.client else "unknown"
        )
        raise to_http_exception(
            ValidationError("Invalid or missing API key", details={"code": "AUTHENTICATION_ERROR"})
        )

    # Expect "Bearer <key>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(
            "auth_invalid_format", client=request.client.host if request.client else "unknown"
        )
        raise to_http_exception(
            ValidationError(
                "Invalid authorization format. Use: Bearer <api_key>",
                details={"code": "AUTHENTICATION_ERROR"},
            )
        )

    api_key = parts[1]

    # Validate prefix
    if not api_key.startswith(settings.api_key_prefix):
        logger.warning(
            "auth_invalid_prefix", client=request.client.host if request.client else "unknown"
        )
        raise to_http_exception(
            ValidationError("Invalid API key format", details={"code": "AUTHENTICATION_ERROR"})
        )

    # Look up all active keys and verify hash
    result = await db.execute(select(APIKey).where(APIKey.is_active is True))
    keys = result.scalars().all()

    matched_key = None
    for key in keys:
        if pwd_context.verify(api_key, key.key_hash):
            matched_key = key
            break

    if not matched_key:
        logger.warning(
            "auth_key_not_found", client=request.client.host if request.client else "unknown"
        )
        raise to_http_exception(
            ValidationError("Invalid or missing API key", details={"code": "AUTHENTICATION_ERROR"})
        )

    # Check expiration
    if matched_key.expires_at and matched_key.expires_at < datetime.now(UTC):
        logger.warning("auth_key_expired", key_id=str(matched_key.id))
        raise to_http_exception(
            ValidationError("API key has expired", details={"code": "AUTHENTICATION_ERROR"})
        )

    # Update last used
    matched_key.last_used_at = datetime.now(UTC)
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
