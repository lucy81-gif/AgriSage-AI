# Evaluation results

## Latest execution

- **Evaluation run:** `EVALRUN-DEAEA454B3`
- **Date:** 2026-10-14
- **Command:** `python -m evaluations.run` (executed with the project `.venv` interpreter)
- **Result:** 14 cases executed; 14 passed and 0 failed. The command exited with code 0.
- **Database:** The runner wrote the evaluation run, 14 case results, workflow runs, MCP tool logs, advisories, approvals, risk assessments, and repeat runs to `runtime/agrisage-eval-20261014.db`. This isolated SQLite copy protected the main local database during evaluation.

EVAL-001 through EVAL-013 primarily use the deterministic `EvaluationOnlyModelProvider` for workflow and risk behaviour checks. EVAL-010 and EVAL-011 directly exercise MCP failure logging. These cases do not measure language-model quality. EVAL-014 uses the configured open-weight runtime model without substitution. The verified runtime configuration was **provider `ollama`**, **model `qwen3:1.7b`**.

## Case results

| ID | Scenario | Observed result | Status |
|---|---|---|---|
| EVAL-001 | Normal maize workflow with public reference | Moderate risk; plot, climate, pest, Fetch, and advisory tools ran; a draft was produced. | PASS |
| EVAL-002 | Drought scenario | Negative rainfall evidence appeared in the risk assessment. | PASS |
| EVAL-003 | Heavy-rain scenario | Heavy-rain evidence appeared in the risk assessment. | PASS |
| EVAL-004 | High pest-risk signal | High risk; the Fall Armyworm factor appeared in the risk assessment. | PASS |
| EVAL-005 | Vulnerable crop stage | The recorded vulnerable crop stage appeared in the risk factors. | PASS |
| EVAL-006 | Missing planting date | Missing planting-date evidence and a follow-up were recorded; no draft was produced. | PASS |
| EVAL-007 | Unavailable climate source | Insufficient evidence and missing climate data were recorded with a follow-up. | PASS |
| EVAL-008 | Conflicting crop-stage records | The conflict was surfaced and a follow-up was created before a cautious draft. | PASS |
| EVAL-009 | Multi-farm prioritisation | All matching farms were assessed and represented in the priority queue. | PASS |
| EVAL-010 | AgriSage MCP tool failure | A forced missing-farm call was persisted as a failure with its input. | PASS |
| EVAL-011 | Official Fetch MCP failure | A forced `.invalid` URL was persisted as a failure; no fetched content was accepted. | PASS |
| EVAL-012 | Named human approval | The named officer approval and timestamp were persisted. | PASS |
| EVAL-013 | Human edit and rejection | The original wording, edit, officer, and rejection reason were persisted. | PASS |
| EVAL-014 | Configured open-weight model run | `ollama/qwen3:1.7b` completed the workflow; its provider and model metadata matched the completed `WorkflowRun`; four required tools succeeded; one advisory was persisted. | PASS |

The EVAL-014 workflow run was `RUN-A7CFC8354877`. It completed with stored provider/model `ollama/qwen3:1.7b`, four successful MCP calls (`get_plot_context`, `get_climate_signals`, `get_pest_signals`, `draft_advisory`), advisory `ADV-C8354877-F012` at `PENDING_APPROVAL`, and zero follow-ups. The deterministic risk assessment was `MODERATE` with confidence `0.74`. Ollama reported 718 input tokens and 1,094 output tokens; the workflow duration was 63,963 ms.

The successful EVAL-001 Fetch call used the official `mcp-server-fetch` process. Node.js and npm were unavailable, so Fetch used its Python article-extraction fallback.

## Repeatability and trace metrics

Three additional F012 fixture runs produced the same `MODERATE` risk and the same four-tool sequence: `get_plot_context`, `get_climate_signals`, `get_pest_signals`, `draft_advisory`.

| Repeat | Risk | Recorded duration |
|---|---|---:|
| 1 | MODERATE | 1,243 ms |
| 2 | MODERATE | 1,258 ms |
| 3 | MODERATE | 1,256 ms |

Mean recorded duration was 1,252 ms (range 1,243-1,258 ms). The 14 case runs recorded 61 MCP calls; the three repeat runs recorded 12 more, for 73 calls total. Repeat timings use the deterministic fixture provider and are not real-model latency measurements.

## Warnings and remaining limitations

- The run emitted a LangGraph serializer pending-deprecation warning about the future default for `allowed_objects`.
- Python 3.14 emitted deprecation warnings for `datetime.utcnow()` calls in the evaluation runner. These warnings did not affect the completed run.
- Fetch used its Python extraction fallback because Node.js and npm were unavailable.
- This evaluation used an isolated local SQLite copy. It verifies local persistence but does not verify Railway PostgreSQL connectivity or a hosted deployment.
- A prior Docker check recorded that the Docker engine was not running, so container build and startup remain unverified.
- EVAL-014 confirms the configured model completes this workflow; it does not constitute a broad evaluation of generated advisory quality. Drafts remain pending named human approval.