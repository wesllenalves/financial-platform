from __future__ import annotations

import uuid

from pydantic import Field

from app.categories.models import CategoryKind, Essentiality
from app.shared.schemas import ApiModel


class CategoryCreate(ApiModel):
    name: str = Field(min_length=1, max_length=80)
    kind: CategoryKind
    parent_id: uuid.UUID | None = None
    essentiality: Essentiality | None = None


class CategoryOut(ApiModel):
    id: uuid.UUID
    name: str
    kind: CategoryKind
    parent_id: uuid.UUID | None
    essentiality: Essentiality | None
    system: bool
    archived: bool
