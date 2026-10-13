# AgriSage AI frontend

Next.js App Router frontend for the AgriSage AI extension office workspace. The UI is built around the principle **Evidence Before Advice** and keeps farm records, risk decisions, tool traces, and human approval in one auditable surface.

## Run

```powershell
Copy-Item .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>.

Set `NEXT_PUBLIC_API_URL` to the FastAPI backend URL. The dashboard reads all
farm, analysis, advisory, trace, and evaluation state from that API. When a
backend response is unavailable, the interface shows an explicit unavailable
state instead of inventing data.

## Routes

- `/` overview dashboard
- `/farms` farm register
- `/farms/:farmId` farm context, climate, pest signals, and evidence chain
- `/priority-queue` urgency groups and ranking explanation
- `/advisories` advisory register
- `/advisories/:advisoryId` human approval, edit, or reject gate
- `/trace` agent run history
- `/trace/:traceId` tool and state trace
- `/evaluations` evaluation results
- `/settings` connection and safety boundaries

## Expected API contracts

The service layer in `src/services` expects:

- `GET /api/v1/bootstrap-summary`
- `GET /api/farms`
- `GET /api/farms/:id`
- `GET /api/farms/:id/evidence`
- `POST /api/analysis/run`
- `GET /api/analysis/:runId`
- `GET /api/priority-queue`
- `GET /api/advisories`
- `GET /api/advisories/:id`
- `POST /api/advisories/:id/approve`
- `POST /api/advisories/:id/edit`
- `POST /api/advisories/:id/reject`
- `GET /api/traces`
- `GET /api/traces/:id`
- `GET /api/evaluations`
- `GET /api/follow-ups`

No permanent mock statistics or farm records are bundled into the frontend. If an endpoint is unavailable, the interface explains what is missing and does not fabricate a result.
