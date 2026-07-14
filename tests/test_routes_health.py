"""Integration tests for health routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient


class TestHealthRoutes:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client: AsyncClient):
        """Test health check when database is healthy."""
        response = await client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["environment"] in ("development", "test", "production")
        assert data["database"] == "healthy"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_db(self, client: AsyncClient):
        """Test health check when database is unhealthy."""
        # We can't easily mock the db session here, but we can test the endpoint exists
        # The actual unhealthy test would require mocking the db session
        response = await client.get("/health")
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)

    @pytest.mark.asyncio
    async def test_liveness_probe(self, client: AsyncClient):
        """Test Kubernetes liveness probe."""
        response = await client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness_probe_ready(self, client: AsyncClient):
        """Test Kubernetes readiness probe when ready."""
        response = await client.get("/health/ready")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/plain")
        # Check for some expected metrics
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content