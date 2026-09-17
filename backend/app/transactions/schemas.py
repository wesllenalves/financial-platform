from __future__ import annotations

import uuid
from datetime import date

from pydantic import Field, model_validator

from app.shared.schemas import ApiModel, MoneyField
from app.transactions.models import (
    PaymentMethod,
    TransactionSource,
    TransactionStatus,
    TransactionType,
    TransferDirection,
)


class TransactionCreate(ApiModel):
    account_id: uuid.UUID
    transaction_type: TransactionType
    description: str = Field(min_length=1, max_length=255)
    amount: MoneyField = Field(gt=0)
    transaction_date: date
    category_id: uuid.UUID | None = None
    due_date: date | None = None
    payment_date: date | None = None
    merchant: str | None = Field(default=None, max_length=160)
    payment_method: PaymentMethod | None = None
    installment_number: int | None = Field(default=None, ge=1)
    installment_count: int | None = Field(default=None, ge=1)
    recurring: bool = False
    status: TransactionStatus = TransactionStatus.paid
    notes: str | None = None

    @model_validator(mode="after")
    def _check_installments(self) -> TransactionCreate:
        if (
            self.installment_number
            and self.installment_count
            and self.installment_number > self.installment_count
        ):
            raise ValueError("installment_number cannot exceed installment_count")
        return self


class TransactionUpdate(ApiModel):
    account_id: uuid.UUID | None = None
    transaction_type: TransactionType | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    amount: MoneyField | None = Field(default=None, gt=0)
    transaction_date: date | None = None
    category_id: uuid.UUID | None = None
    due_date: date | None = None
    payment_date: date | None = None
    merchant: str | None = Field(default=None, max_length=160)
    payment_method: PaymentMethod | None = None
    recurring: bool | None = None
    status: TransactionStatus | None = None
    notes: str | None = None


class TransferCreate(ApiModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount: MoneyField = Field(gt=0)
    transaction_date: date
    description: str = Field(default="Transferência", max_length=255)

    @model_validator(mode="after")
    def _distinct_accounts(self) -> TransferCreate:
        if self.from_account_id == self.to_account_id:
            raise ValueError("A transfer needs two different accounts")
        return self


class TransactionOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    document_id: uuid.UUID | None
    transaction_type: TransactionType
    description: str
    amount: MoneyField
    transaction_date: date
    due_date: date | None
    payment_date: date | None
    merchant: str | None
    payment_method: PaymentMethod | None
    installment_number: int | None
    installment_count: int | None
    recurring: bool
    status: TransactionStatus
    source: TransactionSource
    transfer_direction: TransferDirection | None
    confidence_score: float | None
    notes: str | None
