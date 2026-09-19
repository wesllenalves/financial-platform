from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class FindingSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Finding(Base):
    __tablename__ = "findings"

    # Simple hash of the evidence dictionary for deduplication
    __table_args__ = (
        UniqueConstraint("user_id", "rule_id", "period", "evidence_key", name="uq_finding_evidence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[date] = mapped_column(Date, nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False)
    evidence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    estimated_monthly_impact: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
