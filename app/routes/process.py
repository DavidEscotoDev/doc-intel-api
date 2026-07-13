"""Document processing endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db_session
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentProcessRequest, DocumentStatusResponse
from app.tasks.processor import process_document_task
from app.exceptions import NotFoundError, ValidationError, to_http_exception
from app.logging import get_logger

router = APIRouter(prefix="/process", tags=["Processing"])
logger = get_logger(__name__)


@router.post(
    "/analyze",
    response_model=DocumentStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_dependency)],
)
async def analyze_document(
    request: DocumentProcessRequest,
    background_tasks: BackgroundTasks,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentStatusResponse:
    """Trigger document analysis (async background processing)."""

    # Verify document exists and belongs to API key
    result = await db.execute(
        select(Document).where(
            Document.id == request.document_id,
            Document.api_key_id == api_key.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise to_http_exception(NotFoundError("Document", str(request.document_id)))

    if document.status == DocumentStatus.PROCESSING:
        raise to_http_exception(
            ValidationError("Document is already being processed")
        )

    if document.status == DocumentStatus.COMPLETED:
        raise to_http_exception(
            ValidationError("Document has already been processed. Use /query to retrieve results.")
        )

    # Queue background task
    background_tasks.add_task(process_document_task, str(document.id))

    logger.info(
        "document_analysis_queued",
        document_id=str(document.id),
        api_key_id=str(api_key.id),
    )

    return DocumentStatusResponse(
        id=document.id,
        status=DocumentStatus.PROCESSING,
        progress=0,
    )


@router.get(
    "/status/{document_id}",
    response_model=DocumentStatusResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def get_processing_status(
    document_id: UUID,
    api_key = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentStatusResponse:
    """Get document processing status."""

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.api_key_id == api_key.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise to_http_exception(NotFoundError("Document", str(document_id)))

    # Calculate progress based on status
    progress = 0
    if document.status == DocumentStatus.UPLOADED:
        progress = 0
    elif document.status == DocumentStatus.PROCESSING:
        progress = 50
    elif document.status == DocumentStatus.COMPLETED:
        progress = 100
    elif document.status == DocumentStatus.FAILED:
        progress = 100

    return DocumentStatusResponse(
        id=document.id,
        status=document.status,
        error_message=document.error_message,
        progress=progress,
    )