# tests/conftest.py
"""Pytest configuration and fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db_session
from app.main import create_app
from app.middleware.rate_limit import init_rate_limiter, reset_rate_limiter
from app.models.api_key import APIKey
from app.models.document import Document

# Test settings
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["API_KEY_PREFIX"] = "di_"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Get test settings."""
    return get_settings()


@pytest.fixture()
async def db_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest.fixture()
def override_get_db(db_session: AsyncSession):
    """Override database dependency."""

    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest_asyncio.fixture(scope="function")
async def app(override_get_db):
    """Create FastAPI test app."""
    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db
    # Reset and initialize rate limiter for tests
    await reset_rate_limiter()
    await init_rate_limiter()
    return app


@pytest.fixture(autouse=True)
async def _reset_rate_limiter(app):
    """Automatically reset rate limiter before each test for isolation."""
    await reset_rate_limiter()
    await init_rate_limiter()


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def fake() -> Faker:
    """Faker instance for test data."""
    return Faker()


@pytest.fixture()
def mock_anthropic_client() -> MagicMock:
    """Mock Anthropic client."""
    client = MagicMock()
    client.messages.create = AsyncMock()
    return client


@pytest.fixture()
async def test_api_key(db_session: AsyncSession) -> APIKey:
    """Create a test API key."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    plain_key = "di_testkey123"
    key_hash = pwd_context.hash(plain_key)

    api_key = APIKey(
        key_hash=key_hash,
        name="Test Key",
        rate_limit=100,
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    return api_key


@pytest.fixture()
def auth_headers(test_api_key: APIKey) -> dict[str, str]:
    """Authorization headers for test API key."""
    return {"Authorization": "Bearer di_testkey123"}


@pytest.fixture()
async def test_document(db_session: AsyncSession, test_api_key: APIKey) -> Document:
    """Create a test document."""
    doc = Document(
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status="uploaded",
        api_key_id=test_api_key.id,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc


@pytest.fixture()
async def test_completed_document(db_session: AsyncSession, test_api_key: APIKey) -> Document:
    """Create a test completed document with analysis."""
    doc = Document(
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status="completed",
        api_key_id=test_api_key.id,
        summary="Test summary",
        key_points=["Point 1", "Point 2"],
        entities=["Entity 1"],
        sentiment="positive",
        topics=["Topic 1"],
        tokens_used=100,
        model_version="claude-3-5-sonnet-20241022",
        processing_time_ms=5000,
        raw_response={"content": "raw"},
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc
