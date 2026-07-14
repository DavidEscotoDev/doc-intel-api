"""Common schema definitions."""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    error: ErrorDetail


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    version: str
    environment: str
    database: str
    timestamp: datetime
