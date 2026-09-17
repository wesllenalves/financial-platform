from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import Account


class AccountRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, user_id: uuid.UUID) -> list[Account]:
        stmt = select(Account).where(Account.user_id == user_id).order_by(Account.name)
        return list(self.db.execute(stmt).scalars())

    def get(self, user_id: uuid.UUID, account_id: uuid.UUID) -> Account | None:
        stmt = select(Account).where(Account.user_id == user_id, Account.id == account_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, account: Account) -> Account:
        self.db.add(account)
        self.db.flush()
        return account
