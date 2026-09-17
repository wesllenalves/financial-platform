from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import Field

from app.accounts.models import AccountType
from app.shared.schemas import ApiModel, MoneyField


class AccountCreate(ApiModel):
    name: str = Field(min_length=1, max_length=80)
    type: AccountType
    opening_balance: MoneyField = Decimal("0.00")
    institution: str | None = Field(default=None, max_length=80)


class AccountUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    institution: str | None = Field(default=None, max_length=80)
    opening_balance: MoneyField | None = None
    active: bool | None = None


class AccountOut(ApiModel):
    id: uuid.UUID
    name: str
    type: AccountType
    opening_balance: MoneyField
    institution: str | None
    active: bool


class AccountBalanceOut(AccountOut):
    """Opening balance plus the transaction history, computed on read."""

    current_balance: MoneyField
