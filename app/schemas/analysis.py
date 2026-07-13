"""Analysis-related schemas."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from uuid import UUID

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: UUID
    document_id: UUID
    summary: str
    key_points: list[str]
    entities: list[str]
    sentiment: str
    topics: list[str]
    tokens_used: int
    model_version: str
    processing_time_ms: int
    created_at: datetime

class AnalysisRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_id: UUID
    callback_url: Optional[str] = None
    @field_validator("callback_url")
    @classmethod
    def validate_callback_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Callback URL must be a valid HTTP/HTTPS URL")
        return v

class AnalysisDetailResponse(AnalysisResponse):
    raw_response: Optional[dict] = None