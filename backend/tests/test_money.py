from decimal import Decimal

import pytest

from app.shared.money import money, percent_change, ratio


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10.005", "10.01"),
        ("10.004", "10.00"),
        ("0.1", "0.10"),
        ("-3.456", "-3.46"),
    ],
)
def test_money_quantizes_half_up(value: str, expected: str) -> None:
    assert money(Decimal(value)) == Decimal(expected)


def test_ratio_returns_none_instead_of_a_fabricated_zero() -> None:
    assert ratio(Decimal("100"), Decimal("0")) is None
    assert ratio(Decimal("100"), Decimal("-5")) is None


def test_ratio_computes_four_decimals() -> None:
    assert ratio(Decimal("250"), Decimal("1000")) == Decimal("0.2500")


def test_percent_change() -> None:
    assert percent_change(Decimal("420"), Decimal("610")) == Decimal("0.4524")
    assert percent_change(Decimal("0"), Decimal("610")) is None
