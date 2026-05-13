---
artifact: CLAUDECODE_BRIEF_CONSUME_BUGFIX_S1.md
status: PENDING
session_id: CONSUME-BUGFIX-S1
phase: Consume Module — Five-Bug Fix (DeepSeek blank response + Gemini render loop)
executor: claude-opus-4-6 (anti-gravity VS Code)
run_from: /Users/Dev/Vibe-Coding/Apps/Madhav
branch: fix/consume-bugfix-s1
authored_by: Cowork (Abhisek session 2026-05-13)
authored_on: 2026-05-13
acceptance_criteria_count: 7
---

# CONSUME-BUGFIX-S1 — Five-Bug Fix

## §0 — HOW TO READ THIS BRIEF

Run from the **main** worktree: `/Users/Dev/Vibe-Coding/Apps/Madhav`.
Create branch at the start:

```bash
git checkout -b fix/consume-bugfix-s1
```

Execute all 5 bug fixes in the order given. Do NOT reorder them —
Steps 1–3 all touch `single_model_strategy.ts` and must be applied
sequentially on the same file so diffs don't conflict. Run `tsc --noEmit`
after Step 3. Run it again at the very end. When all 7 ACs are GREEN,
commit and push.

---

## §1 — BACKGROUND

Investigation of the last two live queries through the consume module
(2026-05-13 ~00:13–00:26, from `platform/.next/dev/logs/next-development.log`)
identified five bugs across three files:

| ID | File | Symptom |
|----|------|---------|
| BUG-D | `ConsumeChat.tsx` | React infinite render loop → Gemini response renders ~50% then freezes |
| BUG-C | `single_model_strategy.ts` | `finish_reason=tool-calls` with `final_output=""` silently produces blank UI |
| BUG-B | `single_model_strategy.ts` | Synthesis model receives callable retrieval tools → deepseek-v4-pro calls a tool instead of generating text |
| BUG-E | `single_model_strategy.ts` | `‹reasoning›` tags leak into Gemini synthesis output → p1_layer_separation FAIL |
| BUG-A | `pipeline_planner.ts` | `deepseek-chat` planner returns `tool_calls:[]` for holistic queries with no warning or enforcement |

Evidence from log:
- Query 1 `7c847f53`: `deepseek-chat` planner `tool_calls=0`, synthesis
  `finish_reason=tool-calls output_tokens=249 final_output=""` — blank response
- Query 2 `5e4ed486`: `gemini-2.5-pro` synthesis `finish_reason=stop output_tokens=4992`
  (full text generated) — browser "Maximum update depth exceeded" ×4 immediately
  after stream start, response frozen at ~50%

---

## §2 — MANDATORY READING BEFORE WRITING ANYTHING

```
platform/src/components/consume/ConsumeChat.tsx
platform/src/lib/synthesis/single_model_strategy.ts
platform/src/lib/pipeline/pipeline_planner.ts
platform/src/lib/synthesis/single_model_strategy.ts  (read fully — 3 bugs here)
```

---

## §3 — FIXES (execute in order)

---

### STEP 1 — BUG-D: Fix React infinite render loop in `ConsumeChat.tsx`

**File:** `platform/src/components/consume/ConsumeChat.tsx`

**Root cause:** `handleMarkers` useCallback has `sanskritTerms` in its dependency
array. Inside the callback, `setSanskritTerms(m.sanskrit)` mutates `sanskritTerms`.
The line `void sanskritTerms` at the bottom of the callback was added to silence
a lint warning but forces `sanskritTerms` into the dependency array. This creates
a loop:

```
onMarkers called
 → setSanskritTerms(m.sanskrit)       // updates state
 → sanskritTerms changes
 → new handleMarkers reference (useCallback invalidates)
 → useEffect in StreamingAnswer fires (onMarkers is a dep)
 → onMarkers called again
 → ∞
```

**Find this block** (around line 361):

```ts
  const handleMarkers = useCallback((m: {
    reasoning: ReasoningStepEvent[]
    sanskrit: SanskritTerm[]
    correction: CorrectionEvent | null
    outOfDomain: OutOfDomainEvent | null
    messageId: string | null
  }) => {
    // Reset state when assistant message id changes (new turn).
    if (m.messageId !== activeAssistantId) setActiveAssistantId(m.messageId)
    setReasoningSteps(m.reasoning)
    setSanskritTerms(m.sanskrit)
    if (m.correction) setCorrection(m.correction)
    if (m.outOfDomain) setOutOfDomain(m.outOfDomain)
    // Suppress unused warning for sanskritTerms (passed to children that
    // already get the parsed list via StreamingAnswer).
    void sanskritTerms
  }, [activeAssistantId, sanskritTerms])
```

