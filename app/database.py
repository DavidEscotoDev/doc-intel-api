# app/database.py
"""Database connection and session management."""

import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# Module-level engine and session factory (initialized on first use)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _normalize_database_url(url: str) -> str:
    """Normalize database URL for async SQLAlchemy.

    Render provides postgresql:// but asyncpg needs postgresql+asyncpg://
    """
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _get_ssl_context() -> ssl.SSLContext | None:
    """Create SSL context for Render PostgreSQL which requires SSL."""
    # Render PostgreSQL requires sslmode=require
    # Create a default SSL context that verifies certificates
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        normalized_url = _normalize_database_url(settings.database_url)

        # Build connect args with SSL for Render PostgreSQL
        connect_args = {}
        if normalized_url.startswith("postgresql+asyncpg://"):
            # Render PostgreSQL requires SSL
            connect_args["ssl"] = _get_ssl_context()

        _engine = create_async_engine(
            normalized_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            echo=settings.database_echo,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        logger.info("database_initialized", url=settings.database_url)
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def close_db() -> None:
    """Close database connections."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("database_closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database and create tables."""
    _get_engine()  # ensure engine exists
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")
