from __future__ import annotations

import asyncio
import json
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, func, select

from backend.app.agents.graph import run_analysis_workflow
from backend.app.core.config import get_settings
from backend.app.db.init_db import initialize_database
from backend.app.db.session import SessionLocal
from backend.app.models import (
    AdvisoryRecord,
    EvaluationResult,
    EvaluationRun,
    FollowUpTask,
    HumanApproval,
    RiskAssessment,
    ToolCallLog,
    WorkflowRun,
)
from backend.app.schemas.api import ApprovalRequest, EditRequest, RejectRequest
from backend.app.services.mcp_client import MCPToolClient, MCPToolError
from backend.app.services.model_provider import ModelResponse, get_model_provider
from backend.app.api.routes import approve_advisory, edit_advisory, reject_advisory


class EvaluationOnlyModelProvider:
    """Deterministic test double. It is never selected by the application runtime."""

    provider_name = "evaluation-test-double"
    model_name = "not-a-language-model"

    def plan(self, request: dict[str, Any], farm_count: int) -> ModelResponse:
        return ModelResponse(
            f"Evaluation fixture: retrieve plot, climate, and pest evidence for {farm_count} farm(s)."
        )

    def draft(
        self,
        farm: dict[str, Any],
        assessment: dict[str, Any],
        external_evidence: dict[str, Any] | None = None,
    ) -> ModelResponse:
        return ModelResponse(
            f"TEST FIXTURE ONLY for {farm['farm_id']}: {assessment['recommended_next_action']} "
            "Verify the field evidence with an extension officer before any treatment decision."
        )


TEST_PROVIDER = EvaluationOnlyModelProvider()
ANALYSIS_START = date(2026, 10, 1)
ANALYSIS_END = date(2026, 10, 8)

CASES: list[dict[str, Any]] = [
    {"task_id": "EVAL-001", "scenario": "Normal maize workflow with public reference", "farm_id": "F012", "expected": "Uses plot, climate, pest, and successfully fetched public reference evidence; stores an advisory at PENDING_APPROVAL."},
    {"task_id": "EVAL-002", "scenario": "Drought scenario", "farm_id": "F015", "expected": "Uses drought or negative rainfall evidence and prioritises inspection."},
    {"task_id": "EVAL-003", "scenario": "Heavy-rain scenario", "farm_id": "F020", "expected": "Identifies heavy rain and creates a cautious review record."},
    {"task_id": "EVAL-004", "scenario": "High pest-risk signal", "farm_id": "F002", "expected": "Uses a high-severity nearby pest report without claiming plot infestation."},
    {"task_id": "EVAL-005", "scenario": "Vulnerable crop stage", "farm_id": "F020", "expected": "Includes the recorded vulnerable crop stage as a risk factor."},
    {"task_id": "EVAL-006", "scenario": "Missing planting date", "farm_id": "F006", "expected": "Creates a follow-up and exposes missing planting-date evidence."},
    {"task_id": "EVAL-007", "scenario": "Unavailable climate source", "farm_id": "F017", "expected": "Returns insufficient evidence and does not infer weather values."},
    {"task_id": "EVAL-008", "scenario": "Conflicting crop-stage records", "farm_id": "F008", "expected": "Surfaces the conflict and creates a follow-up task."},
    {"task_id": "EVAL-009", "scenario": "Multi-farm prioritisation", "district": "Berea", "crop": "maize", "expected": "Ranks all matching farms by structured risk and confidence."},
    {"task_id": "EVAL-010", "scenario": "AgriSage MCP tool failure", "tool_failure": True, "expected": "Records a failed call to the AgriSage MCP server with its input and error."},
    {"task_id": "EVAL-011", "scenario": "Official Fetch MCP failure", "fetch_failure": True, "expected": "Records the borrowed server failure without inventing page content."},
    {"task_id": "EVAL-012", "scenario": "Named human approval", "farm_id": "F012", "approval_flow": True, "expected": "Persists a named officer approval with a timestamp."},
    {"task_id": "EVAL-013", "scenario": "Human edit and rejection", "farm_id": "F012", "edit_reject_flow": True, "expected": "Preserves original wording and records officer edit and rejection reason."},
    {"task_id": "EVAL-014", "scenario": "Configured open-weight model run", "farm_id": "F012", "real_model": True, "expected": "Completes a full task with the configured open-weight model; no silent substitute."},
]


