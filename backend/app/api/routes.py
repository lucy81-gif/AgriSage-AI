from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.agents.graph import run_analysis_workflow
from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.models import (
    AdvisoryRecord,
    ClimateSignal,
    DecisionEvent,
    EvaluationResult,
    FarmRecord,
    HumanApproval,
    PestSignal,
    RiskAssessment,
    ToolCallLog,
    WorkflowEvent,
    WorkflowRun,
)
from backend.app.schemas.api import (
    AdvisoryRead,
    AnalysisRequest,
    AnalysisRunResponse,
    ApprovalRequest,
    ClimateSignalRead,
    EditRequest,
    EvaluationResultRead,
    FarmDetailRead,
    FollowUpCreate,
    FollowUpTaskRead,
    PestSignalRead,
    RejectRequest,
    RiskAssessmentRead,
    ToolCallRead,
    TraceEventRead,
    TraceRunRead,
)
from backend.app.services.tool_service import record_tool_call
from backend.app.services.model_provider import ModelUnavailable


router = APIRouter()


def _latest_assessment(db: Session, farm_id: str) -> RiskAssessment | None:
    return db.scalar(
        select(RiskAssessment)
        .where(RiskAssessment.farm_id == farm_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    )


def _latest_climate(db: Session, farm: FarmRecord) -> ClimateSignal | None:
    return db.scalar(
        select(ClimateSignal)
        .where(
            ClimateSignal.district == farm.district,
            ClimateSignal.agroclimatic_zone == farm.agroclimatic_zone,
        )
        .order_by(ClimateSignal.signal_date.desc())
        .limit(1)
    )


def _climate_payload(signal: ClimateSignal | None) -> dict | None:
    if signal is None:
        return None
    age_days = (datetime.utcnow() - signal.observed_at).days
    freshness = (
        "UNAVAILABLE"
        if signal.availability_status == "UNAVAILABLE"
        else "STALE"
        if signal.availability_status == "STALE" or age_days > 14
        else "FRESH"
    )
    return {
        "signal_id": signal.signal_id,
        "district": signal.district,
        "agroclimatic_zone": signal.agroclimatic_zone,
        "signal_date": signal.signal_date,
        "rainfall_mm_7d": signal.rainfall_mm_7d,
        "forecast_rainfall_mm_7d": signal.forecast_rainfall_mm_7d,
        "average_temperature_c": signal.average_temperature_c,
        "rainfall_anomaly_pct": signal.rainfall_anomaly_pct,
        "drought_indicator": signal.drought_indicator,
        "heavy_rain_indicator": signal.heavy_rain_indicator,
        "availability_status": freshness,
        "source_type": signal.source_type,
        "source": signal.source,
        "observed_at": signal.observed_at,
        "data_confidence": signal.data_confidence,
        "freshness": freshness,
        "notes": signal.notes,
    }


def _farm_payload(db: Session, farm: FarmRecord) -> dict:
    assessment = _latest_assessment(db, farm.farm_id)
    climate = _latest_climate(db, farm)
    pests = db.scalars(
        select(PestSignal)
        .where(
            PestSignal.crop == farm.crop,
            PestSignal.agroclimatic_zone == farm.agroclimatic_zone,
        )
        .order_by(PestSignal.report_date.desc())
    ).all()
    advisory = db.scalar(
        select(AdvisoryRecord)
        .where(AdvisoryRecord.farm_id == farm.farm_id)
        .order_by(AdvisoryRecord.created_at.desc())
        .limit(1)
    )
    payload = {
        "farm_id": farm.farm_id,
        "household_id": farm.household_id,
        "district": farm.district,
        "agroclimatic_zone": farm.agroclimatic_zone,
        "crop": farm.crop,
        "crop_variety": farm.crop_variety,
        "planting_date": farm.planting_date,
        "current_growth_stage": farm.current_growth_stage,
        "soil_type": farm.soil_type,
        "previous_crop": farm.previous_crop,
        "previous_pest_incidents": farm.previous_pest_incidents,
        "previous_disease_incidents": farm.previous_disease_incidents,
        "previous_interventions": farm.previous_interventions,
        "field_size_ha": farm.field_size_ha,
        "irrigation_type": farm.irrigation_type,
        "last_inspection_date": farm.last_inspection_date,
        "data_quality_notes": farm.data_quality_notes,
        "risk_level": assessment.risk_level if assessment else None,
        "confidence": assessment.confidence if assessment else None,
        "evidence_strength": assessment.evidence_strength if assessment else None,
        "recommended_next_action": assessment.recommended_next_action if assessment else None,
        "risk_factors": assessment.risk_factors if assessment else [],
        "supporting_evidence": assessment.evidence_chain if assessment else [],
        "missing_evidence": assessment.missing_evidence if assessment else [],
        "climate": _climate_payload(climate),
        "pest_signals": pests,
        "advisory_status": advisory.status if advisory else None,
        "last_analysed_at": assessment.created_at if assessment else None,
        "rank_reason": _rank_reason(assessment) if assessment else None,
    }
    return payload


def _rank_reason(assessment: RiskAssessment | None) -> str:
    if assessment is None:
        return "No risk assessment has been recorded yet."
    factors = ", ".join(assessment.risk_factors[:3]) or "no elevated structured factor"
    if assessment.risk_level == "INSUFFICIENT_EVIDENCE":
        return f"Ranked for follow-up because required evidence is missing: {', '.join(assessment.missing_evidence[:2])}."
    return f"Ranked {assessment.risk_level.lower()} based on {factors}."


def _advisory_payload(db: Session, advisory: AdvisoryRecord) -> dict:
    farm = db.scalar(select(FarmRecord).where(FarmRecord.farm_id == advisory.farm_id))
    return {
        "advisory_id": advisory.advisory_id,
        "farm_id": advisory.farm_id,
        "farm": _farm_payload(db, farm) if farm else None,
        "crop": farm.crop if farm else None,
        "risk_level": advisory.risk_level,
        "recommendation": advisory.recommendation,
        "evidence": advisory.evidence,
        "missing_information": advisory.missing_information,
        "confidence": advisory.confidence,
        "created_at": advisory.created_at,
        "status": advisory.status,
        "reason": advisory.rejection_reason,
        "actor": advisory.actor,
        "approving_officer": advisory.approving_officer,
        "approval_timestamp": advisory.approval_timestamp,
        "edited_text": advisory.edited_text,
        "rejection_reason": advisory.rejection_reason,
    }


def _trace_payload(db: Session, run: WorkflowRun) -> dict:
    workflow_events = db.scalars(
        select(WorkflowEvent)
        .where(WorkflowEvent.workflow_run_id == run.workflow_run_id)
        .order_by(WorkflowEvent.timestamp.asc(), WorkflowEvent.id.asc())
    ).all()
    tool_calls = db.scalars(
        select(ToolCallLog)
        .where(ToolCallLog.workflow_run_id == run.workflow_run_id)
        .order_by(ToolCallLog.timestamp.asc(), ToolCallLog.id.asc())
    ).all()
    decisions = db.scalars(
        select(DecisionEvent)
        .where(DecisionEvent.workflow_run_id == run.workflow_run_id)
        .order_by(DecisionEvent.timestamp.asc(), DecisionEvent.id.asc())
    ).all()
    events = [
        {
            "id": str(event.id),
            "label": event.label,
            "detail": event.detail,
            "timestamp": event.timestamp,
            "status": event.status,
        }
        for event in workflow_events
    ]
    events.extend(
        {
            "id": f"decision-{decision.id}",
            "label": f"Risk changed: {decision.previous_risk} → {decision.new_risk}",
            "detail": decision.reason,
            "timestamp": decision.timestamp,
            "status": "complete",
            "decision_change": {
                "from": decision.previous_risk,
                "to": decision.new_risk,
                "reason": decision.reason,
                "source": decision.source_tool,
                "timestamp": decision.timestamp,
            },
        }
        for decision in decisions
    )
    events.sort(key=lambda event: event["timestamp"])
    return {
        "workflow_run_id": run.workflow_run_id,
        "request": run.user_request,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "status": run.status,
        "events": events,
        "tool_calls": tool_calls,
        "final_summary": run.final_summary,
    }


@router.get("/api/health")
def api_health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(select(1))
    return {"status": "ok", "database": "connected"}


@router.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    """Return dashboard totals derived from the persisted application tables."""

    farms = db.scalars(select(FarmRecord).order_by(FarmRecord.farm_id)).all()
    assessments = [_latest_assessment(db, farm.farm_id) for farm in farms]
    advisories = db.scalars(select(AdvisoryRecord)).all()
    risk_counts = {level: 0 for level in ("HIGH", "MODERATE", "LOW", "INSUFFICIENT_EVIDENCE")}
    for assessment in assessments:
        if assessment:
            risk_counts[assessment.risk_level] = risk_counts.get(assessment.risk_level, 0) + 1
    return {
        "farms": len(farms),
        "climate_signals": db.query(ClimateSignal).count(),
        "pest_signals": db.query(PestSignal).count(),
        "advisories_total": len(advisories),
        "advisories_pending": sum(item.status == "PENDING_APPROVAL" for item in advisories),
        "tool_call_logs": db.query(ToolCallLog).count(),
        "workflow_runs": db.query(WorkflowRun).count(),
        "districts": sorted({farm.district for farm in farms}),
        "crops": sorted({farm.crop for farm in farms}),
        "risk_counts": risk_counts,
    }


@router.get("/api/farms", response_model=list[FarmDetailRead])
def list_farms(
    district: str | None = None,
    crop: str | None = None,
    risk: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(FarmRecord).order_by(FarmRecord.farm_id)
    if district:
        query = query.where(FarmRecord.district == district)
    if crop:
        query = query.where(FarmRecord.crop == crop)
    farms = db.scalars(query).all()
    payloads = [_farm_payload(db, farm) for farm in farms]
    if risk:
        payloads = [farm for farm in payloads if farm.get("risk_level") == risk]
    return payloads


@router.get("/api/farms/{farm_id}", response_model=FarmDetailRead)
def get_farm(farm_id: str, db: Session = Depends(get_db)) -> dict:
    farm = db.scalar(select(FarmRecord).where(FarmRecord.farm_id == farm_id))
    if farm is None:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} was not found")
    return _farm_payload(db, farm)


@router.get("/api/farms/{farm_id}/evidence")
def get_farm_evidence(farm_id: str, db: Session = Depends(get_db)) -> dict:
    farm = db.scalar(select(FarmRecord).where(FarmRecord.farm_id == farm_id))
    if farm is None:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} was not found")
    payload = _farm_payload(db, farm)
    return {
        "farm_id": farm_id,
        "risk": {
            "risk_level": payload["risk_level"],
            "confidence": payload["confidence"],
            "evidence_strength": payload["evidence_strength"],
            "risk_factors": payload["risk_factors"],
            "missing_evidence": payload["missing_evidence"],
        },
        "evidence_chain": payload["supporting_evidence"],
        "climate": payload["climate"],
        "pest_signals": payload["pest_signals"],
    }


