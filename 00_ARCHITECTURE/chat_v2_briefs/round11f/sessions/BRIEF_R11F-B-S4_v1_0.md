---
artifact: BRIEF_R11F-B-S4_v1_0.md
session_id: R11F-B-S4
version: 1.0
phase: B
parallel_safety: false
depends_on: [R11F-B-S3]
estimated_loc_delta: 0  (screenshots only)
---

# R11F-B-S4 — OpenAI Visual Smoke via Chrome MCP

## Scope

Visual smoke for the OpenAI adapter with loop enabled. Same procedure as A-S5 and B-S2.

## Preconditions

1. B-S3 committed. Full vitest passing.
2. `MARSYS_FLAG_R11E_OPENAI_LOOP=true` in target environment.
3. OpenAI API key configured in the environment (`OPENAI_API_KEY`).
4. Chrome MCP connected. Session cookie available.

## Smoke Procedure

Navigate to `/consume`. Select the OpenAI provider via SettingsDropdown (if available) or
via env-var override. Send the dasha query. Screenshot response + tool-flow timeline.

Save evidence:
```
00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/openai/
  smoke_01_response.png
  smoke_02_tool_flow.png
```

## PASS criteria

- Response contains a specific date
- Tool-flow timeline shows ≥1 tool call row
- No error in UI

## FAIL → HALT: write `HALT_R11F-B-S4.md`

## Deliverable Artifacts

- `visual_evidence/openai/smoke_01_response.png`
- `visual_evidence/openai/smoke_02_tool_flow.png`
- Commit: `test(r11f-b-s4): openai visual smoke — tool-flow timeline evidence`
