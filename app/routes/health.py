"""Health check endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db_session
from app.logging import get_logger
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> HealthResponse:
    """Comprehensive health check."""

    settings = get_settings()
    db_status = "healthy"

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        logger.error("health_check_db_failed", error=str(e))
        response.status_code = 503

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        environment=settings.env,
        database=db_status,
        timestamp=datetime.now(UTC),
    )


@router.get("/health/live")
async def liveness_probe() -> dict:
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Kubernetes readiness probe."""

    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Not ready")


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
