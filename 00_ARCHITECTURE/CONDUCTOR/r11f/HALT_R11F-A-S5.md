---
session: R11F-A-S5
status: HALTED
halt_reason: anthropic_tool_schema_400
committed_at: 2026-05-24
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11FBound
branch: chat-v2/r11f-agentic-loop
---

# HALT — R11F-A-S5: Anthropic Tool Schema 400 Error

## Summary

Smoke test FAILED. The Anthropic agentic loop (MARSYS_FLAG_R11E_ANTHROPIC_LOOP=true) was
triggered successfully — flag resolved, tools were built, and the request was dispatched to
the Anthropic API. However, the API returned HTTP 400 before producing any tokens.

No assistant response text appeared. Tool-flow timeline is empty (loop never entered).

## Failure Classification

**FAIL** — tool-flow timeline empty, no dasha date in response, API returned 400.

## Root Cause

Anthropic API rejected the request with:

```
tools.0.custom.input_schema.type: Field required
```

Full error body from `/tmp/marsys-r11f-dev.log`:

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "tools.0.custom.input_schema.type: Field required"
  },
  "request_id": "req_011CbLBrL832ANdRNiQUTAYp"
}
```

HTTP status: 400. `x-should-retry: false`.

## Diagnosis

The Anthropic adapter (`src/lib/providers/anthropic/adapter.ts`, line 107) uses the
Vercel AI SDK `jsonSchema()` helper to wrap tool input schemas:

```ts
parameters: jsonSchema(tool.inputSchema ?? { type: 'object', properties: {} }),
```

`tool_catalogue.ts` supplies `inputSchema: { type: 'object', properties: {} }` for all
retrieval tools. However, the `@ai-sdk/anthropic` package serializes `jsonSchema()`-wrapped
schemas into Anthropic's `custom` tool format, and the resulting wire payload is missing
the `type` field inside `input_schema`. Anthropic requires:

```json
{
  "type": "custom",
  "name": "query_dasha_periods",
  "description": "...",
  "input_schema": {
    "type": "object",
    "properties": {}
  }
}
```

But is receiving `input_schema: { "properties": {} }` — the `"type": "object"` key is
absent on the wire.

The likely cause is that the version of `@ai-sdk/anthropic` in this worktree's
`node_modules` does not forward the `type` field from a bare `jsonSchema()` wrapper when
`properties` is empty. This may be a known quirk of the SDK version in use or a schema
normalization step that strips the top-level `type` when the schema has no required fields.

## Model Used

`claude-opus-4-7` (Anthropic Stack persona).

## Loop Telemetry

```json
{
  "marsys_event_type": "tool_loop_iteration",
  "iteration": 1,
  "providerId": "anthropic",
  "inputTokens": 0,
  "outputTokens": 0,
  "cacheReadTokens": 0,
  "cacheCreationTokens": 0,
  "reasoningTokens": 0,
  "toolCallCount": 0,
  "toolErrorCount": 0,
  "terminationSignal": null,
  "completedAt": "2026-05-23T21:11:09.868Z"
}
```

Iteration 1 completed with 0 tokens — the 400 was returned before any streaming started.

## Screenshot Evidence

- `smoke_00_initial.png` — consume page loaded, Anthropic Stack selected, query typed
- `smoke_01_response.png` — response area empty after 400 error; user bubble visible but no assistant text
- `smoke_02_tool_flow.png` — tool-flow timeline empty; loop was never entered

All screenshots at:
`00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/anthropic/`

## Fix Required (next session)

In `src/lib/providers/anthropic/adapter.ts`, replace the `jsonSchema()` wrapper with a
direct `z.object({})` Zod schema for tools that have no declared input parameters, OR
ensure the `inputSchema` object always has `type: 'object'` preserved on the wire by
using the Anthropic SDK's native tool shape directly instead of going through the Vercel
AI SDK `jsonSchema()` abstraction.

Candidate fix (adapter.ts line 105-108):

```ts
toolsMap[tool.name] = {
  description: tool.description,
  parameters: jsonSchema({
    type: 'object' as const,
    properties: tool.inputSchema?.properties ?? {},
    ...(tool.inputSchema?.required ? { required: tool.inputSchema.required } : {}),
  }),
};
```

Alternatively, if `jsonSchema()` is stripping the top-level `type`, use Zod directly:

```ts
import { z } from 'zod';
// ...
parameters: z.object({}),  // for parameterless tools
```

This fix must be validated with a fresh smoke run (R11F-A-S6) after code change.

## What Was Cleared Before This Session

Commit `a36a2865` cleared the previous HALT (R11F-A-S5 planner 422 / null synthesis_guidance).
That fix (commit `3c0ec662`) is confirmed working — planner returned HTTP 200 and a valid
`tools_authorized` list. The 400 occurs at the Anthropic API call layer, downstream of
the planner fix.
---
