"""Background document processing task."""

import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import _get_session_factory, close_db, init_db
from app.exceptions import ValidationError
from app.logging import get_logger
from app.models.document import Document
from app.services.extractor import get_text_extractor
from app.services.llm import get_llm_service
from app.services.storage import get_storage_service

logger = get_logger(__name__)


async def process_document_task(document_id: str) -> None:
    """Process a document: extract text, analyze with LLM, store results."""

    doc_uuid = UUID(document_id)
    start_time = time.time()

    # Initialize DB for background task
    await init_db()

    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            # Get document
            result = await session.execute(select(Document).where(Document.id == doc_uuid))
            document = result.scalar_one_or_none()

            if not document:
                logger.error("process_document_not_found", document_id=document_id)
                return

            if document.status == "processing":
                logger.warning("process_document_already_processing", document_id=document_id)
                return

            # Update status to processing
            document.status = "processing"
            await session.commit()

            logger.info("process_document_started", document_id=document_id)

            # Get file from storage
            storage = get_storage_service()
            file_path = await storage.get_path(document.file_path)

            # Extract text
            extractor = get_text_extractor()
            text = extractor.extract(file_path, document.mime_type)

            if not text.strip():
                raise ValidationError("No text content extracted from document")

            # Analyze with LLM
            llm = get_llm_service()
            result = await llm.analyze(text)

            # Save analysis to document
            processing_time_ms = int((time.time() - start_time) * 1000)

            document.summary = result.summary
            document.key_points = result.key_points
            document.entities = result.entities
            document.sentiment = result.sentiment
            document.topics = result.topics
            document.tokens_used = result.tokens_used
            document.model_version = llm.model
            document.processing_time_ms = processing_time_ms
            document.raw_response = {"content": result.raw}

            # Mark completed
            document.status = "completed"
            document.processed_at = datetime.now(UTC)

            await session.commit()

            logger.info(
                "process_document_completed",
                document_id=document_id,
                processing_time_ms=processing_time_ms,
                tokens_used=result.tokens_used,
            )

        except ValidationError as e:
            await _mark_failed(session, document, str(e))
            logger.error("process_document_failed", document_id=document_id, error=str(e))
        except Exception as e:
            await _mark_failed(session, document, f"Unexpected error: {str(e)}")
            logger.exception("process_document_unexpected_error", document_id=document_id)
        finally:
            await close_db()


async def _mark_failed(session: AsyncSession, document: Document | None, error: str) -> None:
    """Mark document as failed with error message."""
    if document:
        document.status = "failed"
        document.error_message = error
        await session.commit()
