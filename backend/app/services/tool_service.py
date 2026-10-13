from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from backend.app.models import (
    AdvisoryRecord,
    ClimateSignal,
    FarmRecord,
    FollowUpTask,
    PestSignal,
    ToolCallLog,
)


def _json_date(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


def record_tool_call(
    db: Session,
    workflow_run_id: str,
    tool_name: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    *,
    status: str = "SUCCESS",
    action_type: str | None = None,
    actor: str | None = None,
    human_approval_required: bool = False,
    error_message: str | None = None,
    server_name: str = "AgriSage MCP Server",
    started_at: datetime | None = None,
    duration_ms: int | None = None,
) -> ToolCallLog:
    completed_at = datetime.utcnow()
    log = ToolCallLog(
        workflow_run_id=workflow_run_id,
        server_name=server_name,
        tool_name=tool_name,
        input_payload=input_payload,
        output_payload=output_payload,
        status=status,
        timestamp=started_at or completed_at,
        started_at=started_at or completed_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        output_summary=json.dumps(output_payload, ensure_ascii=False, default=str)[:500],
        action_type=action_type,
        actor=actor,
        human_approval_required=human_approval_required,
        error_message=error_message,
    )
    db.add(log)
    db.flush()
    return log


def get_plot_context(
    db: Session, farm_id: str, workflow_run_id: str, *, record_call: bool = True
) -> dict[str, Any]:
    payload = {"farm_id": farm_id}
    try:
        farm = db.scalar(select(FarmRecord).where(FarmRecord.farm_id == farm_id))
        if farm is None:
            raise ValueError(f"Farm {farm_id} was not found")
        output = {
            "farm_id": farm.farm_id,
            "source": "AgriSage synthetic farm register",
            "timestamp": datetime.utcnow().isoformat(),
            "district": farm.district,
            "agroclimatic_zone": farm.agroclimatic_zone,
            "crop": farm.crop,
            "crop_variety": farm.crop_variety,
            "planting_date": _json_date(farm.planting_date),
            "growth_stage": farm.current_growth_stage,
            "soil_type": farm.soil_type,
            "field_size_ha": farm.field_size_ha,
            "irrigation_type": farm.irrigation_type,
            "previous_crop": farm.previous_crop,
            "previous_pest_incidents": farm.previous_pest_incidents,
            "previous_disease_incidents": farm.previous_disease_incidents,
            "previous_interventions": farm.previous_interventions,
            "last_inspection_date": _json_date(farm.last_inspection_date),
            "data_quality_notes": farm.data_quality_notes,
            "crop_calendar_context": {
                "crop": farm.crop,
                "stage_recorded": bool(farm.current_growth_stage),
                "planting_date_recorded": bool(farm.planting_date),
                "stage_reference": "Synthetic crop calendar; confirm stage during field visit.",
            },
        }
        if record_call:
            record_tool_call(db, workflow_run_id, "get_plot_context", payload, output)
        return output
    except Exception as exc:
        if record_call:
            record_tool_call(
                db,
                workflow_run_id,
                "get_plot_context",
                payload,
                {"available": False},
                status="FAILURE",
                error_message=str(exc),
            )
        raise


def get_climate_signals(
    db: Session,
    workflow_run_id: str,
    district: str,
    agroclimatic_zone: str,
    analysis_start: date,
    analysis_end: date,
    *,
    record_call: bool = True,
) -> dict[str, Any]:
    payload = {
        "district": district,
        "agroclimatic_zone": agroclimatic_zone,
        "analysis_start": analysis_start.isoformat(),
        "analysis_end": analysis_end.isoformat(),
    }
    try:
        exact = db.scalars(
            select(ClimateSignal)
            .where(
                ClimateSignal.district == district,
                ClimateSignal.agroclimatic_zone == agroclimatic_zone,
                ClimateSignal.signal_date >= analysis_start,
                ClimateSignal.signal_date <= analysis_end,
            )
            .order_by(ClimateSignal.signal_date.desc())
        ).all()
        # An older signal is returned explicitly as STALE evidence when no current signal exists.
        signals = exact
        if not signals:
            signals = db.scalars(
                select(ClimateSignal)
                .where(
                    ClimateSignal.district == district,
                    ClimateSignal.agroclimatic_zone == agroclimatic_zone,
                    ClimateSignal.signal_date <= analysis_end,
                )
                .order_by(ClimateSignal.signal_date.desc())
                .limit(1)
            ).all()
        output_signals = [
            {
                "signal_id": signal.signal_id,
                "district": signal.district,
                "agroclimatic_zone": signal.agroclimatic_zone,
                "signal_date": signal.signal_date.isoformat(),
                "rainfall_mm_7d": signal.rainfall_mm_7d,
                "forecast_rainfall_mm_7d": signal.forecast_rainfall_mm_7d,
                "average_temperature_c": signal.average_temperature_c,
                "rainfall_anomaly_pct": signal.rainfall_anomaly_pct,
                "drought_indicator": signal.drought_indicator,
                "heavy_rain_indicator": signal.heavy_rain_indicator,
                "availability_status": (
                    "UNAVAILABLE"
                    if signal.availability_status.upper() == "UNAVAILABLE"
                    else _climate_freshness(
                        signal.observed_at,
                        signal.availability_status,
                        signal.signal_date,
                        analysis_start,
                    )
                ),
                "source_type": signal.source_type,
                "source": signal.source,
                "observed_at": signal.observed_at.isoformat(),
                "freshness": _climate_freshness(
                    signal.observed_at,
                    signal.availability_status,
                    signal.signal_date,
                    analysis_start,
                ),
                "data_confidence": signal.data_confidence,
                "notes": signal.notes,
            }
            for signal in signals
        ]
        output = {
            "available": bool(output_signals),
            "availability_status": output_signals[0]["availability_status"] if output_signals else "UNAVAILABLE",
            "signals": output_signals,
        }
        if record_call:
            record_tool_call(db, workflow_run_id, "get_climate_signals", payload, output)
        return output
    except Exception as exc:
        if record_call:
            record_tool_call(
                db,
                workflow_run_id,
                "get_climate_signals",
                payload,
                {"available": False, "availability_status": "UNAVAILABLE", "signals": []},
                status="FAILURE",
                error_message=str(exc),
            )
        raise


def get_pest_signals(
    db: Session,
    workflow_run_id: str,
    crop: str,
    agroclimatic_zone: str,
    analysis_start: date,
    analysis_end: date,
    *,
    record_call: bool = True,
) -> dict[str, Any]:
    payload = {
        "crop": crop,
        "agroclimatic_zone": agroclimatic_zone,
        "analysis_start": analysis_start.isoformat(),
        "analysis_end": analysis_end.isoformat(),
    }
    try:
        signals = db.scalars(
            select(PestSignal)
            .where(
                PestSignal.crop == crop,
                PestSignal.agroclimatic_zone == agroclimatic_zone,
                PestSignal.report_date >= analysis_start,
                PestSignal.report_date <= analysis_end,
            )
            .order_by(PestSignal.report_date.desc())
        ).all()
        output = {
            "available": True,
            "signals": [
                {
                    "signal_id": signal.signal_id,
                    "district": signal.district,
                    "agroclimatic_zone": signal.agroclimatic_zone,
                    "crop": signal.crop,
                    "pest_type": signal.pest_type,
                    "report_count": signal.report_count,
                    "severity": signal.severity,
                    "report_date": signal.report_date.isoformat(),
                    "confidence": signal.confidence,
                    "source": signal.source,
                    "location_relevance": "same agroclimatic zone",
                    "report_timestamp": signal.created_at.isoformat(),
                    "notes": signal.notes,
                }
                for signal in signals
            ],
        }
        if record_call:
            record_tool_call(db, workflow_run_id, "get_pest_signals", payload, output)
        return output
    except Exception as exc:
        if record_call:
            record_tool_call(
                db,
                workflow_run_id,
                "get_pest_signals",
                payload,
                {"available": False, "signals": []},
                status="FAILURE",
                error_message=str(exc),
            )
        raise


def draft_advisory(
    db: Session,
    workflow_run_id: str,
    farm_id: str,
    risk_level: str,
    recommendation: str,
    evidence: list[dict[str, Any]],
    missing_information: list[str],
    confidence: float,
    *,
    record_call: bool = True,
) -> AdvisoryRecord:
    input_payload = {
        "farm_id": farm_id,
        "risk_level": risk_level,
        "missing_information": missing_information,
    }
    advisory = AdvisoryRecord(
        advisory_id=f"ADV-{workflow_run_id[-8:]}-{farm_id}",
        farm_id=farm_id,
        workflow_run_id=workflow_run_id,
        risk_level=risk_level,
        recommendation=recommendation,
        evidence=evidence,
        missing_information=missing_information,
        confidence=confidence,
        status="PENDING_APPROVAL",
        action_type="draft_advisory",
        actor="agent",
        human_approval_required=True,
    )
    db.add(advisory)
    db.flush()
    if record_call:
        record_tool_call(
            db,
            workflow_run_id,
            "draft_advisory",
            input_payload,
            {
                "advisory_id": advisory.advisory_id,
                "status": advisory.status,
                "human_approval_required": True,
            },
            action_type="draft_advisory",
            actor="agent",
            human_approval_required=True,
        )
    return advisory


def create_follow_up(
    db: Session,
    workflow_run_id: str,
    farm_id: str,
    reason: str,
    priority: str,
    *,
    record_call: bool = True,
) -> FollowUpTask:
    task = FollowUpTask(
        farm_id=farm_id,
        workflow_run_id=workflow_run_id,
        reason=reason,
        priority=priority,
        status="OPEN",
    )
    db.add(task)
    db.flush()
    if record_call:
        record_tool_call(
            db,
            workflow_run_id,
            "create_follow_up",
            {"farm_id": farm_id, "reason": reason, "priority": priority},
            {"follow_up_id": task.id, "status": task.status},
            action_type="create_follow_up",
            actor="agent",
        )
    return task


def _climate_freshness(
    observed_at: datetime,
    source_status: str,
    signal_date: date | None = None,
    analysis_start: date | None = None,
) -> str:
    if source_status.upper() == "UNAVAILABLE":
        return "UNAVAILABLE"
    if observed_at.tzinfo is not None:
        observed_at = observed_at.replace(tzinfo=None)
    age_days = (datetime.utcnow() - observed_at).days
    outside_period = signal_date is not None and analysis_start is not None and signal_date < analysis_start
    return "STALE" if age_days > 14 or outside_period or source_status.upper() == "STALE" else "FRESH"
