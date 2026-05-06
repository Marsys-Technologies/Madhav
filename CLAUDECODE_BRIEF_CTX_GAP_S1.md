---
session_id: CTX-GAP-S1
status: COMPLETE
executor: claude-code-antigravity
phase: Context Contamination Gap Fix — Synthesis Independence
estimated_effort: light-medium (1–2 hours)
---

# CLAUDECODE_BRIEF — CTX-GAP-S1: Synthesis Context Contamination Fixes

## Mission

The synthesis pipeline has been diagnosed with five compounding gaps that allow prior
conversation turns to contaminate LLM responses, particularly for the Gemini stack (gemini-2.5-pro).
Fresh-conversation queries produce corpus-grounded, consistent responses. Mid-conversation queries
on the same topic produce responses that drift toward the conversational narrative established in
prior turns, violating the B.1 facts/interpretation separation principle and producing
inconsistent outputs across sessions.

This session fixes all five gaps in a single coordinated change.

## Root Cause Summary

**GAP-1 (Root):** `route.ts` passes `.slice(0, -1)` (ALL prior turns) to synthesis.
No cap exists. An 8-turn conversation passes 7 prior messages into the synthesis model.

**GAP-2 (Compounding):** The synthesis system prompt in `shared.ts` has no
QUERY_INDEPENDENCE_GATE. The model is never told to treat each query as independently
grounded in the retrieved corpus rather than as a continuation of the conversation.

**GAP-3 (Structural):** Three pipeline stages use three different history depths
with no shared policy:
- Planner (via `planner_context_builder`): last 2 turns, ≤ 300 tokens each
- Classifier (`classify()`): last 4 raw turns (`plannerHistory`)
- Synthesis: ALL prior turns, unbounded

**GAP-4 (Model-specific amplifier):** Gemini 2.5 Pro's context-following training is
stronger than Claude or NIM. Without an independence gate (GAP-2), Gemini inherits
the prior conversation's narrative, framings, and domain weightings when generating
its answer — even when the retrieved corpus clearly points in a different direction.

**GAP-5 (Structural):** `route.ts` slices 4 turns before calling `callLlmPlanner`,
but `planner_context_builder` internally re-slices to 2 turns. The caller believes
the planner sees 4 turns; it actually sees 2. This silent mismatch creates confusion
for anyone reading or maintaining the code and makes the history policy invisible.

---

## Deliverable 1 — Cap synthesis history to last 2 prior exchanges in route.ts

**File:** `platform/src/app/api/chat/consume/route.ts`

Locate the `orchestrator.synthesize({...})` call block (approximately line 583–600).
Find:
```ts
conversation_history: messages
  .filter(m => m.role === 'user' || m.role === 'assistant')
  .slice(0, -1)
  .map(m => ({
    role: m.role as 'user' | 'assistant',
    content: extractText(m.parts ?? []),
  }))
  .filter(m => m.content.length > 0),
```

Replace with:
```ts
// CTX-GAP-S1: Cap synthesis history to the last 4 messages (= 2 prior user+assistant
// exchange pairs) to prevent prior conversation narrative from contaminating the
// corpus-grounded synthesis response. Aligns with planner_context_builder's
// effective 2-turn window. Unbounded history (.slice(0,-1)) was the primary
// vector for context contamination, especially on Gemini stack.
conversation_history: messages
  .filter(m => m.role === 'user' || m.role === 'assistant')
  .slice(-5)       // last 5 = 2 prior pairs + current user message
  .slice(0, -1)    // drop current user message (appended via `query`)
  .map(m => ({
    role: m.role as 'user' | 'assistant',
    content: extractText(m.parts ?? []),
  }))
  .filter(m => m.content.length > 0),
```

**Why `.slice(-5).slice(0, -1)` = 4 messages = 2 prior exchanges:**
- `messages` at synthesis call time always has the current user message last
- `.slice(-5)` takes the last 5: 2 prior pairs (4 messages) + current user message (1)
- `.slice(0, -1)` drops the current user message (which is passed separately via `query`)
- Net: 4 messages = 2 prior user+assistant exchanges — consistent with `planner_context_builder`

---

## Deliverable 2 — Add QUERY_INDEPENDENCE_GATE to the synthesis system prompt

**File:** `platform/src/lib/prompts/templates/shared.ts`

Add the following exported constant after the `CALIBRATION_LANGUAGE_GATE` export
(after line `export const CALIBRATION_LANGUAGE_GATE = ...`):