def _new_run(db, request: dict[str, Any], evaluation_run_id: str | None = None) -> str:
    run_id = f"RUN-{uuid4().hex[:12].upper()}"
    run = WorkflowRun(
        workflow_run_id=run_id,
        user_request=f"Evaluation request for {request.get('farm_id') or request.get('district') or 'scope'}",
        status="RUNNING",
        selected_scope=request,
        model_provider=get_settings().model_provider,
        model_name=get_settings().model_name,
    )
    db.add(run)
    db.commit()
    return run_id


def _tool_rows(db, run_id: str) -> list[ToolCallLog]:
    return db.scalars(
        select(ToolCallLog)
        .where(ToolCallLog.workflow_run_id == run_id)
        .order_by(ToolCallLog.id)
    ).all()


def _request(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": "farm" if case.get("farm_id") else "cluster",
        "farm_id": case.get("farm_id"),
        "district": case.get("district"),
        "crop": case.get("crop"),
        "analysis_start": ANALYSIS_START.isoformat(),
        "analysis_end": ANALYSIS_END.isoformat(),
    }


def _run_mcp_failure(db, case: dict[str, Any], evaluation_run_id: str) -> dict[str, Any]:
    run_id = _new_run(db, case, evaluation_run_id)
    server = "Official Fetch MCP Server" if case.get("fetch_failure") else "AgriSage MCP Server"
    tool_name = "fetch" if case.get("fetch_failure") else "get_plot_context"
    arguments = (
        {"url": "https://agrisage-eval.unreachable.invalid/", "max_length": 300}
        if case.get("fetch_failure")
        else {"farm_id": "F404", "workflow_run_id": run_id}
    )
    async def invoke() -> bool:
        async with MCPToolClient(db, run_id, server) as client:
            try:
                await client.call_tool(tool_name, arguments)
            except MCPToolError:
                return True
        return False

    caught = asyncio.run(invoke())
    row = db.scalar(
        select(ToolCallLog).where(
            ToolCallLog.workflow_run_id == run_id,
            ToolCallLog.server_name == server,
            ToolCallLog.tool_name == tool_name,
        )
    )
    passed = bool(caught and row and row.status == "FAILURE" and row.input_payload == arguments)
    run = db.get(WorkflowRun, run_id)
    if run:
        run.status = "COMPLETE_WITH_FAILURES" if passed else "FAILED"
        run.completed_at = datetime.utcnow()
        run.duration_ms = row.duration_ms if row else 0
        run.tool_call_count = 1 if row else 0
        db.commit()
    actual = (
        f"{server} {tool_name} returned a logged FAILURE; no external content was accepted."
        if passed
        else f"The {server} failure was not returned and persisted as expected."
    )
    return _result(case, actual, [tool_name], False, [], passed, run_id, evaluation_run_id)


