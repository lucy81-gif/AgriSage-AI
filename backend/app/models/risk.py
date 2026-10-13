from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class RiskAssessment(Base):
    """Deterministic structured risk output for one farm in one workflow run."""

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    farm_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_strength: Mapped[float] = mapped_column(Float, nullable=False)
    risk_factors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    missing_evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommended_next_action: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_chain: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