**Replace with:**

```ts
  const handleMarkers = useCallback((m: {
    reasoning: ReasoningStepEvent[]
    sanskrit: SanskritTerm[]
    correction: CorrectionEvent | null
    outOfDomain: OutOfDomainEvent | null
    messageId: string | null
  }) => {
    // Reset state when assistant message id changes (new turn).
    if (m.messageId !== activeAssistantId) setActiveAssistantId(m.messageId)
    setReasoningSteps(m.reasoning)
    setSanskritTerms(m.sanskrit)
    if (m.correction) setCorrection(m.correction)
    if (m.outOfDomain) setOutOfDomain(m.outOfDomain)
    // NOTE: sanskritTerms intentionally NOT in deps and NOT read here.
    // It is SET here; reading it would create a circular setState→render→callback
    // dependency that causes an infinite render loop. Children receive sanskrit
    // terms via the StreamingAnswer parsed prop, not via this callback's state.
  }, [activeAssistantId])
```

**Verify:**
```bash
grep -n "void sanskritTerms" platform/src/components/consume/ConsumeChat.tsx
# Must return zero matches

grep -n "handleMarkers" platform/src/components/consume/ConsumeChat.tsx
# Confirm dep array reads: }, [activeAssistantId])
```

---

### STEP 2 — BUG-E: Extend reasoning-tag stripping to Gemini 2.5

**File:** `platform/src/lib/synthesis/single_model_strategy.ts`

**Root cause:** `isThinkingModel` gate only covers `deepseek-reasoner` and models
with "thinking" in their `hint` string. `gemini-2.5-pro` and `gemini-2.5-flash`
emit `‹reasoning›...‹/reasoning›` markers inline in the synthesis output but are
not classified as thinking models, so the tags are not stripped. Validator
`p1_layer_separation` correctly flagged this as FAIL on query `5e4ed486`.

**Find this block** (search for `isThinkingModel` — it is defined once):

```ts
        const isThinkingModel =
          selected_model_id === 'deepseek-reasoner' ||
          getModelMeta(selected_model_id)?.hint?.toLowerCase().includes('thinking') ||
          false
```

**Replace with:**

```ts
        // BUG-E fix: gemini-2.5-* emits ‹reasoning›...‹/reasoning› markers
        // in synthesis output. Extend isThinkingModel to cover these so
        // extractReasoningTrace / stripThinkBlocks runs and strips the tags
        // before validators and the audit event see the final text.
        const isThinkingModel =
          selected_model_id === 'deepseek-reasoner' ||
          selected_model_id.startsWith('gemini-2.5') ||
          getModelMeta(selected_model_id)?.hint?.toLowerCase().includes('thinking') ||
          false
```

**Verify:**
```bash
grep -A4 "const isThinkingModel" platform/src/lib/synthesis/single_model_strategy.ts
# Must show: selected_model_id.startsWith('gemini-2.5') on the second line
```

---

### STEP 3 — BUG-C + BUG-B: Empty output guard + prevent synthesis tool-calling

**File:** `platform/src/lib/synthesis/single_model_strategy.ts`

These two fixes are applied together because they both address the same
failure mode (synthesis model calling a tool instead of generating text)
at different layers: BUG-B prevents it from happening; BUG-C catches it
if it happens anyway and surfaces a visible error instead of blank output.

#### Part A — BUG-B: Add `toolChoice: 'none'` to synthesis `streamText` call

**Root cause:** The synthesis `streamText` call passes `tools: toolsForModel` — a
`ToolSet` of all retrieval tools wrapped for in-context calling. `deepseek-v4-pro`
(and other tool-capable models) interpret these definitions as callable and emit a
tool call as their synthesis response. `finish_reason=tool-calls` with 249 output
tokens confirms this. Synthesis is the text-generation phase; all retrieval has
already completed. The model must not be permitted to call tools during synthesis.

**Find the `streamText` call block** (search for `stopWhen: stepCountIs(5)`
which is unique to this call):

```ts
    const result = streamText({
      model: resolvedModel,
      messages: modelMessages,
      tools: toolsForModel,
      stopWhen: stepCountIs(5),
      maxOutputTokens: effectiveMaxTokens,
      temperature: synthesisTemperature,
      experimental_transform: smoothStream({ delayInMs: 20, chunking: 'word' }),
```

**Replace with:**

```ts
    const result = streamText({
      model: resolvedModel,
      messages: modelMessages,
      tools: toolsForModel,
      // BUG-B fix: synthesis is the text-generation phase; all retrieval tools
      // have already executed. Prohibit the synthesis model from calling any
      // tool so it must generate text. Without this, tool-capable models
      // (deepseek-v4-pro, gemini-2.5-pro) may emit finish_reason=tool-calls
      // with empty final_output instead of a synthesis response.
      toolChoice: toolsForModel ? ('none' as const) : undefined,
      stopWhen: stepCountIs(5),
      maxOutputTokens: effectiveMaxTokens,
      temperature: synthesisTemperature,
      experimental_transform: smoothStream({ delayInMs: 20, chunking: 'word' }),
```

#### Part B — BUG-C: Add empty-output guard after `cleanText` is derived

**Root cause:** When `finish_reason=tool-calls` and `cleanText=""`, the pipeline
silently produces a blank response. There is no error surface, no fallback, and
no visibility to the user. The audit event records `final_output=""` but the
client renders nothing with no error state.

**Find this block** (the `let cleanText = ...` line followed by the `mbMatch`
fence-strip block — search for `BUG-4: for thinking models`):

```ts
        let cleanText = (isThinkingModel && _cleanAnswer === '' && r1Reasoning)
          ? r1Reasoning
          : _cleanAnswer

        // Synchronous extraction — before any await — so the value is
        // available when the 'finish' SSE part fires in the route handler.
        // BUG-5: also strip the fence from cleanText so stored messages don't
        // accumulate methodology blocks on each turn.
        const mbMatch = cleanText.match(/^```marsys_methodology_block\n([\s\S]*?)\n```\n?/m)
```

**Insert the following block immediately AFTER the `let cleanText = ...` line
and BEFORE the `// Synchronous extraction` comment:**

```ts
        // BUG-C fix: if the synthesis model called a tool instead of generating
        // text (finish_reason=tool-calls), cleanText will be empty. This
        // produces a silent blank response to the user. Detect it here and
        // replace with a visible, actionable error message so the user knows
        // the pipeline failed and can retry with a different stack.
        // BUG-B's toolChoice:'none' should prevent this from occurring, but
        // this guard catches any provider that ignores toolChoice.
        if (cleanText.trim() === '' && finishReason === 'tool-calls') {
          console.error(
            '[synthesis] BUG-C: empty output — model=%s called a tool instead of generating text.' +
            ' query_id=%s output_tokens=%d. Surfacing error message to user.',
            selected_model_id,
            query_plan.query_plan_id,
            usage?.outputTokens ?? 0,
          )
          cleanText =
            `⚠️ The synthesis model (${selected_model_id}) attempted to call a retrieval tool ` +
            `during the text-generation phase instead of producing a response. ` +
            `This is a model configuration issue, not a data issue. ` +
            `Please try again — if the problem persists, switch to the Gemini stack.`
        }

        // Secondary guard: catch any other empty-output case regardless of
        // finish reason (e.g. provider timeout, content filter wipe).
        if (cleanText.trim() === '' && finishReason !== 'error') {
          console.warn(
            '[synthesis] empty output: model=%s finish=%s query_id=%s — returning placeholder.',
            selected_model_id, finishReason, query_plan.query_plan_id,
          )
          cleanText =
            `⚠️ The synthesis model returned an empty response (finish_reason=${finishReason}). ` +
            `Please try again.`
        }
```

**Verify:**
```bash
grep -n "BUG-B fix\|BUG-C fix\|BUG-E fix" platform/src/lib/synthesis/single_model_strategy.ts
# Must show all three fix comments present

grep -n "toolChoice" platform/src/lib/synthesis/single_model_strategy.ts
# Must show: toolChoice: toolsForModel ? ('none' as const) : undefined,
```

---

### STEP 4 — BUG-A: Planner empty tool_calls enforcement in `pipeline_planner.ts`

**File:** `platform/src/lib/pipeline/pipeline_planner.ts`

