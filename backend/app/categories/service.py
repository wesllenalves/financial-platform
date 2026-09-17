from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.categories.defaults import DEFAULT_CATEGORIES
from app.categories.models import Category
from app.categories.repository import CategoryRepository
from app.categories.schemas import CategoryCreate
from app.core.errors import ConflictError, NotFoundError


class CategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    def seed_defaults(self, user_id: uuid.UUID) -> None:
        for name, kind, essentiality, children in DEFAULT_CATEGORIES:
            parent = Category(
                user_id=user_id,
                name=name,
                kind=kind,
                essentiality=essentiality,
                system=True,
            )
            self.repo.add(parent)
            for child_name, child_essentiality in children:
                self.repo.add(
                    Category(
                        user_id=user_id,
                        parent_id=parent.id,
                        name=child_name,
                        kind=kind,
                        essentiality=child_essentiality,
                        system=True,
                    )
                )

    def list(self, user_id: uuid.UUID) -> list[Category]:
        return self.repo.list(user_id)

    def get_or_404(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
        category = self.repo.get(user_id, category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    def create(self, user_id: uuid.UUID, payload: CategoryCreate) -> Category:
        if payload.parent_id is not None:
            parent = self.get_or_404(user_id, payload.parent_id)
            if parent.kind != payload.kind:
                raise ConflictError("A subcategory must have the same kind as its parent.")
        category = self.repo.add(
            Category(
                user_id=user_id,
                parent_id=payload.parent_id,
                name=payload.name.strip(),
                kind=payload.kind,
                essentiality=payload.essentiality,
            )
        )
        self.db.commit()
        return category

    def archive(self, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
        category = self.get_or_404(user_id, category_id)
        if category.system:
            raise ConflictError(
                "Default categories cannot be removed, only archived by the system."
            )
        category.archived = True
        self.db.commit()
