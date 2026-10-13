from __future__ import annotations

import json
import os
import sys
import time
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sqlalchemy.orm import Session

from backend.app.models import ToolCallLog


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MCPToolError(RuntimeError):
    """An MCP server or tool call failed; the attempt is still written to the audit log."""


class MCPToolClient:
    def __init__(self, db: Session, workflow_run_id: str, server_name: str):
        self.db = db
        self.workflow_run_id = workflow_run_id
        self.server_name = server_name
        self.stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None
        self.tools: set[str] = set()
        self.connection_error: str | None = None

    async def __aenter__(self) -> "MCPToolClient":
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        if self.server_name == "AgriSage MCP Server":
            parameters = StdioServerParameters(
                command=sys.executable,
                args=[str(PROJECT_ROOT / "mcp-server" / "server.py")],
                env=self._child_environment(),
            )
        elif self.server_name == "Official Fetch MCP Server":
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "mcp_server_fetch"],
                env=self._child_environment(),
            )
        else:
            raise ValueError(f"Unsupported MCP server: {self.server_name}")

        try:
            read_stream, write_stream = await self.stack.enter_async_context(
                stdio_client(parameters)
            )
            self.session = await self.stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
            listed = await self.session.list_tools()
            self.tools = {tool.name for tool in listed.tools}
        except Exception as exc:  # server absence is handled per requested tool and logged
            self.connection_error = f"{self.server_name} could not be started or initialized."
            await self.stack.aclose()
            self.stack = None
            self.session = None
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        if self.stack is not None:
            await self.stack.aclose()
            self.stack = None

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        started_at = datetime.utcnow()
        timer = time.perf_counter()
        result: dict[str, Any] = {}
        failure: str | None = None
        try:
            # Close the API session's write transaction before an action MCP tool writes
            # through its own SQLAlchemy session to the same database.
            self.db.commit()
            if self.connection_error:
                raise MCPToolError(self.connection_error)
            if self.session is None or tool_name not in self.tools:
                raise MCPToolError(f"{self.server_name} does not expose {tool_name}.")
            response = await self.session.call_tool(tool_name, arguments=arguments)
            if response.isError:
                message = " ".join(
                    block.text for block in response.content if getattr(block, "text", None)
                )
                raise MCPToolError(message or f"{tool_name} returned an MCP tool error.")
            result = self._content_as_dict(response)
        except Exception as exc:
            failure = str(exc)[:1000] or f"{tool_name} failed."
        completed_at = datetime.utcnow()
        duration_ms = max(0, round((time.perf_counter() - timer) * 1000))
        log = ToolCallLog(
            workflow_run_id=self.workflow_run_id,
            server_name=self.server_name,
            tool_name=tool_name,
            input_payload=arguments,
            output_payload=result if result else ({"error": failure} if failure else {}),
            output_summary=(
                json.dumps(result, ensure_ascii=False, default=str)[:500]
                if result
                else failure
            ),
            timestamp=started_at,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            status="FAILURE" if failure else "SUCCESS",
            action_type=tool_name if tool_name in {"draft_advisory", "create_follow_up"} else None,
            actor="agent" if tool_name in {"draft_advisory", "create_follow_up"} else None,
            human_approval_required=tool_name == "draft_advisory",
            error_message=failure,
        )
        self.db.add(log)
        self.db.commit()
        if failure:
            raise MCPToolError(failure)
        return result

    @staticmethod
    def _content_as_dict(response: Any) -> dict[str, Any]:
        structured = getattr(response, "structuredContent", None)
        if isinstance(structured, dict):
            return structured
        text_blocks = [
            block.text for block in response.content if getattr(block, "text", None)
        ]
        text_content = "\n".join(text_blocks)
        try:
            parsed = json.loads(text_content)
            if isinstance(parsed, dict):
                return parsed
            return {"result": parsed}
        except (json.JSONDecodeError, TypeError):
            return {"content": text_content}

    @staticmethod
    def _child_environment() -> dict[str, str]:
        environment = dict(os.environ)
        environment["PYTHONIOENCODING"] = "utf-8"
        current_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(PROJECT_ROOT), current_pythonpath) if part
        )
        return environment
