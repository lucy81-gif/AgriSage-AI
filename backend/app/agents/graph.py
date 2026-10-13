from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from datetime import date, datetime, timedelta, timezone
from typing import Any, TypedDict
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.models import (
    DecisionEvent,
    EvidenceItemRecord,
    FarmRecord,
    FollowUpTask,
    RiskAssessment,
    ToolCallLog,
    WorkflowEvent,
    WorkflowRun,
)
from backend.app.services.mcp_client import MCPToolClient, MCPToolError
from backend.app.services.model_provider import (
    AdvisoryLanguageProvider,
    ModelResponse,
    get_model_provider,
)
from backend.app.services.risk import assess_farm

from langgraph.graph import END, StateGraph


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnalysisState(TypedDict, total=False):
    db: Session
    workflow_run_id: str
    request: dict[str, Any]
    analysis_start: date
    analysis_end: date
    farms: dict[str, dict[str, Any]]
    farm_ids: list[str]
    plots: dict[str, dict[str, Any] | None]
    climates: dict[str, dict[str, Any]]
    pests: dict[str, dict[str, Any]]
    assessments: dict[str, dict[str, Any]]
    advisories: list[str]
    follow_ups: list[int]
    decisions: list[dict[str, Any]]
    errors: list[str]
    priority_queue: list[str]
    quality_issues: dict[str, list[str]]
    external_evidence: dict[str, Any] | None
    mcp: MCPToolClient
    model_provider: AdvisoryLanguageProvider
    plan_summary: str
    input_tokens: int
    output_tokens: int


def add_event(
    db: Session,
    workflow_run_id: str,
    state_name: str,
    label: str,
    detail: str | None = None,
    status: str = "complete",
) -> WorkflowEvent:
    event = WorkflowEvent(
        workflow_run_id=workflow_run_id,
        state_name=state_name,
        label=label,
        detail=detail,
        status=status,
    )
    db.add(event)
    db.flush()
    return event


def receive_request(state: AnalysisState) -> AnalysisState:
    add_event(
        state["db"],
        state["workflow_run_id"],
        "receive_request",
        "Request received",
        "The investigation request was accepted and assigned a workflow run.",
    )
    return state


def identify_scope(state: AnalysisState) -> AnalysisState:
    db = state["db"]
    request = state["request"]
    query = select(FarmRecord)
    if request.get("district"):
        query = query.where(FarmRecord.district == request["district"])
    if request.get("crop"):
        query = query.where(FarmRecord.crop == request["crop"])
    if request.get("scope") == "farm":
        if not request.get("farm_id"):
            raise ValueError("farm_id is required when scope is 'farm'")
        query = query.where(FarmRecord.farm_id == request["farm_id"])
    farms = db.scalars(query.order_by(FarmRecord.farm_id)).all()
    if not farms:
        raise ValueError("No farms matched the selected analysis scope")
    farm_map = {
        farm.farm_id: {
            "farm_id": farm.farm_id,
            "district": farm.district,
            "agroclimatic_zone": farm.agroclimatic_zone,
            "crop": farm.crop,
            "crop_variety": farm.crop_variety,
            "planting_date": farm.planting_date.isoformat() if farm.planting_date else None,
            "growth_stage": farm.current_growth_stage,
            "soil_type": farm.soil_type,
            "irrigation_type": farm.irrigation_type,
            "last_inspection_date": (
                farm.last_inspection_date.isoformat() if farm.last_inspection_date else None
            ),
        }
        for farm in farms
    }
    state["farm_ids"] = list(farm_map)
    state["farms"] = farm_map
    add_event(
        db,
        state["workflow_run_id"],
        "identify_scope",
        "Scope identified",
        f"{len(farms)} farm(s) matched the selected district, crop, and scope filters.",
    )
    return state


