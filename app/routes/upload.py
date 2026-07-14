"""Document upload endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.logging import get_logger
from app.middleware.auth import get_current_api_key, verify_api_key
from app.middleware.rate_limit import rate_limit_dependency
from app.models.document import Document
from app.schemas.document import (
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.security.validation import validate_file_content, validate_filename
from app.services.storage import get_storage_service

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger(__name__)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key), Depends(rate_limit_dependency)],
)
async def upload_document(
    file: UploadFile = File(...),
    api_key=Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentUploadResponse:
    """Upload a document for processing."""

    # Validate file using security validation
    validate_filename(file.filename)

    # Read and validate file content
    content = await file.read()
    validate_file_content(file, content)

    # Save to storage
    storage = get_storage_service()
    from io import BytesIO

    file_obj = BytesIO(content)
    storage_key, file_size = await storage.save_upload(file_obj, file.filename, file.content_type)

    # Create document record
    document = Document(
        filename=file.filename,
        file_path=storage_key,
        mime_type=file.content_type,
        file_size=file_size,
        status="uploaded",
        api_key_id=api_key.id,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    logger.info(
        "document_uploaded",
        document_id=str(document.id),
        filename=document.filename,
        size=file_size,
        api_key_id=str(api_key.id),
    )

    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        message="File uploaded successfully. Use /process/analyze to analyze.",
    )


@router.get(
    "/list",
    response_model=DocumentListResponse,
    dependencies=[Depends(verify_api_key), Depends(rate_limit_dependency)],
)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    api_key=Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentListResponse:
    """List uploaded documents with pagination."""

    # Validate pagination
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    # Build query
    query = select(Document).where(Document.api_key_id == api_key.id)

    if status_filter:
        query = query.where(Document.status == status_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Get paginated results
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
