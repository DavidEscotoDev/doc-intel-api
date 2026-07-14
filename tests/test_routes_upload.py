"""Integration tests for upload routes."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient
from io import BytesIO


class TestUploadRoutes:
    """Test document upload endpoints."""

    @pytest.mark.asyncio
    async def test_upload_valid_pdf(self, client: AsyncClient, auth_headers: dict):
        """Test uploading a valid PDF file."""
        file_content = b"%PDF-1.4\n%Test PDF content"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.pdf"
        assert data["status"] == "uploaded"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_upload_valid_txt(self, client: AsyncClient, auth_headers: dict):
        """Test uploading a valid text file."""
        file_content = b"Hello, this is a test document."
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_upload_valid_docx(self, client: AsyncClient, auth_headers: dict):
        """Test uploading a valid DOCX file."""
        # Minimal DOCX magic bytes (ZIP-based)
        file_content = b"PK\x03\x04" + b"\x00" * 100
        files = {"file": ("test.docx", BytesIO(file_content), 
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "test.docx"

    @pytest.mark.asyncio
    async def test_upload_invalid_mime_type(self, client: AsyncClient, auth_headers: dict):
        """Test uploading file with unsupported MIME type."""
        file_content = b"<?xml version='1.0'?><root/>"
        files = {"file": ("test.xml", BytesIO(file_content), "application/xml")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_mismatched_mime_and_extension(self, client: AsyncClient, auth_headers: dict):
        """Test uploading file with mismatched MIME type and extension."""
        file_content = b"%PDF-1.4\n%PDF content"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        # Should reject due to magic byte validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, auth_headers: dict):
        """Test uploading empty file."""
        files = {"file": ("empty.pdf", BytesIO(b""), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, client: AsyncClient, auth_headers: dict):
        """Test uploading file exceeding size limit."""
        # Create file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.pdf", BytesIO(large_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_dangerous_filename(self, client: AsyncClient, auth_headers: dict):
        """Test uploading file with dangerous filename."""
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": ("../../../etc/passwd", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_filename_too_long(self, client: AsyncClient, auth_headers: dict):
        """Test uploading file with excessively long filename."""
        long_name = "a" * 300 + ".pdf"
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": (long_name, BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_without_auth(self, client: AsyncClient):
        """Test uploading without authentication."""
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_upload_with_invalid_auth(self, client: AsyncClient):
        """Test uploading with invalid API key."""
        file_content = b"%PDF-1.4\n%Test"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
        headers = {"Authorization": "Bearer invalid_key"}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client: AsyncClient, auth_headers: dict):
        """Test listing documents when none exist."""
        response = await client.get(
            "/api/v1/documents/list",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_documents_with_data(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test listing documents with existing data."""
        response = await client.get(
            "/api/v1/documents/list",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "test.pdf"

    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test document list pagination."""
        from app.models.document import Document, DocumentStatus

        for i in range(5):
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

        response = await client.get(
            "/api/v1/documents/list?page=1&page_size=2",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_list_documents_status_filter(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test filtering document list by status."""
        from app.models.document import Document, DocumentStatus

        for status_val in [DocumentStatus.UPLOADED, DocumentStatus.PROCESSING, DocumentStatus.COMPLETED]:
            doc = Document(
                filename=f"doc_{status_val.value}.pdf",
                file_path=f"/tmp/doc_{status_val.value}.pdf",
                mime_type="application/pdf",
                file_size=1024,
                status=status_val,
                api_key_id=test_api_key.id,
            )
            db_session.add(doc)
        await db_session.commit()

        response = await client.get(
            "/api/v1/documents/list?status_filter=completed",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_documents_invalid_status(self, client: AsyncClient, auth_headers: dict):
        """Test listing with invalid status filter."""
        response = await client.get(
            "/api/v1/documents/list?status_filter=invalid",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on upload endpoints."""
        file_content = b"%PDF-1.4\n%Test"

        # Create a test API key with a small rate limit for faster testing
        from app.models.api_key import APIKey
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        key_hash = pwd_context.hash("di_test_ratelimit_123")
        api_key = APIKey(
            key_hash=key_hash,
            name="Rate Limit Test Key",
            rate_limit=5,
            is_active=True,
        )
        db_session.add(api_key)
        await db_session.commit()
        await db_session.refresh(api_key)
        
        auth_headers_rl = {"Authorization": "Bearer di_test_ratelimit_123"}
        
        file_content = b"%PDF-1.4\n%Test"

        # Make 4 requests (all should succeed with rate_limit=5)
        for i in range(4):
            files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers_rl,
            )
            assert response.status_code == status.HTTP_201_CREATED

        # 5th request should be rate limited
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers_rl,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.headers.get("retry-after") is not None
        assert response.headers.get("retry-after") is not None