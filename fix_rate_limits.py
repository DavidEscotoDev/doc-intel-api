import re

# Fix test_routes_auth.py
with open('tests/test_routes_auth.py', 'r') as f:
    c = f.read()

# Fix rate limit tests to use 100 instead of 10
c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_create_key_rate_limited(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on create key endpoint."""
        for i in range(10):
            response = await client.post(
                "/api/v1/auth/keys",
                json={"name": f"Key {i}"},
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_201_CREATED

        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Rate Limited Key"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_create_key_rate_limited(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on create key endpoint."""
        for i in range(100):
            response = await client.post(
                "/api/v1/auth/keys",
                json={"name": f"Key {i}"},
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_201_CREATED

        response = await client.post(
            "/api/v1/auth/keys",
            json={"name": "Rate Limited Key"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_list_keys_rate_limited(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on list keys endpoint."""
        for i in range(10):
            response = await client.get(
                "/api/v1/auth/keys",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/auth/keys",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_list_keys_rate_limited(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on list keys endpoint."""
        for i in range(100):
            response = await client.get(
                "/api/v1/auth/keys",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/auth/keys",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_get_key_rate_limited(self, client: AsyncClient, auth_headers: dict, test_api_key):
        """Test rate limiting on get key endpoint."""
        for i in range(10):
            response = await client.get(
                f"/api/v1/auth/keys/{test_api_key.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_get_key_rate_limited(self, client: AsyncClient, auth_headers: dict, test_api_key):
        """Test rate limiting on get key endpoint."""
        for i in range(100):
            response = await client.get(
                f"/api/v1/auth/keys/{test_api_key.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            f"/api/v1/auth/keys/{test_api_key.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_revoke_key_rate_limited(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on revoke key endpoint."""
        from app.models.api_key import APIKey
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        for i in range(10):
            key = APIKey(
                key_hash=pwd_context.hash(f"di_revoke_{i}"),
                name=f"Revoke Key {i}",
                rate_limit=100,
                is_active=True,
            )
            db_session.add(key)
        await db_session.commit()

        # Revoke 10 keys
        result = await db_session.execute(
            db_session.query(APIKey).where(APIKey.name.like("Revoke Key%")).limit(10)
        )
        keys = result.scalars().all()

        for i, key in enumerate(keys):
            response = await client.delete(
                f"/api/v1/auth/keys/{key.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT

        # Try to revoke another
        response = await client.delete(
            f"/api/v1/auth/keys/{keys[-1].id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_revoke_key_rate_limited(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on revoke key endpoint."""
        from app.models.api_key import APIKey
        from passlib.context import CryptContext
        from sqlalchemy import select

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        for i in range(100):
            key = APIKey(
                key_hash=pwd_context.hash(f"di_revoke_{i}"),
                name=f"Revoke Key {i}",
                rate_limit=100,
                is_active=True,
            )
            db_session.add(key)
        await db_session.commit()

        # Revoke 100 keys
        result = await db_session.execute(
            select(APIKey).where(APIKey.name.like("Revoke Key%")).limit(100)
        )
        keys = result.scalars().all()

        for i, key in enumerate(keys):
            response = await client.delete(
                f"/api/v1/auth/keys/{key.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT

        # Try to revoke another
        response = await client.delete(
            f"/api/v1/auth/keys/{keys[-1].id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

with open('tests/test_routes_auth.py', 'w') as f:
    f.write(c)
print('auth done')

# Fix test_routes_query.py
with open('tests/test_routes_query.py', 'r') as f:
    c = f.read()

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_query(self, client: AsyncClient, auth_headers: dict, test_document, test_analysis):
        """Test rate limiting on query endpoints."""
        # Make 10 requests (all should succeed with rate_limit=100)
        for i in range(10):
            response = await client.get(
                f"/api/v1/query/documents/{test_document.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # 11th request should be rate limited
        response = await client.get(
            f"/api/v1/query/documents/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_query(self, client: AsyncClient, auth_headers: dict, test_document, test_analysis):
        """Test rate limiting on query endpoints."""
        # Make 100 requests (test_api_key has rate_limit=100)
        for i in range(100):
            response = await client.get(
                f"/api/v1/query/documents/{test_document.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # 101st request should be rate limited
        response = await client.get(
            f"/api/v1/query/documents/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_list(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on document list endpoint."""
        for i in range(10):
            response = await client.get(
                "/api/v1/query/documents",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/query/documents",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_list(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on document list endpoint."""
        for i in range(100):
            response = await client.get(
                "/api/v1/query/documents",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/query/documents",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_stats(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on stats endpoint."""
        for i in range(10):
            response = await client.get(
                "/api/v1/query/stats",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/query/stats",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_stats(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on stats endpoint."""
        for i in range(100):
            response = await client.get(
                "/api/v1/query/stats",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/query/stats",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

with open('tests/test_routes_query.py', 'w') as f:
    f.write(c)
print('query done')

# Fix test_routes_process.py
with open('tests/test_routes_process.py', 'r') as f:
    c = f.read()

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_analyze(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on analyze endpoint."""
        from app.models.document import Document, DocumentStatus

        for i in range(10):
            doc = Document(
                filename=f"doc{i}.pdf",
                file_path=f"/tmp/doc{i}.pdf",
                mime_type="application/pdf",
                file_size=1024,
                status=DocumentStatus.UPLOADED,
                api_key_id=test_api_key.id,
            )
            db_session.add(doc)
        await db_session.commit()

        for i in range(10):
            result = await db_session.execute(
                db_session.query(Document).where(Document.filename == f"doc{i}.pdf")
            )
            doc = result.scalar_one()
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(doc.id)},
                headers=auth_headers,
            )
            assert response.status_code in (status.HTTP_202_ACCEPTED, status.HTTP_422_UNPROCESSABLE_ENTITY)

        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(doc.id)},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_rate_limiting_on_analyze(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on analyze endpoint."""
        from app.models.document import Document, DocumentStatus
        from sqlalchemy import select

        for i in range(100):
            doc = Document(
                filename=f"doc{i}.pdf",
                file_path=f"/tmp/doc{i}.pdf",
                mime_type="application/pdf",
                file_size=1024,
                status=DocumentStatus.UPLOADED,
                api_key_id=test_api_key.id,
            )
            db_session.add(doc)
        await db_session.commit()

        for i in range(100):
            result = await db_session.execute(
                select(Document).where(Document.filename == f"doc{i}.pdf")
            )
            doc = result.scalar_one()
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(doc.id)},
                headers=auth_headers,
            )
            assert response.status_code in (status.HTTP_202_ACCEPTED, status.HTTP_422_UNPROCESSABLE_ENTITY)

        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(doc.id)},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

with open('tests/test_routes_process.py', 'w') as f:
    f.write(c)
print('process done')

# Fix test_routes_upload.py
with open('tests/test_routes_upload.py', 'r') as f:
    c = f.read()

c = c.replace(
    '''    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on upload endpoint."""
        for i in range(10):
            file_content = b"%PDF-1.4\n%Test"
            files = {"file": (f"test{i}.pdf", BytesIO(file_content), "application/pdf")}
            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_201_CREATED

        # 11th request should be rate limited
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": ("test_rate_limit.pdf", BytesIO(file_content), "application/pdf")}
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS''',
    '''    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on upload endpoint."""
        for i in range(100):
            file_content = b"%PDF-1.4\n%Test"
            files = {"file": (f"test{i}.pdf", BytesIO(file_content), "application/pdf")}
            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_201_CREATED

        # 101st request should be rate limited
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": ("test_rate_limit.pdf", BytesIO(file_content), "application/pdf")}
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS'''
)

with open('tests/test_routes_upload.py', 'w') as f:
    f.write(c)
print('upload done')

print('All rate limit test fixes applied!')