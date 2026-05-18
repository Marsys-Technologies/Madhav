---
name: R9 — Gemini 2.5 Pro reasoning UX activation
canonical_id: CHAT_V2_R9_REASONING_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored: 2026-05-19
governing_audit: 00_ARCHITECTURE/CHAT_V2_SURFACE_AUDIT_v1_0.md §5.2
branch: feat/chat-v2-r9/gemini-pro-reasoning-activation
base: main (post-PR #92 citation overhaul, commit 9c2886f)
pr_title: "feat(chat-v2/r9): activate Gemini 2.5 Pro reasoning + thought summaries + tools-stripped thinking-synthesis path"
estimated_loc: ~+25 / -3 across 3 files
estimated_files: 3 mod
parallel_stream: standalone (no parallel batch this round)
may_touch:
  - platform/src/app/api/chat/consume/route.ts (sendReasoning:true on toUIMessageStream)
  - platform/src/lib/models/resolver.ts (googleProviderOptions: add includeThoughts:true)
  - platform/src/lib/synthesis/single_model_strategy.ts (extend isThinkingModeSynthesis to cover native-reasoning models)
must_not_touch:
  - platform/src/components/chat/ReasoningProgress.tsx (V1 consumer already wired correctly via useMessagePartReasoning)
  - platform/src/components/consume/ConsumeChatV2.tsx (Reasoning render slot already wired at L565)
  - any test file beyond minor updates necessary for the synthesis call signature
  - any other feature flag or routing override
---

# §1 Mission

Operator named the gap (2026-05-19): "Gemini 2.5 Pro is not being leveraged properly as a reasoning/thinking model. Use Gemini 2.5 Pro with its reasoning capabilities as or even better than DeepSeek V4 Pro."

Pro IS being called (registry default for `gemini` stack synthesis, with no overriding DB row). Pro's `reasoningMode: 'native'` is set correctly. `thinkingConfig.thinkingBudget: 24576` is provisioned via `googleProviderOptions`. But three concrete wiring gaps prevent Pro's reasoning from showing up in V2 chat:

**Gap A — `toUIMessageStream()` strips reasoning by default.**
The route's `writer.merge(result.toUIMessageStream({...}))` call at `route.ts` (around line 916) does NOT include `sendReasoning: true`. AI SDK v6's default for this option is `false`, so any `type:'reasoning'` parts the Google provider emits are filtered out before reaching the SSE stream. V2's `ReasoningProgress` component receives nothing.

**Gap B — Pro emits FULL reasoning paragraphs, not thought summaries.**
`thinkingConfig.thinkingBudget: 24576` allocates the budget. `thinkingConfig.includeThoughts: true` is NOT set — without it, Gemini doesn't emit the short topical "thought summaries" channel that the bullet-ticker UX needs. Currently Pro would dump 5000+ token paragraphs (per operator's DeepSeek observation: same anti-pattern). With `includeThoughts: true`, Gemini emits a separate channel of 3-4 word topical summaries alongside the raw reasoning — perfect for the ticker.

**Gap C — Pro gets tools in context with `toolChoice: 'none'`.**
`isThinkingModeSynthesis` is currently DeepSeek-specific:
```ts
const isThinkingModeSynthesis = !!deepseekProviderOptions(selected_model_id, 'synthesis')
```
This means Pro (native-reasoning) goes down the regular tool-passing path: `synthesisTools = toolsForModel`, `toolChoice: 'none'`. Pro sees the tool definitions in context but is told it can't call them. This is the same anti-pattern that DeepSeek V4 Pro thinking has — confusing for the model's reasoning. The fix: extend `isThinkingModeSynthesis` to ALL reasoning-capable models (`reasoningMode: 'native' | 'markers'`) so tools are stripped consistently.

R9 ships all three fixes. After it lands, sending any query against Gemini stack produces: bullet-ticker thought-summary stream during processing → full reasoning trace collapsible at top → answer streaming below.

# §2 Scope

