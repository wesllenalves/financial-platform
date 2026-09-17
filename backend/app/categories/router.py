from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.categories.models import Category
from app.categories.schemas import CategoryCreate, CategoryOut
from app.categories.service import CategoryService
from app.core.db import get_db
from app.users.models import User

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Category]:
    return CategoryService(db).list(current_user.id)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Category:
    return CategoryService(db).create(current_user.id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    CategoryService(db).archive(current_user.id, category_id)