@router.post("/api/analysis/run", response_model=AnalysisRunResponse, status_code=status.HTTP_201_CREATED)
def run_analysis(request: AnalysisRequest, db: Session = Depends(get_db)) -> AnalysisRunResponse:
    workflow_run_id = f"RUN-{uuid4().hex[:12].upper()}"
    user_request = _request_text(request)
    run = WorkflowRun(
        workflow_run_id=workflow_run_id,
        user_request=user_request,
        status="RUNNING",
        selected_scope=request.model_dump(mode="json"),
        model_provider=get_settings().model_provider,
        model_name=get_settings().model_name,
    )
    db.add(run)
    db.commit()
    try:
        state = run_analysis_workflow(db, workflow_run_id, request.model_dump())
    except ModelUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "MODEL_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "WORKFLOW_UNAVAILABLE", "message": "The analysis workflow could not complete."},
        ) from exc
    return AnalysisRunResponse(
        workflow_run_id=workflow_run_id,
        status="COMPLETE",
        message="Analysis complete; advisory records remain pending human approval.",
        farms_analysed=len(state.get("farm_ids", [])),
        advisories_created=len(state.get("advisories", [])),
    )


@router.get("/api/analysis/{workflow_run_id}")
def get_analysis(workflow_run_id: str, db: Session = Depends(get_db)) -> dict:
    run = db.get(WorkflowRun, workflow_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run was not found")
    return _trace_payload(db, run)


@router.get("/api/priority-queue", response_model=list[FarmDetailRead])
def priority_queue(db: Session = Depends(get_db)) -> list[dict]:
    farms = db.scalars(select(FarmRecord)).all()
    rank = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "INSUFFICIENT_EVIDENCE": 3, None: 4}
    payloads = [_farm_payload(db, farm) for farm in farms]
    payloads.sort(key=lambda farm: (rank.get(farm.get("risk_level"), 4), -(farm.get("confidence") or 0), farm["farm_id"]))
    return payloads


