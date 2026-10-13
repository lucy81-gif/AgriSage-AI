"""First-party MCP server exposing the same audited tool boundary as the agent."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from backend.app.db.init_db import initialize_database
from backend.app.db.session import SessionLocal
from backend.app.services.tool_service import (
    create_follow_up as create_follow_up_service,
    draft_advisory as draft_advisory_service,
    get_climate_signals as get_climate_signals_service,
    get_pest_signals as get_pest_signals_service,
    get_plot_context as get_plot_context_service,
)


mcp = FastMCP("AgriSage AI tools")


def _run_id(value: str | None) -> str:
    return value or "mcp-manual"


@mcp.tool()
def get_plot_context(farm_id: str, workflow_run_id: str | None = None) -> dict:
    """Return farm record, crop calendar context, soil, history, and interventions."""

    with SessionLocal() as db:
        result = get_plot_context_service(
            db, farm_id, _run_id(workflow_run_id), record_call=False
        )
        db.commit()
        return result


@mcp.tool()
def get_climate_signals(
    district: str,
    agroclimatic_zone: str,
    analysis_start: str,
    analysis_end: str,
    workflow_run_id: str | None = None,
) -> dict:
    """Return dated rainfall, forecast, temperature, anomaly, indicators, and confidence."""

    with SessionLocal() as db:
        result = get_climate_signals_service(
            db,
            _run_id(workflow_run_id),
            district,
            agroclimatic_zone,
            date.fromisoformat(analysis_start),
            date.fromisoformat(analysis_end),
            record_call=False,
        )
        db.commit()
        return result


@mcp.tool()
def get_pest_signals(
    crop: str,
    agroclimatic_zone: str,
    analysis_start: str,
    analysis_end: str,
    workflow_run_id: str | None = None,
) -> dict:
    """Return time-bounded pest reports for a crop and agroclimatic zone."""

    with SessionLocal() as db:
        result = get_pest_signals_service(
            db,
            _run_id(workflow_run_id),
            crop,
            agroclimatic_zone,
            date.fromisoformat(analysis_start),
            date.fromisoformat(analysis_end),
            record_call=False,
        )
        db.commit()
        return result


@mcp.tool()
def draft_advisory(
    workflow_run_id: str,
    farm_id: str,
    risk_level: str,
    recommendation: str,
    evidence: list[dict],
    missing_information: list[str],
    confidence: float,
) -> dict:
    """Create a PENDING_APPROVAL advisory. This tool never contacts a farmer."""

    with SessionLocal() as db:
        advisory = draft_advisory_service(
            db,
            workflow_run_id,
            farm_id,
            risk_level,
            recommendation,
            evidence,
            missing_information,
            confidence,
            record_call=False,
        )
        db.commit()
        return {
            "advisory_id": advisory.advisory_id,
            "status": advisory.status,
            "human_approval_required": advisory.human_approval_required,
        }


@mcp.tool()
def create_follow_up(
    workflow_run_id: str,
    farm_id: str,
    reason: str,
    priority: str = "MODERATE",
) -> dict:
    """Create a human follow-up task when evidence is missing or conflicting."""

    with SessionLocal() as db:
        task = create_follow_up_service(
            db, workflow_run_id, farm_id, reason, priority, record_call=False
        )
        db.commit()
        return {"follow_up_id": task.id, "status": task.status, "priority": task.priority}


if __name__ == "__main__":
    initialize_database()
    mcp.run(transport="stdio")
