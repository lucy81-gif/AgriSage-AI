from pydantic import BaseModel, ConfigDict


class BootstrapSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farms: int
    climate_signals: int
    pest_signals: int
    advisory_records: int
    tool_call_logs: int
    districts: list[str]
    crops: list[str]
