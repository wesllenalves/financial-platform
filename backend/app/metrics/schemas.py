from __future__ import annotations

from datetime import date

from app.shared.schemas import ApiModel, MoneyField, RateField


class PeriodSummaryOut(ApiModel):
    period: str
    partial: bool
    income: MoneyField
    expenses: MoneyField
    net_cash_flow: MoneyField
    savings_rate: RateField | None


class CategoryTotalOut(ApiModel):
    category_id: str | None
    category_name: str
    total: MoneyField
    share: RateField | None


class TrendPointOut(ApiModel):
    period: str
    income: MoneyField
    expenses: MoneyField


class RecurringSeriesOut(ApiModel):
    merchant_key: str
    occurrences: int
    mean_amount: MoneyField
    median_interval_days: int
    first_seen: date
    last_seen: date
    expected_next: date | None
    active: bool


class DashboardOut(ApiModel):
    current_balance: MoneyField
    total_debt: MoneyField
    summary: PeriodSummaryOut
    previous_summary: PeriodSummaryOut
    by_category: list[CategoryTotalOut]
    trend: list[TrendPointOut]
    upcoming_bills: list[UpcomingBillOut]


class UpcomingBillOut(ApiModel):
    id: str
    description: str
    amount: MoneyField
    due_date: date
    status: str


DashboardOut.model_rebuild()
