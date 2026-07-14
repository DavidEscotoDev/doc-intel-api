"""Debug test for rate limiter behavior."""
import pytest
from httpx import AsyncClient
from io import BytesIO
from app.main import create_app
from app.middleware.rate_limit import reset_rate_limiter, init_rate_limiter, get_rate_limiter
from app.database import get_db_session, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models.api_key import APIKey
from passlib.context import CryptContext


@pytest.mark.asyncio
async def test_rate_limiter_debug(client: AsyncClient, auth_headers: dict, test_api_key, db_session):
    """Debug test to understand rate limiter behavior."""
    from app.middleware.rate_limit import reset_rate_limiter, init_rate_limiter, get_rate_limiter, _rate_limiter as rl_module
    
    # Create a test API key with small rate limit
    from app.models.api_key import APIKey
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    key_hash = pwd_context.hash("di_test_debug_123")
    api_key = APIKey(
        key_hash=key_hash,
        name="Debug Rate Limit Key",
        rate_limit=5,
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    
    auth_headers_rl = {"Authorization": "Bearer di_test_debug_123"}
    file_content = b"%PDF-1.4\n%Test"
    
    # Check rate limiter state before test
    limiter = get_rate_limiter()
    print(f"Initial backend requests: {len(limiter.backend._requests)}")
    
    # Make 4 requests (should all succeed with rate_limit=5, but rate limiter allows limit-1)
    for i in range(4):
        files = {"file": ("test.pdf", BytesIO(b"%PDF-1.4\n%Test"), "application/pdf")}
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer di_test_debug_123"},
        )
        remaining = response.headers.get("x-rate-limit-remaining", "N/A")
        print(f"Request {i+1}: status={response.status_code}, remaining={response.headers.get('x-rate-limit-remaining', 'N/A')}")
        assert response.status_code == 201, f"Request {i+1} failed with {response.status_code}"
    
    # 5th request should be rate limited
    files = {"file": ("test.pdf", BytesIO(b"%PDF-1.4\n%Test"), "application/pdf")}
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", BytesIO(b"%PDF-1.4\n%Test"), "application/pdf")},
        headers={"Authorization": "Bearer di_test_debug_123"},
    )
    print(f"5th request: status={response.status_code}, remaining={response.headers.get('x-rate-limit-remaining', 'N/A')}")
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"