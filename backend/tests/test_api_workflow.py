from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.models import HumanApproval
from backend.app.services import model_provider as model_module


def test_analysis_creates_trace_and_pending_advisory():
    with TestClient(app) as client:
        response = client.post(
            "/api/analysis/run",
            json={"scope": "farm", "farm_id": "F012", "analysis_start": "2026-10-01", "analysis_end": "2026-10-08"},
        )
        assert response.status_code == 201, response.text
        run_id = response.json()["workflow_run_id"]

        assert client.get("/api/health").json()["status"] == "ok"
        assert client.get("/api/dashboard").json()["farms"] >= 25
        assert len(client.get("/api/farms").json()) >= 25

        traces = client.get(f"/api/traces/{run_id}")
        assert traces.status_code == 200
        assert traces.json()["status"] == "COMPLETE"
        plot_call = next(item for item in traces.json()["tool_calls"] if item["tool_name"] == "get_plot_context")
        assert plot_call["server_name"] == "AgriSage MCP Server"
        assert plot_call["input_payload"] == {"farm_id": "F012", "workflow_run_id": run_id}
        assert plot_call["started_at"] and plot_call["completed_at"]
        assert plot_call["duration_ms"] is not None

        advisories = client.get("/api/advisories").json()
        advisory = next(item for item in advisories if item["farm_id"] == "F012")
        assert advisory["status"] == "PENDING_APPROVAL"

        approved = client.post(
            f"/api/advisories/{advisory['advisory_id']}/approve",
            json={"officer_name": "Test Extension Officer"},
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "APPROVED"
        assert approved.json()["approving_officer"] == "Test Extension Officer"
        assert approved.json()["approval_timestamp"]
        with SessionLocal() as db:
            approval = db.scalar(
                select(HumanApproval).where(
                    HumanApproval.advisory_id == advisory["advisory_id"],
                    HumanApproval.decision == "APPROVED",
                )
            )
        assert approval and approval.officer_name == "Test Extension Officer"


def test_advisory_edit_and_reject_are_persisted():
    with TestClient(app) as client:
        response = client.post(
            "/api/analysis/run",
            json={"scope": "farm", "farm_id": "F012", "analysis_start": "2026-10-01", "analysis_end": "2026-10-08"},
        )
        assert response.status_code == 201, response.text
        advisories = client.get("/api/advisories?status=PENDING_APPROVAL").json()
        advisory = advisories[0]
        original = advisory["recommendation"]

        edited = client.post(
            f"/api/advisories/{advisory['advisory_id']}/edit",
            json={
                "officer_name": "Mpho Review Officer",
                "recommendation": f"{original} Confirm the next field visit with the district office.",
            },
        )
        assert edited.status_code == 200, edited.text
        assert edited.json()["status"] == "EDITED"
        assert edited.json()["edited_text"] == original

        rejected = client.post(
            f"/api/advisories/{advisory['advisory_id']}/reject",
            json={
                "officer_name": "Mpho Review Officer",
                "rejection_reason": "Evidence needs a second field check.",
            },
        )
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["status"] == "REJECTED"
        assert rejected.json()["rejection_reason"] == "Evidence needs a second field check."
        with SessionLocal() as db:
            decisions = db.scalars(
                select(HumanApproval).where(HumanApproval.advisory_id == advisory["advisory_id"])
            ).all()
        assert {item.decision for item in decisions} >= {"EDITED", "REJECTED"}


def test_model_unavailable_is_explicit_and_does_not_substitute_rule_text(monkeypatch):
    from backend.app.agents import graph

    monkeypatch.setattr(
        graph,
        "get_model_provider",
        lambda: model_module.OpenWeightModelProvider(
            provider_name="ollama",
            model_name="qwen3:1.7b",
            base_url="http://127.0.0.1:1",
            api_key="",
            timeout_seconds=0.1,
        ),
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/analysis/run",
            json={"scope": "farm", "farm_id": "F012", "analysis_start": "2026-10-01", "analysis_end": "2026-10-08"},
        )
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "MODEL_UNAVAILABLE"
        traces = client.get("/api/traces").json()
        failed = next(item for item in traces if item["status"] == "FAILED")
        assert any(item["label"] == "Investigation failed" for item in failed["events"])


def test_unavailable_climate_is_exposed_as_insufficient_evidence():
    with TestClient(app) as client:
        response = client.post(
            "/api/analysis/run",
            json={"scope": "farm", "farm_id": "F017", "analysis_start": "2026-10-01", "analysis_end": "2026-10-08"},
        )
        assert response.status_code == 201, response.text
        farm = client.get("/api/farms/F017")
        assert farm.status_code == 200
        assert farm.json()["risk_level"] == "INSUFFICIENT_EVIDENCE"
        assert any("Climate data" in item for item in farm.json()["missing_evidence"])

        follow_up = client.post(
            "/api/follow-ups",
            json={"farm_id": "F017", "reason": "Confirm current climate reading", "priority": "HIGH"},
        )
        assert follow_up.status_code == 201
        assert follow_up.json()["status"] == "OPEN"
