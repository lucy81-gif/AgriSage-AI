# Deployment guide

No hosted deployment or production URL has been created. Hosting account access and an available hosted open-weight model endpoint are required before a real production analysis can complete.

## 1. Prepare the PostgreSQL database

Create the production PostgreSQL database in Railway and set its connection reference as `DATABASE_URL` on the AgriSage backend service. The API and its MCP subprocesses use that same SQLAlchemy database for farm seeds, workflow traces, tool logs, risk assessments, advisories, approvals, follow-ups, and evaluation runs/results. The application accepts Railway's `postgres://` or `postgresql://` URL form and uses the Psycopg 3 driver.

Keep `SEED_DATA=true` for the first startup. The backend creates tables and loads the synthetic demonstration records only when there are no farm rows. It does not wipe existing data or approvals on later starts.

## 2. Deploy the backend on Render

1. Push this repository to a GitHub repository.
2. In Render, create a **Web Service** from that repository and select the Docker runtime.
3. Keep the repository root as the build context and set the Dockerfile path to `backend/Dockerfile`.
4. Set these service environment variables:

```text
ENVIRONMENT=production
DATABASE_URL=<managed PostgreSQL connection URL>
SEED_DATA=true
MODEL_PROVIDER=openai_compatible
MODEL_BASE_URL=<hosted open-weight model API base URL>
MODEL_API_KEY=<hosted endpoint key>
MODEL_NAME=<available open-weight model name>
MODEL_TIMEOUT_SECONDS=180
EXTERNAL_EVIDENCE_URL=https://www.fao.org/policy-support/policy-themes/climate-smart-agriculture/Understanding-climate-smart-agriculture-/en
CORS_ORIGINS=https://<your-vercel-project>.vercel.app
```

`MODEL_BASE_URL`, `MODEL_API_KEY`, and `MODEL_NAME` must come from a real hosted open-weight model provider. Do not enter a proprietary model endpoint or fabricate credentials. The local Ollama URL is not reachable from a hosted backend unless that Ollama service is intentionally exposed through a secure network.

5. Set the health check path to `/api/health` and deploy.
6. Verify `https://<your-render-service>/api/health` returns `{"status":"ok","database":"connected"}` and `GET /api/farms` returns the seeded synthetic records.

## 3. Deploy the backend on Railway instead

1. Create a Railway project from the GitHub repository and add a PostgreSQL service.
2. Configure the application service to build with `backend/Dockerfile` using the repository root as its context.
3. Add the same backend variables listed above. Set `DATABASE_URL` to Railway's PostgreSQL reference/value; set the model URL, key, and name only after choosing a hosted open-weight endpoint.
4. Set the health check to `/api/health`, expose port `8000`, deploy, then verify `/api/health` and `/api/farms`.

## 4. Deploy the frontend on Vercel

1. Import the GitHub repository into Vercel.
2. Set **Root Directory** to `frontend` and use the Next.js framework preset.
3. Add this environment variable before building:

```text
NEXT_PUBLIC_API_URL=https://<your-render-or-railway-service>
```

4. Deploy and open the generated Vercel URL.
5. Update the backend `CORS_ORIGINS` to the exact deployed Vercel origin, without a trailing slash, then redeploy the backend.

## 5. Post-deployment checks

1. `GET https://<backend>/api/health` returns status `ok` and database `connected`.
2. `GET https://<backend>/api/dashboard` and `/api/farms` return database-derived values.
3. Load the Vercel frontend and run one real analysis using the configured open-weight model.
4. Confirm the trace lists AgriSage MCP calls and the Fetch MCP call, if the reference URL is configured.
5. Confirm a draft stays `PENDING_APPROVAL`; approve, edit, and reject actions persist the named officer and timestamp.
6. Refresh the pages and verify the API returns the persisted values.

## Values still needed

- A PostgreSQL `DATABASE_URL` from the selected hosting provider.
- A hosted open-weight endpoint's `MODEL_BASE_URL`, `MODEL_API_KEY`, and `MODEL_NAME`, unless Ollama is securely hosted and reachable from the backend.
- The final Vercel origin for `CORS_ORIGINS`.
- The deployed frontend and backend URLs for the README and competition submission.
