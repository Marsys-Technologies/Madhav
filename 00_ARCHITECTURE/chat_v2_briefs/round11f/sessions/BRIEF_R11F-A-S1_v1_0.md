---
artifact: BRIEF_R11F-A-S1_v1_0.md
session_id: R11F-A-S1
version: 1.0
phase: A
parallel_safety: false
depends_on: [precursor-arc-merged-to-main]
estimated_loc_delta: +60
---

# R11F-A-S1 — Anthropic Adapter: Forward Tools + ToolChoice to streamText

## Scope

Fix Break B2: `anthropic/adapter.ts chat()` builds `streamParams` without `tools` or
`toolChoice`. The model never receives tool definitions, so it cannot call tools even though
the adapter correctly parses tool stream parts. This session patches `chat()` to translate
`request.tools` into the Vercel AI SDK tool map and `request.toolsConfig.toolChoice` into
AI SDK's `toolChoice` parameter. It also promotes the parked PROBE test out of
`describe.skip` and adds three new spy assertions.

## Files May Touch

```
platform/src/lib/providers/anthropic/adapter.ts
platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts
platform/tests/providers/anthropic/anthropic-tool-events.test.ts
```

## Files Must NOT Touch

```
# L1/L2.5 corpus — absolute
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
# Route.ts — covered in A-S2
platform/src/app/api/chat/consume/route.ts
# Other provider adapters — covered in Phase B
platform/src/lib/providers/google/**
platform/src/lib/providers/openai/**
platform/src/lib/providers/deepseek/**
platform/src/lib/providers/nvidia/**
# Governance artifacts
00_ARCHITECTURE/**/*.md (except session artifacts in this arc's own folder)
CLAUDE.md
deploy.yml
```

## Preconditions

1. `feature/r11f-wiring-arc` is merged to main (check: `git log main --oneline | grep r11f-s4`).
2. Working directory is `/Users/Dev/Vibe-Coding/Apps/MadhavR11FBound` on branch
   `chat-v2/r11f-agentic-loop`.
3. Baseline vitest passes: `cd platform && npx vitest run --no-coverage 2>&1 | tail -5`.

## Implementation

### Step 1 — Read the current `chat()` signature

Open `platform/src/lib/providers/anthropic/adapter.ts` and locate the `streamParams`
construction (currently around line 90). Confirm `tools` and `toolChoice` are absent.

### Step 2 — Translate `request.tools` into Vercel AI SDK format

The Vercel AI SDK `streamText` accepts a `tools` parameter shaped as:
```typescript
Record<string, CoreTool>
```
where each `CoreTool` is `{ description?: string; parameters: ZodSchema }`.

However, our `ChatRequest.tools` is already an array of tool definitions with `inputSchema`
(JSON Schema). Use the Vercel AI SDK's `jsonSchema()` helper to bridge:

```typescript
import { jsonSchema } from 'ai'

// Inside streamParams construction, after the existing providerOptions block:
if (request.tools && request.tools.length > 0) {
  const toolsMap: Record<string, import('ai').CoreTool> = {}
  for (const tool of request.tools) {
    toolsMap[tool.name] = {
      description: tool.description,
      parameters: jsonSchema(tool.inputSchema ?? { type: 'object', properties: {} }),
    }
  }
  streamParams.tools = toolsMap
}

if (request.toolsConfig?.toolChoice) {
  streamParams.toolChoice = request.toolsConfig.toolChoice  // 'auto' | 'required' | 'none'
}
```

### Step 3 — Promote PROBE test

File: `platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts`

Change `describe.skip(` → `describe(` on the outer describe block.

Add three new test cases inside the promoted describe block:

**Test A**: "tools array reaches streamText when request.tools is populated"
- Create a mock `ChatRequest` with `tools: [{ name: 'query_ephemeris', description: 'test', inputSchema: {...} }]`
- Spy on `streamText` (vi.spyOn from 'ai')
- Run `adapter.chat(mockRequest)` and drain the async iterator
- Assert `spy.mock.calls[0][0].tools` is defined and has key `'query_ephemeris'`

**Test B**: "toolChoice is forwarded"
- Same setup but add `toolsConfig: { toolChoice: 'auto', tools: [] }` to request
- Assert `spy.mock.calls[0][0].toolChoice === 'auto'`

**Test C**: "no tools key when request.tools is empty"
- Request with no `tools` field
- Assert `spy.mock.calls[0][0].tools === undefined`

### Step 4 — Update existing tool-events test

In `anthropic-tool-events.test.ts`, add a test asserting that the full tool_use round-trip
produces the correct ChatEvent sequence: `tool_use_start` → `tool_use_input_delta` →
`tool_use_complete`. (This test was added in S2 but may not cover the forwarding path.)

## Acceptance Tests

```bash
# AC.a: PROBE test no longer skipped
grep -c "describe.skip" platform/tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts
# expected: 0

# AC.b: spy assertions pass
cd platform && npx vitest run tests/providers/anthropic/PROBE_anthropic_tools_forwarding.test.ts --no-coverage 2>&1 | tail -10
# expected: no failures

# AC.c: full provider test suite passes
cd platform && npx vitest run tests/providers/anthropic/ --no-coverage 2>&1 | tail -10
# expected: no failures

# AC.d: tools forwarding verified in streamParams
grep -n "streamParams.tools" platform/src/lib/providers/anthropic/adapter.ts
# expected: at least 1 match
```

## Deliverable Artifacts

- Patched `platform/src/lib/providers/anthropic/adapter.ts` (tools + toolChoice forwarding)
- Promoted `PROBE_anthropic_tools_forwarding.test.ts` (no more describe.skip)
- Updated `anthropic-tool-events.test.ts` (round-trip coverage)
- Commit message: `fix(r11f-a-s1): anthropic adapter forwards tools+toolChoice to streamText`

## Rollback Steps

```bash
git revert HEAD  # single commit; reverts adapter and test changes
```

The system returns to the pre-S1 state where the adapter emits tool events but the model
cannot call tools (the existing behaviour — no regression).
