"""Rate limiting tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.middleware.rate_limit import (
    InMemoryRateLimiter,
    RateLimiter,
    RateLimitInfo,
)
from app.models.api_key import APIKey


class TestInMemoryRateLimiter:
    """Test in-memory rate limiter."""

    @pytest.fixture
    def limiter(self):
        return InMemoryRateLimiter()

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self, limiter):
        info = await limiter.check_limit("test_key", limit=5, window=60)

        assert info.limit == 5
        assert info.remaining == 4
        assert info.retry_after is None

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self, limiter):
        # Make 5 requests
        for i in range(5):
            info = await limiter.check_limit("test_key", limit=5, window=60)
            assert info.remaining == 4 - i

        # 6th should be blocked
        info = await limiter.check_limit("test_key", limit=5, window=60)

        assert info.remaining == 0
        assert info.retry_after is not None
        assert info.retry_after > 0

    @pytest.mark.asyncio
    async def test_different_keys_independent(self, limiter):
        await limiter.check_limit("key1", limit=2, window=60)
        await limiter.check_limit("key1", limit=2, window=60)

        # key2 should still have full limit
        info = await limiter.check_limit("key2", limit=2, window=60)
        assert info.remaining == 1

    @pytest.mark.asyncio
    async def test_reset_clears_limit(self, limiter):
        await limiter.check_limit("test_key", limit=1, window=60)
        info = await limiter.check_limit("test_key", limit=1, window=60)
        assert info.remaining == 0

        await limiter.reset("test_key")
        info = await limiter.check_limit("test_key", limit=1, window=60)
        assert info.remaining == 0  # First request after reset


class TestRateLimiter:
    """Test high-level rate limiter."""

    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock()
        backend.check_limit = AsyncMock(return_value=RateLimitInfo(
            limit=10, remaining=9, reset=1234567890
        ))
        return backend

    @pytest.fixture
    def limiter(self, mock_backend):
        return RateLimiter(mock_backend)

    @pytest.mark.asyncio
    async def test_check_uses_backend(self, limiter, mock_backend):
        await limiter.check("test_key", limit=10, window=60)

        mock_backend.check_limit.assert_called_once_with("test_key", 10, 60)

    @pytest.mark.asyncio
    async def test_check_uses_defaults(self, mock_backend):
        with patch("app.middleware.rate_limit.get_settings") as mock_settings:
            mock_auth = MagicMock()
            mock_auth.rate_limit_requests = 20
            mock_auth.rate_limit_window = 120
            mock_settings.return_value.auth = mock_auth

            limiter = RateLimiter(mock_backend)
            await limiter.check("test_key")

            call_args = mock_backend.check_limit.call_args
            assert call_args[0][1] == 20
            assert call_args[0][2] == 120