def _run_workflow_case(db, case: dict[str, Any], evaluation_run_id: str) -> dict[str, Any]:
    request = _request(case)
    run_id = _new_run(db, request, evaluation_run_id)
    provider = None if case.get("real_model") else TEST_PROVIDER
    try:
        state = run_analysis_workflow(db, run_id, request, model_provider=provider)
    except Exception as exc:
        rows = _tool_rows(db, run_id)
        is_model_failure = "MODEL_UNAVAILABLE" in str(exc)
        if case.get("real_model"):
            try:
                provider = get_model_provider()
                provider_name = provider.provider_name
                model_name = provider.model_name
            except Exception:
                settings = get_settings()
                provider_name = settings.model_provider
                model_name = settings.model_name
            run = db.get(WorkflowRun, run_id)
            advisory_count = db.scalar(
                select(func.count()).select_from(AdvisoryRecord).where(
                    AdvisoryRecord.workflow_run_id == run_id
                )
            ) or 0
            follow_up_count = db.scalar(
                select(func.count()).select_from(FollowUpTask).where(
                    FollowUpTask.workflow_run_id == run_id
                )
            ) or 0
            required_tools = {
                "get_plot_context",
                "get_climate_signals",
                "get_pest_signals",
                "draft_advisory",
            }
            called_tools = {row.tool_name for row in rows}
            failed_checks = [
                name
                for name, succeeded in {
                    "workflow_run_exists": run is not None,
                    "workflow_completed": bool(run and run.status == "COMPLETE"),
                    "advisory_created": advisory_count > 0,
                    "actual_provider_is_real": provider_name != TEST_PROVIDER.provider_name,
                    "actual_model_is_real": model_name != TEST_PROVIDER.model_name,
                    "stored_provider_matches_actual": bool(run and run.model_provider == provider_name),
                    "stored_model_matches_actual": bool(run and run.model_name == model_name),
                    "required_tools_called": required_tools.issubset(called_tools),
                }.items()
                if not succeeded
            ]
            actual = (
                f"EVAL-014 failed checks={', '.join(failed_checks) or 'workflow_exception'} "
                f"(raised {type(exc).__name__}: {exc}); "
                f"workflow_status={run.status if run else 'MISSING'}; "
                f"provider_name={provider_name}; model_name={model_name}; "
                f"stored_workflow_provider={run.model_provider if run else 'MISSING'}; "
                f"stored_workflow_model={run.model_name if run else 'MISSING'}; "
                f"tools_called={', '.join(row.tool_name for row in rows)}; "
                f"advisories_created={advisory_count}; follow-ups={follow_up_count}."
            )
        else:
            actual = (
                f"Workflow stopped with MODEL_UNAVAILABLE for {get_model_provider().provider_name}/"
                f"{get_model_provider().model_name}; no replacement model or rule output was used."
                if is_model_failure
                else "Workflow stopped after an unhandled dependency error."
            )
        passed = False
        return _result(
            case,
            actual,
            [row.tool_name for row in rows],
            False,
            [],
            passed,
            run_id,
            evaluation_run_id,
        )

    rows = _tool_rows(db, run_id)
    tools = [row.tool_name for row in rows]
    servers = {row.server_name for row in rows}
    assessments = state.get("assessments", {})
    evidence_used = sorted(
        {
            item["source"]
            for assessment in assessments.values()
            for item in assessment.get("evidence_chain", [])
            if item.get("source")
        }
    )
    farm_id = case.get("farm_id")
    assessment = assessments.get(farm_id) if farm_id else None
    passed = False
    real_model_diagnostics: str | None = None
    if case["task_id"] == "EVAL-001":
        called = {(row.server_name, row.tool_name) for row in rows}
        fetch_succeeded = any(
            row.server_name == "Official Fetch MCP Server"
            and row.tool_name == "fetch"
            and row.status == "SUCCESS"
            and len(row.output_summary or "") > 100
            for row in rows
        )
        passed = bool(
            state.get("advisories")
            and fetch_succeeded
            and all(("AgriSage MCP Server", tool) in called for tool in (
                "get_plot_context", "get_climate_signals", "get_pest_signals", "draft_advisory"
            ))
        )
    elif case["task_id"] == "EVAL-002":
        passed = bool(assessment and any("drought" in factor.lower() or "rainfall anomaly" in factor.lower() for factor in assessment["risk_factors"]))
    elif case["task_id"] == "EVAL-003":
        passed = bool(assessment and any("heavy-rain" in factor for factor in assessment["risk_factors"]))
    elif case["task_id"] == "EVAL-004":
        passed = bool(assessment and any("fall armyworm" in factor for factor in assessment["risk_factors"]))
    elif case["task_id"] == "EVAL-005":
        passed = bool(assessment and any("vulnerable crop stage" in factor for factor in assessment["risk_factors"]))
    elif case["task_id"] == "EVAL-006":
        passed = bool(assessment and any("Planting date" in item for item in assessment["missing_evidence"]) and state.get("follow_ups"))
    elif case["task_id"] == "EVAL-007":
        passed = bool(assessment and assessment["risk_level"] == "INSUFFICIENT_EVIDENCE" and any("Climate data" in item for item in assessment["missing_evidence"]))
    elif case["task_id"] == "EVAL-008":
        passed = bool(state.get("follow_ups") and assessment and any("conflicting" in item.lower() for item in assessment["missing_evidence"]))
    elif case["task_id"] == "EVAL-009":
        passed = len(state["priority_queue"]) > 1 and len(state["priority_queue"]) == len(state["farm_ids"])
    elif case["task_id"] == "EVAL-012" and case.get("approval_flow"):
        advisory_id = state["advisories"][0] if state.get("advisories") else None
        if advisory_id:
            approve_advisory(advisory_id, ApprovalRequest(officer_name="Mpho Review Officer"), db)
            approval = db.scalar(
                select(HumanApproval).where(
                    HumanApproval.advisory_id == advisory_id,
                    HumanApproval.decision == "APPROVED",
                )
            )
            advisory = db.scalar(select(AdvisoryRecord).where(AdvisoryRecord.advisory_id == advisory_id))
            passed = bool(
                approval
                and approval.officer_name == "Mpho Review Officer"
                and approval.timestamp
                and advisory
                and advisory.status == "APPROVED"
            )
    elif case["task_id"] == "EVAL-013" and case.get("edit_reject_flow"):
        advisory_id = state["advisories"][0] if state.get("advisories") else None
        if advisory_id:
            before = db.scalar(select(AdvisoryRecord).where(AdvisoryRecord.advisory_id == advisory_id))
            original = before.recommendation if before else ""
            edited = f"{original} Confirm the field observations with the district extension office."
            edit_advisory(
                advisory_id,
                EditRequest(officer_name="Mpho Review Officer", recommendation=edited),
                db,
            )
            reject_advisory(
                advisory_id,
                RejectRequest(
                    officer_name="Mpho Review Officer",
                    rejection_reason="Evidence needs a second field check.",
                ),
                db,
            )
            updated = db.scalar(select(AdvisoryRecord).where(AdvisoryRecord.advisory_id == advisory_id))
            decisions = db.scalars(
                select(HumanApproval).where(HumanApproval.advisory_id == advisory_id)
            ).all()
            passed = bool(
                updated
                and updated.status == "REJECTED"
                and updated.edited_text == original
                and updated.rejection_reason == "Evidence needs a second field check."
                and {item.decision for item in decisions} == {"EDITED", "REJECTED"}
            )
    elif case["task_id"] == "EVAL-014" and case.get("real_model"):
        provider = state.get("model_provider") or get_model_provider()
        run = db.get(WorkflowRun, run_id)
        persisted_advisories = db.scalars(
            select(AdvisoryRecord).where(AdvisoryRecord.workflow_run_id == run_id)
        ).all()
        follow_up_count = db.scalar(
            select(func.count()).select_from(FollowUpTask).where(
                FollowUpTask.workflow_run_id == run_id
            )
        ) or 0
        required_tools = {
            "get_plot_context",
            "get_climate_signals",
            "get_pest_signals",
            "draft_advisory",
        }
        checks = {
            "workflow_run_exists": run is not None,
            "workflow_completed": bool(run and run.status == "COMPLETE"),
            "advisory_persisted": bool(persisted_advisories),
            "actual_provider_is_real": provider.provider_name != TEST_PROVIDER.provider_name,
            "actual_model_is_real": provider.model_name != TEST_PROVIDER.model_name,
            "stored_provider_matches_actual": bool(run and run.model_provider == provider.provider_name),
            "stored_model_matches_actual": bool(run and run.model_name == provider.model_name),
            "required_tools_called": required_tools.issubset(set(tools)),
        }
        passed = all(checks.values())
        failed_checks = [name for name, passed_check in checks.items() if not passed_check]
        real_model_diagnostics = (
            f"stored_provider/model={run.model_provider if run else 'MISSING'}/"
            f"{run.model_name if run else 'MISSING'}; "
            f"workflow_status={run.status if run else 'MISSING'}; "
            f"checks={'all passed' if passed else ', '.join(failed_checks)}"
        )

    actual = (
        f"Risk={assessment['risk_level']}; tools={', '.join(tools)}; "
        f"pending drafts={len(state.get('advisories', []))}; follow-ups={len(state.get('follow_ups', []))}."
        if assessment
        else f"Workflow status=COMPLETE; tools={', '.join(tools)}."
    )
    if case.get("approval_flow"):
        actual = "Named officer approval and timestamp were persisted." if passed else "Named officer approval was not fully persisted."
    if case.get("edit_reject_flow"):
        actual = "Edited text, original draft, named officer, and rejection reason were persisted." if passed else "Edit/reject persistence did not match the expected record."
    if case.get("real_model"):
        provider = state.get("model_provider") or get_model_provider()
        persisted_advisory_count = db.scalar(
            select(func.count()).select_from(AdvisoryRecord).where(
                AdvisoryRecord.workflow_run_id == run_id
            )
        ) or 0
        follow_up_count = db.scalar(
            select(func.count()).select_from(FollowUpTask).where(
                FollowUpTask.workflow_run_id == run_id
            )
        ) or 0
        check_summary = real_model_diagnostics or (
            "checks=all passed" if passed else "checks were not evaluated"
        )
        actual = (
            f"provider/model={provider.provider_name}/{provider.model_name}; "
            f"tools={', '.join(tools)}; advisories={persisted_advisory_count}; "
            f"follow-ups={follow_up_count}; {check_summary}."
        )
    return _result(
        case,
        actual,
        tools,
        bool(state.get("advisories")),
        evidence_used,
        passed,
        run_id,
        evaluation_run_id,
    )


