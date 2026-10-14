# Production deployment guide

## Current status

The Railway `AgriSage AI` project and `Postgres` service are running. The FastAPI service is connected to GitHub `main`, uses the Railway PostgreSQL connection reference, and is available at `https://api-production-9585.up.railway.app`. Its public `/api/health` endpoint returned HTTP 200 with `database: connected`. After restarting the API, `/api/farms` still returned 26 seeded farm records.

The Vercel production deployment is ready at `https://frontend-lucy81-gifs-projects.vercel.app`, with `NEXT_PUBLIC_API_URL` set to the Railway API. The Railway CORS preflight accepts the Vercel origin. Vercel SSO protection currently blocks unauthenticated visitors from `.vercel.app` domains, so the frontend is not publicly accessible yet. A project-wide protection change needs explicit approval; a user-owned custom domain is the other path.

The production advisory, workflow trace, and evaluation lists are empty. The Railway service still needs a hosted open-weight model endpoint and secret before it can run analysis. The local frontend build and backend test suite passed on 2026-10-14.

## 1. Create Railway PostgreSQL and deploy the API

1. Create a Railway project and add a PostgreSQL service named `Postgres`.
2. Add a service from the `AgriSage-AI` GitHub repository. Keep the repository root as the service root so the Python build can access `requirements.txt`, `data/`, and `mcp-server/`.
3. The current GitHub-connected service uses Railway Railpack's Python detection and listens on Railway's injected `PORT`. The repository also contains `backend/Dockerfile` for Docker-based deployments.
4. Add these variables to the backend service:

```text
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SEED_DATA=true
MODEL_PROVIDER=openai_compatible
MODEL_BASE_URL=<hosted open-weight chat-completions base URL>
MODEL_API_KEY=<store as a Railway secret>
MODEL_NAME=<model available from that endpoint>
MODEL_TIMEOUT_SECONDS=180
EXTERNAL_EVIDENCE_URL=https://www.fao.org/policy-support/policy-themes/climate-smart-agriculture/Understanding-climate-smart-agriculture-/en
CORS_ORIGINS=<set to the Vercel production origin in step 3>
```

Use a real hosted open-weight model endpoint that supports the OpenAI chat-completions API. Do not use `http://localhost:11434` from Railway: it refers to the Railway container itself, not the development computer. Keep `MODEL_API_KEY` in Railway's secret variables and never put credentials in Git or the README.

On its first start, the API creates the SQLAlchemy tables and seeds the synthetic records if the farm table is empty. The database service reference keeps application records in Railway PostgreSQL across API restarts. The `/api/health` readiness endpoint returns HTTP 2xx with `status: ok` and `database: connected` when the database is reachable.

The API is deployed at `https://api-production-9585.up.railway.app`. Check:

```text
GET https://<railway-api-domain>/api/health
GET https://<railway-api-domain>/api/dashboard
GET https://<railway-api-domain>/api/farms
```

The deployment environment and actual production verification are recorded above. The health endpoint is `/api/health`.

## 2. Deploy the frontend on Vercel

1. Import the same GitHub repository as a Vercel project.
2. Set **Root Directory** to `frontend` and use the Next.js preset.
3. Set this environment variable for Production before the build:

```text
NEXT_PUBLIC_API_URL=https://<railway-api-domain>
```

4. The current production deployment is `https://frontend-lucy81-gifs-projects.vercel.app`. Check Vercel deployment protection and ensure the chosen production origin is publicly reachable before submitting it.

`NEXT_PUBLIC_API_URL` is included in the frontend build, so changing it requires a new Vercel deployment.

## 3. Connect Vercel to Railway

Set the Railway backend variable `CORS_ORIGINS` to the exact Vercel production origin, without a trailing slash. Redeploy the backend after changing it. If preview deployments need API access, add their exact origins deliberately; do not use a wildcard for the production API.

Once Vercel public access is resolved, open the site and verify the dashboard and farms load from the Railway API. The Settings page shows the configured API base URL. The current Railway CORS configuration includes the production Vercel deployment aliases and has passed an OPTIONS preflight check.

## 4. Verify PostgreSQL persistence and the public workflow

1. Confirm `/api/health` reports a connected database and `/api/dashboard` returns counts from the database. This has been verified; seeded farm records also remained after a service restart.
2. From the public Vercel workspace, run one full climate-smart analysis with the real configured hosted model. Record the workflow run ID.
3. Open Agent Trace and verify the run is `COMPLETE`, its tool calls are stored, and the trace includes `get_plot_context`, `get_climate_signals`, `get_pest_signals`, and `draft_advisory`. The optional Fetch call may fail independently and should show its recorded status.
4. Open the generated advisory and verify it is `PENDING_APPROVAL` before the officer acts.
5. Approve the advisory using the authorized officer's exact name. Verify the approval record and timestamp are visible.
6. Restart the Railway API service from its deployment controls. Refresh the Vercel page and fetch the same trace, advisory, and approval again. Confirm their IDs and statuses are unchanged. This verifies the records survived a backend restart in Railway PostgreSQL.

The app's relevant read endpoints are `GET /api/traces/{run_id}` and `GET /api/advisories/{advisory_id}`. Approval uses `POST /api/advisories/{advisory_id}/approve` with the officer name in the request body.

## 5. README, recording, and submission

After the public checks pass, update the README deployment section with the actual Railway API and Vercel URLs. Do not publish placeholders as production URLs. Use `DEMO_SCRIPT.md` to record an unedited run from the public workspace, including its trace and human approval. Add the resulting recording URL to the README and demo script, then complete the competition form and update `SUBMISSION_CHECKLIST.md` with the actual repository, deployments, analysis, approval, and recording evidence.

## Items that require account setup

- Railway project access and PostgreSQL service.
- A hosted open-weight provider's base URL, model name, and API key. Set the key only in Railway's secret settings.
- Vercel project access and Git repository integration.
- The authorized extension officer's exact name for the approval audit record.
- The competition submission URL and any required form fields.
