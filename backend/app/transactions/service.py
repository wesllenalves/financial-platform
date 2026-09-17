from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.accounts.service import AccountService
from app.categories.service import CategoryService
from app.core.errors import NotFoundError, ValidationError
from app.shared.money import money
from app.transactions.domain import normalize_merchant
from app.transactions.models import (
    PaymentMethod,
    Transaction,
    TransactionSource,
    TransactionStatus,
    TransactionType,
    TransferDirection,
)
from app.transactions.repository import TransactionFilters, TransactionRepository
from app.transactions.schemas import TransactionCreate, TransactionUpdate, TransferCreate


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TransactionRepository(db)
        self.accounts = AccountService(db)
        self.categories = CategoryService(db)

    def list(
        self, user_id: uuid.UUID, filters: TransactionFilters, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        return self.repo.list(user_id, filters, limit, offset)

    def get_or_404(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
        transaction = self.repo.get(user_id, transaction_id)
        if transaction is None:
            raise NotFoundError("Transaction not found.")
        return transaction

    def create(
        self,
        user_id: uuid.UUID,
        payload: TransactionCreate,
        source: TransactionSource = TransactionSource.manual,
        document_id: uuid.UUID | None = None,
    ) -> Transaction:
        if payload.transaction_type is TransactionType.transfer:
            raise ValidationError("Use the transfer endpoint to move money between accounts.")

        self.accounts.get_or_404(user_id, payload.account_id)
        if payload.category_id is not None:
            category = self.categories.get_or_404(user_id, payload.category_id)
            if category.kind.value != payload.transaction_type.value:
                raise ValidationError(
                    "The category does not match the transaction type.",
                    {"category_kind": category.kind.value},
                )

        transaction = self.repo.add(
            Transaction(
                user_id=user_id,
                account_id=payload.account_id,
                category_id=payload.category_id,
                document_id=document_id,
                transaction_type=payload.transaction_type,
                description=payload.description.strip(),
                amount=money(payload.amount),
                transaction_date=payload.transaction_date,
                due_date=payload.due_date,
                payment_date=payload.payment_date
                or (payload.transaction_date if payload.status is TransactionStatus.paid else None),
                merchant=payload.merchant,
                merchant_normalized=normalize_merchant(payload.merchant or payload.description),
                payment_method=payload.payment_method,
                installment_number=payload.installment_number,
                installment_count=payload.installment_count,
                recurring=payload.recurring,
                status=payload.status,
                source=source,
                notes=payload.notes,
            )
        )
        self.db.commit()
        return transaction

    def update(
        self, user_id: uuid.UUID, transaction_id: uuid.UUID, payload: TransactionUpdate
    ) -> Transaction:
        transaction = self.get_or_404(user_id, transaction_id)
        data = payload.model_dump(exclude_unset=True)

        if data.get("account_id"):
            self.accounts.get_or_404(user_id, data["account_id"])
        if data.get("category_id"):
            self.categories.get_or_404(user_id, data["category_id"])
        if "amount" in data and data["amount"] is not None:
            data["amount"] = money(data["amount"])

        for field, value in data.items():
            setattr(transaction, field, value)

        if "merchant" in data or "description" in data:
            transaction.merchant_normalized = normalize_merchant(
                transaction.merchant or transaction.description
            )
        self.db.commit()
        return transaction

    def delete(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
        """Soft delete: financial data is never silently destroyed."""
        from datetime import datetime, timezone

        transaction = self.get_or_404(user_id, transaction_id)
        transaction.deleted_at = datetime.now(timezone.utc)
        self.db.commit()

    def create_transfer(self, user_id: uuid.UUID, payload: TransferCreate) -> Sequence[Transaction]:
        """Transfers are two linked rows and are excluded from income/expense metrics."""
        self.accounts.get_or_404(user_id, payload.from_account_id)
        self.accounts.get_or_404(user_id, payload.to_account_id)
        amount = money(payload.amount)

        outgoing = Transaction(
            user_id=user_id,
            account_id=payload.from_account_id,
            transaction_type=TransactionType.transfer,
            description=payload.description,
            amount=amount,
            transaction_date=payload.transaction_date,
            payment_date=payload.transaction_date,
            payment_method=PaymentMethod.transfer,
            status=TransactionStatus.paid,
            source=TransactionSource.manual,
            transfer_direction=TransferDirection.outgoing,
        )
        incoming = Transaction(
            user_id=user_id,
            account_id=payload.to_account_id,
            transaction_type=TransactionType.transfer,
            description=payload.description,
            amount=amount,
            transaction_date=payload.transaction_date,
            payment_date=payload.transaction_date,
            payment_method=PaymentMethod.transfer,
            status=TransactionStatus.paid,
            source=TransactionSource.manual,
            transfer_direction=TransferDirection.incoming,
        )
        self.repo.add(outgoing)
        self.repo.add(incoming)
        outgoing.transfer_peer_id = incoming.id
        incoming.transfer_peer_id = outgoing.id
        self.db.commit()
        return [outgoing, incoming]
