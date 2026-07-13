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