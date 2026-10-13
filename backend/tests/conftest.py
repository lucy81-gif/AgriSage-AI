from __future__ import annotations

import pytest

from backend.app.agents import graph
from backend.app.core.config import get_settings
from backend.app.services.model_provider import ModelResponse


class WorkflowTestModel:
    """Explicit deterministic test fixture; production never selects this provider."""

    provider_name = "pytest-test-fixture"
    model_name = "workflow-test-double"

    def plan(self, request, farm_count):
        return ModelResponse(f"Fixture plan for {farm_count} matched farm(s).")

    def draft(self, farm, assessment, external_evidence=None):
        return ModelResponse(
            f"Test draft for {farm['farm_id']}: {assessment['recommended_next_action']} "
            "An extension officer must verify the field before any treatment decision."
        )


@pytest.fixture(autouse=True)
def configured_workflow_test_dependencies(monkeypatch):
    monkeypatch.setattr(graph, "get_model_provider", lambda: WorkflowTestModel())
    monkeypatch.setattr(get_settings(), "external_evidence_url", "")
