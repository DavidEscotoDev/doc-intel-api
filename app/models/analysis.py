# app/models/analysis.py
"""Analysis database model."""

from datetime import datetime
from uuid import uuid4
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base


class Analysis(Base):
    """Document analysis results from LLM."""

    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Analysis results
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    entities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    # Metadata
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Raw response for debugging
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="analysis")

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, document_id={self.document_id}, sentiment={self.sentiment})>"