async def plan_investigation(state: AnalysisState) -> AnalysisState:
    provider = state.get("model_provider") or get_model_provider()
    state["model_provider"] = provider
    result = provider.plan(state["request"], len(state["farm_ids"]))
    state["plan_summary"] = result.text[:800]
    state["input_tokens"] = state.get("input_tokens", 0) + (result.input_tokens or 0)
    state["output_tokens"] = state.get("output_tokens", 0) + (result.output_tokens or 0)
    add_event(
        state["db"],
        state["workflow_run_id"],
        "plan_investigation",
        "Investigation plan prepared",
        state["plan_summary"],
    )
    return state


async def retrieve_plot_context(state: AnalysisState) -> AnalysisState:
    plots: dict[str, dict[str, Any] | None] = {}
    errors = state.setdefault("errors", [])
    for farm_id in state["farm_ids"]:
        try:
            plots[farm_id] = await state["mcp"].call_tool(
                "get_plot_context",
                {"farm_id": farm_id, "workflow_run_id": state["workflow_run_id"]},
            )
        except MCPToolError as exc:
            plots[farm_id] = None
            errors.append(f"{farm_id}: plot context unavailable ({exc})")
    state["plots"] = plots
    unavailable = sum(plot is None for plot in plots.values())
    add_event(
        state["db"],
        state["workflow_run_id"],
        "retrieve_plot_context",
        "Plot context retrieved",
        f"Plot history was retrieved for {len(plots) - unavailable} of {len(plots)} farm(s).",
        "blocked" if unavailable == len(plots) else "complete",
    )
    return state


async def retrieve_climate_signals(state: AnalysisState) -> AnalysisState:
    climates: dict[str, dict[str, Any]] = {}
    errors = state.setdefault("errors", [])
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    for farm_id in state["farm_ids"]:
        farm = state["farms"][farm_id]
        key = (farm["district"], farm["agroclimatic_zone"])
        if key not in cache:
            try:
                cache[key] = await state["mcp"].call_tool(
                    "get_climate_signals",
                    {
                        "district": farm["district"],
                        "agroclimatic_zone": farm["agroclimatic_zone"],
                        "analysis_start": state["analysis_start"].isoformat(),
                        "analysis_end": state["analysis_end"].isoformat(),
                        "workflow_run_id": state["workflow_run_id"],
                    },
                )
            except MCPToolError as exc:
                cache[key] = {
                    "available": False,
                    "availability_status": "UNAVAILABLE",
                    "signals": [],
                }
                errors.append(f"{farm_id}: climate signals unavailable ({exc})")
        climates[farm_id] = cache[key]
    state["climates"] = climates
    add_event(
        state["db"],
        state["workflow_run_id"],
        "retrieve_climate_signals",
        "Climate evidence retrieved",
        f"Climate views were resolved for {len(cache)} district and zone combination(s).",
        "blocked" if not any(item.get("signals") for item in climates.values()) else "complete",
    )
    return state


async def retrieve_pest_signals(state: AnalysisState) -> AnalysisState:
    pests: dict[str, dict[str, Any]] = {}
    errors = state.setdefault("errors", [])
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    for farm_id in state["farm_ids"]:
        farm = state["farms"][farm_id]
        key = (farm["crop"], farm["agroclimatic_zone"])
        if key not in cache:
            try:
                cache[key] = await state["mcp"].call_tool(
                    "get_pest_signals",
                    {
                        "crop": farm["crop"],
                        "agroclimatic_zone": farm["agroclimatic_zone"],
                        "analysis_start": state["analysis_start"].isoformat(),
                        "analysis_end": state["analysis_end"].isoformat(),
                        "workflow_run_id": state["workflow_run_id"],
                    },
                )
            except MCPToolError as exc:
                cache[key] = {"available": False, "signals": []}
                errors.append(f"{farm_id}: pest signals unavailable ({exc})")
        pests[farm_id] = cache[key]
    state["pests"] = pests
    add_event(
        state["db"],
        state["workflow_run_id"],
        "retrieve_pest_signals",
        "Pest evidence retrieved",
        f"Pest views were resolved for {len(cache)} crop and zone combination(s).",
    )
    return state


def _valid_external_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


