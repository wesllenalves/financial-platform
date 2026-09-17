from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.service import AccountService
from app.categories.models import Category
from app.metrics import domain
from app.metrics.domain import TransactionFact
from app.shared.money import ZERO, money
from app.shared.periods import Period
from app.transactions.models import Transaction, TransactionStatus, TransactionType


class MetricsService:
    """Loads facts once and delegates every calculation to the pure engine."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.accounts = AccountService(db)

    def load_facts(self, user_id: uuid.UUID, since: date | None = None) -> list[TransactionFact]:
        stmt = (
            select(Transaction, Category.name)
            .join(Category, Category.id == Transaction.category_id, isouter=True)
            .where(Transaction.user_id == user_id, Transaction.deleted_at.is_(None))
        )
        if since is not None:
            stmt = stmt.where(Transaction.transaction_date >= since)

        facts = []
        for transaction, category_name in self.db.execute(stmt).all():
            facts.append(
                TransactionFact(
                    id=str(transaction.id),
                    amount=Decimal(transaction.amount),
                    transaction_date=transaction.transaction_date,
                    is_income=transaction.transaction_type is TransactionType.income,
                    is_transfer=transaction.transaction_type is TransactionType.transfer,
                    category_id=str(transaction.category_id) if transaction.category_id else None,
                    category_name=category_name,
                    merchant_key=transaction.merchant_normalized,
                )
            )
        return facts

    def current_balance(self, user_id: uuid.UUID) -> Decimal:
        return money(sum(self.accounts.balances(user_id).values(), ZERO))

    def upcoming_bills(self, user_id: uuid.UUID, days: int = 30) -> list[Transaction]:
        today = date.today()
        stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                Transaction.status.in_([TransactionStatus.pending, TransactionStatus.overdue]),
                Transaction.due_date.is_not(None),
                Transaction.due_date <= today + timedelta(days=days),
            )
            .order_by(Transaction.due_date)
        )
        return list(self.db.execute(stmt).scalars())

    def summary(self, user_id: uuid.UUID, period: Period) -> domain.PeriodSummary:
        return domain.summarize_period(self.load_facts(user_id), period, date.today())

    def by_category(self, user_id: uuid.UUID, period: Period) -> list[domain.CategoryTotal]:
        return domain.expenses_by_category(self.load_facts(user_id), period)

    def trend(self, user_id: uuid.UUID, period: Period, months: int) -> list[domain.TrendPoint]:
        periods = [*period.previous_months(months - 1), period]
        return domain.monthly_trend(self.load_facts(user_id), periods)

    def recurring(self, user_id: uuid.UUID) -> list[domain.RecurringSeries]:
        return domain.detect_recurring(self.load_facts(user_id), date.today())
