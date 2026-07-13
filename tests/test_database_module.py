# tests/test_database.py
"""Tests for database module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.database import Database, db, init_db, close_db, get_db_session, Base


class TestDatabase:
    """Test Database class."""

    def test_init(self) -> None:
        database = Database()
        assert database._engine is None
        assert database._session_factory is None

    @patch("app.database.create_async_engine")
    @patch("app.database.async_sessionmaker")
    @patch("app.database.get_settings")
    def test_initialize(
        self, mock_get_settings, mock_sessionmaker, mock_create_engine
    ) -> None:
        mock_settings = MagicMock()
        mock_settings.database.url = "sqlite+aiosqlite:///:memory:"
        mock_settings.database.pool_size = 10
        mock_settings.database.max_overflow = 20
        mock_settings.database.pool_timeout = 30
        mock_settings.database.pool_recycle = 3600
        mock_settings.database.echo = False
        mock_get_settings.return_value = mock_settings

        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine

        mock_factory = MagicMock(spec=async_sessionmaker)
        mock_sessionmaker.return_value = mock_factory

        database = Database()
        database.initialize()

        assert database._engine is mock_engine
        assert database._session_factory is mock_factory
        mock_create_engine.assert_called_once()
        mock_sessionmaker.assert_called_once_with(
            mock_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    def test_engine_property_not_initialized(self) -> None:
        database = Database()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            _ = database.engine

    def test_engine_property_initialized(self) -> None:
        database = Database()
        mock_engine = MagicMock(spec=AsyncEngine)
        database._engine = mock_engine
        assert database.engine is mock_engine

    def test_session_factory_property_not_initialized(self) -> None:
        database = Database()
        with pytest.raises(RuntimeError, match="Database not initialized"):
            _ = database.session_factory

    def test_session_factory_property_initialized(self) -> None:
        database = Database()
        mock_factory = MagicMock(spec=async_sessionmaker)
        database._session_factory = mock_factory
        assert database.session_factory is mock_factory

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        database = Database()
        mock_engine = AsyncMock(spec=AsyncEngine)
        database._engine = mock_engine

        await database.close()

        mock_engine.dispose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_no_engine(self) -> None:
        database = Database()
        # Should not raise
        await database.close()

    @pytest.mark.asyncio
    async def test_session_context_manager(self) -> None:
        database = Database()
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock(return_value=mock_session.__aenter__.return_value)
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        database._session_factory = mock_factory

        async with database.session() as session:
            assert session is mock_session

        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_session_rollback_on_exception(self) -> None:
        database = Database()
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        database._session_factory = mock_factory

        with pytest.raises(ValueError):
            async with database.session():
                raise ValueError("test error")

        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()


class TestGlobalDatabase:
    """Test global database instance."""

    def test_db_instance(self) -> None:
        assert isinstance(db, Database)


class TestInitDb:
    """Test init_db function."""

    @pytest.mark.asyncio
    @patch("app.database.db")
    async def test_init_db(self, mock_db) -> None:
        mock_db.initialize = MagicMock()
        mock_engine = AsyncMock()
        mock_db.engine = mock_engine
        mock_conn = AsyncMock()
        mock_engine.begin = MagicMock(return_value=mock_conn)
        mock_conn.run_sync = AsyncMock()

        await init_db()

        mock_db.initialize.assert_called_once()
        mock_conn.run_sync.assert_awaited_once_with(Base.metadata.create_all)


class TestCloseDb:
    """Test close_db function."""

    @pytest.mark.asyncio
    @patch("app.database.db")
    async def test_close_db(self, mock_db) -> None:
        mock_db.close = AsyncMock()

        await close_db()

        mock_db.close.assert_awaited_once()


class TestGetDbSession:
    """Test get_db_session dependency."""

    @pytest.mark.asyncio
    @patch("app.database.db")
    async def test_get_db_session(self, mock_db) -> None:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db.session = AsyncMock()
        mock_db.session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.session.__aexit__ = AsyncMock(return_value=None)

        async for session in get_db_session():
            assert session is mock_session