**Root cause:** When `deepseek-chat` returns a `PipelinePlan` with `tool_calls: []`
for a non-factual query, `callPipelinePlanner` accepts it silently and returns the
empty plan. The B.11 floor enforcement in `route.ts` injects `msr_sql` +
`cgm_graph_walk` as a safety net, but the pipeline has already lost all
planner-specified context (domains, synthesis_guidance structure, graph_seed_hints,
etc.). The planner's intent is discarded. This must be caught at the planner level
with a WARN so it is visible in logs and the observatory.

**Find the log line near the end of `callPipelinePlanner`** (unique string):

```ts
  if (process.env.NODE_ENV !== 'production') {
    console.log(
      `[pipeline_planner] callPipelinePlanner ok model=${plannerModelId} ` +
        `latency_ms=${latency_ms} tool_calls=${parsed.data.tool_calls.length} ` +
        `query_class=${parsed.data.query_class}`,
    )
  }

  return parsed.data
```

**Replace with:**

```ts
  // BUG-A fix: validate that the planner produced at least one tool call for
  // non-factual query classes. An empty tool_calls array is valid for 'factual'
  // (single-lookup, no synthesis tools needed) but indicates model non-compliance
  // for all other classes. Log a WARN so this is visible in observatory + logs.
  // B.11 floor enforcement in route.ts will inject msr_sql + cgm_graph_walk as
  // a safety net, but a WARN here ensures the gap is tracked per query.
  const FACTUAL_CLASSES = ['factual', 'cross_native'] as const
  const isTrivialClass = (FACTUAL_CLASSES as readonly string[]).includes(parsed.data.query_class)
  if (parsed.data.tool_calls.length === 0 && !isTrivialClass) {
    console.warn(
      '[pipeline_planner] BUG-A: planner returned tool_calls:[] for non-factual query.' +
      ' model=%s query_class=%s query_id=%s.' +
      ' B.11 floor will inject floor tools but planner intent is lost.' +
      ' Check PLANNER_PROMPT compliance for this model.',
      plannerModelId,
      parsed.data.query_class,
      queryId ?? 'unknown',
    )
  }

  if (process.env.NODE_ENV !== 'production') {
    console.log(
      `[pipeline_planner] callPipelinePlanner ok model=${plannerModelId} ` +
        `latency_ms=${latency_ms} tool_calls=${parsed.data.tool_calls.length} ` +
        `query_class=${parsed.data.query_class}`,
    )
  }

  return parsed.data
```

**Verify:**
```bash
grep -n "BUG-A" platform/src/lib/pipeline/pipeline_planner.ts
# Must show the new warn block present
```

---

### STEP 5 — TypeScript check

Run from the platform directory:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx tsc --noEmit
```

**Required:** zero errors in `src/`. Pre-existing test-file errors are allowed
(baseline from Pipeline-Transform-S1 module deletions — out of scope).

If `toolChoice: 'none' as const` produces a type error (some AI SDK versions
use `toolChoice: 'none'` as a plain string), try:

```ts
// Alternative if 'none' as const causes TS error:
toolChoice: toolsForModel ? 'none' : undefined,
```

If `streamText` does not accept `toolChoice` as a top-level option, check
the Vercel AI SDK version in `package.json` — in AI SDK ≥3.3 it is a
top-level `streamText` parameter; in older versions it may be nested under
`experimental_toolChoice`. Adapt accordingly and document in the commit message.

---

### STEP 6 — Final verification sweep

```bash
# BUG-D: confirm circular dep removed
grep -n "void sanskritTerms" platform/src/components/consume/ConsumeChat.tsx
# → zero matches

# BUG-D: confirm dep array is clean
grep -A2 "}, \[activeAssistantId\]" platform/src/components/consume/ConsumeChat.tsx
# → handleMarkers closing line shows [activeAssistantId] only

# BUG-E: confirm gemini-2.5 in isThinkingModel
grep -A5 "const isThinkingModel" platform/src/lib/synthesis/single_model_strategy.ts
# → second line: selected_model_id.startsWith('gemini-2.5')

# BUG-B: confirm toolChoice present
grep -n "toolChoice" platform/src/lib/synthesis/single_model_strategy.ts
# → one match in the streamText call

# BUG-C: confirm empty-output guards present
grep -n "BUG-C\|empty output\|finish_reason.*tool" platform/src/lib/synthesis/single_model_strategy.ts
# → both guards present

# BUG-A: confirm warn present
grep -n "BUG-A\|tool_calls.*\[\].*non-factual" platform/src/lib/pipeline/pipeline_planner.ts
# → warn block present

