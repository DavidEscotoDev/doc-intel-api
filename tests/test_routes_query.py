"""Integration tests for query routes."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select


class TestQueryRoutes:
    """Test query endpoints for retrieving analysis results."""

    @pytest.mark.asyncio
    async def test_query_documents_empty(self, client: AsyncClient, auth_headers: dict):
        """Test querying documents when none exist."""
        response = await client.get(
            "/api/v1/query/documents",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_query_documents_with_data(self, client: AsyncClient, auth_headers: dict, test_document, test_analysis):
        """Test querying documents with existing data."""
        response = await client.get(
            "/api/v1/query/documents",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "test.pdf"
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_query_documents_pagination(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test document query pagination."""
        from app.models.document import Document, DocumentStatus

        for i in range(5):
            doc = Document(
                filename=f"doc{i}.pdf",
                file_path=f"/tmp/doc{i}.pdf",
                mime_type="application/pdf",
                file_size=1024,
                status=DocumentStatus.COMPLETED,
                api_key_id=test_api_key.id,
            )
            db_session.add(doc)
        await db_session.commit()

        response = await client.get(
            "/api/v1/query/documents?page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_query_documents_status_filter(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test filtering documents by status."""
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
            "/api/v1/query/documents?status=completed",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_query_documents_invalid_status(self, client: AsyncClient, auth_headers: dict):
        """Test filtering with invalid status."""
        response = await client.get(
            "/api/v1/query/documents?status=invalid",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_document_analysis_success(self, client: AsyncClient, auth_headers: dict, test_document, test_analysis):
        """Test retrieving analysis results for completed document."""
        response = await client.get(
            f"/api/v1/query/documents/{test_document.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["document_id"] == str(test_document.id)
        assert data["summary"] == "Test summary"
        assert data["sentiment"] == "positive"
        assert data["key_points"] == ["Point 1", "Point 2"]
        assert data["entities"] == ["Entity 1"]
        assert data["topics"] == ["Topic 1"]
        assert data["tokens_used"] == 100
        assert data["model_version"] == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_get_document_analysis_with_raw(self, client: AsyncClient, auth_headers: dict, test_document, test_analysis):
        """Test retrieving analysis with raw response included."""
        response = await client.get(
            f"/api/v1/query/documents/{test_document.id}?include_raw=true",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "raw_response" in data

    @pytest.mark.asyncio
    async def test_get_document_analysis_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test retrieving analysis for non-existent document."""
        response = await client.get(
            f"/api/v1/query/documents/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_document_analysis_not_processed(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test retrieving analysis for document not yet processed."""
        from app.models.document import DocumentStatus
        test_document.status = DocumentStatus.UPLOADED

        response = await client.get(
            f"/api/v1/query/documents/{test_document.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_document_analysis_wrong_owner(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test retrieving analysis for document owned by another key."""
        from app.models.document import Document, DocumentStatus
        from app.models.analysis import Analysis
        from app.models.api_key import APIKey
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other_key = APIKey(
            key_hash=pwd_context.hash("di_other_key"),
            name="Other Key",
            rate_limit=100,
            is_active=True,
        )
        db_session.add(other_key)
        await db_session.commit()
        await db_session.refresh(other_key)

        other_doc = Document(
            filename="other.pdf",
            file_path="/tmp/other.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.COMPLETED,
            api_key_id=other_key.id,
        )
        db_session.add(other_doc)
        await db_session.commit()
        await db_session.refresh(other_doc)

        other_analysis = Analysis(
            document_id=other_doc.id,
            summary="Other summary",
            key_points=[],
            entities=[],
            sentiment="neutral",
            topics=[],
            tokens_used=50,
            model_version="claude-3-5-sonnet-20241022",
        )
        db_session.add(other_analysis)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/query/documents/{other_doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test getting usage statistics."""
        from app.models.document import Document, DocumentStatus
        from app.models.analysis import Analysis

        for status_val in [DocumentStatus.UPLOADED, DocumentStatus.COMPLETED, DocumentStatus.FAILED]:
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

        completed_doc = await db_session.execute(
            select(Document).where(Document.status == DocumentStatus.COMPLETED)
        )
        completed = completed_doc.scalar_one()

        analysis = Analysis(
            document_id=completed.id,
            summary="Test",
            key_points=[],
            entities=[],
            sentiment="positive",
            topics=[],
            tokens_used=150,
            model_version="claude-3-5-sonnet-20241022",
        )
        db_session.add(analysis)
        await db_session.commit()

        response = await client.get(
            "/api/v1/query/stats",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["api_key_id"] == str(test_api_key.id)
        assert data["total_documents"] == 3
        assert "documents_by_status" in data
        assert data["total_tokens_used"] == 150
        assert data["rate_limit"] == 100

    @pytest.mark.asyncio
    async def test_rate_limiting_on_query(self, client: AsyncClient, auth_headers: dict, test_document, test_analysis):
        """Test rate limiting on query endpoints."""
        # Make 100 requests (all should succeed with rate_limit=100)
        for i in range(99):
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
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_rate_limiting_on_list(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on document list endpoint."""
        for i in range(99):
            response = await client.get(
                "/api/v1/query/documents",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/query/documents",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_rate_limiting_on_stats(self, client: AsyncClient, auth_headers: dict):
        """Test rate limiting on stats endpoint."""
        for i in range(99):
            response = await client.get(
                "/api/v1/query/stats",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_200_OK

        response = await client.get(
            "/api/v1/query/stats",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS