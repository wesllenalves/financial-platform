from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.core.errors import ValidationError
from app.metrics.schemas import (
    CategoryTotalOut,
    DashboardOut,
    PeriodSummaryOut,
    RecurringSeriesOut,
    TrendPointOut,
    UpcomingBillOut,
)
from app.metrics.service import MetricsService
from app.shared.periods import Period, parse_period
from app.users.models import User

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


def _period(value: str | None) -> Period:
    if value is None:
        return Period.from_date(date.today())
    try:
        return parse_period(value)
    except ValueError as exc:
        raise ValidationError("Period must be formatted as YYYY-MM.") from exc


@router.get("/summary", response_model=PeriodSummaryOut)
def summary(
    period: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MetricsService(db).summary(current_user.id, _period(period))


@router.get("/by-category", response_model=list[CategoryTotalOut])
def by_category(
    period: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MetricsService(db).by_category(current_user.id, _period(period))


@router.get("/trend", response_model=list[TrendPointOut])
def trend(
    period: str | None = None,
    months: int = Query(default=6, ge=2, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MetricsService(db).trend(current_user.id, _period(period), months)


@router.get("/recurring", response_model=list[RecurringSeriesOut])
def recurring(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return MetricsService(db).recurring(current_user.id)


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    period: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardOut:
    service = MetricsService(db)
    selected = _period(period)
    previous = selected.shift(-1)
    return DashboardOut(
        current_balance=service.current_balance(current_user.id),
        total_debt=0,
        summary=PeriodSummaryOut.model_validate(service.summary(current_user.id, selected)),
        previous_summary=PeriodSummaryOut.model_validate(
            service.summary(current_user.id, previous)
        ),
        by_category=[
            CategoryTotalOut.model_validate(item)
            for item in service.by_category(current_user.id, selected)
        ],
        trend=[
            TrendPointOut.model_validate(item)
            for item in service.trend(current_user.id, selected, 6)
        ],
        upcoming_bills=[
            UpcomingBillOut(
                id=str(bill.id),
                description=bill.description,
                amount=bill.amount,
                due_date=bill.due_date,
                status=bill.status.value,
            )
            for bill in service.upcoming_bills(current_user.id)
        ],
    )
