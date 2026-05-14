---
status: OPEN
session_id: AIOPS_CO_1
phase: CO.1
phase_name: "Chat lifecycle state machine + useChatLifecycle hook"
next_session: AIOPS_CO_2
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_1
## AIOps Phase 3, Step 1 — State machine + event subscription

---

## §0 — Executor orientation

CO.1 introduces the single source of truth for chat session state, driven
entirely by Phase 2's `ModelInteractionEvent` stream. Replaces ad-hoc
state management in `ConsumeChat.tsx` + `StreamingAnswer.tsx`.

After CO.1 closes, every UI surface (reasoning panel, tool calls, status
indicator, final answer) is positioned in a stable DOM slot, populated as
typed events arrive. This is the foundation for fixing Bug 3.3 (CO.3) and
all subsequent CO sub-phases.

Behind feature flag `CONSUME_UI_V2_ENABLED` (default false). Flag-off
behavior is byte-identical to today.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/AIOPS_PHASE_3_MASTER_PLAN_v1_0.md
3. 00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md (CO.0 deliverable; §4 state machine)
4. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md (CO.0 deliverable)
5. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
6. platform/src/lib/adapters/types.ts (ModelInteractionEvent)
7. platform/src/components/consume/ConsumeChat.tsx (existing state management)
8. platform/src/components/consume/StreamingAnswer.tsx
9. platform/src/components/consume/LiveReasoningCard.tsx
10. platform/src/app/api/chat/consume/route.ts (SSE producer; verify event shape)
11. platform/src/lib/config/feature_flags.ts (add CONSUME_UI_V2_ENABLED)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/hooks/useChatLifecycle.ts                # NEW
platform/src/lib/hooks/__tests__/useChatLifecycle.test.ts # NEW
platform/src/components/consume/lifecycle/**              # NEW dir for state-machine UI primitives
platform/src/components/consume/ConsumeChat.tsx           # refactor to use the hook
platform/src/components/consume/StreamingAnswer.tsx       # refactor; remove ad-hoc state
platform/src/components/consume/__tests__/**              # add new tests
platform/src/lib/config/feature_flags.ts                  # add CONSUME_UI_V2_ENABLED
platform/src/app/api/chat/consume/route.ts                # only if SSE shape needs tightening for typed events
CLAUDECODE_BRIEF.md
```

### must_not_touch
- platform/src/lib/adapters/**  (Phase 2 sealed)
- platform/src/lib/synthesis/**  (Phase 2 territory)
- platform/src/lib/models/**     (Phase 1 + 2)
- platform/src/lib/components/observatory/**  (sealed)
- platform/src/components/consume/LiveReasoningCard.tsx  (CO.3 territory)
- platform/src/components/consume/AnswerView.tsx          (legacy renderer — preserve for forward-only)
- platform/src/components/chat/ConversationSidebar.tsx   (CO.4 territory)
- platform/src/components/consume/TierPicker.tsx         (CO.2 territory)

---

## §3 — Work plan

### 3.1 — Feature flag

Add to `feature_flags.ts`:
```ts
| 'CONSUME_UI_V2_ENABLED'
```
In `DEFAULT_FLAGS`: `CONSUME_UI_V2_ENABLED: false`.
Flag-off → consume UI behaves identically to today (legacy components mount).

### 3.2 — State machine types

`platform/src/lib/hooks/useChatLifecycle.ts`:

```ts
export type ChatLifecycleState =
  | 'idle'
  | 'queued'
  | 'planning'
  | 'retrieving'
  | 'reasoning'
  | 'tool_calling'
  | 'composing'
  | 'complete'
  | 'error'
  | 'cancelled'

export interface ChatLifecycleSnapshot {
  state: ChatLifecycleState
  reasoningText: string       // accumulated reasoning_delta events
  toolCalls: ToolCallRecord[] // chronological tool_call + tool_result pairs
  finalText: string           // accumulated text_delta events
  modelMeta: { modelId: string; cost?: number; latencyMs?: number; usage?: any } | null
  error?: { message: string; code?: string }
}

export interface UseChatLifecycleOptions {
  stream: ReadableStream<ModelInteractionEvent> | null
}

export function useChatLifecycle(opts: UseChatLifecycleOptions): ChatLifecycleSnapshot
```

The hook subscribes to the event stream and produces a snapshot React can
render. Implementation uses `useReducer` for state transitions; the reducer
is exported separately for unit testing.

### 3.3 — Stable DOM slots

`platform/src/components/consume/lifecycle/`:

New sub-components, each with a stable position in the answer container:
- `StatusPip.tsx` — inline pulse showing current state (queued/planning/retrieving/composing)
- `ReasoningSlot.tsx` — anchored slot for reasoning text (filled by CO.3)
- `ToolCallChronology.tsx` — collapsible accordion (filled by CO.3)
- `FinalAnswerSlot.tsx` — main response area
- `MetadataBadge.tsx` — model+cost+latency capsule (positioned at end of message; CO.2 evolves)

The slot order is fixed:
```
<UserMessage />
<StatusPip />              {/* visible during processing; hides at 'complete' */}
<ReasoningSlot />          {/* present iff model.quirks.reasoning_via !== 'none' */}
<ToolCallChronology />     {/* present iff intermediate.tool_call events emitted */}
<FinalAnswerSlot />        {/* always present */}
<MetadataBadge />          {/* present at 'complete' */}
```

This is the structural fix for Bug 3.3 — every slot exists from submission;
content streams into it. No layout shift.

### 3.4 — Refactor ConsumeChat + StreamingAnswer

- Replace state derivations in `ConsumeChat.tsx` with `useChatLifecycle(stream)` subscription.
- Replace ad-hoc rendering in `StreamingAnswer.tsx` with the slot composition above.
- Behind `CONSUME_UI_V2_ENABLED`: if flag is off, render the OLD components (preserve them).
- The new component tree mounts only when flag is on.

### 3.5 — Tests

`useChatLifecycle.test.ts`:
- State transition table — for every (state, event) → (new state, side effects) pair, assert correctness.
- Reasoning accumulation across multiple `reasoning_delta` events.
- Tool call chronology preservation (order).
- Final text accumulation.
- Error path.
- ≥25 cases.

Component tests for the lifecycle/ primitives — ≥8 cases (mount, render, slot visibility, model-aware hiding).

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO1.1 | `useChatLifecycle.ts` exists; exports the hook + types | grep |
| AC.CO1.2 | State machine has 10 states + transitions for all 7 ModelInteractionEvent types | reducer test |
| AC.CO1.3 | Lifecycle slot components all exist | `ls lifecycle/` ≥ 5 |
| AC.CO1.4 | Feature flag CONSUME_UI_V2_ENABLED declared, default false | grep |
| AC.CO1.5 | With flag off, ConsumeChat + StreamingAnswer render identically to pre-CO.1 main | snapshot test |
| AC.CO1.6 | Reducer tests: ≥25 cases pass | test count |
| AC.CO1.7 | typecheck + lint clean | exit 0 |
| AC.CO1.8 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
feat(aiops-CO.1): chat lifecycle state machine + useChatLifecycle hook

- useChatLifecycle: ReadableStream<ModelInteractionEvent> → ChatLifecycleSnapshot
- 10 states (idle, queued, planning, retrieving, reasoning, tool_calling,
  composing, complete, error, cancelled) driven by Phase 2 events
- Lifecycle slot components: StatusPip, ReasoningSlot, ToolCallChronology,
  FinalAnswerSlot, MetadataBadge — anchored DOM positions from submission
- ConsumeChat + StreamingAnswer refactored to subscribe to the hook
- Behind feature flag CONSUME_UI_V2_ENABLED (default false; flag-off identical to today)
- 25+ reducer tests covering all (state, event) transitions

AC summary: 8/8 PASS
```

Rotate `CLAUDECODE_BRIEF.md` → `PHASE_CO_2_BRIEF.md`.

---

## §6 — BAIL OUT

- The current consume route doesn't emit events conforming to ModelInteractionEvent — the SSE shape changed since Phase 2's design assumed.
- Refactoring ConsumeChat pulls in >5 unrelated component changes (scope creep).

---

*End of PHASE_CO_1_BRIEF.md*
