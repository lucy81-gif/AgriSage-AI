from datetime import date, datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.farm import FarmRead


RiskLevel = Literal["LOW", "MODERATE", "HIGH", "INSUFFICIENT_EVIDENCE"]
AdvisoryStatus = Literal["PENDING_APPROVAL", "APPROVED", "EDITED", "REJECTED"]


class EvidenceItem(BaseModel):
    id: str | None = None
    label: str
    detail: str
    source: str
    observed_at: datetime | date | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    kind: str = "decision"


class ClimateSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    signal_id: str
    district: str
    agroclimatic_zone: str
    signal_date: date
    rainfall_mm_7d: float | None
    forecast_rainfall_mm_7d: float | None
    average_temperature_c: float | None
    rainfall_anomaly_pct: float | None
    drought_indicator: bool | None
    heavy_rain_indicator: bool | None
    availability_status: str
    source_type: str = "SYNTHETIC"
    freshness: str | None = None
    source: str
    observed_at: datetime
    data_confidence: float
    notes: str | None = None


class PestSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    signal_id: str
    district: str
    agroclimatic_zone: str
    crop: str
    pest_type: str
    report_count: int
    severity: str
    report_date: date
    confidence: float
    source: str
    notes: str | None = None


class RiskAssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    risk_level: RiskLevel
    confidence: float
    evidence_strength: float
    risk_factors: list[str]
    missing_evidence: list[str]
    recommended_next_action: str
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)
    created_at: datetime


class FarmDetailRead(FarmRead):
    risk_level: RiskLevel | None = None
    confidence: float | None = None
    evidence_strength: float | None = None
    recommended_next_action: str | None = None
    risk_factors: list[str] = Field(default_factory=list)
    supporting_evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    climate: ClimateSignalRead | None = None
    pest_signals: list[PestSignalRead] = Field(default_factory=list)
    advisory_status: AdvisoryStatus | None = None
    last_analysed_at: datetime | None = None
    rank_reason: str | None = None


class AdvisoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    advisory_id: str
    farm_id: str
    farm: FarmDetailRead | None = None
    crop: str | None = None
    risk_level: RiskLevel
    recommendation: str
    evidence: list[EvidenceItem]
    missing_information: list[str]
    confidence: float | None
    created_at: datetime
    status: AdvisoryStatus
    reason: str | None = None
    actor: str | None = None
    approving_officer: str | None = None
    approval_timestamp: datetime | None = None
    edited_text: str | None = None
    rejection_reason: str | None = None


class ToolCallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    server_name: str | None = None
    tool_name: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    timestamp: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    output_summary: str | None = None
    status: str
    action_type: str | None = None
    human_approval_required: bool = False
    error_message: str | None = None


class DecisionChangeRead(BaseModel):
    from_: str = Field(alias="from")
    to: str
    reason: str
    source: str
    timestamp: datetime

    model_config = ConfigDict(populate_by_name=True)


class TraceEventRead(BaseModel):
    id: str
    label: str
    detail: str | None = None
    timestamp: datetime
    status: str
    tool_call: ToolCallRead | None = None
    decision_change: DecisionChangeRead | None = None


class TraceRunRead(BaseModel):
    workflow_run_id: str
    request: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    events: list[TraceEventRead]
    tool_calls: list[ToolCallRead]
    final_summary: dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    district: str | None = Field(default=None, max_length=80)
    crop: str | None = Field(default=None, max_length=40)
    analysis_start: date | None = None
    analysis_end: date | None = None
    scope: Literal["all", "farm", "cluster"] = "all"
    farm_id: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def validate_analysis_scope(self) -> "AnalysisRequest":
        if self.scope == "farm" and not self.farm_id:
            raise ValueError("farm_id is required for one-farm analysis")
        if self.analysis_start and self.analysis_end and self.analysis_start > self.analysis_end:
            raise ValueError("analysis_start must not be after analysis_end")
        return self


class AnalysisRunResponse(BaseModel):
    workflow_run_id: str
    status: str
    message: str
    farms_analysed: int
    advisories_created: int


class ApprovalRequest(BaseModel):
    officer_name: str = Field(
        min_length=2,
        max_length=120,
        validation_alias=AliasChoices("officer_name", "officer"),
    )


class EditRequest(BaseModel):
    officer_name: str = Field(
        min_length=2,
        max_length=120,
        validation_alias=AliasChoices("officer_name", "officer"),
    )
    recommendation: str = Field(min_length=10, max_length=5000)


class RejectRequest(BaseModel):
    officer_name: str = Field(
        min_length=2,
        max_length=120,
        validation_alias=AliasChoices("officer_name", "officer"),
    )
    rejection_reason: str = Field(
        min_length=3,
        max_length=1000,
        validation_alias=AliasChoices("rejection_reason", "reason"),
    )


class EvaluationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    evaluation_run_id: str | None = None
    scenario: str
    expected_behaviour: str
    actual_behaviour: str
    tools_called: list[str]
    advisory_produced: bool
    evidence_used: list[str]
    result: str
    run_id: str | None = None
    recorded_at: datetime | None = None


class FollowUpTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: str
    workflow_run_id: str | None
    reason: str
    priority: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class FollowUpCreate(BaseModel):
    farm_id: str
    reason: str = Field(min_length=3, max_length=2000)
    priority: str = Field(default="MODERATE", max_length=30)
    workflow_run_id: str | None = None
