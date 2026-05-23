---
artifact: BRIEF_R11F-B-S3_v1_0.md
session_id: R11F-B-S3
version: 1.0
phase: B
parallel_safety: true  (can run concurrent with B-S1 on separate sub-branches)
depends_on: [R11F-A-S2]
estimated_loc_delta: +75
---

# R11F-B-S3 — OpenAI Adapter: Forward Tools in OpenAI Format + Integration Test

## Scope

Fix Break B2-O: `openai/adapter.ts chat()` does not forward `tools` to the OpenAI API.
OpenAI's tool format uses `tools: [{ type: 'function', function: { name, description, parameters } }]`.

## Files May Touch

```
platform/src/lib/providers/openai/adapter.ts
platform/tests/providers/openai-tool-events.test.ts
platform/tests/providers/openai/e2e-loop-roundtrip.test.ts  (new)
platform/tests/providers/openai/fixtures/tool_use_stream.ts  (new)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/anthropic/**
platform/src/lib/providers/google/**
platform/src/lib/providers/deepseek/**
platform/src/lib/providers/nvidia/**
platform/src/app/api/chat/consume/route.ts
CLAUDE.md
deploy.yml
```

## Implementation

### Step 1 — Inspect openai/adapter.ts

Read the `chat()` method. Verify current `streamParams`. Check whether `openai-tool-events.test.ts`
(added in F-S2 of precursor arc) uses a mock that already shapes tool events — if so, the
tool-part parsing is present, but the forwarding to `streamText` is likely still missing.

### Step 2 — Forward tools

```typescript
import { jsonSchema } from 'ai'

if (request.tools && request.tools.length > 0) {
  streamParams.tools = request.tools.map(tool => ({
    type: 'function' as const,
    function: {
      name: tool.name,
      description: tool.description ?? '',
      parameters: jsonSchema(tool.inputSchema ?? { type: 'object', properties: {} }),
    },
  }))
}

if (request.toolsConfig?.toolChoice) {
  streamParams.toolChoice = request.toolsConfig.toolChoice
}
```

The Vercel AI SDK's `streamText` with `@ai-sdk/openai` accepts this format.

### Step 3 — Verify tool_calls multi-turn message format

For the loop second iteration, the messages must include the assistant message with
`tool_calls` and a `tool` message with `tool_call_id`. Verify that `agentic_loop.ts`
constructs this correctly for OpenAI format. Document or patch.

### Step 4 — E2E test

Mirror A-S4 structure. OpenAI stream parts use `tool-call-streaming-start`, `tool-call-delta`,
`tool-call` (same Vercel AI SDK abstraction layer — the underlying OpenAI format differs but
the SDK normalises it). Use the same fixture shape as `anthropic/fixtures/tool_use_stream.ts`.

## Acceptance Tests

```bash
# AC.a: tools forwarding in openai adapter
grep -n "streamParams.tools" platform/src/lib/providers/openai/adapter.ts
# expected: >= 1 match

# AC.b: E2E test passes
cd platform && npx vitest run tests/providers/openai/e2e-loop-roundtrip.test.ts --no-coverage 2>&1 | tail -5
# expected: 3 tests pass

# AC.c: full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- Patched `platform/src/lib/providers/openai/adapter.ts`
- `tests/providers/openai/e2e-loop-roundtrip.test.ts` (new)
- `tests/providers/openai/fixtures/tool_use_stream.ts` (new)
- Commit: `fix(r11f-b-s3): openai adapter forwards tools in OpenAI format + E2E test`

## Rollback Steps

```bash
git revert HEAD
```