```ts
export const QUERY_INDEPENDENCE_GATE = `QUERY INDEPENDENCE GATE (mandatory for all query classes):
Each query is answered independently from the retrieved corpus assembled in this system message. Prior conversation turns are provided as linguistic context only — do not weight prior assistant conclusions, tonal framings, domain emphases, or interpretive directions when constructing this response. Ground every claim in the retrieved artifacts (CHART_CONTEXT_BLOCK, PRE_FETCHED_TOOL_RESULTS, tool call results) and in the current query alone. If a prior turn discussed Venus transits and the current query is about Saturn's dasha, the prior Venus discussion has zero weight on this response. Treat the retrieved corpus as ground truth; treat conversation history as background noise.`
```

Then add `QUERY_INDEPENDENCE_GATE` to the `buildOpeningBlock()` function, immediately
after `${CALIBRATION_LANGUAGE_GATE}`:

Find:
```ts
export function buildOpeningBlock(): string {
  return `${NATIVE_CONTEXT}

${BUNDLE_CONTEXT}

${TOOL_AVAILABILITY}

${ACHARYA_GRADE}

${CITATION_DISCIPLINE}

${NO_FABRICATION}

${CONTRADICTION_FRAMING}

${METHODOLOGY_INSTRUCTION}`
}
```

Replace with:
```ts
export function buildOpeningBlock(): string {
  return `${NATIVE_CONTEXT}

${BUNDLE_CONTEXT}

${TOOL_AVAILABILITY}

${ACHARYA_GRADE}

${CITATION_DISCIPLINE}

${NO_FABRICATION}

${CONTRADICTION_FRAMING}

${QUERY_INDEPENDENCE_GATE}

${METHODOLOGY_INSTRUCTION}`
}
```

---

## Deliverable 3 — Align plannerHistory slice in route.ts to match planner_context_builder's effective window

**File:** `platform/src/app/api/chat/consume/route.ts`

**GAP-5 fix:** The current code passes 4 raw turns to `callLlmPlanner`, but
`planner_context_builder` internally uses only the last 2. This silent mismatch
makes the effective window invisible at the call site. Fix by explicitly passing
only 2 turns, matching what `planner_context_builder` will actually use.

Find (approximately line 273):
```ts
const plannerHistory = messages
  .filter(m => m.role === 'user' || m.role === 'assistant')
  .slice(-4)
  .map(m => ({
    role: m.role as 'user' | 'assistant',
    content: extractText(m.parts ?? []),
  }))
  .filter(m => m.content.length > 0)
```

Replace with:
```ts
// CTX-GAP-S1: Explicitly pass last 2 turns (= the effective window that
// planner_context_builder will actually use after its internal slice(-MAX_TURNS=2)).
// Previous slice(-4) created a silent mismatch — caller believed planner saw 4
// turns, but planner_context_builder re-sliced to 2 internally.
// Also used by classify() — both stages now see the same explicit 2-turn window.
const plannerHistory = messages
  .filter(m => m.role === 'user' || m.role === 'assistant')
  .slice(-2)
  .map(m => ({
    role: m.role as 'user' | 'assistant',
    content: extractText(m.parts ?? []),
  }))
  .filter(m => m.content.length > 0)
