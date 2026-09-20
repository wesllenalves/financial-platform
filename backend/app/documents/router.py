from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.documents.schemas import ConfirmExtractionRequest, DocumentOut, ExtractedItemOut
from app.documents.service import DocumentService
from app.users.models import User

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).list_documents(current_user.id)


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: Annotated[UploadFile, File()],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).upload_document(current_user.id, file)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).get_document(current_user.id, document_id)


@router.get("/{document_id}/items", response_model=list[ExtractedItemOut])
def get_extracted_items(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).get_extracted_items(current_user.id, document_id)


@router.post("/items/{item_id}/confirm", response_model=ExtractedItemOut)
def confirm_extraction(
    item_id: uuid.UUID,
    payload: ConfirmExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.transaction_override:
        raise ValueError("transaction_override is required to confirm.")
    return DocumentService(db).confirm_extraction(current_user.id, item_id, payload.transaction_override)


@router.post("/items/{item_id}/reject", response_model=ExtractedItemOut)
def reject_extraction(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DocumentService(db).reject_extraction(current_user.id, item_id)
