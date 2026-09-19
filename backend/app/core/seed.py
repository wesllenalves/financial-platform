import random
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.db import SessionLocal
from app.auth.service import AuthService
from app.auth.schemas import RegisterRequest
from app.accounts.service import AccountService
from app.accounts.schemas import AccountCreate
from app.accounts.models import AccountType
from app.transactions.service import TransactionService
from app.transactions.schemas import TransactionCreate
from app.transactions.models import TransactionType, TransactionStatus
from app.categories.models import Category
from app.users.models import User

def seed():
    with SessionLocal() as db:
        # Create user
        auth_service = AuthService(db)
        email = "seed@example.com"

        user = db.execute(select(User).where(User.email == email)).scalar()
        if not user:
            user = auth_service.register(RegisterRequest(
                name="Seed User",
                email=email,
                password="password"
            ))
            print(f"Created user: {user.email}")
        else:
            print("User already exists, aborting seed to prevent duplicates.")
            return

        # Create account
        account_service = AccountService(db)
        account = account_service.create(user.id, AccountCreate(
            name="Checking Account",
            type=AccountType.checking,
            opening_balance=Decimal("1000.00"),
            institution="Bank"
        ))

        # Load categories
        categories = db.execute(select(Category).where(Category.user_id == user.id)).scalars().all()
        income_cat = next(c for c in categories if c.name == "Salário")
        market_cat = next(c for c in categories if c.name == "Mercado")
        rent_cat = next(c for c in categories if c.name == "Aluguel")

        # Create transactions for 12 months
        transaction_service = TransactionService(db)
        start_date = date.today() - relativedelta(months=11)

        for i in range(12):
            current_date = start_date + relativedelta(months=i)

            # Income
            transaction_service.create(user.id, TransactionCreate(
                account_id=account.id,
                transaction_type=TransactionType.income,
                description="Salário",
                amount=Decimal("5000.00"),
                transaction_date=current_date.replace(day=5),
                category_id=income_cat.id,
                status=TransactionStatus.paid
            ))

            # Rent
            transaction_service.create(user.id, TransactionCreate(
                account_id=account.id,
                transaction_type=TransactionType.expense,
                description="Aluguel",
                amount=Decimal("1500.00"),
                transaction_date=current_date.replace(day=10),
                category_id=rent_cat.id,
                status=TransactionStatus.paid if current_date <= date.today() else TransactionStatus.pending
            ))

            # Variable expenses
            for _ in range(random.randint(3, 8)):
                day = random.randint(1, 28)
                transaction_service.create(user.id, TransactionCreate(
                    account_id=account.id,
                    transaction_type=TransactionType.expense,
                    description="Supermercado",
                    amount=Decimal(str(random.uniform(50.0, 300.0))).quantize(Decimal("0.01")),
                    transaction_date=current_date.replace(day=day),
                    category_id=market_cat.id,
                    status=TransactionStatus.paid if current_date.replace(day=day) <= date.today() else TransactionStatus.pending
                ))

        print("Successfully seeded 12 months of data.")

if __name__ == "__main__":
    seed()
