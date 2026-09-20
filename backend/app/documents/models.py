from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DocumentType(str, enum.Enum):
    pdf = "pdf"
    xml = "xml"
    json = "json"
    png = "png"
    jpeg = "jpeg"


class ProcessingStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    awaiting_confirmation = "awaiting_confirmation"
    confirmed = "confirmed"
    failed = "failed"
    rejected = "rejected"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("user_id", "content_hash", name="uq_document_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), nullable=False
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"), nullable=False, default=ProcessingStatus.uploaded
    )
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    extraction_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExtractedItemStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    edited_confirmed = "edited_confirmed"


class ExtractedItem(Base):
    __tablename__ = "extracted_items"

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    field_confidence: Mapped[dict] = mapped_column(JSONB, nullable=False)

    duplicate_of_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )
    duplicate_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[ExtractedItemStatus] = mapped_column(
        Enum(ExtractedItemStatus, name="extracted_item_status"), nullable=False, default=ExtractedItemStatus.pending
    )
    created_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
