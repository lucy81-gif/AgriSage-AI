# AgriSage AI

## Evidence Before Advice

AgriSage AI is a climate-smart advisory workspace for the **Agentic AI for Africa Innovation Challenge**, Agriculture & Food Security track. Its primary user is an agricultural extension officer. The prototype combines synthetic farm records with dated climate and pest signals, ranks farms for review, and drafts an advisory that remains under officer control.

## Problem statement

Extension officers may support many farmers while crop records, farm history, climate information, and pest reports sit in different places. That makes it hard to see which farms need attention, why they are at risk, and what information still needs checking.

## Solution overview

An officer selects a district, crop, scope, and analysis period, then runs **Climate-Smart Analysis**. A LangGraph workflow plans an investigation, retrieves evidence through MCP, checks freshness and missing data, calculates a deterministic risk assessment, builds an evidence chain, ranks farms, and creates reviewable advisory drafts. The workflow stops at `PENDING_APPROVAL`.

AgriSage AI does not message farmers. A named extension officer must approve, edit, or reject each consequential advisory.

## Target users and theme

- **Primary user:** agricultural extension officers.
- **Beneficiaries:** farmers, farm managers, and agricultural organisations.
- **Competition theme:** Climate-Smart Advisory.

## Architecture

The Next.js workspace calls a FastAPI backend. FastAPI creates a `WorkflowRun` and invokes a LangGraph state machine. The graph uses an MCP client over stdio to call the AgriSage MCP server and, when configured, the official Fetch MCP server. SQLAlchemy persists farm data, signals, evidence, risk assessments, tool calls, workflow events, advisories, approvals, follow-ups, and evaluation runs. See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/architecture.png](docs/architecture.png).

## Technology stack

- Next.js 16, React 19, TypeScript, Tailwind CSS 4
- FastAPI, Pydantic, SQLAlchemy 2, LangGraph
- Python MCP SDK and the official `mcp-server-fetch` reference server
- SQLite at `./runtime/agrisage.db` when `DATABASE_URL` is omitted; PostgreSQL through `DATABASE_URL` for deployment (Railway PostgreSQL)
- Ollama with the open-weight `qwen3:1.7b` model by default; OpenAI-compatible open-weight endpoints are also supported

The risk engine is deterministic. The language model plans evidence retrieval and drafts concise officer-facing language; it does not assign risk scores or fill missing fields. If the configured model is unavailable, the API returns `MODEL_UNAVAILABLE` and does not substitute rule-generated text.

## Synthetic data and provenance

The checked-in dataset contains **26 synthetic Lesotho farms** across Maseru, Berea, Leribe, Mafeteng, and Mohale's Hoek. It includes maize, beans, sorghum, and wheat, plus missing planting dates, old records, crop-stage conflicts, prior incidents, and varied climate scenarios. The records are seeded into SQLAlchemy tables only when the database has no farm records.

Farm and pest records are synthetic. The checked-in climate records are also synthetic and carry `source_type`, source, and observation timestamp. The interface labels the demonstration data as synthetic. A public external reference is retrieved only through the configured Fetch MCP server; fetched page text is stored as reference context and never changes the deterministic risk score.

## MCP servers and tools

### MCP server built for AgriSage

The Python server in `mcp-server/server.py` exposes:

- `get_plot_context` — plot, crop stage, soil, history, and intervention context.
- `get_climate_signals` — dated rainfall, forecast, temperature, anomaly, freshness, and confidence.
- `get_pest_signals` — crop and zone reports with severity, count, date, and confidence.
- `draft_advisory` — writes an advisory that is always `PENDING_APPROVAL`.
- `create_follow_up` — creates an officer task for missing or conflicting evidence.

The LangGraph workflow launches this server as a child process and communicates using MCP stdio. It does not call these functions directly.

### Borrowed MCP server: official Fetch

AgriSage installs and launches the official `mcp-server-fetch` package as a separate MCP process. We use the official Fetch MCP server because web retrieval is a generic capability already provided through a reusable MCP implementation; AgriSage's own MCP server remains focused on agriculture-specific domain tools and actions. The configurable `EXTERNAL_EVIDENCE_URL` is fetched through the MCP `fetch` tool. A failed fetch is logged with its error; its content is never invented.

The official server can access public web pages and applies its own address checks. Configure only a public HTTPS reference URL. The Fetch server is optional to the risk calculation; an unavailable page does not replace climate or farm evidence.

## Setup and local run

### Option A: Docker Compose

Install Docker Desktop, then run from the repository root:

```powershell
docker compose up --build
```

Compose starts the frontend, API, Ollama, and a one-shot Qwen model pull. The first model pull is large and may take several minutes. The dashboard is at <http://localhost:3000>; the API health check is <http://localhost:8000/api/health>.

### Option B: Windows PowerShell

Install Python 3.11 or newer, Node.js 20 or newer, and Ollama. From the repository root:

```powershell
Copy-Item .env.example .env
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull qwen3:1.7b
python -m backend.app.db.init_db
```

In another terminal, start Ollama if it is not already running:

```powershell
ollama serve
```

In separate terminals, start the API and frontend:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>. `frontend/.env.local` sets `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` for local development. The API launches the AgriSage MCP server itself for each workflow; it does not require a separate MCP terminal.

## Usage

1. Open the overview and check the backend-derived farm counts.
2. Select **Run climate-smart analysis**. Choose a district, crop, all/cluster/one-farm scope, and analysis period. One-farm scope requires a farm record selection.
3. Wait for the LangGraph run to finish. If Ollama or the configured model endpoint is unavailable, the UI displays the explicit model error and the run is recorded as failed.
4. Open **Priority Queue**, choose a farm, and review the evidence chain, risk factors, missing data, and sources.
5. Open **Advisories** and review the draft. Enter an officer name to approve or edit; rejection also records a reason.
6. Open **Agent Trace** to inspect state transitions and MCP inputs, outputs, timestamps, durations, server names, and failures.
7. Open **Evaluations** to review persisted evaluation results. Re-run the suite with `python -m evaluations.run`.

## Agent architecture

LangGraph runs these public states: `receive_request`, `identify_scope`, `plan_investigation`, `retrieve_plot_context`, `retrieve_climate_signals`, `retrieve_pest_signals`, `retrieve_external_evidence`, `assess_data_quality`, `handle_missing_or_conflicting_data`, `calculate_risk`, `build_evidence_chain`, `prioritise_farms`, `draft_advisories`, `await_human_approval`, and `complete`. A conditional edge routes incomplete evidence through follow-up handling before risk calculation. Tool failures are recorded and do not become fabricated evidence.

The model interprets the request, prepares a short retrieval plan, and writes advisory language from structured evidence. Deterministic code handles data freshness, missing evidence, risk thresholds, prioritisation, and approval states. Public traces contain tool results and concise summaries, not private chain of thought.

## Human review and auditability

The action tool creates only `PENDING_APPROVAL` records. Approve, edit, and reject actions persist the officer name and timestamp in `HumanApproval`; edits retain the original draft, and rejection stores its reason. No farmer-facing delivery endpoint exists.

Each MCP invocation has a `ToolCallLog` with server, tool, JSON input, JSON output or error, status, start/end timestamps, duration, and summary. Risk recommendations store evidence items that identify their source and confidence. Workflow runs also store model and provider metadata, tool count, duration, and token counts when the provider returns them.

## API

The frontend uses these backend endpoints:

- `GET /api/health`, `GET /api/dashboard`, `GET /api/farms`, `GET /api/farms/{id}`
- `POST /api/analysis/run`, `GET /api/analysis/{run_id}`
- `GET /api/priority-queue`, `GET /api/advisories`, `GET /api/advisories/{id}`
- `POST /api/advisories/{id}/approve`, `/edit`, and `/reject`
- `GET /api/traces`, `GET /api/traces/{run_id}`, `GET /api/evaluations`, `GET /api/follow-ups`

## Configuration

See [.env.example](.env.example). Key variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Optional locally; omitted means `./runtime/agrisage.db` (SQLite). Set to Railway's PostgreSQL connection reference for deployment. `postgres://` and `postgresql://` URLs are supported. |
| `MODEL_PROVIDER` | `ollama` or `openai_compatible`. |
| `MODEL_NAME` | Defaults to `qwen3:1.7b`. |
| `OLLAMA_BASE_URL` | Local Ollama URL; defaults to `http://localhost:11434`. |
| `MODEL_BASE_URL`, `MODEL_API_KEY` | Hosted OpenAI-compatible open-weight endpoint. |
| `EXTERNAL_EVIDENCE_URL` | Public HTTPS URL retrieved through the Fetch MCP server. |
| `CORS_ORIGINS` | Comma-separated frontend origins for the FastAPI backend. |
| `NEXT_PUBLIC_API_URL` | Frontend build/runtime API URL. |

Do not commit `.env`, API keys, database credentials, or private URLs. `.env` is ignored by Git.

## Tests and evaluations

Run the backend tests and scenario suite from the repository root:

```powershell
python -m pytest
python -m evaluations.run
```

The evaluation runner persists each case and three repeated normal-workflow runs. Deterministic fixture workflows use an explicitly named test-only model provider so risk, MCP, persistence, and approval behavior can be exercised without pretending that Ollama ran. A separate evaluation attempts the configured real open-weight model. Results, including failures, are written to the database and summarized in [EVALS.md](EVALS.md).

## Deployment

The API uses Railway PostgreSQL through `DATABASE_URL`; the frontend receives the API origin through `NEXT_PUBLIC_API_URL` at build time. The Railway API currently builds from the GitHub `main` branch using Railpack's Python detection. The Vercel project is connected to the same repository with `frontend` as its root directory. The repository also includes [backend/Dockerfile](backend/Dockerfile) for Docker-based deployments. Configure a hosted open-weight model through `MODEL_PROVIDER=openai_compatible`, `MODEL_BASE_URL`, `MODEL_NAME`, and `MODEL_API_KEY`. Never point production model configuration at a local-only URL.

**Production URLs (2026-10-14):**

- Frontend: [https://frontend-lucy81-gifs-projects.vercel.app](https://frontend-lucy81-gifs-projects.vercel.app) — the deployment is ready, but Vercel SSO currently requires authentication, so public access is pending.
- Backend: [https://api-production-9585.up.railway.app](https://api-production-9585.up.railway.app) — `/api/health` returned HTTP 200 with PostgreSQL connected. After a Railway restart, the API still returned all 26 seeded farms.

The frontend's production API URL and Railway CORS origins are configured. A browser CORS preflight from the Vercel production origin returned HTTP 200. Full public analysis and advisory persistence verification are pending a hosted model endpoint; the production advisory, trace, and evaluation lists are currently empty. The local EVAL-014 run completed with `ollama/qwen3:1.7b` on 2026-10-14. See [DEPLOYMENT.md](DEPLOYMENT.md) for current checks and remaining setup.

## Limitations

- All included farm, pest, and climate data is synthetic and intended for demonstration, not operational farming decisions.
- A successful full workflow requires an available configured open-weight model. The local EVAL-014 evaluation completed with Ollama `qwen3:1.7b`; a public Railway deployment needs a hosted endpoint because its `localhost` address cannot reach the development machine.
- Public Fetch content is optional context and can fail independently.
- The production dependency audit is clean. The full npm audit reports five high findings in the ESLint development dependency chain through `braces`; the [upstream advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) lists no patched version as of 2026-10-13.
- Officer names are recorded for audit and are not authenticated identities; production use needs extension-office identity controls.
- The workflow is synchronous and is designed for the small competition dataset, not large-scale field operations.
- Lesotho field validation, local language support, offline sync, and live extension-office integrations remain future work.

## Future improvements

Validate with extension officers and real, permissioned datasets; add Sesotho support, offline synchronisation, USSD access, more African crops, and approved extension-office integrations.

## Demo

Recording: **not recorded yet**. Add the public YouTube or Vimeo URL here after recording. Use [DEMO_SCRIPT.md](DEMO_SCRIPT.md); the recording must show an unedited workflow run.

## Repository structure

```text
backend/        FastAPI routes, LangGraph, SQLAlchemy models, tests
data/           Synthetic farm, climate, and pest seed records
evaluations/    Executable evaluation scenarios
frontend/       Next.js extension-office workspace
mcp-server/     AgriSage agriculture-specific MCP tools
docs/           Architecture diagram and supporting material
```

## Competition compliance checklist

| Requirement | Status | Evidence |
|---|---|---|
| AgriSage MCP server and three distinct tools | COMPLETE | `mcp-server/server.py`; MCP protocol tests |
| MCP action tool with human approval gate | COMPLETE | `draft_advisory`; persisted `PENDING_APPROVAL` |
| Borrowed MCP server | COMPLETE | Official Fetch MCP call returned FAO page content in EVAL-001; failure logging verified in EVAL-011 |
| Open-source orchestration | COMPLETE | LangGraph state graph in `backend/app/agents/graph.py` |
| Full open-weight model workflow | COMPLETE locally; public hosting pending | EVAL-014 used `ollama/qwen3:1.7b`; see `EVALS.md` |
| Tool-call inputs, outputs, timestamps, and failures | COMPLETE | `ToolCallLog` and Agent Trace |
| Named human approval, edit, and rejection | COMPLETE | `HumanApproval` and advisory API routes |
| Evidence-backed recommendations | COMPLETE | Risk assessment evidence chain and farm detail |
| At least eight evaluation tasks and honest failure | COMPLETE; 14 executed, 13 passed, 1 real-model failure | Persisted suite results and run ID in EVALS.md |
| OSI-approved licence | COMPLETE | MIT in [LICENSE](LICENSE) |
| Public-repository-ready documentation | COMPLETE | README, ARCHITECTURE.md, EVALS.md, DEMO_SCRIPT.md |
| Local Docker run | PARTIAL until Docker acceptance is run | `docker-compose.yml` |
| Production deployment | NOT DEPLOYED | No hosting credentials or URLs supplied |
| Dependency audit | PARTIAL | Production npm audit clean; one unpatched development-tool advisory remains |

## Licence

MIT. See [LICENSE](LICENSE).