```

**Note:** `plannerHistory` is also passed to `classify()` on line ~292 as
`conversation_history: plannerHistory`. This same change fixes GAP-3 for the
classifier too — classifier now uses 2 turns matching the planner, instead of 4.

---

## Deliverable 4 — Export QUERY_INDEPENDENCE_GATE from the prompts index (if applicable)

**File:** `platform/src/lib/prompts/index.ts`

Check if `index.ts` re-exports items from `shared.ts`. If it does, add
`QUERY_INDEPENDENCE_GATE` to the exports list so downstream tests can reference it.

Example pattern to look for and extend:
```ts
export { QUERY_INDEPENDENCE_GATE } from './templates/shared'
```

If `index.ts` does not export from `shared.ts`, skip this deliverable — the constant
is already accessible via direct import from `./templates/shared`.

---

## Deliverable 5 — Add/update tests

**Files:**
```
platform/src/lib/prompts/__tests__/
platform/src/lib/synthesis/__tests__/
```

### 5a — Prompt template test: verify QUERY_INDEPENDENCE_GATE appears in rendered output

In the existing prompt template test file (likely
`platform/src/lib/prompts/__tests__/registry.test.ts` or similar), add a test:

```ts
it('buildOpeningBlock includes QUERY_INDEPENDENCE_GATE', () => {
  const block = buildOpeningBlock()
  expect(block).toContain('QUERY INDEPENDENCE GATE')
  expect(block).toContain('answered independently from the retrieved corpus')
})
```

### 5b — Synthesis history cap test

In `single_model_strategy` tests or a new integration test, verify that when
`conversation_history` contains more than 4 messages, the synthesis prompt is
NOT contaminated with all of them. The simplest test: confirm `historyMessages`
in the constructed `modelMessages` has length ≤ 4 when passed to the model.

If `single_model_strategy.ts` does not have a direct test for `modelMessages`
construction, add a focused unit test for the history cap:

```ts
it('synthesis history is bounded — does not exceed 4 messages', () => {
  // Build a fake 10-turn history (10 user+assistant pairs = 20 messages)
  const longHistory: Array<{ role: 'user' | 'assistant'; content: string }> =
    Array.from({ length: 20 }, (_, i) => ({
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `turn ${i}`,
    }))
  // After the route.ts slice(-5).slice(0,-1), at most 4 messages survive.
  const capped = longHistory.slice(-5).slice(0, -1)
  expect(capped.length).toBeLessThanOrEqual(4)
})
```

---

## Acceptance Criteria

- [ ] AC.CTX.1 — `route.ts` synthesis `conversation_history` uses `.slice(-5).slice(0,-1)` — not `.slice(0,-1)`
- [ ] AC.CTX.2 — `plannerHistory` in `route.ts` uses `.slice(-2)` — not `.slice(-4)`
- [ ] AC.CTX.3 — `QUERY_INDEPENDENCE_GATE` constant exists and is exported from `shared.ts`
- [ ] AC.CTX.4 — `buildOpeningBlock()` includes `QUERY_INDEPENDENCE_GATE` in its returned string
- [ ] AC.CTX.5 — `buildOpeningBlock()` test asserts the gate is present
- [ ] AC.CTX.6 — History cap test passes: a 20-message history produces ≤ 4 `historyMessages`
- [ ] AC.CTX.7 — `npx tsc --noEmit` 0 new errors
- [ ] AC.CTX.8 — All existing synthesis and prompt tests pass

---

## may_touch
```
platform/src/app/api/chat/consume/route.ts
platform/src/lib/prompts/templates/shared.ts
platform/src/lib/prompts/index.ts
platform/src/lib/synthesis/__tests__/**
platform/src/lib/prompts/__tests__/**
```

## must_not_touch
```
platform/src/lib/pipeline/planner_context_builder.ts
platform/src/lib/pipeline/manifest_planner.ts
platform/src/lib/synthesis/single_model_strategy.ts
platform/src/lib/models/registry.ts
platform/src/lib/models/resolver.ts
platform/migrations/**
platform/src/app/api/admin/**
```

---

## Notes for executor

1. **Do not touch `planner_context_builder.ts`** — its internal 2-turn cap is correct.
   We are aligning the *caller* (route.ts) to the *policy already declared in* the builder,
   not changing the builder itself.

2. **Do not touch `single_model_strategy.ts`** — the fix is at the call site (route.ts),
   not inside synthesis. `single_model_strategy` already faithfully injects whatever
   `conversation_history` it receives — the caller was sending the wrong window.

3. **The `.slice(-5).slice(0,-1)` arithmetic:** The synthesis call always receives
   `messages` with the current user message at index `-1`. So `-5` takes 2 prior pairs
   + current message (5 items total), then `.slice(0,-1)` removes the current message.
   Net = 4 messages = 2 prior (user, assistant) pairs. This matches the planner's policy.

4. **The QUERY_INDEPENDENCE_GATE placement:** Insert it AFTER the CONTRADICTION_FRAMING
   block and BEFORE the METHODOLOGY_INSTRUCTION block. It must appear in the system
   message (before the history messages in the final `modelMessages` array) to be
   effective. This is already guaranteed because `renderedPrompt` becomes the system
   message and `historyMessages` are injected after it.

5. **Gemini-specific behavior:** Once the gate is in the system prompt, Gemini 2.5 Pro
   will honour it because it IS a well-instruction-following model. The prior problem
   was the absence of the instruction, not a model limitation.
