---
artifact: BRIEF_R11F-A-S5_v1_0.md
session_id: R11F-A-S5
version: 1.0
phase: A
parallel_safety: false
depends_on: [R11F-A-S4]
estimated_loc_delta: 0  (screenshots only — no code changes)
---

# R11F-A-S5 — Anthropic Visual Smoke via Chrome MCP

## Scope

Visual verification that the Anthropic agentic loop produces visible tool-flow timeline
rows in the UI. Uses the Chrome DevTools MCP to navigate to `/consume` on a deployed or
local preview instance, send a query that forces a dasha tool call, and screenshot the
result. Screenshots are saved to the evidence directory.

**No code changes in this session.** Outcome: PASS or FAIL with evidence.

## Preconditions

1. A-S4 committed. Full vitest passing.
2. A preview deployment is accessible (Cloud Run staging, Vercel preview, or `npm run dev`
   locally). Record the URL at session open.
3. Chrome DevTools MCP is available and connected (run `chrome-devtools` troubleshooting
   skill if not).
4. A valid session cookie for the Marsys app is available (Supabase auth session). Set
   `SMOKE_SESSION_COOKIE` env-var or paste into browser manually.
5. `MARSYS_FLAG_R11E_ANTHROPIC_LOOP=true` is set in the target environment. If testing
   locally, set it in `.env.local`.
6. `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is set (already in Cloud Run from R11.G).

## Smoke Procedure

### Step 1 — Navigate to /consume

```
Tool: navigate_page
URL: <preview-url>/consume
```

Wait for the composer to appear.

### Step 2 — Send the dasha query

Type and submit:
```
When does my next Saturn mahadasha start? Give me the exact date and the sub-dasha sequence.
```

This query forces the planner to authorise `query_dasha_periods` and the loop to call it.

### Step 3 — Wait for streaming to complete

Wait for the loading indicator to disappear (up to 60 seconds). Take a screenshot.

### Step 4 — Verify tool-flow timeline

Scroll to find the "Tool Activity" or "Steps" panel (R9-S4 tool-flow timeline). It should
show at least one row for `query_dasha_periods` or a dasha-related tool.

Take a screenshot capturing the tool-flow timeline rows.

### Step 5 — Save evidence

Save all screenshots to:
```
00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/anthropic/
  smoke_01_response.png
  smoke_02_tool_flow.png
```

### Step 6 — Assert

PASS if:
- Response contains a specific future date (not a hedged "it depends")
- Tool-flow timeline shows at least 1 tool call row
- No error message or 422 in the UI

FAIL if:
- Tool-flow timeline is empty (loop not entered)
- Response is a generic "I cannot determine" (tools not called)
- UI shows an error

## Acceptance Tests

```bash
# AC.g: screenshots exist
ls 00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/anthropic/
# expected: smoke_01_response.png + smoke_02_tool_flow.png (or similar)
```

Report: PASS / FAIL with reason. Attach screenshot path.

## Deliverable Artifacts

- `visual_evidence/anthropic/smoke_01_response.png`
- `visual_evidence/anthropic/smoke_02_tool_flow.png`
- Commit: `test(r11f-a-s5): anthropic visual smoke — tool-flow timeline evidence`

## Rollback Steps

N/A — no production code changes. If FAIL: open a HALT document and stop.
The HALT document goes to `00_ARCHITECTURE/CONDUCTOR/r11f/HALT_R11F-A-S5.md` with
the screenshot and failure description. Do NOT proceed to Phase B.
