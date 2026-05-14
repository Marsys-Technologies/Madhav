---
status: OPEN
session_id: AIOPS_CO_3
phase: CO.3
phase_name: "Reasoning slot + tool-call chronology (Bug 3.3 + Bug 3.4)"
next_session: AIOPS_CO_4
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_3
## AIOps Phase 3, Step 3 — Reasoning + intermediate display

---

## §0 — Executor orientation

CO.3 fixes Bugs 3.3 and 3.4:

**Bug 3.3** — Reasoning panel renders at the top of the chat during streaming
then snaps to between query+response when the response arrives. Layout
flicker. ROOT CAUSE: the reasoning panel's parent container doesn't have a
stable DOM position from the moment of query submission. CO.1's
`ReasoningSlot` introduced the anchored slot; CO.3 wires real content
into it.

**Bug 3.4** — Reasoning shows for some queries, absent for others,
inconsistently. ROOT CAUSE: previous behavior depended on substring-matching
DeepSeek's `<think>` blocks; now the Phase 2 adapter emits typed
`reasoning_delta` events, and `model.quirks.reasoning_via` reliably
indicates whether reasoning is expected. CO.3 makes the panel
**model-aware**: present iff `reasoning_via !== 'none'`.

Plus: the `tool_call` + `tool_result` chronology from the event stream
populates the `ToolCallChronology` slot (CO.1 placeholder).

Behind `CONSUME_UI_V2_ENABLED`.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md (components 4, 5)
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/lib/adapters/types.ts (reasoning_delta, tool_call, tool_result event types)
5. platform/src/lib/models/registry.ts (ProviderQuirks.reasoning_via)
6. platform/src/lib/hooks/useChatLifecycle.ts (snapshot.reasoningText, snapshot.toolCalls)
7. platform/src/components/consume/lifecycle/ReasoningSlot.tsx (CO.1 placeholder; populate here)
8. platform/src/components/consume/lifecycle/ToolCallChronology.tsx (CO.1 placeholder; populate here)
9. platform/src/components/consume/LiveReasoningCard.tsx (legacy — replaced by ReasoningSlot in v2)
```

---

## §2 — Scope

### may_touch
```
platform/src/components/consume/lifecycle/ReasoningSlot.tsx        # fill in real impl
platform/src/components/consume/lifecycle/ToolCallChronology.tsx   # fill in real impl
platform/src/components/consume/StreamingAnswer.tsx                # wire slots per model.quirks
platform/src/components/consume/LiveReasoningCard.tsx              # mark legacy; preserve for flag-off
platform/src/components/consume/__tests__/**                       # tests
CLAUDECODE_BRIEF.md
```

### must_not_touch
- useChatLifecycle.ts (CO.1 sealed)
- AnswerView.tsx (legacy)
- ConsumeChat.tsx parent layout (CO.1/CO.2 sealed)
- adapters/, synthesis/, models/registry.ts

---

## §3 — Work plan

### 3.1 — ReasoningSlot

`ReasoningSlot.tsx` props:
```ts
interface ReasoningSlotProps {
  reasoningText: string         // from useChatLifecycle().reasoningText
  isStreaming: boolean          // true while state === 'reasoning'
  modelId: string               // for ProviderQuirks lookup
  collapsedByDefault?: boolean  // default false during streaming, true after composing
}
```

Behavior:
1. Look up `getModelMeta(modelId).quirks.reasoning_via`.
2. If `'none'` → render nothing. Slot collapses to zero height.
3. If `'native'` or `'markers'` → render an expandable card:
   - Header: "Thinking..." while streaming; "Thought for Ns" after composing.
   - Body: scrollable, markdown-rendered reasoningText.
   - Collapsed by default after streaming completes; click to expand.

Crucially: when `reasoning_via !== 'none'`, the slot renders an EMPTY
placeholder from the moment the query is submitted. No layout shift when
content streams in.

### 3.2 — ToolCallChronology

`ToolCallChronology.tsx` props:
```ts
interface ToolCallChronologyProps {
  toolCalls: ToolCallRecord[]   // chronological from useChatLifecycle
}
```

Renders as collapsible cards in chronological order. Each card shows:
- Tool name
- Arguments (collapsed by default, expandable)
- Result (collapsed by default, expandable)

Empty array → render nothing (zero-height collapse). When the first
`tool_call` event arrives, the slot expands with the card.

### 3.3 — Wire slots in StreamingAnswer

Update `StreamingAnswer.tsx`:
```tsx
const lifecycle = useChatLifecycle(...)
const meta = getModelMeta(lifecycle.modelMeta?.modelId ?? '')

return (
  <div className="message">
    <UserMessage ... />
    <StatusPip state={lifecycle.state} />
    {meta?.quirks.reasoning_via !== 'none' && (
      <ReasoningSlot
        reasoningText={lifecycle.reasoningText}
        isStreaming={lifecycle.state === 'reasoning'}
        modelId={meta?.id ?? ''}
        collapsedByDefault={lifecycle.state === 'complete'}
      />
    )}
    {lifecycle.toolCalls.length > 0 && (
      <ToolCallChronology toolCalls={lifecycle.toolCalls} />
    )}
    <FinalAnswerSlot text={lifecycle.finalText} />
    <MetadataBadge meta={lifecycle.modelMeta} />
  </div>
)
```

The conditional rendering for ReasoningSlot uses the model's quirks —
this is the fix for Bug 3.4 (model-aware).

### 3.4 — CLS verification

Use the existing dev-tools workflow or a manual measurement:
1. Load `/consume`, submit a query that triggers a reasoning model.
2. Open Performance tab, measure CLS during the streaming response.
3. CLS should be < 0.05 (essentially zero).

Document the measurement in a comment in the test file.

### 3.5 — Tests

- ReasoningSlot renders empty for `reasoning_via: 'none'` models.
- ReasoningSlot renders progressively as `reasoningText` accumulates.
- ToolCallChronology renders cards in order; nested expand state preserved.
- Snapshot tests for the full StreamingAnswer with mock streams covering: reasoning-only, tool-call-only, both, neither.
- CLS regression test (or documented manual measurement).
- ≥15 cases.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO3.1 | ReasoningSlot renders nothing for `reasoning_via: 'none'` | parametrized test |
| AC.CO3.2 | ReasoningSlot has stable DOM position from submission (no layout shift) | UI test asserting parent container height stable |
| AC.CO3.3 | ReasoningSlot reasoning text accumulates from `reasoning_delta` events | snapshot |
| AC.CO3.4 | ReasoningSlot collapses to "Thought for Ns" after composing | snapshot |
| AC.CO3.5 | ToolCallChronology renders chronological cards | render test |
| AC.CO3.6 | StreamingAnswer wiring respects model.quirks.reasoning_via | parametrized |
| AC.CO3.7 | CLS < 0.05 measured during a typical streaming response | manual + documented |
| AC.CO3.8 | LiveReasoningCard preserved for flag-off path | grep + render test |
| AC.CO3.9 | typecheck + lint clean | exit 0 |
| AC.CO3.10 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
feat(aiops-CO.3): fix Bugs 3.3 + 3.4 — reasoning slot + tool chronology

Bug 3.3 (reasoning placement flicker):
- ReasoningSlot rendered in stable DOM position from the moment of query
  submission. Empty placeholder mounts immediately; content streams in via
  reasoning_delta events. No layout shift (CLS < 0.05 verified).

Bug 3.4 (reasoning inconsistency):
- ReasoningSlot is model-aware via ProviderQuirks.reasoning_via:
  - 'native' / 'markers' → slot present
  - 'none' → slot absent (no false-empty panels)

ToolCallChronology:
- Renders tool_call + tool_result events as chronological collapsible cards.
- Empty array → zero-height; first tool_call expands the slot.

LiveReasoningCard preserved for flag-off path (forward-only commitment).
15+ new tests; full suite green.

AC summary: 10/10 PASS
```

Rotate → CO.4.

---

## §6 — BAIL OUT

- `useChatLifecycle()` doesn't expose `reasoningText` or `toolCalls` the way CO.1 said it would (contract mismatch).
- ProviderQuirks data not accessible from the consume component path without a deep refactor.

---

*End of PHASE_CO_3_BRIEF.md*
