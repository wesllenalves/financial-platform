from datetime import date
from decimal import Decimal

from app.metrics import domain
from app.metrics.domain import TransactionFact
from app.shared.periods import Period

TODAY = date(2026, 9, 17)


def fact(
    amount: str,
    day: int,
    month: int = 9,
    *,
    income: bool = False,
    transfer: bool = False,
    category: str = "food",
    merchant: str | None = None,
    year: int = 2026,
    identifier: str = "t",
) -> TransactionFact:
    return TransactionFact(
        id=identifier,
        amount=Decimal(amount),
        transaction_date=date(year, month, day),
        is_income=income,
        is_transfer=transfer,
        category_id=category,
        category_name=category,
        merchant_key=merchant,
    )


def test_summary_excludes_transfers_and_computes_savings_rate() -> None:
    facts = [
        fact("5000.00", 5, income=True, category="salary"),
        fact("1200.00", 6),
        fact("800.00", 7),
        fact("2000.00", 8, transfer=True),
    ]
    summary = domain.summarize_period(facts, Period(2026, 9), TODAY)

    assert summary.income == Decimal("5000.00")
    assert summary.expenses == Decimal("2000.00")
    assert summary.net_cash_flow == Decimal("3000.00")
    assert summary.savings_rate == Decimal("0.6000")
    assert summary.partial is True


def test_summary_without_income_reports_no_savings_rate() -> None:
    summary = domain.summarize_period([fact("100.00", 2)], Period(2026, 9), TODAY)

    assert summary.income == Decimal("0.00")
    assert summary.savings_rate is None


def test_summary_ignores_other_months() -> None:
    facts = [fact("100.00", 2, month=8), fact("50.00", 2, month=9)]
    assert domain.summarize_period(facts, Period(2026, 9), TODAY).expenses == Decimal("50.00")


def test_expenses_by_category_shares_sum_to_one() -> None:
    facts = [
        fact("300.00", 2, category="food"),
        fact("100.00", 3, category="food"),
        fact("100.00", 4, category="transport"),
    ]
    totals = domain.expenses_by_category(facts, Period(2026, 9))

    assert [item.total for item in totals] == [Decimal("400.00"), Decimal("100.00")]
    assert sum(item.share for item in totals) == Decimal("1.0000")


def test_average_expenses_uses_complete_months_only() -> None:
    facts = [
        fact("300.00", 10, month=6),
        fact("500.00", 10, month=7),
        fact("400.00", 10, month=8),
        fact("9999.00", 10, month=9),
    ]
    baseline = Period(2026, 9).previous_months(3)

    assert domain.average_expenses(facts, baseline) == Decimal("400.00")


def test_category_growth_reports_relative_change_against_the_baseline() -> None:
    facts = [
        fact("420.00", 10, month=6),
        fact("420.00", 10, month=7),
        fact("420.00", 10, month=8),
        fact("610.00", 10, month=9),
    ]
    growth = domain.category_growth(facts, Period(2026, 9), Period(2026, 9).previous_months(3))

    item, average, change = growth[0]
    assert item.total == Decimal("610.00")
    assert average == Decimal("420.00")
    assert change == Decimal("0.4524")


def test_detect_recurring_finds_a_stable_monthly_subscription() -> None:
    facts = [
        fact("55.90", 10, month=month, merchant="netflix", identifier=f"n{month}")
        for month in (6, 7, 8, 9)
    ]
    series = domain.detect_recurring(facts, TODAY)

    assert len(series) == 1
    assert series[0].merchant_key == "netflix"
    assert series[0].occurrences == 4
    assert series[0].mean_amount == Decimal("55.90")
    assert series[0].active is True


def test_detect_recurring_ignores_unstable_amounts() -> None:
    facts = [
        fact("40.00", 10, month=6, merchant="mercado", identifier="m6"),
        fact("300.00", 10, month=7, merchant="mercado", identifier="m7"),
        fact("120.00", 10, month=8, merchant="mercado", identifier="m8"),
    ]
    assert domain.detect_recurring(facts, TODAY) == []


def test_detect_recurring_ignores_merchants_seen_in_too_few_months() -> None:
    facts = [
        fact("55.90", 10, month=8, merchant="spotify", identifier="s8"),
        fact("55.90", 10, month=9, merchant="spotify", identifier="s9"),
    ]
    assert domain.detect_recurring(facts, TODAY) == []


def test_detect_recurring_marks_a_stopped_series_inactive() -> None:
    facts = [
        fact("29.90", 10, month=month, year=2026, merchant="gym", identifier=f"g{month}")
        for month in (3, 4, 5)
    ]
    series = domain.detect_recurring(facts, TODAY, lookback_months=9)

    assert series and series[0].active is False