def _result(
    case: dict[str, Any],
    actual: str,
    tools: list[str],
    advisory: bool,
    evidence: list[str],
    passed: bool,
    run_id: str,
    evaluation_run_id: str,
) -> dict[str, Any]:
    return {
        "task_id": case["task_id"],
        "evaluation_run_id": evaluation_run_id,
        "scenario": case["scenario"],
        "expected_behaviour": case["expected"],
        "actual_behaviour": actual,
        "tools_called": tools,
        "advisory_produced": advisory,
        "evidence_used": evidence,
        "result": "PASS" if passed else "FAIL",
        "run_id": run_id,
        "recorded_at": datetime.utcnow().isoformat(),
    }


def _run_variation(db, evaluation_run_id: str) -> list[dict[str, Any]]:
    variations: list[dict[str, Any]] = []
    for index in range(1, 4):
        request = _request({"farm_id": "F012"})
        run_id = _new_run(db, request, evaluation_run_id)
        started = datetime.utcnow()
        state = run_analysis_workflow(db, run_id, request, model_provider=TEST_PROVIDER)
        run = db.get(WorkflowRun, run_id)
        assessment = state["assessments"]["F012"]
        advisory = db.scalar(
            select(AdvisoryRecord)
            .where(AdvisoryRecord.workflow_run_id == run_id)
            .order_by(AdvisoryRecord.created_at.desc())
        )
        variations.append(
            {
                "run": index,
                "workflow_run_id": run_id,
                "risk_level": assessment["risk_level"],
                "tool_sequence": [
                    f"{row.server_name}:{row.tool_name}" for row in _tool_rows(db, run_id)
                ],
                "advisory_summary": (advisory.recommendation[:180] if advisory else None),
                "latency_ms": run.duration_ms if run and run.duration_ms is not None else round((datetime.utcnow() - started).total_seconds() * 1000),
            }
        )
    return variations


