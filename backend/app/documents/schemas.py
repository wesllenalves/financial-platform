from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.shared.schemas import ApiModel
from app.documents.models import DocumentType, ProcessingStatus, ExtractedItemStatus
from app.transactions.schemas import TransactionCreate


class DocumentOut(ApiModel):
    id: uuid.UUID
    filename: str
    file_type: DocumentType
    size_bytes: int
    processing_status: ProcessingStatus
    error_message: str | None
    extraction_confidence: Decimal | None
    uploaded_at: datetime
    processed_at: datetime | None


class ExtractedItemOut(ApiModel):
    id: uuid.UUID
    document_id: uuid.UUID
    raw_payload: dict
    normalized_payload: dict
    field_confidence: dict
    duplicate_of_transaction_id: uuid.UUID | None
    duplicate_reason: str | None
    status: ExtractedItemStatus
    created_transaction_id: uuid.UUID | None


class ConfirmExtractionRequest(ApiModel):
    # Overrides anything in the normalized_payload.
    # The client might change the date or category, for example.
    transaction_override: TransactionCreate | None = None
