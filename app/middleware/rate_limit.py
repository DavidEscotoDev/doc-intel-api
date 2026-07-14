"""Simple in-memory rate limiter."""
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, Request

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


class InMemoryRateLimiter:
    """Simple in-memory rate limiter (single instance only)."""

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

    def clear_all(self) -> None:
        """Clear all rate limit data (for testing)."""
        self._requests.clear()


# Global rate limiter instance
_rate_limiter: Optional[InMemoryRateLimiter] = None


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter()
    return _rate_limiter


async def init_rate_limiter() -> None:
    """Initialize rate limiter."""
    global _rate_limiter
    _rate_limiter = InMemoryRateLimiter()
    logger.info("rate_limiter_initialized", backend="InMemoryRateLimiter")


async def reset_rate_limiter() -> None:
    """Reset rate limiter for testing."""
    global _rate_limiter
    if _rate_limiter:
        _rate_limiter.clear_all()
    _rate_limiter = None


async def close_rate_limiter() -> None:
    """Close rate limiter (no-op for in-memory)."""
    global _rate_limiter
    _rate_limiter = None


async def rate_limit_dependency(
    request: Request,
    api_key = Depends(get_current_api_key),
) -> None:
    """FastAPI dependency for rate limiting."""
    limiter = get_rate_limiter()
    settings = get_settings()

    # Use API key ID as rate limit identifier
    identifier = f"apikey:{api_key.id}"

    info = await limiter.check_limit(identifier, settings.rate_limit_requests, settings.rate_limit_window)

    # Add rate limit headers
    request.state.rate_limit_info = info

    if info.remaining <= 0:
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