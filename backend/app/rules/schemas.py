from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.shared.schemas import ApiModel
from app.rules.models import FindingSeverity


class FindingOut(ApiModel):
    id: uuid.UUID
    rule_id: str
    period: date
    severity: FindingSeverity
    title: str
    evidence: dict
    estimated_monthly_impact: Decimal | None

class AnalysisRunResponse(ApiModel):
    message: str
    findings_count: int
