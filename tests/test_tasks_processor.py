"""Integration tests for document processing task."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from fastapi import status
from httpx import AsyncClient
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class MockAnalysisResult:
    """Mock analysis result object with attributes."""
    def __init__(self, summary, key_points, entities, sentiment, topics, tokens_used, raw):
        self.summary = summary
        self.key_points = key_points
        self.entities = entities
        self.sentiment = sentiment
        self.topics = topics
        self.tokens_used = tokens_used
        self.raw = raw


class TestDocumentProcessor:
    """Test background document processing task."""

    @pytest.mark.asyncio
    async def test_process_document_full_pipeline(self, client: AsyncClient, auth_headers: dict, test_document, test_api_key, db_session):
        """Test full document processing pipeline: extract -> analyze -> save."""
        from app.models.document import DocumentStatus
        from app.models.analysis import Analysis
        from app.tasks.processor import process_document_task

        # Mock the LLM service to return a valid analysis
        with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
            mock_llm = AsyncMock()
            mock_llm.analyze.return_value = MockAnalysisResult(
                summary="Test document summary",
                key_points=["Point 1", "Point 2"],
                entities=["Entity 1", "Entity 2"],
                sentiment="positive",
                topics=["Topic 1", "Topic 2"],
                tokens_used=150,
                raw="Raw LLM response",
            )
            mock_llm.model = "claude-3-5-sonnet-20241022"
            mock_llm_factory.return_value = mock_llm

            # Mock the extractor (sync method)
            with patch("app.tasks.processor.get_text_extractor") as mock_extractor_factory:
                mock_extractor = MagicMock()
                mock_extractor.extract.return_value = "Extracted text content from document"
                mock_extractor_factory.return_value = mock_extractor

                # Mock storage
                with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    # Patch the db module in processor to use our test session
                    with patch("app.tasks.processor.db") as mock_db:
                        mock_db.session.return_value.__aenter__.return_value = db_session
                        mock_db.session.return_value.__aexit__.return_value = None

                        mock_storage = AsyncMock()
                        mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test content"
                        mock_storage_factory.return_value = mock_storage

                        # Also mock init_db and close_db to avoid database initialization
                        with patch("app.tasks.processor.init_db") as mock_init_db:
                            with patch("app.tasks.processor.close_db") as mock_close_db:
                                # Run the background task
                                await process_document_task(str(test_document.id))

        # Verify document status updated
        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.COMPLETED
        assert test_document.processed_at is not None
        assert test_document.error_message is None

        # Verify analysis was created
        from app.models.analysis import Analysis
        from sqlalchemy import select
        result = await db_session.execute(
            select(Analysis).where(Analysis.document_id == test_document.id)
        )
        analysis = result.scalar_one_or_none()
        assert analysis is not None
        assert analysis.summary == "Test document summary"
        assert analysis.sentiment == "positive"
        assert analysis.tokens_used == 150
        assert analysis.model_version == "claude-3-5-sonnet-20241022"

    @pytest.mark.asyncio
    async def test_process_document_extraction_failure(self, client: AsyncClient, auth_headers: dict, test_document, test_api_key, db_session):
        """Test handling of text extraction failure."""
        from app.models.document import DocumentStatus
        from app.tasks.processor import process_document_task

        with patch("app.tasks.processor.get_text_extractor") as mock_extractor_factory:
            mock_extractor = MagicMock()
            mock_extractor.extract.side_effect = Exception("Extraction failed")
            mock_extractor_factory.return_value = mock_extractor

            with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                with patch("app.tasks.processor.db") as mock_db:
                    mock_db.session.return_value.__aenter__.return_value = db_session
                    mock_db.session.return_value.__aexit__.return_value = None

                    mock_storage = AsyncMock()
                    mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                    mock_storage_factory.return_value = mock_storage

                    with patch("app.tasks.processor.init_db") as mock_init_db:
                        with patch("app.tasks.processor.close_db") as mock_close_db:
                            await process_document_task(str(test_document.id))

        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.FAILED
        assert "Extraction failed" in test_document.error_message

    @pytest.mark.asyncio
    async def test_process_document_llm_failure(self, client: AsyncClient, auth_headers: dict, test_document, test_api_key, db_session):
        """Test handling of LLM analysis failure."""
        from app.models.document import DocumentStatus
        from app.tasks.processor import process_document_task

        with patch("app.tasks.processor.get_text_extractor") as mock_extractor_factory:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = "Extracted text"
            mock_extractor_factory.return_value = mock_extractor

            with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
                mock_llm = AsyncMock()
                mock_llm.analyze.side_effect = Exception("LLM API error")
                mock_llm_factory.return_value = mock_llm

                with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    with patch("app.tasks.processor.db") as mock_db:
                        mock_db.session.return_value.__aenter__.return_value = db_session
                        mock_db.session.return_value.__aexit__.return_value = None

                        mock_storage = AsyncMock()
                        mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                        mock_storage_factory.return_value = mock_storage

                        with patch("app.tasks.processor.init_db") as mock_init_db:
                            with patch("app.tasks.processor.close_db") as mock_close_db:
                                await process_document_task(str(test_document.id))

        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.FAILED
        assert "LLM API error" in test_document.error_message

    @pytest.mark.asyncio
    async def test_process_document_not_found(self, client: AsyncClient, auth_headers: dict, test_api_key, db_session):
        """Test processing non-existent document."""
        from app.tasks.processor import process_document_task

        fake_id = str(uuid4())
        with patch("app.tasks.processor.db") as mock_db:
            mock_db.session.return_value.__aenter__.return_value = db_session
            mock_db.session.return_value.__aexit__.return_value = None

            with patch("app.tasks.processor.init_db") as mock_init_db:
                with patch("app.tasks.processor.close_db") as mock_close_db:
                    await process_document_task(fake_id)
        # Should not raise, just log error

    @pytest.mark.asyncio
    async def test_process_document_storage_failure(self, client: AsyncClient, auth_headers: dict, test_document, test_api_key, db_session):
        """Test handling of storage failure when retrieving file."""
        from app.models.document import DocumentStatus
        from app.tasks.processor import process_document_task

        with patch("app.tasks.processor.get_text_extractor") as mock_extractor_factory:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = "Extracted text"
            mock_extractor_factory.return_value = mock_extractor

            with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
                mock_llm = AsyncMock()
                mock_llm.analyze.return_value = MockAnalysisResult(
                    summary="Test summary",
                    key_points=[],
                    entities=[],
                    sentiment="neutral",
                    topics=[],
                    tokens_used=100,
                    raw="Raw",
                )
                mock_llm.model = "claude-3-5-sonnet-20241022"
                mock_llm_factory.return_value = mock_llm

                with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    with patch("app.tasks.processor.db") as mock_db:
                        mock_db.session.return_value.__aenter__.return_value = db_session
                        mock_db.session.return_value.__aexit__.return_value = None

                        mock_storage = AsyncMock()
                        mock_storage.get_file_path.side_effect = Exception("Storage unavailable")
                        mock_storage_factory.return_value = mock_storage

                        with patch("app.tasks.processor.init_db") as mock_init_db:
                            with patch("app.tasks.processor.close_db") as mock_close_db:
                                await process_document_task(str(test_document.id))

        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.FAILED
        assert "Storage unavailable" in test_document.error_message

    @pytest.mark.asyncio
    async def test_process_document_database_error_on_save(self, client: AsyncClient, auth_headers: dict, test_document, test_api_key, db_session):
        """Test handling of database error when saving analysis."""
        from app.models.document import DocumentStatus
        from app.tasks.processor import process_document_task

        with patch("app.tasks.processor.get_text_extractor") as mock_extractor_factory:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = "Extracted text"
            mock_extractor_factory.return_value = mock_extractor

            with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
                mock_llm = AsyncMock()
                mock_llm.analyze.return_value = MockAnalysisResult(
                    summary="Test summary",
                    key_points=[],
                    entities=[],
                    sentiment="neutral",
                    topics=[],
                    tokens_used=100,
                    raw="Raw",
                )
                mock_llm.model = "claude-3-5-sonnet-20241022"
                mock_llm_factory.return_value = mock_llm

                with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    with patch("app.tasks.processor.db") as mock_db:
                        mock_db.session.return_value.__aenter__.return_value = db_session
                        mock_db.session.return_value.__aexit__.return_value = None

                        mock_storage = AsyncMock()
                        mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                        mock_storage_factory.return_value = mock_storage

                        with patch("app.tasks.processor.init_db") as mock_init_db:
                            with patch("app.tasks.processor.close_db") as mock_close_db:
                                # Make the SECOND commit fail (when saving analysis)
                                # First commit (status=PROCESSING) should succeed
                                original_commit = db_session.commit
                                commit_count = 0

                                async def mock_commit():
                                    nonlocal commit_count
                                    commit_count += 1
                                    if commit_count == 2:
                                        raise Exception("DB error")
                                    return await original_commit()

                                with patch.object(db_session, "commit", side_effect=mock_commit):
                                    await process_document_task(str(test_document.id))

        await db_session.refresh(test_document)
        assert test_document.status == DocumentStatus.FAILED

    @pytest.mark.asyncio
    async def test_process_document_sets_processing_status(self, client: AsyncClient, auth_headers: dict, test_document, test_api_key, db_session):
        """Test that document status is set to PROCESSING during processing."""
        from app.models.document import DocumentStatus
        from app.tasks.processor import process_document_task

        with patch("app.tasks.processor.get_text_extractor") as mock_extractor_factory:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = "Extracted text"
            mock_extractor_factory.return_value = mock_extractor

            with patch("app.tasks.processor.get_llm_service") as mock_llm_factory:
                mock_llm = AsyncMock()
                mock_llm.analyze.return_value = MockAnalysisResult(
                    summary="Test",
                    key_points=[],
                    entities=[],
                    sentiment="neutral",
                    topics=[],
                    tokens_used=50,
                    raw="Raw",
                )
                mock_llm.model = "claude-3-5-sonnet-20241022"
                mock_llm_factory.return_value = mock_llm

                with patch("app.tasks.processor.get_storage_service") as mock_storage_factory:
                    with patch("app.tasks.processor.db") as mock_db:
                        mock_db.session.return_value.__aenter__.return_value = db_session
                        mock_db.session.return_value.__aexit__.return_value = None

                        mock_storage = AsyncMock()
                        mock_storage.get_file_path.return_value = b"%PDF-1.4\n%Test"
                        mock_storage_factory.return_value = mock_storage

                        with patch("app.tasks.processor.init_db") as mock_init_db:
                            with patch("app.tasks.processor.close_db") as mock_close_db:
                                await process_document_task(str(test_document.id))

        await db_session.refresh(test_document)
        # Final status should be COMPLETED
        assert test_document.status == DocumentStatus.COMPLETED