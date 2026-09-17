from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Money crosses the wire as a string: JSON numbers are IEEE floats in
# JavaScript and would silently lose cents.
MoneyField = Annotated[
    Decimal,
    Field(max_digits=14, decimal_places=2),
    PlainSerializer(lambda v: format(v, "f"), return_type=str, when_used="json"),
]

RateField = Annotated[
    Decimal,
    PlainSerializer(lambda v: format(v, "f"), return_type=str, when_used="json"),
]

T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
