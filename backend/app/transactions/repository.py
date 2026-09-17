from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, timedelta

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.transactions.models import Transaction, TransactionStatus, TransactionType


class TransactionFilters:
    def __init__(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        category_id: uuid.UUID | None = None,
        account_id: uuid.UUID | None = None,
        transaction_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        search: str | None = None,
    ) -> None:
        self.date_from = date_from
        self.date_to = date_to
        self.category_id = category_id
        self.account_id = account_id
        self.transaction_type = transaction_type
        self.status = status
        self.search = search


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _scoped(self, user_id: uuid.UUID) -> Select:
        return select(Transaction).where(
            Transaction.user_id == user_id, Transaction.deleted_at.is_(None)
        )

    def _apply(self, stmt: Select, filters: TransactionFilters) -> Select:
        if filters.date_from:
            stmt = stmt.where(Transaction.transaction_date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Transaction.transaction_date <= filters.date_to)
        if filters.category_id:
            stmt = stmt.where(Transaction.category_id == filters.category_id)
        if filters.account_id:
            stmt = stmt.where(Transaction.account_id == filters.account_id)
        if filters.transaction_type:
            stmt = stmt.where(Transaction.transaction_type == filters.transaction_type)
        if filters.status:
            stmt = stmt.where(Transaction.status == filters.status)
        if filters.search:
            pattern = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(Transaction.description.ilike(pattern), Transaction.merchant.ilike(pattern))
            )
        return stmt

    def list(
        self, user_id: uuid.UUID, filters: TransactionFilters, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        stmt = self._apply(self._scoped(user_id), filters)
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        rows = self.db.execute(
            stmt.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).scalars()
        return list(rows), total

    def get(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction | None:
        stmt = self._scoped(user_id).where(Transaction.id == transaction_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def find_possible_duplicates(
        self,
        user_id: uuid.UUID,
        merchant_normalized: str | None,
        amount,
        transaction_date: date,
        window_days: int = 3,
    ) -> Sequence[Transaction]:
        if merchant_normalized is None:
            return []
        window = timedelta(days=window_days)
        stmt = self._scoped(user_id).where(
            Transaction.merchant_normalized == merchant_normalized,
            Transaction.amount == amount,
            Transaction.transaction_date >= transaction_date - window,
            Transaction.transaction_date <= transaction_date + window,
        )
        return list(self.db.execute(stmt).scalars())