@router.get("/api/advisories", response_model=list[AdvisoryRead])
def list_advisories(
    advisory_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(AdvisoryRecord).order_by(AdvisoryRecord.created_at.desc())
    if advisory_status:
        query = query.where(AdvisoryRecord.status == advisory_status)
    return [_advisory_payload(db, advisory) for advisory in db.scalars(query).all()]


@router.get("/api/advisories/{advisory_id}", response_model=AdvisoryRead)
def get_advisory(advisory_id: str, db: Session = Depends(get_db)) -> dict:
    advisory = db.scalar(select(AdvisoryRecord).where(AdvisoryRecord.advisory_id == advisory_id))
    if advisory is None:
        raise HTTPException(status_code=404, detail="Advisory was not found")
    return _advisory_payload(db, advisory)


def _get_editable_advisory(db: Session, advisory_id: str) -> AdvisoryRecord:
    advisory = db.scalar(select(AdvisoryRecord).where(AdvisoryRecord.advisory_id == advisory_id))
    if advisory is None:
        raise HTTPException(status_code=404, detail="Advisory was not found")
    if advisory.status not in {"PENDING_APPROVAL", "EDITED"}:
        raise HTTPException(status_code=409, detail=f"Advisory is already {advisory.status}")
    return advisory


@router.post("/api/advisories/{advisory_id}/approve", response_model=AdvisoryRead)
def approve_advisory(advisory_id: str, request: ApprovalRequest, db: Session = Depends(get_db)) -> dict:
    advisory = _get_editable_advisory(db, advisory_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    advisory.status = "APPROVED"
    advisory.approving_officer = request.officer_name
    advisory.approval_timestamp = now
    advisory.approved_at = now
    db.add(HumanApproval(
        advisory_id=advisory_id,
        officer_name=request.officer_name,
        decision="APPROVED",
        timestamp=now,
    ))
    record_tool_call(
        db,
        advisory.workflow_run_id or "approval-manual",
        "approve_advisory",
        {"advisory_id": advisory_id, "officer_name": request.officer_name},
        {"status": advisory.status},
        action_type="approve_advisory",
        actor=request.officer_name,
        server_name="AgriSage API",
    )
    db.commit()
    return _advisory_payload(db, advisory)


@router.post("/api/advisories/{advisory_id}/edit", response_model=AdvisoryRead)
def edit_advisory(advisory_id: str, request: EditRequest, db: Session = Depends(get_db)) -> dict:
    advisory = _get_editable_advisory(db, advisory_id)
    if advisory.edited_text is None:
        advisory.edited_text = advisory.recommendation
    advisory.recommendation = request.recommendation
    advisory.status = "EDITED"
    advisory.approving_officer = request.officer_name
    db.add(HumanApproval(
        advisory_id=advisory_id,
        officer_name=request.officer_name,
        decision="EDITED",
        edited_text=request.recommendation,
    ))
    record_tool_call(
        db,
        advisory.workflow_run_id or "approval-manual",
        "edit_advisory",
        {"advisory_id": advisory_id, "officer_name": request.officer_name},
        {"status": advisory.status, "original_preserved": True},
        action_type="edit_advisory",
        actor=request.officer_name,
        human_approval_required=True,
        server_name="AgriSage API",
    )
    db.commit()
    return _advisory_payload(db, advisory)


@router.post("/api/advisories/{advisory_id}/reject", response_model=AdvisoryRead)
def reject_advisory(advisory_id: str, request: RejectRequest, db: Session = Depends(get_db)) -> dict:
    advisory = _get_editable_advisory(db, advisory_id)
    advisory.status = "REJECTED"
    advisory.rejection_reason = request.rejection_reason
    advisory.approving_officer = request.officer_name
    db.add(HumanApproval(
        advisory_id=advisory_id,
        officer_name=request.officer_name,
        decision="REJECTED",
        reason=request.rejection_reason,
    ))
    record_tool_call(
        db,
        advisory.workflow_run_id or "approval-manual",
        "reject_advisory",
        {"advisory_id": advisory_id, "officer_name": request.officer_name, "rejection_reason": request.rejection_reason},
        {"status": advisory.status},
        action_type="reject_advisory",
        actor=request.officer_name,
        server_name="AgriSage API",
    )
    db.commit()
    return _advisory_payload(db, advisory)


@router.get("/api/traces", response_model=list[TraceRunRead])
def list_traces(db: Session = Depends(get_db)) -> list[dict]:
    runs = db.scalars(select(WorkflowRun).order_by(WorkflowRun.started_at.desc())).all()
    return [_trace_payload(db, run) for run in runs]


@router.get("/api/traces/{workflow_run_id}", response_model=TraceRunRead)
def get_trace(workflow_run_id: str, db: Session = Depends(get_db)) -> dict:
    run = db.get(WorkflowRun, workflow_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run was not found")
    return _trace_payload(db, run)


@router.get("/api/evaluations", response_model=list[EvaluationResultRead])
def list_evaluations(db: Session = Depends(get_db)) -> list[EvaluationResult]:
    return db.scalars(select(EvaluationResult).order_by(EvaluationResult.task_id)).all()


@router.get("/api/follow-ups", response_model=list[FollowUpTaskRead])
def list_follow_ups(db: Session = Depends(get_db)) -> list:
    from backend.app.models import FollowUpTask

    return db.scalars(select(FollowUpTask).order_by(FollowUpTask.created_at.desc())).all()


@router.post("/api/follow-ups", response_model=FollowUpTaskRead, status_code=status.HTTP_201_CREATED)
def create_follow_up_endpoint(request: FollowUpCreate, db: Session = Depends(get_db)):
    from backend.app.models import FollowUpTask

    farm = db.scalar(select(FarmRecord).where(FarmRecord.farm_id == request.farm_id))
    if farm is None:
        raise HTTPException(status_code=404, detail=f"Farm {request.farm_id} was not found")
    task = FollowUpTask(
        farm_id=request.farm_id,
        workflow_run_id=request.workflow_run_id,
        reason=request.reason,
        priority=request.priority,
        status="OPEN",
    )
    db.add(task)
    db.flush()
    record_tool_call(
        db,
        request.workflow_run_id or "manual-follow-up",
        "create_follow_up",
        request.model_dump(),
        {"follow_up_id": task.id, "status": task.status},
        action_type="create_follow_up",
        actor="extension_officer",
    )
    db.commit()
    return task


def _request_text(request: AnalysisRequest) -> str:
    filters = [value for value in (request.district, request.crop, request.farm_id) if value]
    scope = request.scope
    return f"Run climate-smart analysis for {scope} scope" + (f" ({', '.join(filters)})" if filters else "")