def run_evaluations() -> list[dict[str, Any]]:
    initialize_database()
    settings = get_settings()
    evaluation_run_id = f"EVALRUN-{uuid4().hex[:10].upper()}"
    with SessionLocal() as db:
        db.execute(delete(EvaluationResult))
        run = EvaluationRun(
            evaluation_run_id=evaluation_run_id,
            model_provider=settings.model_provider,
            model_name=settings.model_name,
            status="RUNNING",
        )
        db.add(run)
        db.commit()

        original_external_url = settings.external_evidence_url
        results: list[dict[str, Any]] = []
        try:
            # The first full fixture run exercises the configured borrowed MCP server.
            # Later cases isolate farm/risk behavior and avoid repeating external fetches.
            for index, case in enumerate(CASES):
                if index == 1:
                    settings.external_evidence_url = ""
                if case.get("tool_failure") or case.get("fetch_failure"):
                    result = _run_mcp_failure(db, case, evaluation_run_id)
                else:
                    result = _run_workflow_case(db, case, evaluation_run_id)
                results.append(result)

            settings.external_evidence_url = ""
            variation = _run_variation(db, evaluation_run_id)
            run = db.get(EvaluationRun, evaluation_run_id)
            run.summary = {
                "variation_runs": variation,
                "variation_stable_risk": len({item["risk_level"] for item in variation}) == 1,
                "evaluation_model_note": "EVAL-001 to EVAL-013 use a named deterministic test double for workflow/risk checks; EVAL-014 attempts the configured provider without substitution.",
            }
        finally:
            settings.external_evidence_url = original_external_url

        db.add_all(
            [
                EvaluationResult(
                    task_id=result["task_id"],
                    evaluation_run_id=evaluation_run_id,
                    scenario=result["scenario"],
                    expected_behaviour=result["expected_behaviour"],
                    actual_behaviour=result["actual_behaviour"],
                    tools_called=result["tools_called"],
                    advisory_produced=result["advisory_produced"],
                    evidence_used=result["evidence_used"],
                    result=result["result"],
                    run_id=result["run_id"],
                )
                for result in results
            ]
        )
        run = db.get(EvaluationRun, evaluation_run_id)
        run.total_cases = len(results)
        run.passed_cases = sum(item["result"] == "PASS" for item in results)
        run.failed_cases = sum(item["result"] == "FAIL" for item in results)
        run.status = "COMPLETE_WITH_FAILURES" if run.failed_cases else "COMPLETE"
        run.completed_at = datetime.utcnow()
        db.commit()
        return results


if __name__ == "__main__":
    output = run_evaluations()
    print(json.dumps(output, indent=2))
    raise SystemExit(0 if all(item["result"] == "PASS" for item in output) else 1)
