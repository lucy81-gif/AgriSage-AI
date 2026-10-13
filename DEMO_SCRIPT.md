# AgriSage AI demo script (under three minutes)

Record one unedited application run with the Agent Trace visible. Use a real configured open-weight model. Do not record or imply a successful run if the model is unavailable.

| Time | Screen and action | Spoken line |
|---|---|---|
| 0:00–0:20 | Show the extension workspace overview. | “An extension officer may need to support many farms while climate, pest, and crop records are scattered. AgriSage brings those signals together for review.” |
| 0:20–0:35 | Show the database-derived counts and the synthetic-data notice. | “These are synthetic Lesotho demonstration records. Every risk and signal should be checked in the field before operational use.” |
| 0:35–1:20 | Open Run Climate-Smart Analysis, select one district/crop and the demonstration period, then run it. Keep the Agent Trace or live trace page visible. | “The workflow plans its investigation, calls the AgriSage MCP tools, attempts the configured Fetch reference, checks evidence quality, and calculates risk in deterministic code.” |
| 1:20–1:50 | Open the highest-priority farm returned by this actual run. Expand its evidence chain. | “This farm is ranked using these dated plot, climate, and pest records. Missing or stale information remains visible.” |
| 1:50–2:15 | Open the advisory record returned by the run. Show `PENDING_APPROVAL` and its evidence. | “The agent creates a draft only. It cannot contact a farmer or approve its own recommendation.” |
| 2:15–2:30 | Enter the officer's name and approve or edit the draft. Show the persisted status. | “A named extension officer makes and records the decision.” |
| 2:30–2:50 | Run the insufficient-evidence example for F017 or open the result from a separately recorded safe-failure run. | “When climate evidence is unavailable, AgriSage records the gap and requests follow-up instead of guessing.” |
| 2:50–3:00 | Return to the overview or close on the AgriSage title. | “AgriSage AI. Evidence Before Advice.” |

Before recording, verify `GET /api/health`, confirm the configured open-weight model responds, and confirm the Fetch MCP server is installed. If any dependency fails, show the actual failure state and describe it honestly. Do not replace it with a mocked screen or a test-fixture evaluation run.

**Public video URL:** not recorded yet.
