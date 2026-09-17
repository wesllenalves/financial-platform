"""Calendar-month period helpers.

Periods are calendar months. The current month is partial and is always
labelled as such, because comparing 12 elapsed days against a full month is
the most common way a financial dashboard misleads.
"""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Period:
    year: int
    month: int

    @classmethod
    def from_date(cls, value: date) -> Period:
        return cls(value.year, value.month)

    @property
    def start(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def end(self) -> date:
        return date(self.year, self.month, monthrange(self.year, self.month)[1])

    @property
    def label(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def shift(self, months: int) -> Period:
        index = (self.year * 12 + (self.month - 1)) + months
        return Period(index // 12, index % 12 + 1)

    def previous_months(self, count: int) -> list[Period]:
        """The `count` complete months immediately before this one, oldest first."""
        return [self.shift(-offset) for offset in range(count, 0, -1)]

    def is_partial(self, today: date) -> bool:
        return self.year == today.year and self.month == today.month


def parse_period(value: str) -> Period:
    """Parse a 'YYYY-MM' string."""
    year_text, _, month_text = value.partition("-")
    year, month = int(year_text), int(month_text)
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month in period: {value}")
    return Period(year, month)
