"""Document-related schemas."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from uuid import UUID
from app.constants import DocumentStatus
from app.schemas.common import PaginatedResponse

class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    filename: str
    status: DocumentStatus
    message: str

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    filename: str
    mime_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None

class DocumentListResponse(PaginatedResponse[DocumentListItem]):
    pass

class DocumentStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: DocumentStatus
    error_message: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)

class DocumentProcessRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_id: UUID
    callback_url: Optional[str] = None
    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Callback URL must be a valid HTTP/HTTPS URL")
        return v