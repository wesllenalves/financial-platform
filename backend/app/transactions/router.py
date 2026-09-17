from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.shared.schemas import Page
from app.transactions.models import TransactionStatus, TransactionType
from app.transactions.repository import TransactionFilters
from app.transactions.schemas import (
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
    TransferCreate,
)
from app.transactions.service import TransactionService
from app.users.models import User

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=Page[TransactionOut])
def list_transactions(
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    transaction_type: TransactionType | None = None,
    status_filter: TransactionStatus | None = Query(default=None, alias="status"),
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[TransactionOut]:
    filters = TransactionFilters(
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        account_id=account_id,
        transaction_type=transaction_type,
        status=status_filter,
        search=search,
    )
    items, total = TransactionService(db).list(current_user.id, filters, limit, offset)
    return Page[TransactionOut](
        items=[TransactionOut.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).create(current_user.id, payload)


@router.post("/transfers", response_model=list[TransactionOut], status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).create_transfer(current_user.id, payload)


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).get_or_404(current_user.id, transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionOut)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).update(current_user.id, transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    TransactionService(db).delete(current_user.id, transaction_id)
