from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class FarmRecord(Base):
    """Synthetic plot and household context used by the advisory workflow."""

    __tablename__ = "farm_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    household_id: Mapped[str] = mapped_column(String(20), nullable=False)
    district: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    agroclimatic_zone: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    crop: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    crop_variety: Mapped[str] = mapped_column(String(80), nullable=False)
    planting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    current_growth_stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    previous_crop: Mapped[str | None] = mapped_column(String(40), nullable=True)
    previous_pest_incidents: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    previous_disease_incidents: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    previous_interventions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    field_size_ha: Mapped[float] = mapped_column(Float, nullable=False)
    irrigation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    last_inspection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_quality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
