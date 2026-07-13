# app/main.py
"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.logging import setup_logging, get_logger
from app.telemetry import setup_telemetry
from app.routes import upload, process, query, health, auth
from app.middleware.logging import RequestLoggingMiddleware
from app.security.headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()

    # Setup logging
    setup_logging(log_level=settings.log_level, json_logs=settings.is_production)
    logger.info("application_starting", env=settings.env)

    # Setup telemetry
    setup_telemetry(
        service_name=settings.otel_service_name,
        enable_azure_monitor=bool(settings.azure.monitor_connection_string),
        azure_connection_string=settings.azure.monitor_connection_string,
    )
    logger.info("telemetry_initialized")

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    yield

    # Shutdown
    await close_db()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Document Intelligence API",
        description="AI-powered document analysis API with Claude",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Security headers (first, so they apply to all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers
    app.include_router(health.router, prefix="")
    app.include_router(upload.router, prefix="/api/v1")
    app.include_router(process.router, prefix="/api/v1")
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers if not settings.is_development else 1,
    )