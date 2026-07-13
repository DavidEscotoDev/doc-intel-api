"""Background document processing task."""

import time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import db, init_db, close_db
from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.services.storage import get_storage_service
from app.services.extractor import get_text_extractor
from app.services.llm import get_llm_service
from app.exceptions import ProcessingError
from app.logging import get_logger

logger = get_logger(__name__)


async def process_document_task(document_id: str) -> None:
    """Process a document: extract text, analyze with LLM, store results."""

    doc_uuid = UUID(document_id)
    start_time = time.time()

    # Initialize DB for background task
    await init_db()

    async with db.session() as session:
        try:
            # Get document
            result = await session.execute(
                select(Document).where(Document.id == doc_uuid)
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.error("process_document_not_found", document_id=document_id)
                return

            if document.status == DocumentStatus.PROCESSING:
                logger.warning("process_document_already_processing", document_id=document_id)
                return

            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await session.commit()

            logger.info("process_document_started", document_id=document_id)

            # Get file from storage
            storage = get_storage_service()
            file_path = await storage.get_file_path(document.file_path)

            # Extract text
            extractor = get_text_extractor()
            text = extractor.extract(file_path, document.mime_type)

            if not text.strip():
                raise ProcessingError("No text content extracted from document")

            # Analyze with LLM
            llm = get_llm_service()
            result = await llm.analyze(text)

            # Save analysis
            processing_time_ms = int((time.time() - start_time) * 1000)

            analysis = Analysis(
                document_id=document.id,
                summary=result.summary,
                key_points=result.key_points,
                entities=result.entities,
                sentiment=result.sentiment,
                topics=result.topics,
                tokens_used=result.tokens_used,
                model_version=llm.model,
                processing_time_ms=processing_time_ms,
                raw_response={"content": result.raw},
            )
            session.add(analysis)

            # Mark completed
            document.status = DocumentStatus.COMPLETED
            document.processed_at = time.time()

            await session.commit()

            logger.info(
                "process_document_completed",
                document_id=document_id,
                processing_time_ms=processing_time_ms,
                tokens_used=result.tokens_used,
            )

        except ProcessingError as e:
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
        document.status = DocumentStatus.FAILED
        document.error_message = error
        await session.commit()