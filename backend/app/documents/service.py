import hashlib
import os
import uuid
from typing import BinaryIO
from decimal import Decimal
from fastapi import UploadFile

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.errors import ValidationError, NotFoundError
from app.documents.models import Document, ExtractedItem, DocumentType, ProcessingStatus, ExtractedItemStatus
from app.documents.parsers import PARSER_REGISTRY
from app.transactions.models import TransactionSource
from app.transactions.schemas import TransactionCreate
from app.transactions.service import TransactionService

MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB
MAGIC_BYTES_MAP = {
    b"%PDF": DocumentType.pdf,
    b"<?xml": DocumentType.xml,
    b"{": DocumentType.json,
    b"\x89PNG": DocumentType.png,
    b"\xFF\xD8": DocumentType.jpeg,
}

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.transaction_service = TransactionService(db)

    def _detect_type(self, file_bytes: bytes) -> DocumentType:
        for magic, file_type in MAGIC_BYTES_MAP.items():
            if file_bytes.startswith(magic):
                return file_type
        # Fallback heuristic for JSON if it didn't strictly start with { due to whitespace
        if b"{" in file_bytes[:10]:
            return DocumentType.json
        raise ValidationError("Unsupported file type or invalid magic bytes.")

    def upload_document(self, user_id: uuid.UUID, file: UploadFile) -> Document:
        file_bytes = file.file.read()
        size_bytes = len(file_bytes)

        if size_bytes > MAX_FILE_SIZE:
            raise ValidationError("File size exceeds 10MB limit.")

        file_type = self._detect_type(file_bytes)
        content_hash = hashlib.sha256(file_bytes).hexdigest()

        # Duplicate check
        existing = self.db.execute(
            select(Document).where(Document.user_id == user_id, Document.content_hash == content_hash)
        ).scalar_one_or_none()

        if existing:
            raise ValidationError("A document with identical content has already been uploaded.")

        # Simulate storage
        storage_path = f"/tmp/doc_{uuid.uuid4()}_{file.filename}"
        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        doc = Document(
            user_id=user_id,
            filename=file.filename,
            file_type=file_type,
            content_hash=content_hash,
            size_bytes=size_bytes,
            storage_path=storage_path,
            processing_status=ProcessingStatus.processing
        )
        self.db.add(doc)
        self.db.flush()

        # Process Document
        self._process_document(doc, file_bytes)
        self.db.commit()
        return doc

    def _process_document(self, doc: Document, file_bytes: bytes):
        from app.transactions.models import Transaction
        try:
            parser = PARSER_REGISTRY[doc.file_type]

            # Use dummy parsing
            from io import BytesIO
            result = parser.parse(BytesIO(file_bytes), doc.file_type)

            doc.extraction_metadata = result.metadata
            doc.extraction_confidence = Decimal(str(result.confidence))

            for item in result.items:
                norm = self._normalize_payload(item)
                duplicate_of = None
                duplicate_reason = None

                # Duplicate check based on date, amount and normalized merchant
                if "transaction_date" in norm and "amount" in norm and "merchant_normalized" in norm:
                    from datetime import datetime
                    try:
                        date_obj = datetime.strptime(norm["transaction_date"], "%Y-%m-%d").date()
                        amount = Decimal(norm["amount"])
                        dup_txn = self.db.execute(
                            select(Transaction).where(
                                Transaction.user_id == doc.user_id,
                                Transaction.transaction_date == date_obj,
                                Transaction.amount == amount,
                                Transaction.merchant_normalized == norm["merchant_normalized"]
                            )
                        ).scalar_one_or_none()

                        if dup_txn:
                            duplicate_of = dup_txn.id
                            duplicate_reason = "Date, amount, and merchant match an existing transaction."
                    except (ValueError, TypeError):
                        pass

                extracted = ExtractedItem(
                    document_id=doc.id,
                    user_id=doc.user_id,
                    raw_payload=item,
                    normalized_payload=norm,
                    field_confidence={"amount": 0.9, "date": 0.9, "merchant": 0.8},
                    status=ExtractedItemStatus.pending,
                    duplicate_of_transaction_id=duplicate_of,
                    duplicate_reason=duplicate_reason
                )
                self.db.add(extracted)

            doc.processing_status = ProcessingStatus.awaiting_confirmation

        except Exception as e:
            doc.processing_status = ProcessingStatus.failed
            doc.error_message = str(e)

    def _normalize_payload(self, item: dict) -> dict:
        from app.transactions.domain import normalize_merchant
        return {
            "transaction_date": item.get("transaction_date"),
            "amount": item.get("amount"),
            "description": item.get("description", "Imported transaction"),
            "merchant": item.get("merchant"),
            "merchant_normalized": normalize_merchant(item.get("merchant") or item.get("description"))
        }

    def list_documents(self, user_id: uuid.UUID) -> list[Document]:
        return list(self.db.execute(select(Document).where(Document.user_id == user_id)).scalars().all())

    def get_document(self, user_id: uuid.UUID, doc_id: uuid.UUID) -> Document:
        doc = self.db.execute(select(Document).where(Document.id == doc_id, Document.user_id == user_id)).scalar_one_or_none()
        if not doc:
            raise NotFoundError("Document not found.")
        return doc

    def get_extracted_items(self, user_id: uuid.UUID, doc_id: uuid.UUID) -> list[ExtractedItem]:
        return list(self.db.execute(
            select(ExtractedItem).where(ExtractedItem.document_id == doc_id, ExtractedItem.user_id == user_id)
        ).scalars().all())

    def confirm_extraction(self, user_id: uuid.UUID, item_id: uuid.UUID, override_data: TransactionCreate) -> ExtractedItem:
        item = self.db.execute(
            select(ExtractedItem).where(ExtractedItem.id == item_id, ExtractedItem.user_id == user_id)
        ).scalar_one_or_none()

        if not item:
            raise NotFoundError("Extracted item not found.")

        if item.status in (ExtractedItemStatus.confirmed, ExtractedItemStatus.edited_confirmed):
            raise ValidationError("Item is already confirmed.")

        # Create the transaction
        txn = self.transaction_service.create(user_id, override_data)
        txn.source = TransactionSource.pdf # Simple hardcode for now
        txn.document_id = item.document_id

        item.created_transaction_id = txn.id
        item.status = ExtractedItemStatus.edited_confirmed

        # Check if all items for the document are confirmed/rejected
        doc = self.db.execute(select(Document).where(Document.id == item.document_id)).scalar_one_or_none()
        if doc:
             doc.processing_status = ProcessingStatus.confirmed

        self.db.commit()
        return item

    def reject_extraction(self, user_id: uuid.UUID, item_id: uuid.UUID) -> ExtractedItem:
        item = self.db.execute(
            select(ExtractedItem).where(ExtractedItem.id == item_id, ExtractedItem.user_id == user_id)
        ).scalar_one_or_none()

        if not item:
            raise NotFoundError("Extracted item not found.")

        item.status = ExtractedItemStatus.rejected
        self.db.commit()
        return item
