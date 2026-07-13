# app/models/document.py
"""Document database model."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.constants import DocumentStatus


class Document(Base):
    """Document model representing uploaded files."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Foreign keys
    api_key_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    api_key: Mapped["APIKey"] = relationship(back_populates="documents")
    analysis: Mapped["Analysis | None"] = relationship(
        back_populates="document",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_documents_api_key_id_created_at", "api_key_id", "created_at"),
        Index("ix_documents_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"