async def retrieve_external_evidence(state: AnalysisState) -> AnalysisState:
    url = get_settings().external_evidence_url.strip()
    if not url:
        state["external_evidence"] = None
        add_event(
            state["db"],
            state["workflow_run_id"],
            "retrieve_external_evidence",
            "External reference skipped",
            "No EXTERNAL_EVIDENCE_URL is configured.",
            "complete",
        )
        return state
    if not _valid_external_url(url):
        state["external_evidence"] = {"status": "FAILED", "url": url}
        state.setdefault("errors", []).append("External reference URL must be a public HTTPS URL.")
        add_event(
            state["db"],
            state["workflow_run_id"],
            "retrieve_external_evidence",
            "External reference rejected",
            "Only HTTPS reference URLs are accepted.",
            "blocked",
        )
        return state

    async with MCPToolClient(
        state["db"], state["workflow_run_id"], "Official Fetch MCP Server"
    ) as fetch_client:
        try:
            fetched = await fetch_client.call_tool("fetch", {"url": url, "max_length": 3000})
            content = str(fetched.get("content", ""))[:3000]
            state["external_evidence"] = {
                "status": "SUCCESS",
                "source": url,
                "retrieved_at": _utcnow().isoformat(),
                "content_excerpt": content,
            }
            status = "complete"
            detail = f"Retrieved public reference content from {url}. It is advisory context only."
        except MCPToolError as exc:
            state["external_evidence"] = {"status": "FAILED", "source": url}
            state.setdefault("errors", []).append(f"External reference retrieval failed ({exc})")
            status = "blocked"
            detail = "The Fetch MCP call failed; no page content was assumed or invented."
    add_event(
        state["db"],
        state["workflow_run_id"],
        "retrieve_external_evidence",
        "External reference retrieved" if status == "complete" else "External reference unavailable",
        detail,
        status,
    )
    return state


def assess_data_quality(state: AnalysisState) -> AnalysisState:
    issues: dict[str, list[str]] = {}
    for farm_id in state["farm_ids"]:
        reasons: list[str] = []
        plot = state["plots"].get(farm_id)
        climate = state["climates"].get(farm_id, {})
        if not plot:
            reasons.append("plot context unavailable")
        else:
            for key, label in (
                ("planting_date", "planting date missing"),
                ("growth_stage", "growth stage missing"),
                ("soil_type", "soil information missing"),
            ):
                if not plot.get(key):
                    reasons.append(label)
            notes = str(plot.get("data_quality_notes") or "").lower()
            if "conflict" in notes:
                reasons.append("conflicting crop-stage record")
        climate_status = climate.get("availability_status")
        if climate_status == "UNAVAILABLE":
            reasons.append("climate data unavailable")
        if climate_status == "STALE" or any(
            row.get("freshness") == "STALE" for row in climate.get("signals", [])
        ):
            reasons.append("climate evidence is stale")
        if reasons:
            issues[farm_id] = reasons
    state["quality_issues"] = issues
    add_event(
        state["db"],
        state["workflow_run_id"],
        "assess_data_quality",
        "Evidence quality assessed",
        f"{sum(map(len, issues.values()))} missing, stale, or conflicting condition(s) were flagged.",
        "blocked" if issues else "complete",
    )
    return state


def route_after_quality(state: AnalysisState) -> str:
    return "handle_missing_or_conflicting_data" if state.get("quality_issues") else "calculate_risk"


async def handle_missing_or_conflicting_data(state: AnalysisState) -> AnalysisState:
    follow_ups: list[int] = []
    for farm_id, reasons in state.get("quality_issues", {}).items():
        try:
            result = await state["mcp"].call_tool(
                "create_follow_up",
                {
                    "workflow_run_id": state["workflow_run_id"],
                    "farm_id": farm_id,
                    "reason": "; ".join(reasons),
                    "priority": "HIGH" if len(reasons) > 1 else "MODERATE",
                },
            )
            if isinstance(result.get("follow_up_id"), int):
                follow_ups.append(result["follow_up_id"])
        except MCPToolError as exc:
            state.setdefault("errors", []).append(f"{farm_id}: follow-up creation failed ({exc})")
    state["follow_ups"] = follow_ups
    add_event(
        state["db"],
        state["workflow_run_id"],
        "handle_missing_or_conflicting_data",
        "Missing evidence handled",
        f"Created {len(follow_ups)} follow-up task(s); missing data was not replaced with guesses.",
        "blocked" if state.get("quality_issues") and not follow_ups else "complete",
    )
    return state


