"""Monetary helpers. Money is always Decimal, never float."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | int | str) -> Decimal:
    """Quantize a value to two decimal places using half-up rounding."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    """Safe ratio. Returns None when the denominator is zero or negative.

    A fabricated zero would be read as a real financial fact, so a missing
    ratio stays missing.
    """
    if denominator <= 0:
        return None
    return (numerator / denominator).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def percent_change(previous: Decimal, current: Decimal) -> Decimal | None:
    """Relative change from previous to current, as a fraction."""
    if previous <= 0:
        return None
    return ((current - previous) / previous).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
