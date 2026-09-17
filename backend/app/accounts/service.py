from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.accounts.repository import AccountRepository
from app.accounts.schemas import AccountCreate, AccountUpdate
from app.core.errors import ConflictError, NotFoundError
from app.shared.money import money
from app.transactions.models import Transaction, TransactionType, TransferDirection


class AccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AccountRepository(db)

    def list(self, user_id: uuid.UUID) -> list[Account]:
        return self.repo.list(user_id)

    def get_or_404(self, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
        account = self.repo.get(user_id, account_id)
        if account is None:
            raise NotFoundError("Account not found.")
        return account

    def create(self, user_id: uuid.UUID, payload: AccountCreate) -> Account:
        account = self.repo.add(
            Account(
                user_id=user_id,
                name=payload.name.strip(),
                type=payload.type,
                opening_balance=money(payload.opening_balance),
                institution=payload.institution,
            )
        )
        self.db.commit()
        return account

    def update(self, user_id: uuid.UUID, account_id: uuid.UUID, payload: AccountUpdate) -> Account:
        account = self.get_or_404(user_id, account_id)
        data = payload.model_dump(exclude_unset=True)
        if "opening_balance" in data and data["opening_balance"] is not None:
            data["opening_balance"] = money(data["opening_balance"])
        for field, value in data.items():
            setattr(account, field, value)
        self.db.commit()
        return account

    def delete(self, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
        account = self.get_or_404(user_id, account_id)
        used = self.db.execute(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.account_id == account.id, Transaction.deleted_at.is_(None))
        ).scalar_one()
        if used:
            raise ConflictError(
                "This account has transactions. Deactivate it instead of deleting it."
            )
        self.db.delete(account)
        self.db.commit()

    def balances(self, user_id: uuid.UUID) -> dict[uuid.UUID, Decimal]:
        """Current balance per account: opening balance plus income minus expenses.

        Transfers move money between accounts and are stored as two rows, so
        they are included here but cancel out across accounts.
        """
        signed = case(
            (Transaction.transaction_type == TransactionType.income, Transaction.amount),
            (Transaction.transfer_direction == TransferDirection.incoming, Transaction.amount),
            else_=-Transaction.amount,
        )
        rows = self.db.execute(
            select(Transaction.account_id, func.coalesce(func.sum(signed), 0))
            .where(Transaction.user_id == user_id, Transaction.deleted_at.is_(None))
            .group_by(Transaction.account_id)
        ).all()
        movement = {account_id: Decimal(total) for account_id, total in rows}
        return {
            account.id: money(account.opening_balance + movement.get(account.id, Decimal("0")))
            for account in self.repo.list(user_id)
        }