def _decision_source(new_factors: list[str]) -> str:
    joined = " ".join(new_factors).lower()
    if "pest" in joined or "armyworm" in joined:
        return "get_pest_signals"
    if any(word in joined for word in ("rainfall", "drought", "heavy-rain", "climate")):
        return "get_climate_signals"
    return "get_plot_context"


def calculate_risk(state: AnalysisState) -> AnalysisState:
    db = state["db"]
    assessments: dict[str, dict[str, Any]] = {}
    decisions: list[dict[str, Any]] = []
    for farm_id in state["farm_ids"]:
        plot = state["plots"].get(farm_id) or state["farms"][farm_id]
        assessment = assess_farm(
            plot,
            state["climates"].get(farm_id, {}),
            state["pests"].get(farm_id, {}),
        )
        assessments[farm_id] = assessment
        db.add(
            RiskAssessment(
                workflow_run_id=state["workflow_run_id"],
                farm_id=farm_id,
                risk_level=assessment["risk_level"],
                confidence=assessment["confidence"],
                evidence_strength=assessment["evidence_strength"],
                risk_factors=assessment["risk_factors"],
                missing_evidence=assessment["missing_evidence"],
                recommended_next_action=assessment["recommended_next_action"],
                evidence_chain=assessment["evidence_chain"],
            )
        )
        for item in assessment["evidence_chain"]:
            db.add(
                EvidenceItemRecord(
                    workflow_run_id=state["workflow_run_id"],
                    farm_id=farm_id,
                    label=item["label"],
                    detail=item["detail"],
                    source=item["source"],
                    kind=item["kind"],
                    confidence=item.get("confidence"),
                )
            )
        previous = db.scalar(
            select(RiskAssessment)
            .where(
                RiskAssessment.farm_id == farm_id,
                RiskAssessment.workflow_run_id != state["workflow_run_id"],
            )
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        if previous and previous.risk_level != assessment["risk_level"]:
            previous_factors = set(previous.risk_factors or [])
            new_factors = [factor for factor in assessment["risk_factors"] if factor not in previous_factors]
            source_tool = _decision_source(new_factors)
            reason = (
                f"New evidence changed the risk from {previous.risk_level} to "
                f"{assessment['risk_level']}: "
                + ("; ".join(new_factors[:3]) or "the current evidence set changed")
                + "."
            )
            db.add(
                DecisionEvent(
                    workflow_run_id=state["workflow_run_id"],
                    farm_id=farm_id,
                    previous_risk=previous.risk_level,
                    new_risk=assessment["risk_level"],
                    reason=reason,
                    source_tool=source_tool,
                )
            )
            decisions.append(
                {"farm_id": farm_id, "from": previous.risk_level, "to": assessment["risk_level"], "reason": reason}
            )
    db.flush()
    state["assessments"] = assessments
    state["decisions"] = decisions
    add_event(
        db,
        state["workflow_run_id"],
        "calculate_risk",
        "Structured risk calculated",
        f"Risk was calculated for {len(assessments)} farm(s) with deterministic thresholds.",
    )
    return state


def build_evidence_chain(state: AnalysisState) -> AnalysisState:
    add_event(
        state["db"],
        state["workflow_run_id"],
        "build_evidence_chain",
        "Evidence chains built",
        "Each assessment stores the plot, climate, pest, history, and missing-data facts used by the risk engine.",
    )
    return state


def prioritise_farms(state: AnalysisState) -> AnalysisState:
    rank = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "INSUFFICIENT_EVIDENCE": 3}
    state["priority_queue"] = sorted(
        state["farm_ids"],
        key=lambda farm_id: (
            rank[state["assessments"][farm_id]["risk_level"]],
            -state["assessments"][farm_id]["confidence"],
            farm_id,
        ),
    )
    add_event(
        state["db"],
        state["workflow_run_id"],
        "prioritise_farms",
        "Priority queue ranked",
        "Farms were ranked by structured risk and confidence; insufficient evidence remains visible for follow-up.",
    )
    return state


