"""Request logging middleware."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.logging import get_logger, setup_logging
from app.telemetry import http_requests_total, http_request_duration_seconds

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with correlation IDs."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Add to contextvars for structlog
        import contextvars
        correlation_var = contextvars.ContextVar("correlation_id", default=None)
        token = correlation_var.set(correlation_id)

        # Add to request state
        request.state.correlation_id = correlation_id

        start_time = time.time()

        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )

        try:
            response = await call_next(request)

            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Add rate limit headers if available
            if hasattr(request.state, "rate_limit_info"):
                info = request.state.rate_limit_info
                response.headers["X-Rate-Limit-Limit"] = str(info.limit)
                response.headers["X-Rate-Limit-Remaining"] = str(max(0, info.remaining))
                response.headers["X-Rate-Limit-Reset"] = str(info.reset)

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=int(duration * 1000),
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=int(duration * 1000),
            )

            # Record error metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500,
            ).inc()

            raise
        finally:
            correlation_var.reset(token)