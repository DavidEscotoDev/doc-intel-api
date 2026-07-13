"""Rate limiting middleware with in-memory and Redis backends."""
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from contextlib import asynccontextmanager

from app.config import get_settings
from app.middleware.auth import get_current_api_key
from app.exceptions import RateLimitError, to_http_exception
from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for response headers."""
    limit: int
    remaining: int
    reset: int
    retry_after: Optional[int] = None


class RateLimitBackend(ABC):
    """Abstract rate limit backend."""

    @abstractmethod
    async def check_limit(self, key: str, limit: int, window: int) -> RateLimitInfo:
        """Check and increment rate limit. Returns limit info."""
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        pass


class InMemoryRateLimiter(RateLimitBackend):
    """In-memory rate limiter (single instance only)."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def check_limit(self, key: str, limit: int, window: int) -> RateLimitInfo:
        now = time.time()
        window_start = now - window

        # Clean old entries
        self._requests[key] = [ts for ts in self._requests[key] if ts > window_start]

        current = len(self._requests[key])

        if current >= limit:
            oldest = min(self._requests[key]) if self._requests[key] else now
            retry_after = int(oldest + window - now) + 1
            return RateLimitInfo(
                limit=limit,
                remaining=0,
                reset=int(oldest + window),
                retry_after=retry_after,
            )

        self._requests[key].append(now)

        return RateLimitInfo(
            limit=limit,
            remaining=limit - current - 1,
            reset=int(now + window),
        )

    async def reset(self, key: str) -> None:
        if key in self._requests:
            del self._requests[key]


class RedisRateLimiter(RateLimitBackend):
    """Redis-backed rate limiter (distributed)."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def check_limit(self, key: str, limit: int, window: int) -> RateLimitInfo:
        client = await self._get_client()
        redis_key = f"ratelimit:{key}"

        now = time.time()
        window_start = now - window

        # Use sorted set with timestamps as scores
        pipe = client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window + 1)
        results = await pipe.execute()

        current = results[1]

        if current >= limit:
            oldest_entries = await client.zrange(redis_key, 0, 0, withscores=True)
            if oldest_entries:
                oldest_ts = oldest_entries[0][1]
                retry_after = int(oldest_ts + window - now) + 1
            else:
                retry_after = window

            return RateLimitInfo(
                limit=limit,
                remaining=0,
                reset=int(now + window),
                retry_after=retry_after,
            )

        return RateLimitInfo(
            limit=limit,
            remaining=limit - current - 1,
            reset=int(now + window),
        )

    async def reset(self, key: str) -> None:
        client = await self._get_client()
        await client.delete(f"ratelimit:{key}")

    async def close(self) -> None:
        if self._client:
            await self._client.close()


class RateLimiter:
    """High-level rate limiter."""

    def __init__(self, backend: RateLimitBackend) -> None:
        self.backend = backend
        self.settings = get_settings()

    async def check(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> RateLimitInfo:
        """Check rate limit for identifier."""
        limit = limit or self.settings.auth.rate_limit_requests
        window = window or self.settings.auth.rate_limit_window

        return await self.backend.check_limit(identifier, limit, window)


# Global rate limiter (initialized in main.py)
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized")
    return _rate_limiter


async def init_rate_limiter() -> None:
    """Initialize rate limiter based on configuration."""
    global _rate_limiter
    settings = get_settings()

    if settings.env == "production" and hasattr(settings, "redis_url") and settings.redis_url:
        backend = RedisRateLimiter(settings.redis_url)
    else:
        backend = InMemoryRateLimiter()

    _rate_limiter = RateLimiter(backend)
    logger.info("rate_limiter_initialized", backend=type(backend).__name__)


async def close_rate_limiter() -> None:
    """Close rate limiter connections."""
    global _rate_limiter
    if _rate_limiter and hasattr(_rate_limiter.backend, "close"):
        await _rate_limiter.backend.close()
    _rate_limiter = None


async def rate_limit_dependency(
    request: Request,
    api_key = Depends(get_current_api_key),
) -> None:
    """FastAPI dependency for rate limiting."""
    limiter = get_rate_limiter()

    # Use API key ID as rate limit identifier
    identifier = f"apikey:{api_key.id}"

    info = await limiter.check(identifier, api_key.rate_limit)

    # Add rate limit headers
    request.state.rate_limit_info = info

    if info.remaining < 0:
        logger.warning(
            "rate_limit_exceeded",
            api_key_id=str(api_key.id),
            limit=info.limit,
        )
        raise to_http_exception(RateLimitError(info.retry_after or 60))

    logger.debug(
        "rate_limit_checked",
        api_key_id=str(api_key.id),
        remaining=info.remaining,
    )