async def draft_advisories(state: AnalysisState) -> AnalysisState:
    provider = state["model_provider"]
    advisory_ids: list[str] = []
    for farm_id in state["priority_queue"]:
        assessment = state["assessments"][farm_id]
        if assessment["risk_level"] in {"LOW", "INSUFFICIENT_EVIDENCE"}:
            continue
        farm = state["plots"].get(farm_id) or state["farms"][farm_id]
        response: ModelResponse = provider.draft(
            farm, assessment, state.get("external_evidence")
        )
        state["input_tokens"] = state.get("input_tokens", 0) + (response.input_tokens or 0)
        state["output_tokens"] = state.get("output_tokens", 0) + (response.output_tokens or 0)
        recommendation = response.text
        if assessment["evidence_chain"]:
            evidence = list(assessment["evidence_chain"])
        else:
            evidence = []
        external = state.get("external_evidence")
        if external and external.get("status") == "SUCCESS":
            evidence.append(
                {
                    "label": "External public reference",
                    "detail": f"Reference context was retrieved; it did not change the deterministic risk score. {external.get('content_excerpt', '')[:500]}",
                    "source": external.get("source", "Official Fetch MCP Server"),
                    "confidence": None,
                    "kind": "reference_context",
                }
            )
        result = await state["mcp"].call_tool(
            "draft_advisory",
            {
                "workflow_run_id": state["workflow_run_id"],
                "farm_id": farm_id,
                "risk_level": assessment["risk_level"],
                "recommendation": recommendation,
                "evidence": evidence,
                "missing_information": assessment["missing_evidence"],
                "confidence": assessment["confidence"],
            },
        )
        if result.get("status") != "PENDING_APPROVAL":
            raise RuntimeError("The advisory action tool did not return PENDING_APPROVAL.")
        advisory_ids.append(str(result["advisory_id"]))
    state["advisories"] = advisory_ids
    add_event(
        state["db"],
        state["workflow_run_id"],
        "draft_advisories",
        "Advisories drafted for officer review",
        f"Created {len(advisory_ids)} advisory record(s), all stopped at PENDING_APPROVAL.",
    )
    return state


def await_human_approval(state: AnalysisState) -> AnalysisState:
    add_event(
        state["db"],
        state["workflow_run_id"],
        "await_human_approval",
        "Approval gate reached",
        "No farmer-facing action was taken. A named extension officer must approve, edit, or reject each draft.",
        "blocked" if state.get("advisories") else "complete",
    )
    return state


def complete(state: AnalysisState) -> AnalysisState:
    db = state["db"]
    run = db.get(WorkflowRun, state["workflow_run_id"])
    if run:
        run.status = "COMPLETE"
        run.completed_at = _utcnow()
        run.duration_ms = max(0, round((run.completed_at - run.started_at).total_seconds() * 1000))
        run.tool_call_count = db.scalar(
            select(func.count()).select_from(ToolCallLog).where(
                ToolCallLog.workflow_run_id == state["workflow_run_id"]
            )
        ) or 0
        provider = state.get("model_provider")
        if provider:
            run.model_provider = provider.provider_name
            run.model_name = provider.model_name
        run.input_tokens = state.get("input_tokens") or None
        run.output_tokens = state.get("output_tokens") or None
        run.estimated_model_cost_usd = 0.0 if provider and provider.provider_name == "ollama" else None
        run.final_summary = {
            "farms_analysed": len(state["farm_ids"]),
            "advisories_created": len(state.get("advisories", [])),
            "follow_ups_created": len(state.get("follow_ups", [])),
            "priority_queue": state.get("priority_queue", []),
            "errors": state.get("errors", []),
            "plan_summary": state.get("plan_summary"),
        }
    add_event(
        db,
        state["workflow_run_id"],
        "complete",
        "Investigation complete",
        "The run is complete and the reviewable priority queue is ready.",
    )
    db.commit()
    return state


