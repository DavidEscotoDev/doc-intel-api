# tests/test_database.py
"""Database layer tests."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.models.api_key import APIKey
from app.database import Base


class TestDatabaseModels:
    """Test database model creation and relationships."""

    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession):
        api_key = APIKey(
            key_hash="hashed_key",
            name="Test Key",
            rate_limit=100,
        )
        db_session.add(api_key)
        await db_session.commit()
        await db_session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.name == "Test Key"
        assert api_key.rate_limit == 100
        assert api_key.is_active is True
        assert api_key.total_requests == 0

    @pytest.mark.asyncio
    async def test_create_document(self, db_session: AsyncSession, test_api_key: APIKey):
        doc = Document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            status=DocumentStatus.UPLOADED,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        assert doc.id is not None
        assert doc.filename == "test.pdf"
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.api_key_id == test_api_key.id

    @pytest.mark.asyncio
    async def test_create_analysis(self, db_session: AsyncSession, test_document: Document):
        analysis = Analysis(
            document_id=test_document.id,
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            entities=["Entity 1"],
            sentiment="positive",
            topics=["Topic 1"],
            tokens_used=150,
            model_version="claude-3-5-sonnet-20241022",
            processing_time_ms=1200,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        assert analysis.id is not None
        assert analysis.document_id == test_document.id
        assert analysis.summary == "Test summary"
        assert analysis.sentiment == "positive"
        assert len(analysis.key_points) == 2

    @pytest.mark.asyncio
    async def test_document_analysis_relationship(
        self, db_session: AsyncSession, test_document: Document
    ):
        analysis = Analysis(
            document_id=test_document.id,
            summary="Test summary",
            key_points=["Point 1"],
            entities=[],
            sentiment="neutral",
            topics=[],
            tokens_used=100,
            model_version="claude-3-5-sonnet-20241022",
        )
        db_session.add(analysis)
        await db_session.commit()

        # Refresh and check relationship
        await db_session.refresh(test_document, attribute_names=["analysis"])
        assert test_document.analysis is not None
        assert test_document.analysis.id == analysis.id
        assert test_document.analysis.summary == "Test summary"

    @pytest.mark.asyncio
    async def test_api_key_documents_relationship(
        self, db_session: AsyncSession, test_api_key: APIKey
    ):
        doc1 = Document(
            filename="doc1.pdf",
            file_path="/tmp/doc1.pdf",
            mime_type="application/pdf",
            file_size=1024,
            api_key_id=test_api_key.id,
        )
        doc2 = Document(
            filename="doc2.pdf",
            file_path="/tmp/doc2.pdf",
            mime_type="application/pdf",
            file_size=2048,
            api_key_id=test_api_key.id,
        )
        db_session.add_all([doc1, doc2])
        await db_session.commit()

        await db_session.refresh(test_api_key, attribute_names=["documents"])
        assert len(test_api_key.documents) == 2

    @pytest.mark.asyncio
    async def test_cascade_delete_document_deletes_analysis(
        self, db_session: AsyncSession, test_document: Document
    ):
        analysis = Analysis(
            document_id=test_document.id,
            summary="Test",
            key_points=[],
            entities=[],
            sentiment="neutral",
            topics=[],
            tokens_used=50,
            model_version="claude-3-5-sonnet-20241022",
        )
        db_session.add(analysis)
        await db_session.commit()

        # Delete document - analysis should cascade
        await db_session.delete(test_document)
        await db_session.commit()

        result = await db_session.execute(select(Analysis).where(Analysis.id == analysis.id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cascade_delete_api_key_deletes_documents(
        self, db_session: AsyncSession, test_api_key: APIKey
    ):
        doc = Document(
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            api_key_id=test_api_key.id,
        )
        db_session.add(doc)
        await db_session.commit()

        await db_session.delete(test_api_key)
        await db_session.commit()

        result = await db_session.execute(select(Document).where(Document.id == doc.id))
        assert result.scalar_one_or_none() is None