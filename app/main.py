# app/main.py
"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.logging import setup_logging, get_logger
from app.telemetry import setup_telemetry


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
        description="AI-powered document analysis API",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # Include routers (will be added in later tasks)
    # app.include_router(health_router, prefix="/health")
    # app.include_router(documents_router, prefix=settings.API_PREFIX)
    # app.include_router(analysis_router, prefix=settings.API_PREFIX)
    # app.include_router(auth_router, prefix=settings.API_PREFIX)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "document-intelligence-api"}

    return app