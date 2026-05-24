---
artifact: BRIEF_R11F-A-S3_v1_0.md
session_id: R11F-A-S3
version: 1.0
phase: A
parallel_safety: false
depends_on: [R11F-A-S2]
estimated_loc_delta: +140
---

# R11F-A-S3 — B.11 Floor Preservation + onFinish Parity

## Scope

Two critical invariants are missing from the adapter-dispatch code path:

**B.11 floor**: The existing plan-and-execute path pre-executes MSR, UCN, CGM retrieval
tools deterministically before any model call. The adapter branch must preserve this. The
loop is entered ONLY after floor results have been injected into context. This is an
architectural guarantee — the model cannot skip it by not calling floor tools.

**onFinish parity**: The adapter branch at route.ts:~1082 returns via
`createUIMessageStreamResponse()` without executing the `onFinish` block that the
legacy path runs. Missing: `context_assembly_log` write, `prediction_candidate` detection,
`conversation_messages` persistence. This session wires all three into the adapter-branch
completion path.

## Files May Touch

```
platform/src/app/api/chat/consume/route.ts
platform/src/lib/synthesis/agentic_loop.ts
platform/tests/synthesis/agentic-loop-b11-floor.test.ts  (new)
platform/tests/routes/adapter-branch-onfinis.test.ts     (new)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/**
CLAUDE.md
deploy.yml
```

## Preconditions

1. A-S2 committed. Baseline vitest passes.
2. Read `route.ts` lines 480–560 to understand current floor pre-execution block.
3. Read `route.ts` lines 1240–1520 to understand the full `onFinish` block structure.

## Implementation

### Part 1 — B.11 Floor Preservation

#### Step 1: Locate the floor pre-execution block

In `route.ts`, search for the section that fires `query_chart_facts`, `holistic_bundle`,
or retrieves MSR/UCN/CGM before synthesis. It likely runs before the `synthesize()` call.
Note the variable names that hold the floor results and the array of floor tool names.

#### Step 2: Verify floor runs before the adapter dispatch

The adapter dispatch block (starting with `if (useAdapters)`) must be downstream of the
floor pre-execution. If it's currently at the same level (both inside the main request
handler, floor first), the structure is already correct — add a comment confirming this.

If the floor pre-execution is INSIDE the legacy synthesize path and does NOT run for the
adapter path, you must extract it. Create a `runB11Floor(context) → FloorResults` helper
that is called unconditionally BEFORE the `if (useAdapters)` branch.

#### Step 3: Inject floor results into adapterChatReq

Floor results (retrieved chunks from MSR/UCN/CGM) must be present in `adapterChatReq.messages`
as a system-layer context block before the loop starts. The existing prompt assembly
(`prompt_assembler.ts`) should handle this if the floor results are in the correct shape.
Verify and patch if needed.

#### Step 4: Document the contract

Add a block comment at the top of the adapter dispatch section in route.ts:

```typescript
/**
 * B.11 FLOOR CONTRACT (binding for all adapter dispatch paths):
 *
 * B.11 floor tools (MSR, UCN, CGM holistic synthesis) are pre-executed
 * deterministically above this block and their results injected into
 * adapterChatReq.messages before any model call. The agentic loop receives
 * a context that already contains the holistic synthesis layer — the model
 * cannot skip or defer it.
 *
 * Loop tools are the PLANNER-AUTHORISED SUBSET only. The loop adds gap-recovery
 * and ambiguity-resolution capability. It does not replace the planner.
 */
```

### Part 2 — onFinish Parity

#### Step 5: Identify the three missing persistence actions

Read route.ts lines 1240–1520 in the legacy `onFinish` callback:
1. `context_assembly_log` write (~line 1306)
2. Prediction candidate detection and `data-prediction-candidate` emit (~line 1501)
3. `conversation_messages` persistence (~line 1427)

#### Step 6: Extract into a shared `runPostLoopPersistence` helper

Create a helper (either in route.ts or a new `platform/src/lib/synthesis/post_loop.ts`):

```typescript
interface PostLoopContext {
  queryId: string
  userId: string
  conversationId: string
  finalMessages: UIMessage[]
  systemContent: string | undefined
  usageData: UsageData
  traceSteps: TraceStep[]
  emit: (part: StreamPart) => void
}

async function runPostLoopPersistence(ctx: PostLoopContext): Promise<void> {
  // 1. context_assembly_log write
  // 2. detectPredictionCandidates + emit data-prediction-candidate
  // 3. upsert conversation_messages
}
```

The implementation is extracted from the existing `onFinish` block. Do NOT delete the
existing `onFinish` block — call `runPostLoopPersistence` from BOTH the adapter completion
path AND from within the existing `onFinish` (or restructure so both call the same function).

#### Step 7: Call from adapter completion path

At the point where the adapter stream ends (after draining `adapterStream`), call:

```typescript
await runPostLoopPersistence({
  queryId,
  userId,
  conversationId,
  finalMessages: collectedMessages,
  systemContent,
  usageData: collectedUsage,
  traceSteps: collectedTraceSteps,
  emit,
})
```

### Part 3 — Tests

#### Test file 1: `agentic-loop-b11-floor.test.ts`

```typescript
describe('B.11 floor preservation in adapter dispatch', () => {
  it('MSR/UCN/CGM appear in adapterChatReq.messages regardless of model behaviour', async () => {
    // Mock the planner to authorise only non-floor tools
    // Mock the floor pre-execution to inject a marker chunk
    // Run the adapter dispatch path with a mock adapter
    // Assert: adapterChatReq.messages contains the floor marker
    // Assert: the model's first request includes floor context
  })
})
```

#### Test file 2: `adapter-branch-onfinish.test.ts`

```typescript
describe('onFinish parity: adapter branch vs legacy branch', () => {
  it('adapter branch writes context_assembly_log row', async () => { ... })
  it('adapter branch detects prediction candidates', async () => { ... })
  it('adapter branch persists conversation_messages', async () => { ... })
})
```

## Acceptance Tests

```bash
# AC.a: floor contract comment present
grep -c "B.11 FLOOR CONTRACT" platform/src/app/api/chat/consume/route.ts
# expected: 1

# AC.b: floor test passes
cd platform && npx vitest run tests/synthesis/agentic-loop-b11-floor.test.ts --no-coverage 2>&1 | tail -5
# expected: no failures

# AC.c: onFinish parity test passes
cd platform && npx vitest run tests/routes/adapter-branch-onfinish.test.ts --no-coverage 2>&1 | tail -5
# expected: no failures

# AC.d: full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- Patched `route.ts` (floor contract comment + onFinish parity wiring)
- `platform/tests/synthesis/agentic-loop-b11-floor.test.ts` (new)
- `platform/tests/routes/adapter-branch-onfinish.test.ts` (new)
- Optionally: `platform/src/lib/synthesis/post_loop.ts` (new helper)
- Commit: `fix(r11f-a-s3): B.11 floor preservation + onFinish parity for adapter dispatch`

## Rollback Steps

```bash
git revert HEAD
```
