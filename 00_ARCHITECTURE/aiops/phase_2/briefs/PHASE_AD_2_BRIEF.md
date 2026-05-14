---
status: OPEN
session_id: AIOPS_AD_2
phase: AD.2
phase_name: "Dispatcher + non-streaming wrapper + base adapter contract"
next_session: AIOPS_AD_3
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_AD_2
## AIOps Phase 2, Step 2 — Dispatcher + runAdapter / streamAdapter

---

## §0 — Executor orientation

AD.2 wires up the public surface — `runAdapter()` and `streamAdapter()` —
that call sites will use in AD.4. The provider-specific adapters
themselves are still stubs from AD.0; this phase implements the *plumbing*
that routes a `QueryRequest` to the right adapter and assembles a
`ModelInteraction` from the event stream.

After AD.2, calling `streamAdapter(req)` from a test should successfully
route to the right provider stub (which throws "not implemented" —
that's AD.3 work). The dispatcher + non-streaming wrapper are
testable in isolation.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md §4, §5, §7
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/lib/adapters/types.ts (from AD.0)
5. platform/src/lib/adapters/dispatcher.ts (from AD.0)
6. platform/src/lib/models/registry.ts (now has quirks per AD.1)
7. platform/src/lib/models/runtime_config.ts (Phase 1 — getEffectiveModel)
8. platform/src/lib/models/resolver.ts (resolveModel — DO NOT MODIFY yet)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/adapters/index.ts            # export runAdapter, streamAdapter
platform/src/lib/adapters/run_adapter.ts      # NEW — non-streaming wrapper
platform/src/lib/adapters/stream_adapter.ts   # NEW — streaming entry + collector
platform/src/lib/adapters/event_collector.ts  # NEW — folds events into ModelInteraction
platform/src/lib/adapters/__tests__/*         # NEW dispatcher + collector tests
CLAUDECODE_BRIEF.md
```

### must_not_touch
- Provider adapter implementations (AD.3 territory).
- Call sites (AD.4 territory).
- Anything outside lib/adapters/ except what's already in may_touch list above.

---

## §3 — Work plan

### 3.1 — streamAdapter

`platform/src/lib/adapters/stream_adapter.ts`:

```ts
import 'server-only'
import type { QueryRequest, ModelInteractionEvent } from './types'
import { adapterFor } from './dispatcher'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { getModelMeta } from '@/lib/models/registry'

export function streamAdapter(req: QueryRequest): ReadableStream<ModelInteractionEvent> {
  const modelId = resolveModelId(req)
  const meta = getModelMeta(modelId)
  if (!meta) {
    throw new Error(`streamAdapter: unknown model ${modelId}`)
  }
  const adapter = adapterFor(meta.provider)
  return adapter.stream(req, meta)
}

function resolveModelId(req: QueryRequest): string {
  if (req.modelOverride) return req.modelOverride.modelId
  // For now, do a synchronous fallback to registry default; AD.4 will thread
  // async getEffectiveModel through the call sites.
  // SYNCHRONOUS PATH FOR AD.2 — replaced with Promise<string> in AD.4.
  // ...
}
```

Note the synchronous-resolution shortcut: AD.2 doesn't yet integrate with
async `getEffectiveModel`. That migration happens in AD.4. Document this in
a comment and make the test fixtures use `modelOverride` to avoid the
resolution path.

### 3.2 — runAdapter (non-streaming wrapper)

`platform/src/lib/adapters/run_adapter.ts`:

```ts
import 'server-only'
import type { QueryRequest, ModelInteraction } from './types'
import { streamAdapter } from './stream_adapter'
import { collectInteraction } from './event_collector'

export async function runAdapter(req: QueryRequest): Promise<ModelInteraction> {
  const stream = streamAdapter(req)
  return collectInteraction(stream)
}
```

### 3.3 — Event collector

`platform/src/lib/adapters/event_collector.ts`:

```ts
import type {
  ModelInteractionEvent,
  ModelInteraction,
  IntermediateEvent,
} from './types'

export async function collectInteraction(
  stream: ReadableStream<ModelInteractionEvent>,
): Promise<ModelInteraction> {
  const reader = stream.getReader()
  let reasoningText = ''
  let reasoningTokens = 0
  let finalText: string | undefined
  let finalStructured: unknown | undefined
  const intermediate: IntermediateEvent[] = []
  let finishedInteraction: ModelInteraction | undefined

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    switch (value.type) {
      case 'reasoning_delta':
        reasoningText += value.text
        break
      case 'text_delta':
        finalText = (finalText ?? '') + value.text
        break
      case 'tool_call':
      case 'tool_result':
      case 'status':
        intermediate.push({ type: value.type as IntermediateEvent['type'], ts: value.ts, payload: value })
        break
      case 'finish':
        finishedInteraction = value.interaction
        break
      case 'error':
        throw new Error(value.error.message)
    }
  }

  if (!finishedInteraction) {
    throw new Error('collectInteraction: stream ended without finish event')
  }

  // Merge collected text/reasoning with the finish event's interaction
  // (the adapter is expected to populate everything in the finish event,
  // but we double-check here for resilience):
  return {
    ...finishedInteraction,
    reasoning: reasoningText ? { text: reasoningText, tokens: reasoningTokens } : finishedInteraction.reasoning,
    intermediate,
    finalText: finalText ?? finishedInteraction.finalText,
    finalStructured: finalStructured ?? finishedInteraction.finalStructured,
  }
}
```

### 3.4 — Public exports

`platform/src/lib/adapters/index.ts` (replace AD.0 placeholder):

```ts
export type {
  QueryRequest,
  ModelInteraction,
  ModelInteractionEvent,
  IntermediateEvent,
  ToolDefinition,
  ProviderQuirks,
} from './types'

export { runAdapter } from './run_adapter'
export { streamAdapter } from './stream_adapter'
export { adapterFor } from './dispatcher'
```

### 3.5 — Tests

Two new test files:

`platform/src/lib/adapters/__tests__/dispatcher.test.ts`:
- Provider routing: for each of 5 providers + every model, verify `adapterFor` returns the right adapter.
- 132 cases (6 stacks × 11 call types × 2 roles) parametrized via the same matrix used in cutover_smoke; assert correct adapter for each.
- Edge: MARSYS stack with mixed-provider routing dispatches per-model, not per-stack.

`platform/src/lib/adapters/__tests__/event_collector.test.ts`:
- Stream with only `text_delta` + `finish` → ModelInteraction.finalText populated.
- Stream with `reasoning_delta` events → reasoning text accumulates correctly.
- Stream with interleaved `tool_call` + `tool_result` → intermediate array preserves order.
- Stream with `error` event → throws.
- Stream without `finish` event → throws.
- ≥15 cases total.

Both test files use a **mock provider adapter** that emits a scripted event
stream. No real LLM calls in unit tests.

### 3.6 — Smoke

```bash
npm --prefix platform run typecheck 2>&1 | tail -5
npm --prefix platform run lint 2>&1 | tail -5
npm --prefix platform run test -- --run platform/src/lib/adapters/
```

All three must pass.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD2.1 | streamAdapter exported from index | grep |
| AC.AD2.2 | runAdapter exported from index | grep |
| AC.AD2.3 | adapterFor exported (re-exported from dispatcher) | grep |
| AC.AD2.4 | Dispatcher tests parametrize over 5 providers + every model | test count ≥ 30 |
| AC.AD2.5 | Event collector tests cover all 7 event types | ≥15 cases |
| AC.AD2.6 | Stream-without-finish raises clear error | test asserts |
| AC.AD2.7 | typecheck + lint + full test suite green | exit 0 each |
| AC.AD2.8 | scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Final commit:
```
feat(aiops-AD.2): dispatcher + runAdapter/streamAdapter + event collector

- streamAdapter: looks up model meta, dispatches to provider adapter
- runAdapter: async wrapper that collects the stream into ModelInteraction
- collectInteraction: folds events into final shape; preserves intermediate order
- dispatcher_test parametrizes across all 5 providers + every model
- event_collector_test covers all 7 event types + error edges
- 45+ new tests; full suite green

AC summary: 8/8 PASS
```

Rotate brief → AD.3.

---

## §7 — BAIL OUT triggers

- The async vs sync resolution shortcut in §3.1 doesn't compile cleanly — investigate, but if it pulls in unrelated refactoring, bail.
- The event collector's resilience logic conflicts with how providers will emit (some emit final text in `finish` instead of as deltas); this is a real ambiguity — bail and let native shape the contract.

---

*End of PHASE_AD_2_BRIEF.md*
