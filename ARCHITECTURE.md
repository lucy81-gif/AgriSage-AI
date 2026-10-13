# AgriSage AI architecture

AgriSage AI supports an agricultural extension officer investigating which farms need attention. The operating principle is **Evidence Before Advice**: the officer can inspect sources and missing information before approving any advisory.

![AgriSage AI architecture]

## Components and data flow

1. The Next.js frontend loads farm and dashboard data from FastAPI. The officer submits a district, crop, farm/cluster scope, and analysis dates.
2. FastAPI persists a `WorkflowRun` and invokes the LangGraph state machine. The graph uses the configured open-weight model for a short investigation plan and advisory language. Ollama/Qwen3 is the local default; an OpenAI-compatible open-weight endpoint is also supported.
3. The MCP client launches the **MCP server built for AgriSage** as a stdio child process. It calls `get_plot_context`, `get_climate_signals`, `get_pest_signals`, and, where needed, `create_follow_up` and `draft_advisory`.
4. When `EXTERNAL_EVIDENCE_URL` is configured, the client launches the **borrowed official Fetch MCP server** and calls `fetch`. Fetch is a reusable public-page retrieval capability; the AgriSage server remains focused on agriculture-specific records and actions. A failed call is logged and its content is not guessed.
5. SQLAlchemy reads and writes one durable database: SQLite at `./runtime/agrisage.db` when `DATABASE_URL` is absent, or PostgreSQL when a URL is provided. Railway supplies the production PostgreSQL URL through the backend's `DATABASE_URL` environment variable. Farm, climate, and pest signals are synthetic and are seeded into that database only when it has no farm records.
6. A deterministic risk service checks rainfall, drought/heavy rain, pest reports, crop stage, incidents, freshness, and missing fields. It creates `RiskAssessment` and `EvidenceItemRecord` records, then ranks farms. External reference text can inform advisory wording but does not change the risk score.
7. `draft_advisory` writes the draft as `PENDING_APPROVAL`. The workflow reaches `await_human_approval` and stops. The extension officer separately approves, edits, or rejects it; `HumanApproval` stores the officer and timestamp. No farmer message is sent by the agent.
8. `ToolCallLog` stores each MCP server/tool, JSON input, JSON output or failure, status, timestamps, and duration. `WorkflowEvent` stores public workflow states and concise results. Neither trace exposes private chain of thought.

## LangGraph states

`receive_request → identify_scope → plan_investigation → retrieve_plot_context → retrieve_climate_signals → retrieve_pest_signals → retrieve_external_evidence → assess_data_quality → [conditional follow-up] → calculate_risk → build_evidence_chain → prioritise_farms → draft_advisories → await_human_approval → complete`

If farm, climate, or crop-stage evidence is missing, stale, conflicting, or unavailable, the graph records it and may create a follow-up before scoring. Tool failures are preserved in the trace. The deterministic risk engine returns `INSUFFICIENT_EVIDENCE` when critical evidence is unavailable.

## MCP servers

**Built by AgriSage:** `mcp-server/server.py`, implemented with the Python MCP SDK. Its tools operate on the AgriSage SQLAlchemy database and handle agriculture-specific context and draft actions.

**Borrowed:** the official [`mcp-server-fetch`](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) reference server, installed as an external package and launched as a separate process. It fetches configured public web pages. Its reusable generic capability avoids copying a second web-fetch implementation into this repository.

## Database entities

`FarmRecord`, `ClimateSignal`, `PestSignal`, `WorkflowRun`, `ToolCallLog`, `WorkflowEvent`, `RiskAssessment`, `EvidenceItemRecord`, `DecisionEvent`, `AdvisoryRecord`, `FollowUpTask`, `EvaluationRun`, `EvaluationResult`, and `HumanApproval` are SQLAlchemy models. Initialization creates missing tables and applies additive column upgrades. Seed rows, workflow traces, MCP logs, risk assessments, advisories, named approval decisions, follow-ups, and evaluation runs/results all use the configured database; none are held only in process memory.

## Model and safety boundary

The model interprets the request, plans retrieval, synthesizes evidence, and drafts concise officer-facing wording. Risk thresholds, freshness checks, missing-data handling, priority ordering, and approval state transitions stay in code. An unavailable model returns `MODEL_UNAVAILABLE`; the runtime does not substitute a proprietary model or rule-generated advisory. Human approval remains required before use.
