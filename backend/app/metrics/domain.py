"""Deterministic financial calculations.

Pure functions over plain dataclasses: no database, no HTTP, no LLM. Every
number the product shows is produced here, so this module is where the
hand-computed unit tests live.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from statistics import median

from app.shared.money import ZERO, money, percent_change, ratio
from app.shared.periods import Period


@dataclass(frozen=True)
class TransactionFact:
    """The only transaction shape the engine knows about."""

    id: str
    amount: Decimal
    transaction_date: date
    is_income: bool
    is_transfer: bool
    category_id: str | None
    category_name: str | None
    merchant_key: str | None


@dataclass
class PeriodSummary:
    period: str
    partial: bool
    income: Decimal
    expenses: Decimal
    net_cash_flow: Decimal
    savings_rate: Decimal | None


@dataclass
class CategoryTotal:
    category_id: str | None
    category_name: str
    total: Decimal
    share: Decimal | None


@dataclass
class TrendPoint:
    period: str
    income: Decimal
    expenses: Decimal


@dataclass
class RecurringSeries:
    merchant_key: str
    occurrences: int
    mean_amount: Decimal
    median_interval_days: int
    first_seen: date
    last_seen: date
    expected_next: date | None
    active: bool
    transaction_ids: list[str] = field(default_factory=list)


def _in_period(fact: TransactionFact, period: Period) -> bool:
    return period.start <= fact.transaction_date <= period.end


def summarize_period(facts: list[TransactionFact], period: Period, today: date) -> PeriodSummary:
    income = ZERO
    expenses = ZERO
    for fact in facts:
        if fact.is_transfer or not _in_period(fact, period):
            continue
        if fact.is_income:
            income += fact.amount
        else:
            expenses += fact.amount
    income, expenses = money(income), money(expenses)
    return PeriodSummary(
        period=period.label,
        partial=period.is_partial(today),
        income=income,
        expenses=expenses,
        net_cash_flow=money(income - expenses),
        savings_rate=ratio(income - expenses, income),
    )


def expenses_by_category(facts: list[TransactionFact], period: Period) -> list[CategoryTotal]:
    totals: dict[tuple[str | None, str], Decimal] = {}
    for fact in facts:
        if fact.is_transfer or fact.is_income or not _in_period(fact, period):
            continue
        key = (fact.category_id, fact.category_name or "Sem categoria")
        totals[key] = totals.get(key, ZERO) + fact.amount

    total = money(sum(totals.values(), ZERO))
    results = [
        CategoryTotal(
            category_id=category_id,
            category_name=name,
            total=money(value),
            share=ratio(value, total),
        )
        for (category_id, name), value in totals.items()
    ]
    return sorted(results, key=lambda item: item.total, reverse=True)


def monthly_trend(facts: list[TransactionFact], periods: list[Period]) -> list[TrendPoint]:
    points = []
    for period in periods:
        income = ZERO
        expenses = ZERO
        for fact in facts:
            if fact.is_transfer or not _in_period(fact, period):
                continue
            if fact.is_income:
                income += fact.amount
            else:
                expenses += fact.amount
        points.append(TrendPoint(period.label, money(income), money(expenses)))
    return points


def average_expenses(facts: list[TransactionFact], periods: list[Period]) -> Decimal | None:
    """Mean monthly expense over complete months. A partial month is never averaged in."""
    if not periods:
        return None
    totals = [point.expenses for point in monthly_trend(facts, periods)]
    return money(sum(totals, ZERO) / Decimal(len(totals)))


def category_growth(
    facts: list[TransactionFact], period: Period, baseline: list[Period]
) -> list[tuple[CategoryTotal, Decimal, Decimal | None]]:
    """Per-category current total, baseline average, and relative change."""
    current = {item.category_id: item for item in expenses_by_category(facts, period)}
    baseline_totals: dict[str | None, list[Decimal]] = {}
    for baseline_period in baseline:
        for item in expenses_by_category(facts, baseline_period):
            baseline_totals.setdefault(item.category_id, []).append(item.total)

    results: list[tuple[CategoryTotal, Decimal, Decimal | None]] = []
    for category_id, item in current.items():
        history = baseline_totals.get(category_id, [])
        if not history:
            results.append((item, ZERO, None))
            continue
        average = money(sum(history, ZERO) / Decimal(len(baseline)))
        results.append((item, average, percent_change(average, item.total)))
    return results


def detect_recurring(
    facts: list[TransactionFact],
    today: date,
    lookback_months: int = 6,
    min_occurrences: int = 3,
) -> list[RecurringSeries]:
    """Group expenses by merchant and keep the stable, repeating ones.

    Stability means both the amount and the interval repeat: a merchant billed
    at wildly different amounts is shopping, not a subscription.
    """
    window_start = Period.from_date(today).shift(-lookback_months).start
    groups: dict[str, list[TransactionFact]] = {}
    for fact in facts:
        if fact.is_income or fact.is_transfer or fact.merchant_key is None:
            continue
        if fact.transaction_date < window_start:
            continue
        groups.setdefault(fact.merchant_key, []).append(fact)

    series: list[RecurringSeries] = []
    for merchant_key, items in groups.items():
        items.sort(key=lambda fact: fact.transaction_date)
        months = {(fact.transaction_date.year, fact.transaction_date.month) for fact in items}
        if len(months) < min_occurrences:
            continue

        amounts = [fact.amount for fact in items]
        mean_amount = money(sum(amounts, ZERO) / Decimal(len(amounts)))
        if mean_amount <= 0:
            continue
        spread = max(amounts) - min(amounts)
        if spread > mean_amount * Decimal("0.30"):
            continue

        gaps = [
            (items[index].transaction_date - items[index - 1].transaction_date).days
            for index in range(1, len(items))
        ]
        median_gap = int(median(gaps)) if gaps else 0
        if not (6 <= median_gap <= 96):
            continue

        last_seen = items[-1].transaction_date
        expected_next = date.fromordinal(last_seen.toordinal() + median_gap)
        series.append(
            RecurringSeries(
                merchant_key=merchant_key,
                occurrences=len(items),
                mean_amount=mean_amount,
                median_interval_days=median_gap,
                first_seen=items[0].transaction_date,
                last_seen=last_seen,
                expected_next=expected_next,
                active=(today - last_seen).days <= median_gap * 2,
                transaction_ids=[fact.id for fact in items],
            )
        )
    return sorted(series, key=lambda item: item.mean_amount, reverse=True)
