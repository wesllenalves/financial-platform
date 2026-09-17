from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.accounts.schemas import AccountBalanceOut, AccountCreate, AccountOut, AccountUpdate
from app.accounts.service import AccountService
from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.users.models import User

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountBalanceOut])
def list_accounts(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AccountBalanceOut]:
    service = AccountService(db)
    balances = service.balances(current_user.id)
    return [
        AccountBalanceOut(
            **AccountOut.model_validate(account).model_dump(),
            current_balance=balances[account.id],
        )
        for account in service.list(current_user.id)
    ]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AccountService(db).create(current_user.id, payload)


@router.patch("/{account_id}", response_model=AccountOut)
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return AccountService(db).update(current_user.id, account_id, payload)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    AccountService(db).delete(current_user.id, account_id)
