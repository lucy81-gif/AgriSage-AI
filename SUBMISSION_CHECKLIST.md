# Competition submission checklist

Updated from repository state and the evaluation execution on 2026-10-13.

## Product and evidence

- [ ] Public GitHub repository created and verified
- [x] MIT / OSI-approved licence
- [x] README covers problem, solution, users, theme, setup, usage, stack, architecture, agent, MCP, human review, sources, limitations, future work, deployment, demo, and compliance
- [x] Architecture documentation and diagram (`ARCHITECTURE.md`, `docs/architecture.png`)
- [x] AgriSage MCP protocol verified; plot, climate, pest, draft, and follow-up tools exercised
- [x] Draft action remains `PENDING_APPROVAL`
- [x] Official Fetch MCP server invoked successfully and its failure path recorded
- [ ] Successful full workflow with the configured open-weight model; local Ollama endpoint is unavailable
- [x] Named approval, edit, and rejection persisted with audit records
- [x] Tool logs contain server, input, output/error, status, timestamps, and duration
- [x] Evidence provenance and synthetic data limitations documented
- [x] `EVALS.md` records 14 executed cases: 13 pass, 1 honest failure
- [x] Three repeated fixture runs recorded; risk stayed MODERATE
- [x] Actual run IDs, tool sequences, and latency results recorded

## Build, deployment, and demo

- [x] Backend tests: 13 passed
- [x] Frontend production build passed on 2026-10-13
- [x] Python dependency consistency check passed
- [x] `docker compose config` parsed successfully
- [ ] Docker image build and container startup; Docker daemon is not available on this machine
- [ ] Frontend deployed
- [ ] Backend deployed
- [x] `DEMO_SCRIPT.md` created
- [ ] Demo recording completed and published
- [ ] Final competition submission form completed

## Dependency audit

- [x] Production npm dependencies: `npm audit --omit=dev` found no vulnerabilities
- [ ] Full npm audit clean; it reports five high findings through the ESLint development dependency chain (`braces`), with no patched version currently listed by the upstream advisory
