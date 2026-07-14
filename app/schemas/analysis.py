"""Analysis-related schemas (now from Document model)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalysisDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    raw_response: dict | None = None
