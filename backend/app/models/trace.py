from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ToolCallLog(Base):
    """Audit record for tool calls and future workflow actions."""

    __tablename__ = "tool_call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    server_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    human_approval_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    approving_officer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approval_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkflowRun(Base):
    """A user-requested investigation and its auditable completion state."""

    __tablename__ = "workflow_runs"

    workflow_run_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_request: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_model_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_scope: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    final_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class WorkflowEvent(Base):
    """Public workflow state transition; deliberately excludes private chain-of-thought."""

    __tablename__ = "workflow_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    state_name: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DecisionEvent(Base):
    """Explicit risk change caused by newly combined evidence."""

    __tablename__ = "decision_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    farm_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    previous_risk: Mapped[str] = mapped_column(String(30), nullable=False)
    new_risk: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_tool: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FollowUpTask(Base):
    """Human task created when an investigation cannot safely complete."""

    __tablename__ = "follow_up_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    workflow_run_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EvaluationResult(Base):
    """Persisted result from a deterministic evaluation scenario."""

    __tablename__ = "evaluation_results"

    task_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    evaluation_run_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    scenario: Mapped[str] = mapped_column(String(160), nullable=False)
    expected_behaviour: Mapped[str] = mapped_column(Text, nullable=False)
    actual_behaviour: Mapped[str] = mapped_column(Text, nullable=False)
    tools_called: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    advisory_produced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence_used: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EvaluationRun(Base):
    """One persisted execution of the complete evaluation suite."""

    __tablename__ = "evaluation_runs"

    evaluation_run_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EvidenceItemRecord(Base):
    """Queryable copy of a retrieved fact that contributed to a farm assessment."""

    __tablename__ = "evidence_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    farm_id: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class HumanApproval(Base):
    """Immutable named officer decision associated with an advisory."""

    __tablename__ = "human_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    advisory_id: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    officer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
