from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.app.db.init_db import initialize_database
from backend.app.db.session import SessionLocal
from backend.app.models import AdvisoryRecord, ToolCallLog, WorkflowRun
from backend.app.services.mcp_client import MCPToolClient, MCPToolError


def _create_run(db) -> str:
    run_id = f"MCP-{uuid4().hex[:10].upper()}"
    db.add(
        WorkflowRun(
            workflow_run_id=run_id,
            user_request="MCP protocol integration test",
            status="RUNNING",
            selected_scope={"scope": "farm", "farm_id": "F012"},
        )
    )
    db.commit()
    return run_id


def test_agrisage_mcp_protocol_lists_and_calls_domain_tools():
    initialize_database()
    with SessionLocal() as db:
        run_id = _create_run(db)

        async def invoke():
            async with MCPToolClient(db, run_id, "AgriSage MCP Server") as client:
                assert {
                    "get_plot_context",
                    "get_climate_signals",
                    "get_pest_signals",
                    "draft_advisory",
                    "create_follow_up",
                }.issubset(client.tools)
                return await client.call_tool(
                    "get_plot_context",
                    {"farm_id": "F012", "workflow_run_id": run_id},
                )

        result = asyncio.run(invoke())
        assert result["farm_id"] == "F012"
        assert result["source"] == "AgriSage synthetic farm register"
        call = db.scalar(
            select(ToolCallLog).where(
                ToolCallLog.workflow_run_id == run_id,
                ToolCallLog.tool_name == "get_plot_context",
            )
        )
        assert call and call.server_name == "AgriSage MCP Server"
        assert call.status == "SUCCESS"
        assert call.started_at and call.completed_at and call.duration_ms is not None
        assert call.input_payload["farm_id"] == "F012"
        assert call.output_payload["farm_id"] == "F012"


def test_mcp_action_creates_only_pending_approval_advisory():
    initialize_database()
    with SessionLocal() as db:
        run_id = _create_run(db)

        async def invoke():
            async with MCPToolClient(db, run_id, "AgriSage MCP Server") as client:
                return await client.call_tool(
                    "draft_advisory",
                    {
                        "workflow_run_id": run_id,
                        "farm_id": "F012",
                        "risk_level": "HIGH",
                        "recommendation": "Inspect the field and confirm symptoms with the extension officer.",
                        "evidence": [{"label": "rainfall", "source": "get_climate_signals", "detail": "Below normal"}],
                        "missing_information": [],
                        "confidence": 0.8,
                    },
                )

        result = asyncio.run(invoke())
        advisory = db.scalar(
            select(AdvisoryRecord).where(AdvisoryRecord.advisory_id == result["advisory_id"])
        )
        assert result["status"] == "PENDING_APPROVAL"
        assert result["human_approval_required"] is True
        assert advisory and advisory.status == "PENDING_APPROVAL"


def test_mcp_failure_is_logged_with_the_attempted_input():
    initialize_database()
    with SessionLocal() as db:
        run_id = _create_run(db)

        async def invoke():
            async with MCPToolClient(db, run_id, "AgriSage MCP Server") as client:
                with pytest.raises(MCPToolError):
                    await client.call_tool(
                        "get_plot_context",
                        {"farm_id": "F404", "workflow_run_id": run_id},
                    )

        asyncio.run(invoke())
        call = db.scalar(
            select(ToolCallLog).where(
                ToolCallLog.workflow_run_id == run_id,
                ToolCallLog.tool_name == "get_plot_context",
            )
        )
        assert call and call.status == "FAILURE"
        assert call.input_payload["farm_id"] == "F404"
        assert call.error_message


def test_official_fetch_mcp_server_is_a_separate_protocol_server():
    initialize_database()
    with SessionLocal() as db:
        run_id = _create_run(db)

        async def list_tools():
            async with MCPToolClient(db, run_id, "Official Fetch MCP Server") as client:
                return client.tools

        tools = asyncio.run(list_tools())
        assert "fetch" in tools
