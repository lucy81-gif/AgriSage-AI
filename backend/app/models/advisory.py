from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AdvisoryRecord(Base):
    """Evidence-backed draft that cannot become farmer-facing without approval."""

    __tablename__ = "advisory_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    advisory_id: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    farm_id: Mapped[str] = mapped_column(
        ForeignKey("farm_records.farm_id"), index=True, nullable=False
    )
    workflow_run_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    missing_information: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_APPROVAL", nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), default="draft_advisory", nullable=False)
    actor: Mapped[str] = mapped_column(String(120), default="agent", nullable=False)
    human_approval_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    approving_officer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approval_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