# Final TS check
cd platform && npx tsc --noEmit && echo "TSC CLEAN"
```

---

## §4 — ACCEPTANCE CRITERIA (7 items)

- [ ] **AC-1** `grep -n "void sanskritTerms" platform/src/components/consume/ConsumeChat.tsx` → zero matches; `handleMarkers` dep array contains only `activeAssistantId`.
- [ ] **AC-2** `const isThinkingModel` block in `single_model_strategy.ts` includes `selected_model_id.startsWith('gemini-2.5')` as the second condition.
- [ ] **AC-3** `streamText` call in `single_model_strategy.ts` includes `toolChoice: toolsForModel ? ('none' as const) : undefined` (or equivalent valid TypeScript for the installed AI SDK version).
- [ ] **AC-4** Two empty-output guards are present in `single_model_strategy.ts` immediately after the `let cleanText = ...` line: one targeting `finish_reason=tool-calls`, one as a general empty-output catch.
- [ ] **AC-5** `callPipelinePlanner` in `pipeline_planner.ts` emits a `console.warn` when `tool_calls.length === 0` for non-factual query classes.
- [ ] **AC-6** `cd platform && npx tsc --noEmit` exits `0` (zero errors in `src/`).
- [ ] **AC-7** `git diff --name-only` shows exactly three files changed: `platform/src/components/consume/ConsumeChat.tsx`, `platform/src/lib/synthesis/single_model_strategy.ts`, `platform/src/lib/pipeline/pipeline_planner.ts`.

---

## §5 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
platform/src/components/consume/ConsumeChat.tsx
platform/src/lib/synthesis/single_model_strategy.ts
platform/src/lib/pipeline/pipeline_planner.ts
CLAUDECODE_BRIEF.md  (set status: COMPLETE at end)
```

### must_not_touch
```
platform/tests/**                         (no test changes in this session)
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md   (prompt tuning is a separate session)
platform/src/app/api/chat/consume/route.ts
platform/src/hooks/useChatSession.ts
platform/src/components/consume/StreamingAnswer.tsx
```

---

## §6 — COMPLETION SEQUENCE

When all 7 ACs are PASS:

1. Set `status: COMPLETE` in this file's frontmatter.

2. Commit:
```bash
git add platform/src/components/consume/ConsumeChat.tsx \
        platform/src/lib/synthesis/single_model_strategy.ts \
        platform/src/lib/pipeline/pipeline_planner.ts \
        CLAUDECODE_BRIEF.md
git commit -m "fix(consume): 5-bug fix — DeepSeek blank response + Gemini render loop

BUG-D (ConsumeChat.tsx): remove 'void sanskritTerms' from handleMarkers;
  eliminates circular useCallback/useEffect dependency causing React infinite
  render loop (Maximum update depth exceeded) on Gemini responses. Root cause
  of ~50% partial render on query 5e4ed486.

BUG-E (single_model_strategy.ts): extend isThinkingModel to cover gemini-2.5-*;
  reasoning tags now stripped from Gemini synthesis output. Fixes p1_layer_separation
  FAIL on gemini-2.5-pro responses.

BUG-B (single_model_strategy.ts): add toolChoice:'none' to synthesis streamText
  call; prevents synthesis model from calling retrieval tools during text-generation
  phase. Root cause of deepseek-v4-pro finish_reason=tool-calls on query 7c847f53.

BUG-C (single_model_strategy.ts): add empty-output guard after cleanText derivation;
  surfaces visible error message instead of silent blank response when final_output
  is empty. Catches both tool-calls and other empty-finish scenarios.

BUG-A (pipeline_planner.ts): add console.warn when planner returns tool_calls:[]
  for non-factual query class; makes deepseek-chat compliance gaps visible in
  logs + observatory per query.

tsc --noEmit: exit 0 confirmed"
```

3. Push:
```bash
git push -u origin fix/consume-bugfix-s1
```

4. Notify: CONSUME-BUGFIX-S1 COMPLETE on branch `fix/consume-bugfix-s1`.

---

*CLAUDECODE_BRIEF_CONSUME_BUGFIX_S1.md · Consume module 5-bug fix · 2026-05-13*
*7 acceptance criteria across 3 files · tsc clean required*
*Fixes: DeepSeek blank output (BUG-A/B/C) + Gemini render loop (BUG-D) + reasoning tag leak (BUG-E)*
