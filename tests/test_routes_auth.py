"""Integration tests for auth routes."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


class TestAuthRoutes:
    """Test API key management endpoints."""

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, client: AsyncClient, auth_headers: dict):
        """Test creating a new API key."""
        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Test Key", "rate_limit": 50, "expires_in_days": 30},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert "key" in data
        assert data["name"] == "Test Key"
        assert data["rate_limit"] == 50
        assert data["is_active"] is True
        assert "created_at" in data
        assert "expires_at" in data
        assert data["key"].startswith("di_")

    @pytest.mark.asyncio
    async def test_create_api_key_defaults(self, client: AsyncClient, auth_headers: dict):
        """Test creating API key with default values."""
        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Default Key"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Default Key"
        assert data["rate_limit"] == 10  # default from config
        assert data["is_active"] is True
        assert data["expires_at"] is None

    @pytest.mark.asyncio
    async def test_create_api_key_no_expiration(self, client: AsyncClient, auth_headers: dict):
        """Test creating API key without expiration."""
        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "No Expiry Key"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["expires_at"] is None

    @pytest.mark.asyncio
    async def test_create_api_key_without_auth(self, client: AsyncClient):
        """Test creating API key without authentication."""
        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Test Key"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_api_keys(self, client: AsyncClient, auth_headers: dict, test_api_key):
        """Test listing all API keys."""
        response = await client.get(
            "/api/v1/auth/keys",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert any(k["id"] == str(test_api_key.id) for k in data["items"])

    @pytest.mark.asyncio
    async def test_list_api_keys_structure(self, client: AsyncClient, auth_headers: dict):
        """Test API key list response structure."""
        response = await client.get(
            "/api/v1/auth/keys",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)

        if data["items"]:
            key = data["items"][0]
            assert "id" in key
            assert "name" in key
            assert "rate_limit" in key
            assert "is_active" in key
            assert "created_at" in key
            assert "updated_at" in key
            assert "last_used_at" in key
            assert "total_requests" in key
            assert "expires_at" in key

    @pytest.mark.asyncio
    async def test_get_api_key_success(self, client: AsyncClient, auth_headers: dict, test_api_key):
        """Test getting a specific API key."""
        response = await client.get(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_api_key.id)
        assert data["name"] == test_api_key.name
        assert data["rate_limit"] == test_api_key.rate_limit
        assert data["is_active"] == test_api_key.is_active
        assert "key" not in data  # Key itself should not be returned

    @pytest.mark.asyncio
    async def test_get_api_key_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent API key."""
        response = await client.get(
            f"/api/v1/auth/keys/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test revoking an API key."""
        # Create another key to revoke
        from app.models.api_key import APIKey
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        key_to_revoke = APIKey(
            key_hash=pwd_context.hash("di_revoke_me"),
            name="Key to Revoke",
            rate_limit=100,
            is_active=True,
        )
        db_session.add(key_to_revoke)
        await db_session.commit()
        await db_session.refresh(key_to_revoke)

        response = await client.delete(
            f"/api/v1/auth/keys/{key_to_revoke.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify key is deactivated
        from sqlalchemy import select
        result = await db_session.execute(select(APIKey).where(APIKey.id == key_to_revoke.id))
        key = result.scalar_one()
        assert key.is_active is False

    @pytest.mark.asyncio
    async def test_revoke_self_prevention(self, client: AsyncClient, auth_headers: dict, test_api_key):
        """Test that user cannot revoke their own API key."""
        response = await client.delete(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "cannot revoke your own" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self, client: AsyncClient, auth_headers: dict):
        """Test revoking non-existent API key."""
        response = await client.delete(
            f"/api/v1/auth/keys/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_revoke_without_auth(self, client: AsyncClient, test_api_key):
        """Test revoking API key without authentication."""
        response = await client.delete(
            f"/api/v1/auth/keys/{test_api_key.id}",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_key_rate_limited(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on create key endpoint."""
        for i in range(99):
            response = await client.post(
                "/api/v1/auth/keys",
                json={"name": f"Key {i}"},
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_201_CREATED

        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Rate Limited Key"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_list_keys_rate_limited(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on list keys endpoint."""
        for i in range(99):
            response = await client.get(
                "/api/v1/auth/keys",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/auth/keys",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_get_key_rate_limited(self, client: AsyncClient, auth_headers: dict, test_api_key):
        """Test rate limiting on get key endpoint."""
        for i in range(99):
            response = await client.get(
                f"/api/v1/auth/keys/{test_api_key.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_revoke_key_rate_limited(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on revoke key endpoint."""
        from app.models.api_key import APIKey
        from passlib.context import CryptContext
        from sqlalchemy import select

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        for i in range(99):
            key = APIKey(
                key_hash=pwd_context.hash(f"di_revoke_{i}"),
                name=f"Revoke Key {i}",
                rate_limit=100,
                is_active=True,
            )
            db_session.add(key)
        await db_session.commit()

        # Revoke 100 keys
        result = await db_session.execute(
            select(APIKey).where(APIKey.name.like("Revoke Key%")).limit(100)
        )
        keys = result.scalars().all()

        for i, key in enumerate(keys):
            response = await client.delete(
                f"/api/v1/auth/keys/{key.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT

        # Try to revoke another
        response = await client.delete(
            f"/api/v1/auth/keys/{keys[-1].id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS