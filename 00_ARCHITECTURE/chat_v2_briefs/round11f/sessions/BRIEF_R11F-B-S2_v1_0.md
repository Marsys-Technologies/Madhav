---
artifact: BRIEF_R11F-B-S2_v1_0.md
session_id: R11F-B-S2
version: 1.0
phase: B
parallel_safety: false
depends_on: [R11F-B-S1]
estimated_loc_delta: 0  (screenshots only)
---

# R11F-B-S2 — Google Visual Smoke via Chrome MCP

## Scope

Same procedure as A-S5 but with the Google Gemini adapter selected via the SettingsDropdown.
Verifies that the tool-flow timeline appears for a Gemini-streamed response.

## Preconditions

1. B-S1 committed. Full vitest passing.
2. `MARSYS_FLAG_R11E_GEMINI_LOOP=true` and `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` set in
   the target environment.
3. Chrome MCP connected. Session cookie available.

## Smoke Procedure

### Step 1 — Navigate and select Google stack

Navigate to `<preview-url>/consume`. Open the SettingsDropdown (gear icon). Select the
Google Gemini provider option if visible. If the dropdown does not surface a per-provider
selector, confirm via URL param or env-var override.

### Step 2 — Send the dasha query

Same query as A-S5:
```
When does my next Saturn mahadasha start? Give me the exact date and the sub-dasha sequence.
```

### Step 3 — Screenshot

Take screenshots:
- Full response with text
- Tool-flow timeline panel

### Step 4 — Save evidence

```
00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/google/
  smoke_01_response.png
  smoke_02_tool_flow.png
```

## PASS criteria

- Response contains a specific date
- Tool-flow timeline shows at least 1 tool call row
- No error in UI

## FAIL → HALT

Write `HALT_R11F-B-S2.md` with screenshot. Stop. Do NOT proceed to B-S3/B-S4.
(B-S3 is parallel-eligible from A-S2, not from B-S2, so it may already be in progress —
coordinate with conductor.)

## Deliverable Artifacts

- `visual_evidence/google/smoke_01_response.png`
- `visual_evidence/google/smoke_02_tool_flow.png`
- Commit: `test(r11f-b-s2): google visual smoke — tool-flow timeline evidence`
