# Competition submission checklist

Updated 2026-10-14 after evaluation run `EVALRUN-DEAEA454B3` and the local production-build check.

## Product and evidence

- [x] Configured GitHub origin `lucy81-gif/AgriSage-AI` and authenticated read access verified; repository visibility is not confirmed
- [x] MIT / OSI-approved licence
- [x] README covers problem, solution, users, theme, setup, usage, stack, architecture, agent, MCP, human review, sources, limitations, future work, deployment, demo, and compliance
- [x] Architecture documentation and diagram (`ARCHITECTURE.md`, `docs/architecture.png`)
- [x] AgriSage MCP protocol and plot, climate, pest, draft, and follow-up tools exercised
- [x] Draft action remains `PENDING_APPROVAL`
- [x] Official Fetch MCP success and failure paths recorded
- [x] Full workflow with the configured local open-weight model completed: `ollama/qwen3:1.7b` (EVAL-014); production still needs a hosted endpoint
- [x] Named approval, edit, and rejection persisted in the evaluation database
- [x] Tool logs contain server, input, output/error, status, timestamps, and duration
- [x] Evidence provenance and synthetic-data limitations documented
- [x] `EVALS.md` records 14 executed cases: 14 pass, 0 fail
- [x] Three repeated fixture runs recorded; risk stayed MODERATE
- [x] Actual evaluation and workflow run IDs, tool sequences, and timings recorded

## Build, deployment, and demo

- [x] Backend test suite passed locally
- [x] Frontend production build passed on 2026-10-14
- [x] Railway deployment config added (`railway.toml`); API container binds the injected `PORT`
- [x] Railway project and PostgreSQL service created; persistence across an API restart remains to verify
- [ ] FastAPI backend deployed and public health endpoint verified
- [ ] Vercel frontend deployed and connected to the Railway API
- [ ] Full public analysis run completed with the hosted open-weight model
- [ ] Public MCP trace and tool logs verified
- [ ] Advisory approved by the authorized named officer and persisted after refresh/restart
- [ ] README updated with actual production URLs
- [x] `DEMO_SCRIPT.md` created
- [ ] Demo recording completed
- [ ] Git changes committed and pushed (GitHub authentication is still required)
- [ ] Competition submission form completed

## Previously recorded checks

- `python -m pip check` passed.
- `docker compose config` parsed successfully; container build/start remains unverified because the Docker engine was unavailable at the last check.
- The 2026-10-13 npm audit recorded no production dependency vulnerabilities and five high findings in the development dependency chain. Rerun the audit before final submission if dependency versions change.