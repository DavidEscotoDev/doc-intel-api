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
    from app.middleware.rate_limit import reset_rate_limiter, init_rate_limiter, get_rate_limiter
    from app.models.api_key import APIKey
    from passlib.context import CryptContext
    
    # Create a test API key with small rate limit
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    plain_key = "di_test_debug_123"
    key_hash = pwd_context.hash(plain_key)
    
    api_key = APIKey(
        key_hash=pwd_context.hash("di_test_debug_123"),
        name="Debug Rate Limit Key",
        rate_limit=5,
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)
    
    auth_headers_rl = {"Authorization": f"Bearer di_test_debug_123"}
    file_content = b"%PDF-1.4\n%Test"
    
    # Check rate limiter state
    limiter = get_rate_limiter()
    print(f"Backend requests before test: {len(limiter.backend._requests)}")
    
    # Make 5 requests (should all succeed with rate_limit=5)
    for i in range(6):
        files = {"file": ("test.pdf", BytesIO(b"%PDF-1.4\n%Test"), "application/pdf")}
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer di_test_debug_123"},
        )
        remaining = response.headers.get("x-rate-limit-remaining", "N/A")
        print(f"Request {i+1}: status={response.status_code}, remaining={response.headers.get('x-rate-limit-remaining', 'N/A')}")
        if response.status_code == 429:
            print(f"Rate limited at request {i+1}")
            break
        if i < 5:
            assert response.status_code == 201, f"Request {i+1} failed with {response.status_code}"
    
    # Check rate limiter state after test
    limiter = get_rate_limiter()
    print(f"Backend requests after test: {len(limiter.backend._requests)}")
    for k, v in limiter.backend._requests.items():
        print(f"  Key: {k}, count: {len(v)}")