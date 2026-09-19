from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.rules.schemas import FindingOut, AnalysisRunResponse
from app.rules.service import RuleService
from app.users.models import User
from app.shared.periods import Period
from datetime import date

router = APIRouter(tags=["rules"])


@router.post("/api/v1/analysis/run", response_model=AnalysisRunResponse, status_code=status.HTTP_200_OK)
def run_analysis(
    period_str: str | None = Query(None, alias="period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not period_str:
        period = Period.from_date(date.today())
    else:
        from app.shared.periods import parse_period
        period = parse_period(period_str)

    count = RuleService(db).run_analysis(current_user.id, period)
    return AnalysisRunResponse(message="Analysis complete", findings_count=count)


@router.get("/api/v1/findings", response_model=list[FindingOut])
def list_findings(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RuleService(db).list_findings(current_user.id, limit, offset)
