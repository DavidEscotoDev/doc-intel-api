"""Pydantic schemas package."""
from app.schemas.document import (
    DocumentUploadResponse, DocumentListResponse, DocumentResponse, DocumentStatusResponse,
)
from app.schemas.analysis import (AnalysisDetailResponse,)
from app.schemas.auth import (APIKeyCreate, APIKeyResponse, APIKeyListResponse,)
from app.schemas.common import (PaginatedResponse, ErrorResponse, HealthResponse,)

__all__ = [
    "DocumentUploadResponse", "DocumentListResponse", "DocumentResponse", "DocumentStatusResponse",
    "AnalysisDetailResponse",
    "APIKeyCreate", "APIKeyResponse", "APIKeyListResponse",
    "PaginatedResponse", "ErrorResponse", "HealthResponse",
]