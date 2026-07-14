f=open('tests/test_middleware.py')
c=f.read()
f.close()

old = """    @pytest.mark.asyncio
    async def test_different_keys_have_separate_limits(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session, test_document):
        \"\"\"Test that different API keys have separate rate limits.\"\"\"
        from app.models.api_key import APIKey
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other_key = APIKey(
            key_hash=pwd_context.hash("di_other_key_1234567890123456"),
            name="Other Key",
            rate_limit=100,
            is_active=True,
        )
        db_session.add(other_key)
        await db_session.commit()
        await db_session.refresh(other_key)

        other_headers = {"Authorization": f"Bearer di_other_key_1234567890123456"}

        # Use up limit on first key
        for _ in range(99):
            response = await client.get(
                f"/api/v1/process/status/{test_document.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # Other key should still have full limit
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=other_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        remaining = int(response.headers["x-rate-limit-remaining"])
        assert remaining >= 90  # Should have most of its limit left"""

new = """    @pytest.mark.asyncio
    async def test_different_keys_have_separate_limits(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session, test_document):
        \"\"\"Test that different API keys have separate rate limits.\"\"\"
        from app.models.api_key import APIKey
        from app.models.document import Document, DocumentStatus
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other_key = APIKey(
            key_hash=pwd_context.hash("di_other_key_1234567890123456"),
            name="Other Key",
            rate_limit=100,
            is_active=True,
        )
        db_session.add(other_key)
        await db_session.commit()
        await db_session.refresh(other_key)

        # Create a document for the other key
        other_doc = Document(
            filename="other.pdf",
            file_path="/tmp/other.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.UPLOADED,
            api_key_id=other_key.id,
        )
        db_session.add(other_doc)
        await db_session.commit()
        await db_session.refresh(other_doc)

        other_headers = {"Authorization": f"Bearer di_other_key_1234567890123456"}

        # Use up limit on first key
        for _ in range(99):
            response = await client.get(
                f"/api/v1/process/status/{test_document.id}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        # Other key should still have full limit
        response = await client.get(
            f"/api/v1/process/status/{other_doc.id}",
            headers=other_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        remaining = int(response.headers["x-rate-limit-remaining"])
        assert remaining >= 90  # Should have most of its limit left"""

c = c.replace(old, new)
f=open('tests/test_middleware.py','w')
f.write(c)
f.close()
print('Done')