def build_graph():
    graph = StateGraph(AnalysisState)
    nodes = [
        ("receive_request", receive_request),
        ("identify_scope", identify_scope),
        ("plan_investigation", plan_investigation),
        ("retrieve_plot_context", retrieve_plot_context),
        ("retrieve_climate_signals", retrieve_climate_signals),
        ("retrieve_pest_signals", retrieve_pest_signals),
        ("retrieve_external_evidence", retrieve_external_evidence),
        ("assess_data_quality", assess_data_quality),
        ("handle_missing_or_conflicting_data", handle_missing_or_conflicting_data),
        ("calculate_risk", calculate_risk),
        ("build_evidence_chain", build_evidence_chain),
        ("prioritise_farms", prioritise_farms),
        ("draft_advisories", draft_advisories),
        ("await_human_approval", await_human_approval),
        ("complete", complete),
    ]
    for name, node in nodes:
        graph.add_node(name, node)
    for (current, _), (next_name, _) in zip(nodes, nodes[1:]):
        if current != "assess_data_quality":
            graph.add_edge(current, next_name)
    graph.add_conditional_edges(
        "assess_data_quality",
        route_after_quality,
        {
            "handle_missing_or_conflicting_data": "handle_missing_or_conflicting_data",
            "calculate_risk": "calculate_risk",
        },
    )
    graph.add_edge("handle_missing_or_conflicting_data", "calculate_risk")
    graph.set_entry_point("receive_request")
    graph.add_edge("complete", END)
    return graph.compile()


async def _run_analysis_async(
    db: Session,
    workflow_run_id: str,
    request: dict[str, Any],
    model_provider: AdvisoryLanguageProvider | None,
) -> AnalysisState:
    analysis_end = request.get("analysis_end") or date.today()
    analysis_start = request.get("analysis_start") or analysis_end - timedelta(days=7)
    if isinstance(analysis_start, str):
        analysis_start = date.fromisoformat(analysis_start)
    if isinstance(analysis_end, str):
        analysis_end = date.fromisoformat(analysis_end)

    async with AsyncExitStack() as stack:
        mcp_client = await stack.enter_async_context(
            MCPToolClient(db, workflow_run_id, "AgriSage MCP Server")
        )
        state: AnalysisState = {
            "db": db,
            "workflow_run_id": workflow_run_id,
            "request": request,
            "analysis_start": analysis_start,
            "analysis_end": analysis_end,
            "farms": {},
            "farm_ids": [],
            "plots": {},
            "climates": {},
            "pests": {},
            "assessments": {},
            "advisories": [],
            "follow_ups": [],
            "decisions": [],
            "errors": [],
            "priority_queue": [],
            "quality_issues": {},
            "external_evidence": None,
            "mcp": mcp_client,
            "input_tokens": 0,
            "output_tokens": 0,
        }
        if model_provider:
            state["model_provider"] = model_provider
        return await build_graph().ainvoke(state)


def run_analysis_workflow(
    db: Session,
    workflow_run_id: str,
    request: dict[str, Any],
    *,
    model_provider: AdvisoryLanguageProvider | None = None,
) -> AnalysisState:
    """Run the async LangGraph while keeping the HTTP and evaluation API synchronous."""

    try:
        return asyncio.run(_run_analysis_async(db, workflow_run_id, request, model_provider))
    except Exception as exc:
        run = db.get(WorkflowRun, workflow_run_id)
        if run:
            run.status = "FAILED"
            run.completed_at = _utcnow()
            run.duration_ms = max(0, round((run.completed_at - run.started_at).total_seconds() * 1000))
        safe_detail = "The workflow stopped after a model or backend dependency failed."
        if "MODEL_UNAVAILABLE" in str(exc):
            safe_detail = "MODEL_UNAVAILABLE: the configured open-weight model could not complete this workflow."
        add_event(
            db,
            workflow_run_id,
            "failed",
            "Investigation failed",
            safe_detail,
            "failed",
        )
        db.commit()
        raise
