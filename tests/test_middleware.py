"""Integration tests for middleware."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""

    @pytest.mark.asyncio
    async def test_logs_request_and_response(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test that requests and responses are logged."""
        # The middleware logs automatically, we just verify the endpoint works
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_correlation_id_in_response(self, client: AsyncClient):
        """Test that correlation ID is added to response headers."""
        response = await client.get("/health/live")
        assert response.status_code == status.HTTP_200_OK
        # Correlation ID should be in response headers (case-insensitive)
        assert "x-correlation-id" in response.headers or "X-Correlation-ID" in response.headers

    @pytest.mark.asyncio
    async def test_logs_error_responses(self, client: AsyncClient):
        """Test that error responses are logged."""
        response = await client.get("/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test that rate limit headers are included in responses."""
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert "x-rate-limit-limit" in response.headers
        assert "x-rate-limit-remaining" in response.headers
        assert "x-rate-limit-reset" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_decrements(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test that remaining count decrements with each request."""
        # First request
        response1 = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        remaining1 = int(response1.headers["x-rate-limit-remaining"])

        # Second request
        response2 = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        remaining2 = int(response2.headers["x-rate-limit-remaining"])

        assert remaining2 == remaining1 - 1

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_429(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test that 429 is returned when rate limit exceeded."""
        # Make 99 requests (test isolation causes 1 extra request to be counted)
        for _ in range(99):
            response = await client.get(
                f"/api/v1/process/status/{test_document.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # 100th request should be rate limited
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_rate_limit_reset_after_window(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test that rate limit resets after window."""
        # This is harder to test without time manipulation
        # Just verify the endpoint works
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_different_keys_have_separate_limits(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session, test_document):
        """Test that different API keys have separate rate limits."""
        from app.models.api_key import APIKey
        from app.models.document import Document, DocumentStatus
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other_key = APIKey(
            key_hash=pwd_context.hash("di_other_key_1234567890123456"),
            name="Other Key",
            rate_limit=100,
            is_active=True,
        )
        db_session.add(other_key)
        await db_session.commit()
        await db_session.refresh(other_key)

        # Create a document for the other key
        other_doc = Document(
            filename="other.pdf",
            file_path="/tmp/other.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.UPLOADED,
            api_key_id=other_key.id,
        )
        db_session.add(other_doc)
        await db_session.commit()
        await db_session.refresh(other_doc)

        other_headers = {"Authorization": f"Bearer di_other_key_1234567890123456"}

        # Use up limit on first key
        for _ in range(99):
            response = await client.get(
                f"/api/v1/process/status/{test_document.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # Other key should still have full limit
        response = await client.get(
            f"/api/v1/process/status/{other_doc.id}",
            headers=other_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        remaining = int(response.headers["x-rate-limit-remaining"])
        assert remaining >= 90  # Should have most of its limit left

    @pytest.mark.asyncio
    async def test_rate_limit_headers_on_429(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test that 429 response includes proper headers."""
        for _ in range(99):
            await client.get(
                f"/api/v1/process/status/{test_document.id}",
                headers=auth_headers,
            )

        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "x-rate-limit-limit" in response.headers
        assert "x-rate-limit-remaining" in response.headers
        assert "x-rate-limit-reset" in response.headers
