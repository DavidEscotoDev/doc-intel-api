"""Integration tests for process routes."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone


class TestProcessRoutes:
    """Test document processing endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_document_success(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test successful document analysis queueing."""
        # Mock the background task to avoid init_db issues with SQLite
        with patch("app.routes.process.process_document_task") as mock_task:
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(test_document.id)},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["status"] == "processing"
        assert data["progress"] == 0
        mock_task.assert_called_once_with(str(test_document.id))

    @pytest.mark.asyncio
    async def test_analyze_document_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test analyzing non-existent document."""
        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(uuid4())},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_analyze_document_wrong_owner(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test analyzing document owned by different API key."""
        from app.models.document import Document, DocumentStatus
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
            status=DocumentStatus.UPLOADED,
            api_key_id=other_key.id,
        )
        db_session.add(other_doc)
        await db_session.commit()
        await db_session.refresh(other_doc)

        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(other_doc.id)},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_analyze_already_processing(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test analyzing document already being processed."""
        from app.models.document import Document, DocumentStatus

        doc = Document(
            filename="processing.pdf",
            file_path="/tmp/processing.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.PROCESSING,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        with patch("app.routes.process.process_document_task") as mock_task:
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(doc.id)},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "already being processed" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_analyze_already_completed(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test analyzing document already completed."""
        from app.models.document import Document, DocumentStatus

        doc = Document(
            filename="completed.pdf",
            file_path="/tmp/completed.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.COMPLETED,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        with patch("app.routes.process.process_document_task") as mock_task:
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(doc.id)},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "already been processed" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_analyze_without_auth(self, client: AsyncClient, test_document):
        """Test analyzing without authentication."""
        response = await client.post(
            "/api/v1/process/analyze",
            json={"document_id": str(test_document.id)},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_processing_status_uploaded(self, client: AsyncClient, auth_headers: dict, test_document):
        """Test getting status of uploaded document."""
        response = await client.get(
            f"/api/v1/process/status/{test_document.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["status"] == "uploaded"
        assert data["progress"] == 0

    @pytest.mark.asyncio
    async def test_get_processing_status_processing(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test getting status of processing document."""
        from app.models.document import Document, DocumentStatus

        doc = Document(
            filename="processing.pdf",
            file_path="/tmp/processing.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.PROCESSING,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        response = await client.get(
            f"/api/v1/process/status/{doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 50

    @pytest.mark.asyncio
    async def test_get_processing_status_completed(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test getting status of completed document."""
        from app.models.document import Document, DocumentStatus

        doc = Document(
            filename="completed.pdf",
            file_path="/tmp/completed.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.COMPLETED,
            api_key_id=test_api_key.id,
            processed_at=datetime.now(timezone.utc),
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        response = await client.get(
            f"/api/v1/process/status/{doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100

    @pytest.mark.asyncio
    async def test_get_processing_status_failed(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test getting status of failed document."""
        from app.models.document import Document, DocumentStatus

        doc = Document(
            filename="failed.pdf",
            file_path="/tmp/failed.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.FAILED,
            api_key_id=test_api_key.id,
            error_message="Processing failed: timeout",
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        response = await client.get(
            f"/api/v1/process/status/{doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "failed"
        assert data["progress"] == 100
        assert data["error_message"] == "Processing failed: timeout"

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting status of non-existent document."""
        response = await client.get(
            f"/api/v1/process/status/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_status_wrong_owner(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test getting status of document owned by different key."""
        from app.models.document import Document, DocumentStatus
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
            status=DocumentStatus.UPLOADED,
            api_key_id=other_key.id,
        )
        db_session.add(other_doc)
        await db_session.commit()
        await db_session.refresh(other_doc)

        response = await client.get(
            f"/api/v1/process/status/{other_doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_rate_limiting_on_analyze(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test rate limiting on analyze endpoint."""
        from app.models.document import Document, DocumentStatus
        from sqlalchemy import select

        for i in range(99):
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

        for i in range(99):
            result = await db_session.execute(
                select(Document).where(Document.filename == f"doc{i}.pdf")
            )
            doc = result.scalar_one()
            with patch("app.routes.process.process_document_task") as mock_task:
                response = await client.post(
                    "/api/v1/process/analyze",
                    json={"document_id": str(doc.id)},
                    headers=auth_headers,
                )
            assert response.status_code in (status.HTTP_202_ACCEPTED, status.HTTP_422_UNPROCESSABLE_ENTITY)

        with patch("app.routes.process.process_document_task") as mock_task:
            response = await client.post(
                "/api/v1/process/analyze",
                json={"document_id": str(doc.id)},
                headers=auth_headers,
            )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS