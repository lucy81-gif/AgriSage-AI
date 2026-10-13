# Evaluation results

## Latest execution

- **Evaluation run:** `EVALRUN-F65A19DB77`
- **Date:** 2026-10-13
- **Command:** `python -m evaluations.run`
- **Result:** 14 cases executed; 13 passed and 1 failed. The runner returned exit code 1 because the real-model case could not run without an Ollama endpoint.
- **Persistence:** Per-case results, workflow/tool traces, the summary, and three repeat runs were written to the configured SQLite database.

Cases EVAL-001 through EVAL-009 and EVAL-012 through EVAL-013 use the named `EvaluationOnlyModelProvider` test fixture. They verify workflow control flow, deterministic risk assessment, MCP calls, persistence, and officer review; they do not evaluate real model quality. EVAL-010 and EVAL-011 directly exercise and inspect MCP failure logs. EVAL-014 calls the configured provider without a substitute.

## Case results

| ID | Scenario | Observed result | Status |
|---|---|---|---|
| EVAL-001 | Normal maize workflow with public reference | Moderate risk; AgriSage plot, climate, pest, and draft tools ran; official Fetch returned FAO page content; draft remained pending approval. | PASS |
| EVAL-002 | Drought scenario | Negative rainfall evidence was used in the risk factors; a reviewable draft was created. | PASS |
| EVAL-003 | Heavy-rain scenario | Heavy-rain evidence was surfaced with a cautious reviewable draft. | PASS |
| EVAL-004 | High pest-risk signal | Risk was HIGH; the nearby pest signal was used without claiming a confirmed plot infestation. | PASS |
| EVAL-005 | Vulnerable crop stage | Recorded vulnerable stage appeared in the risk factors. | PASS |
| EVAL-006 | Missing planting date | Risk was `INSUFFICIENT_EVIDENCE`; a follow-up was created and no advisory draft was created. | PASS |
| EVAL-007 | Unavailable climate source | Risk was `INSUFFICIENT_EVIDENCE`; missing climate evidence was surfaced and a follow-up was created. | PASS |
| EVAL-008 | Conflicting crop-stage records | The conflict was surfaced and a follow-up was created before a cautious draft. | PASS |
| EVAL-009 | Multi-farm prioritisation | Four matching farms were assessed and included in the priority queue. | PASS |
| EVAL-010 | AgriSage MCP tool failure | A forced missing-farm call was recorded as a failure with its input and error. | PASS |
| EVAL-011 | Official Fetch MCP failure | A forced `.invalid` URL was recorded as a failure; no fetched content was accepted. | PASS |
| EVAL-012 | Named human approval | The named officer approval and timestamp were persisted. | PASS |
| EVAL-013 | Human edit and rejection | The original draft, edited text, named officer, and rejection reason were persisted. | PASS |
| EVAL-014 | Configured open-weight model run | `ollama/qwen3:1.7b` returned `MODEL_UNAVAILABLE`; no replacement model or rule-generated advisory was used. | **FAIL — unresolved runtime dependency** |

The successful EVAL-001 Fetch response was recorded through the official `mcp-server-fetch` MCP process. The Fetch tool-call summary contains page content from [FAO's climate-smart agriculture page](https://www.fao.org/policy-support/policy-themes/climate-smart-agriculture/Understanding-climate-smart-agriculture-/en). External page text is context only and does not change deterministic risk scores.

## Repeatability and trace metrics

Three additional F012 fixture runs produced the same `MODERATE` risk result and the same four-tool sequence: `get_plot_context`, `get_climate_signals`, `get_pest_signals`, `draft_advisory`.

| Repeat | Risk | Recorded duration |
|---|---|---:|
| 1 | MODERATE | 1,602 ms |
| 2 | MODERATE | 1,411 ms |
| 3 | MODERATE | 1,429 ms |

Mean recorded duration was 1,481 ms (range 1,411–1,602 ms). These timings include local MCP process startup and use the deterministic fixture provider; they are not real-model latency measurements. Across the 14 case runs and three repeats, 66 MCP calls were recorded. Model token counts are absent because no real model response completed.

## Verification results

- Backend: `python -m pytest backend/tests -q` — **13 passed**.
- Python dependencies: `python -m pip check` — **no broken requirements**.
- Frontend: `npm run build` — **passed**, including TypeScript and static page generation.
- Production npm dependencies: `npm audit --omit=dev` — **0 vulnerabilities**.
- Full npm dependency tree: **5 high findings** are reported through the ESLint development dependency chain (`braces` → `micromatch` → `fast-glob`). The [GitHub advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) lists affected `braces` versions through 3.0.3 and no patched version as of this report date.
- Docker: `docker compose config` — **passed**. `docker info` could not connect because the Docker engine is not running, so image build and container startup remain unverified.
- API health: the health route and database connectivity were exercised by the backend API tests. No hosted health URL exists.
- Deployment: **not deployed**; no frontend or backend URL exists.

## Required next step

Start Ollama, pull `qwen3:1.7b`, and rerun `python -m evaluations.run`. EVAL-014 must pass with a real model response before claiming the full open-weight workflow has been validated. The exact setup and deployment values are in [DEPLOYMENT.md](DEPLOYMENT.md).
