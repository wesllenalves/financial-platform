from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.categories.models import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, user_id: uuid.UUID, include_archived: bool = False) -> list[Category]:
        stmt = select(Category).where(Category.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Category.archived.is_(False))
        return list(self.db.execute(stmt.order_by(Category.name)).scalars())

    def get(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Category | None:
        stmt = select(Category).where(Category.user_id == user_id, Category.id == category_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category
