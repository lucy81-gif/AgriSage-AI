from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class PestSignal(Base):
    """Synthetic pest or disease reports grouped by crop and location."""

    __tablename__ = "pest_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    agroclimatic_zone: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    crop: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    pest_type: Mapped[str] = mapped_column(String(100), nullable=False)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
