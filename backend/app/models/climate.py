from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ClimateSignal(Base):
    """Structured synthetic weather observations and short forecasts."""

    __tablename__ = "climate_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    agroclimatic_zone: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False)
    rainfall_mm_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_rainfall_mm_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_anomaly_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    drought_indicator: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    heavy_rain_indicator: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    availability_status: Mapped[str] = mapped_column(String(30), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="SYNTHETIC", nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    data_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
