import uuid
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.shared.periods import Period
from app.transactions.models import Transaction, TransactionType
from app.accounts.models import Account
from app.rules.models import FindingSeverity


@dataclass
class FinancialContext:
    user_id: uuid.UUID
    period: Period
    transactions: list[Transaction]
    accounts: list[Account]

    @classmethod
    def build(cls, db: Session, user_id: uuid.UUID, period: Period) -> "FinancialContext":
        # Start and end dates for the given period
        date_from = period.start
        date_to = period.end

        transactions = list(
            db.execute(
                select(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= date_from,
                    Transaction.transaction_date <= date_to,
                    Transaction.deleted_at.is_(None)
                )
            ).scalars().all()
        )

        accounts = list(
            db.execute(
                select(Account).where(Account.user_id == user_id, Account.active.is_(True))
            ).scalars().all()
        )

        return cls(user_id=user_id, period=period, transactions=transactions, accounts=accounts)


@dataclass
class RuleResult:
    rule_id: str
    severity: FindingSeverity
    title: str
    evidence: dict
    estimated_monthly_impact: Decimal | None

    @property
    def evidence_key(self) -> str:
        # A stable hash of the evidence dictionary
        serialized = json.dumps(self.evidence, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class Rule(Protocol):
    rule_id: str

    def evaluate(self, ctx: FinancialContext) -> list[RuleResult]:
        ...
