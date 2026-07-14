"""Query endpoints for retrieving analysis results."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db_session
from app.middleware.auth import verify_api_key, get_current_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.models.document import Document, DocumentStatus
from app.models.analysis import Analysis
from app.schemas.document import DocumentListResponse, DocumentListItem
from app.schemas.analysis import AnalysisResponse, AnalysisDetailResponse
from app.schemas.common import PaginatedResponse
from app.exceptions import NotFoundError, ValidationError
from app.logging import get_logger

router = APIRouter(prefix="/query", tags=["Query"])
logger = get_logger(__name__)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    dependencies=[Depends(verify_api_key), Depends(rate_limit_dependency)],
)
async def query_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    api_key = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentListResponse:
    """List documents with pagination and optional status filter."""

    query = select(Document).where(Document.api_key_id == api_key.id)

    if status:
        try:
            status_enum = DocumentStatus(status)
            query = query.where(Document.status == status_enum)
        except ValueError:
            raise ValidationError(f"Invalid status: {status}")

    # Total count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginated results with analysis loaded
    query = query.options(selectinload(Document.analysis))
    query = query.order_by(Document.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    items = [
        DocumentListItem(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            status=doc.status,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
        )
        for doc in documents
    ]

    total_pages = (total + page_size - 1) // page_size

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/documents/{document_id}",
    response_model=AnalysisDetailResponse,
    dependencies=[Depends(verify_api_key), Depends(rate_limit_dependency)],
)
async def get_document_analysis(
    document_id: UUID,
    include_raw: bool = Query(False),
    api_key = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisDetailResponse:
    """Get full analysis results for a document."""

    # Verify document ownership
    doc_result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.api_key_id == api_key.id,
        )
    )
    document = doc_result.scalar_one_or_none()

    if not document:
        raise NotFoundError("Document", str(document_id))

    if document.status != DocumentStatus.COMPLETED:
        raise NotFoundError("Analysis not available - document not processed", str(document_id))

    # Get analysis
    analysis_result = await db.execute(
        select(Analysis).where(Analysis.document_id == document_id)
    )
    analysis = analysis_result.scalar_one_or_none()

    if not analysis:
        raise NotFoundError("Analysis", str(document_id))

    response = AnalysisDetailResponse(
        id=analysis.id,
        document_id=analysis.document_id,
        summary=analysis.summary,
        key_points=analysis.key_points,
        entities=analysis.entities,
        sentiment=analysis.sentiment,
        topics=analysis.topics,
        tokens_used=analysis.tokens_used,
        model_version=analysis.model_version,
        processing_time_ms=analysis.processing_time_ms,
        created_at=analysis.created_at,
    )

    if include_raw:
        response.raw_response = analysis.raw_response

    logger.info("analysis_retrieved", document_id=str(document_id), api_key_id=str(api_key.id))

    return response


@router.get(
    "/stats",
    response_model=dict,
    dependencies=[Depends(verify_api_key), Depends(rate_limit_dependency)],
)
async def get_stats(
    api_key = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get usage statistics for the API key."""

    from app.models.document import DocumentStatus

    # Document counts by status
    status_counts = {}
    for status in DocumentStatus:
        count = await db.scalar(
            select(func.count(Document.id)).where(
                Document.api_key_id == api_key.id,
                Document.status == status,
            )
        )
        status_counts[status.value] = count

    total_docs = sum(status_counts.values())

    # Total tokens used
    from app.models.analysis import Analysis
    total_tokens = await db.scalar(
        select(func.sum(Analysis.tokens_used))
        .join(Document)
        .where(Document.api_key_id == api_key.id)
    ) or 0

    return {
        "api_key_id": str(api_key.id),
        "api_key_name": api_key.name,
        "total_documents": total_docs,
        "documents_by_status": status_counts,
        "total_tokens_used": total_tokens,
        "rate_limit": api_key.rate_limit,
        "total_requests": api_key.total_requests,
    }