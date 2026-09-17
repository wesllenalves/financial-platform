"""Seed a demo user with six months of realistic transactions.

Usage: python -m app.cli.seed [email] [password]
"""

from __future__ import annotations

import random
import sys
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.accounts.models import Account, AccountType
from app.auth.schemas import RegisterRequest
from app.auth.service import AuthService
from app.categories.models import Category
from app.core.db import SessionLocal
from app.transactions.domain import normalize_merchant
from app.transactions.models import (
    Transaction,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)
from app.users.models import User

MONTHLY_INCOME = Decimal("7400.00")

FIXED = [
    ("Aluguel", "Moradia", Decimal("2100.00"), 5, "Imobiliária Central"),
    ("Energia elétrica", "Moradia", Decimal("180.00"), 12, "Enel"),
    ("Internet", "Moradia", Decimal("119.90"), 15, "Vivo Fibra"),
    ("Plano de saúde", "Saúde", Decimal("430.00"), 10, "Unimed"),
    ("Netflix", "Assinaturas", Decimal("55.90"), 8, "Netflix"),
    ("Spotify", "Assinaturas", Decimal("21.90"), 8, "Spotify"),
    ("Academia", "Saúde", Decimal("99.00"), 6, "Smart Fit"),
]

VARIABLE = [
    ("Supermercado", "Mercado", (280, 520), 4, "Supermercado Bom Preço"),
    ("Restaurante", "Restaurantes", (45, 130), 5, "Restaurante do Bairro"),
    ("Combustível", "Transporte", (150, 260), 2, "Posto Ipiranga"),
    ("Aplicativo de transporte", "Transporte", (18, 60), 4, "Uber"),
    ("Farmácia", "Saúde", (30, 140), 1, "Drogaria São Paulo"),
]


def _month_starts(today: date, months: int) -> list[date]:
    starts = []
    year, month = today.year, today.month
    for _ in range(months):
        starts.append(date(year, month, 1))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(starts))


def seed(email: str, password: str) -> None:
    random.seed(20260917)
    db = SessionLocal()
    try:
        existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing is not None:
            print(f"User {email} already exists; nothing to seed.")
            return

        user = AuthService(db).register(
            RegisterRequest(name="Usuário Demo", email=email, password=password)
        )
        checking = Account(
            user_id=user.id,
            name="Conta Corrente",
            type=AccountType.checking,
            opening_balance=Decimal("3200.00"),
            institution="Banco Demo",
        )
        savings = Account(
            user_id=user.id,
            name="Reserva",
            type=AccountType.savings,
            opening_balance=Decimal("8000.00"),
            institution="Banco Demo",
        )
        db.add_all([checking, savings])
        db.flush()

        categories = {
            category.name: category
            for category in db.execute(
                select(Category).where(Category.user_id == user.id)
            ).scalars()
        }

        def add(
            description: str,
            category_name: str,
            amount: Decimal,
            when: date,
            merchant: str,
            kind: TransactionType,
        ) -> None:
            category = categories.get(category_name)
            db.add(
                Transaction(
                    user_id=user.id,
                    account_id=checking.id,
                    category_id=category.id if category else None,
                    transaction_type=kind,
                    description=description,
                    amount=amount,
                    transaction_date=when,
                    payment_date=when,
                    merchant=merchant,
                    merchant_normalized=normalize_merchant(merchant),
                    status=TransactionStatus.paid,
                    source=TransactionSource.manual,
                    recurring=kind is TransactionType.expense
                    and description in {item[0] for item in FIXED},
                )
            )

        today = date.today()
        for start in _month_starts(today, 6):
            add(
                "Salário",
                "Salário",
                MONTHLY_INCOME,
                min(start.replace(day=5), today),
                "Empresa Demo",
                TransactionType.income,
            )
            for description, category, amount, day, merchant in FIXED:
                when = start.replace(day=day)
                if when <= today:
                    add(description, category, amount, when, merchant, TransactionType.expense)
            for description, category, (low, high), count, merchant in VARIABLE:
                for _ in range(count):
                    day = random.randint(1, 28)
                    when = start.replace(day=day)
                    if when <= today:
                        amount = Decimal(random.randint(low * 100, high * 100)) / 100
                        add(
                            description,
                            category,
                            amount.quantize(Decimal("0.01")),
                            when,
                            merchant,
                            TransactionType.expense,
                        )

        db.commit()
        print(f"Seeded {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed(
        sys.argv[1] if len(sys.argv) > 1 else "demo@example.com",
        sys.argv[2] if len(sys.argv) > 2 else "demo12345",
    )