| File | Action | LoC |
|---|---|---|
| `platform/src/app/api/chat/consume/route.ts` | Add `sendReasoning: true` to `toUIMessageStream({...})` call | +1 |
| `platform/src/lib/models/resolver.ts` | Add `includeThoughts: true` to `googleProviderOptions.thinkingConfig` | +1 |
| `platform/src/lib/synthesis/single_model_strategy.ts` | Extend `isThinkingModeSynthesis` to include all reasoning-capable models | +2 -1 |

Total: ~3 critical edits, ~25 LoC counting comments + a fallback safety.

# §3 Implementation specification

## §3.1 — `platform/src/app/api/chat/consume/route.ts`

**Site:** the synthesis stream merge point. Locate by the token `result.toUIMessageStream({` — should be around line 916 (post-PR #92 may have drifted slightly; grep first).

**Current:**

```ts
writer.merge(result.toUIMessageStream({
  originalMessages: messages,
  generateMessageId: createIdGenerator({ prefix: 'msg', size: 16 }),
  messageMetadata: ({ part }: { part: { type: string } }) => {
    if (part.type === 'start' && isFirstTurn) {
      return {
        // ...metadata fields...
      }
    }
    // ...
  },
}))
```

**Target:**

```ts
writer.merge(result.toUIMessageStream({
  sendReasoning: true,  // R9: forward AI SDK reasoning parts to V2's ReasoningProgress
  originalMessages: messages,
  generateMessageId: createIdGenerator({ prefix: 'msg', size: 16 }),
  messageMetadata: ({ part }: { part: { type: string } }) => {
    if (part.type === 'start' && isFirstTurn) {
      return {
        // ...metadata fields unchanged...
      }
    }
    // ...
  },
}))
```

One-line addition: `sendReasoning: true` inside the options object. Order doesn't matter; place it first for visibility (the most consequential option).

## §3.2 — `platform/src/lib/models/resolver.ts`

**Site:** the `googleProviderOptions` function body (around lines 130-150 of resolver.ts; check the actual file at execution time).

**Current** (the thinkingConfig block):

```ts
return {
  google: {
    safetySettings: [
      { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_CIVIC_INTEGRITY',   threshold: 'BLOCK_NONE' },
    ],
    thinkingConfig: {
      thinkingBudget: 24576,
    },
  },
}
```

**Target:**

```ts
return {
  google: {
    safetySettings: [
      { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
      { category: 'HARM_CATEGORY_CIVIC_INTEGRITY',   threshold: 'BLOCK_NONE' },
    ],
    thinkingConfig: {
      thinkingBudget: 24576,
      includeThoughts: true,  // R9: emit short thought-summary channel for V2 bullet ticker
    },
  },
}
```

One-line addition: `includeThoughts: true` inside `thinkingConfig`. This opts into Gemini's thought-summary channel (separate from the full reasoning text channel). The AI SDK Google provider surfaces these summaries as `type:'reasoning'` parts with a `metadata.thought: true` flag (per the @ai-sdk/google v1.x+ Gemini 2.5 contract).

If type-checking complains about `includeThoughts` being unknown on `thinkingConfig` (depending on installed `@ai-sdk/google` version), fall back to inline type assertion:

```ts
thinkingConfig: {
  thinkingBudget: 24576,
  includeThoughts: true,
} as any,
```

Use the proper type if available; fall back to `as any` only if version mismatch forces it.

## §3.3 — `platform/src/lib/synthesis/single_model_strategy.ts`

**Site:** the `isThinkingModeSynthesis` definition (around line 410 of single_model_strategy.ts).

**Current:**

```ts
const isThinkingModeSynthesis = !!deepseekProviderOptions(selected_model_id, 'synthesis')
```

**Target:**

```ts
// R9: any reasoning-capable synthesis model — DeepSeek thinking-mode (markers),
// Gemini Pro/Flash with thinkingBudget>0 (native), Claude extended thinking, etc.
// All get the no-tools treatment: tools are pre-injected via FUB-2/FUB-3 into the
// system context, so the model needs to focus solely on synthesis reasoning.
const reasoningMode = getReasoningMode(selected_model_id)
const isThinkingModeSynthesis = reasoningMode !== 'none' ||
  !!deepseekProviderOptions(selected_model_id, 'synthesis')
```

**Why both conditions:** the `getReasoningMode` check catches Pro/Flash natively. The `deepseekProviderOptions` check is preserved for backward-compat (if `deepseekProviderOptions` ever returns truthy for a model whose `reasoningMode` is mis-set to `'none'`, we still want the thinking-mode path). The first check is the primary; the OR is defensive.

The downstream `synthesisTools = isThinkingModeSynthesis ? undefined : toolsForModel` line stays unchanged — it now strips tools for Pro too.

The downstream `effectiveMaxTokens = isThinkingModeSynthesis ? ... : ...` line also stays unchanged — Pro now gets the larger thinking-mode token budget if there's a branch for that (verify by reading the surrounding 10 lines at execution time).

## §3.4 — Pre-existing pieces that DO NOT change

These already work — no edits needed:

- `gemini-2.5-pro` registry entry: `reasoningMode: 'native'`, `quirks.reasoning_via: 'native'`, `maxOutputTokens: 65_536`. All correct.
- `ConsumeChatV2.tsx:565` `Reasoning: (props) => <ReasoningProgress text={props.text} />` mounted in MessagePrimitive.Parts. Correct.
- `ReasoningProgress.tsx` uses `useMessagePartReasoning()` for live status. Correct.
- `googleProviderOptions` is already spread into `streamText`'s `providerOptions.google`. Correct.

The chain after R9:

```
Gemini 2.5 Pro server
  → emits reasoning + thought summaries (thinkingBudget=24576, includeThoughts=true)
  → AI SDK @ai-sdk/google provider parses both channels into type:'reasoning' parts
  → streamText.result.toUIMessageStream({sendReasoning: true, ...}) forwards them
  → route.ts writer.merge() pipes them into SSE
  → useChatRuntime in V2 receives them
  → MessagePrimitive.Parts.Reasoning fires
  → ReasoningProgress component renders
```

# §4 Acceptance criteria

- [ ] `grep -n 'sendReasoning: true' platform/src/app/api/chat/consume/route.ts` returns ≥1 hit.
- [ ] `grep -n 'includeThoughts: true' platform/src/lib/models/resolver.ts` returns 1 hit.
- [ ] `grep -n 'reasoningMode !== ' platform/src/lib/synthesis/single_model_strategy.ts` returns ≥1 hit (the new condition).
- [ ] `cd platform && npx tsc --noEmit` exits 0 (any type errors with `includeThoughts` get resolved per §3.2 fallback).
- [ ] `cd platform && npx eslint src/app/api/chat/consume/route.ts src/lib/models/resolver.ts src/lib/synthesis/single_model_strategy.ts` exits 0.
- [ ] `cd platform && npm test` exits 0 (no test depends on the exact `isThinkingModeSynthesis` shape that we'd break; if any do, update the test to match the new condition).
- [ ] **Manual operator verification (post-merge in dev server)**: send a query while on Gemini stack. Confirm:
  - `ReasoningProgress` component renders during streaming (not just empty).
  - Reasoning text accumulates progressively.
  - At end of stream, reasoning auto-collapses if >2000 tokens (existing behavior).
  - Final answer is at least as detailed/grounded as the operator observed from DeepSeek V4 Pro on similar queries.

# §5 Verification commands

```bash
cd platform

# Grep proofs
grep -n 'sendReasoning: true' src/app/api/chat/consume/route.ts                                    # expect ≥1
grep -n 'includeThoughts: true' src/lib/models/resolver.ts                                          # expect 1
grep -n 'reasoningMode !== ' src/lib/synthesis/single_model_strategy.ts                             # expect ≥1

# Compile + lint
npx tsc --noEmit
npx eslint src/app/api/chat/consume/route.ts src/lib/models/resolver.ts src/lib/synthesis/single_model_strategy.ts

# Existing tests
npm test

cd ..

# Operator manual smoke (post-merge)
# 1. cd platform && npm run dev
# 2. Open localhost:3000/clients/<chart>/consume in browser
# 3. Confirm Gemini stack is selected in the composer picker
# 4. Send: "What does my Mercury placement suggest about my career?"
# 5. Observe: ReasoningProgress drawer renders during streaming
# 6. Observe: At end, drawer auto-collapses with "N tokens of reasoning" affordance
# 7. Confirm: answer quality at least matches DeepSeek V4 Pro on the same query
```

# §6 Hard constraints

- DO NOT modify `ReasoningProgress.tsx` — already correct.
- DO NOT modify the V2 consumer wiring at `ConsumeChatV2.tsx:565`.
- DO NOT modify the registry's `gemini-2.5-pro` entry — already `reasoningMode: 'native'`.
- DO NOT modify any other model's `reasoningMode` in the registry.
- DO NOT touch the synthesis prompt or `CITATION_APPENDIX` (PR #92 territory).
- DO NOT modify `getEffectiveStack` or `llm_stack_config` — that's the active_stack cleanup, separate work.
- DO NOT auto-merge if any gate fails.

# §7 Risks + mitigations

| Risk | Mitigation |
|---|---|
| AI SDK Google provider version doesn't expose `includeThoughts` in `thinkingConfig` type | §3.2 fallback: use `as any` to bypass type-check if needed. Runtime behavior depends on the underlying provider; the option flows through to Gemini's API verbatim. Verify by inspecting network response in dev server for `thoughtSummary` content. |
| Pro thinking on long Jyotish queries hits the 65536 output cap and truncates the final answer | Pro's `maxOutputTokens: 65_536`. With `thinkingBudget=24576`, the answer gets ~40K tokens. Long queries are rare; if truncation observed, increase `maxOutputTokens` on Pro's registry row. R9 doesn't change this; flag as R10 if it shows up. |
| Stripping tools for Pro causes Pro to halucinate tool data | Tools are pre-injected into the system context via FUB-2/FUB-3 (chart data + retrieved bundle). Pro receives all relevant data in the prompt; stripping the tool definitions just prevents tool-calling, not data access. Same pattern works for DeepSeek thinking — no hallucination risk demonstrated there. |
| `isThinkingModeSynthesis` change affects `effectiveMaxTokens` calculation in a way that under-budgets Pro | Verify by reading the `effectiveMaxTokens` line (a few lines below the isThinkingModeSynthesis definition). If it's `isThinkingModeSynthesis ? HIGH : LOW`, Pro gets HIGH (correct). If it's reversed somehow, Pro gets squeezed. Adjust accordingly. |
| `sendReasoning: true` flag name varies across AI SDK v6 minor versions | If TS complains about `sendReasoning` being unknown, check alternates: `forwardReasoning`, `enableReasoning`, `experimental_sendReasoning`. The current ai package is `@^6.0.168` per `package.json`. Confirm against the installed version's UIMessageStream options interface. |
| The route handler's `result.toUIMessageStream` signature has changed since PR #92 (citation overhaul rebased onto it) | Verify by reading the call site post-clone. The `sendReasoning` option should be inside the options object; if signature shape changed, adapt. |

# §8 PR description template

```
## What this PR fixes

Operator named the gap (2026-05-19): Gemini 2.5 Pro should leverage its reasoning capabilities and reach V2's ReasoningProgress UI. Currently Pro is being called correctly but its reasoning never reaches the browser.

Three precise wiring gaps closed:

1. **`toUIMessageStream` default-drops reasoning.** Added `sendReasoning: true` to the options object in route.ts. AI SDK v6 default is false; without this, type:'reasoning' parts the Google provider emits are filtered out before SSE.

2. **No thought-summary channel.** Added `includeThoughts: true` to `googleProviderOptions.thinkingConfig`. Gemini API emits a separate channel of 3-4 word topical summaries alongside the full reasoning paragraphs — needed for the bullet-ticker UX pattern the operator described (ChatGPT o1 / Gemini Thinking / Grok Thinking style).

3. **Pro was getting tools-with-toolChoice-none.** Extended `isThinkingModeSynthesis` to cover ALL reasoning-capable models (`reasoningMode: 'native' | 'markers'`), not just DeepSeek. Pro now goes down the same no-tools path: tools are pre-injected into the system context via FUB-2/FUB-3; the model focuses solely on synthesis reasoning.

## What's already correct (no edits needed)

- `gemini-2.5-pro` registry entry: `reasoningMode: 'native'`, `quirks.reasoning_via: 'native'`, `maxOutputTokens: 65_536`.
- `googleProviderOptions.thinkingConfig.thinkingBudget: 24576`.
- `ConsumeChatV2.tsx:565` Reasoning render slot mounted in MessagePrimitive.Parts.
- `ReasoningProgress.tsx` uses `useMessagePartReasoning()` for live status.

The chain post-R9:

```
Gemini 2.5 Pro → reasoning + thought summaries
  → @ai-sdk/google parses both channels into type:'reasoning' parts
  → streamText.result.toUIMessageStream({sendReasoning:true}) forwards
  → route writer.merge() pipes into SSE
  → V2 useChatRuntime receives
  → MessagePrimitive.Parts.Reasoning fires
  → ReasoningProgress renders
```

## Files touched

- MOD `platform/src/app/api/chat/consume/route.ts` (+1 LoC — sendReasoning:true)
- MOD `platform/src/lib/models/resolver.ts` (+1 LoC — includeThoughts:true)
- MOD `platform/src/lib/synthesis/single_model_strategy.ts` (+2 -1 — extended isThinkingModeSynthesis)

Net: ~+3 LoC. Smallest possible change for the biggest visible UX impact.

## Manual verification post-merge

1. `cd platform && npm run dev`
2. Open `http://localhost:3000/clients/<chart>/consume`
3. Confirm Gemini stack is selected in the composer
4. Send: "What does my Mercury placement suggest about my career?"
5. Observe: ReasoningProgress drawer renders during streaming, accumulates text, auto-collapses at end if >2000 tokens.
6. Confirm answer quality matches/exceeds DeepSeek V4 Pro baseline on similar queries.

## Refs

- `00_ARCHITECTURE/chat_v2_briefs/round9/R9-gemini-pro-reasoning-activation.md` (this brief)
- `00_ARCHITECTURE/CHAT_V2_SURFACE_AUDIT_v1_0.md` §5.2 (reasoning gap diagnosis)
- Operator decision 2026-05-19: prioritize Gemini Pro reasoning activation
```

# §9 Post-merge follow-ups

After R9 lands:

1. **Manual smoke against a real Gemini Pro query** — confirms the three wiring fixes work end-to-end.

2. **Bullet-ticker component (R9.B, separate brief if needed)**: the current `ReasoningProgress` renders full reasoning text. If thought summaries arrive as separate parts (per Gemini API contract), V2 could split them: bullet ticker for thought summaries + collapsible drawer for full reasoning. This is a UX polish that depends on what shape the AI SDK Google provider surfaces them as. After R9, inspect the SSE stream in dev tools; if thought summaries arrive as `reasoning` parts with a `metadata.thought:true` flag, split the rendering. ~30 LoC.

3. **`active_stack` cleanup (separate work)** — the dead-config issue where `llm_stack_config.active_stack='anthropic'` is set but the consume route doesn't honor it. Either delete/change the DB row to `gemini` or document explicitly that active_stack is informational. Per operator decision deferred.

# §10 Changelog

- **v1.0 (2026-05-19, READY_FOR_EXECUTION)** — Three precise wiring fixes (sendReasoning, includeThoughts, isThinkingModeSynthesis extension). Minimum-viable activation of Gemini Pro reasoning UX. R9.B (bullet-ticker thought-summary split) deferred to post-merge inspection of AI SDK Google provider behavior.
