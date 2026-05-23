---
artifact: BRIEF_R11F-B-S1_v1_0.md
session_id: R11F-B-S1
version: 1.0
phase: B
parallel_safety: true  (can run concurrent with B-S3 on separate sub-branches)
depends_on: [R11F-A-S2]
estimated_loc_delta: +80
---

# R11F-B-S1 — Google Adapter: Forward Tools in Gemini Format + Integration Test

## Scope

Fix Break B2-G: `google/adapter.ts chat()` does not forward `tools` to the Gemini API.
Gemini's tool format differs from Anthropic — it uses `tools: [{ functionDeclarations: [...] }]`
rather than a flat tools map. Additionally, Google's adapter may need to translate
`tool_result` turns into `functionResponse` message parts for the multi-turn loop.

This session also confirms whether `adapter.cache()` D.3 (Gemini cachedContent) was
wired correctly in the precursor arc (F-S4) and documents any remaining gaps.

## Files May Touch

```
platform/src/lib/providers/google/adapter.ts
platform/tests/providers/google-tool-events.test.ts
platform/tests/providers/google/e2e-loop-roundtrip.test.ts  (new)
platform/tests/providers/google/fixtures/tool_use_stream.ts  (new)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/anthropic/**
platform/src/lib/providers/openai/**
platform/src/lib/providers/deepseek/**
platform/src/lib/providers/nvidia/**
platform/src/app/api/chat/consume/route.ts
CLAUDE.md
deploy.yml
```

## Preconditions

1. A-S2 committed. `chat-v2/r11f-agentic-loop` branch clean.
2. Read `google/adapter.ts` chat() method fully before patching.
3. If running parallel with B-S3 (OpenAI), use `isolation: worktree` per Conductor.

## Implementation

### Step 1 — Inspect current google/adapter.ts

Read `platform/src/lib/providers/google/adapter.ts`. Locate:
- The `chat()` method and its `streamParams`/equivalent construction
- How `providerOptions.google.cachedContent` is (or is not) forwarded (D.3 check)
- What stream parts are currently processed for tool calls

### Step 2 — Translate ChatTool[] to Gemini FunctionDeclaration format

```typescript
import { jsonSchema } from 'ai'

// Inside google adapter chat(), after building existing stream params:
if (request.tools && request.tools.length > 0) {
  // Gemini AI SDK (via Vercel AI SDK @ai-sdk/google) accepts tools as:
  // tools: [{ type: 'function', function: { name, description, parameters } }]
  // OR the SDK may accept functionDeclarations directly — check @ai-sdk/google docs.
  // Use jsonSchema() helper for the parameters field.
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

**Important**: Verify the exact Vercel AI SDK `@ai-sdk/google` tool format by reading the
existing `google-tool-events.test.ts` (added in F-S2 of precursor arc) — it likely has
the correct shape.

### Step 3 — Verify D.3 cachedContent forwarding

Check if `request.cacheConfig?.providerPayload?.cachedContentName` is already being
forwarded to `providerOptions.google.cachedContent` (wired in precursor F-S4). If not,
add it. If yes, add a comment confirming D.3 is wired.

### Step 4 — Tool result injection for multi-turn

For the loop to work, when the executor returns a tool result, the adapter's second
`chat()` call must include the tool result as a `functionResponse` message. Verify that
`agentic_loop.ts` correctly formats the tool result into the messages array for Google's
format. Document the message shape in a comment if correct; patch if not.

Gemini's tool result format via Vercel AI SDK:
```typescript
{ role: 'tool', content: [{ type: 'tool-result', toolCallId: '...', result: '...' }] }
```
(Verify — may be `functionResponse` wrapped differently in Google's SDK.)

### Step 5 — Write E2E test

Mirror the Anthropic E2E test structure from A-S4 for Google:
- `tests/providers/google/fixtures/tool_use_stream.ts` — fixture emitting Gemini-format tool parts
- `tests/providers/google/e2e-loop-roundtrip.test.ts` — 3 test cases (round-trip, cap, floor context)

Mock `@ai-sdk/google` equivalent of `streamText`. The Vercel AI SDK wraps Google, so
the spy target may be the same `streamText` from `'ai'` with a different model provider.

## Acceptance Tests

```bash
# AC.a: tools forwarding in google adapter
grep -n "streamParams.tools\|functionDeclarations" platform/src/lib/providers/google/adapter.ts
# expected: at least 1 match

# AC.b: existing google tool events test still passes
cd platform && npx vitest run tests/providers/google-tool-events.test.ts --no-coverage 2>&1 | tail -5
# expected: no failures

# AC.c: E2E round-trip test passes
cd platform && npx vitest run tests/providers/google/e2e-loop-roundtrip.test.ts --no-coverage 2>&1 | tail -5
# expected: 3 tests pass

# AC.d: full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- Patched `platform/src/lib/providers/google/adapter.ts`
- `tests/providers/google/e2e-loop-roundtrip.test.ts` (new)
- `tests/providers/google/fixtures/tool_use_stream.ts` (new)
- Commit: `fix(r11f-b-s1): google adapter forwards tools in Gemini format + E2E test`

## Rollback Steps

```bash
git revert HEAD
```
