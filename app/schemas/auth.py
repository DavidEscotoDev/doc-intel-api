"""Authentication-related schemas."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID

class APIKeyCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., min_length=1, max_length=100)
    rate_limit: int = Field(10, ge=1, le=1000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)

class APIKeyCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    key: str
    name: str
    rate_limit: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    rate_limit: int
    is_active: bool
    last_used_at: Optional[datetime] = None
    total_requests: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

class APIKeyListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[APIKeyResponse]
    total: int