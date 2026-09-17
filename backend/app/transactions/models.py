from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    transfer = "transfer"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    canceled = "canceled"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    debit = "debit"
    credit = "credit"
    pix = "pix"
    boleto = "boleto"
    transfer = "transfer"
    other = "other"


class TransferDirection(str, enum.Enum):
    outgoing = "outgoing"
    incoming = "incoming"


class TransactionSource(str, enum.Enum):
    manual = "manual"
    pdf = "pdf"
    xml = "xml"
    json = "json"
    image = "image"
    ai_extraction = "ai_extraction"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_amount_positive"),
        CheckConstraint(
            "installment_count IS NULL OR installment_number <= installment_count",
            name="ck_transaction_installments",
        ),
        CheckConstraint(
            "(transaction_type = 'transfer') = (transfer_direction IS NOT NULL)",
            name="ck_transaction_transfer_direction",
        ),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_category_date", "user_id", "category_id", "transaction_date"),
        Index("ix_transactions_user_account_date", "user_id", "account_id", "transaction_date"),
        Index("ix_transactions_user_due", "user_id", "due_date"),
        Index(
            "ix_transactions_dedup", "user_id", "merchant_normalized", "amount", "transaction_date"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # Amounts are always positive; direction is carried by transaction_type.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    merchant: Mapped[str | None] = mapped_column(String(160), nullable=True)
    merchant_normalized: Mapped[str | None] = mapped_column(String(160), nullable=True)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod, name="payment_method"), nullable=True
    )

    installment_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    installment_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    installment_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )

    recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recurrence_group_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), nullable=True
    )

    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"),
        nullable=False,
        default=TransactionStatus.paid,
    )
    source: Mapped[TransactionSource] = mapped_column(
        Enum(TransactionSource, name="transaction_source"),
        nullable=False,
        default=TransactionSource.manual,
    )
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    transfer_peer_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    transfer_direction: Mapped[TransferDirection | None] = mapped_column(
        Enum(TransferDirection, name="transfer_direction"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
