from datetime import date

from pydantic import BaseModel, ConfigDict


class FarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farm_id: str
    household_id: str
    district: str
    agroclimatic_zone: str
    crop: str
    crop_variety: str
    planting_date: date | None
    current_growth_stage: str | None
    soil_type: str | None
    previous_crop: str | None
    previous_pest_incidents: list
    previous_disease_incidents: list
    previous_interventions: list
    field_size_ha: float
    irrigation_type: str
    last_inspection_date: date | None
    data_quality_notes: str | None
