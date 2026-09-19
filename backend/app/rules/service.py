import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.rules.engine import FinancialContext
from app.rules.registry import RULES_REGISTRY
from app.rules.models import Finding
from app.shared.periods import Period


class RuleService:
    def __init__(self, db: Session):
        self.db = db

    def list_findings(self, user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[Finding]:
        return list(
            self.db.execute(
                select(Finding)
                .where(Finding.user_id == user_id)
                .order_by(Finding.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).scalars().all()
        )

    def run_analysis(self, user_id: uuid.UUID, period: Period) -> int:
        """Run all rules and upsert findings based on evidence key."""
        ctx = FinancialContext.build(self.db, user_id, period)

        all_results = []
        for rule in RULES_REGISTRY:
            all_results.extend(rule.evaluate(ctx))

        if not all_results:
            return 0

        # Upsert findings
        for res in all_results:
            stmt = insert(Finding).values(
                user_id=user_id,
                rule_id=res.rule_id,
                period=period.start,
                severity=res.severity,
                title=res.title,
                evidence=res.evidence,
                evidence_key=res.evidence_key,
                estimated_monthly_impact=res.estimated_monthly_impact
            )

            # On conflict (meaning we already found this exact evidence in this period for this rule), update it.
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "rule_id", "period", "evidence_key"],
                set_=dict(
                    severity=stmt.excluded.severity,
                    title=stmt.excluded.title,
                    evidence=stmt.excluded.evidence,
                    estimated_monthly_impact=stmt.excluded.estimated_monthly_impact
                )
            )
            self.db.execute(stmt)

        self.db.commit()
        return len(all_results)
