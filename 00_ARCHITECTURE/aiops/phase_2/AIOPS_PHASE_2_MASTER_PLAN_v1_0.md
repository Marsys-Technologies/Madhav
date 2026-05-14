---
artifact: AIOPS_PHASE_2_MASTER_PLAN_v1_0.md
canonical_id: AIOPS_PHASE_2_MASTER_PLAN
version: 1.0
status: AWAITING_NATIVE_GO
phase: AIOps-AD (Adapter Layer)
authored_at: 2026-05-14
authored_by: Cowork brainstorm session (Opus 4.7)
predecessor: 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md (Phase 1 — SHIPPED 2026-05-13)
execution_rules: 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md (reused from Phase 1)
related:
  - 00_ARCHITECTURE/aiops/phase_2/briefs/PHASE_AD_0_BRIEF.md … PHASE_AD_5_BRIEF.md
  - 00_ARCHITECTURE/aiops/phase_3/AIOPS_PHASE_3_MASTER_PLAN_v1_0.md (downstream)
trigger_protocol: >
  Native approves this plan, then copies
  00_ARCHITECTURE/aiops/phase_2/briefs/PHASE_AD_0_BRIEF.md
  to project root as CLAUDECODE_BRIEF.md and triggers Claude Code with
  --dangerously-skip-permissions. The harness then executes AD.0 → AD.5
  sequentially with no further native involvement until the final cutover
  acceptance gate at the end of AD.5.
changelog:
  - v1.0 (2026-05-14): initial master plan; native-approved Q1–Q10 decisions baked in.
---

# AIOps Phase 2 — Adapter Layer
## Master Plan v1.0

---

## §0 — TL;DR

Phase 2 introduces a single boundary — the **Adapter Layer** — that normalizes
provider-specific behavior into one abstract contract. Today, DeepSeek's
thinking-mode toggle, Gemini's `thinkingBudget` + safety settings, Anthropic's
system blocks + cache headers, OpenAI's structured outputs, and NIM's
OpenAI-compat quirks each leak into call sites in slightly different ways. As
of Phase 1, there are six stacks. Without a centralizing layer, every stack
addition and every model change ripples through `resolver.ts`,
`single_model_strategy.ts`, `panel/adjudicator.ts`, `consume/route.ts`, plus
the eval scripts and probe runner.

The adapter:

1. Accepts an abstract `QueryRequest` (system prompt, messages, tools, schema, call type, reasoning preference). No provider-specific fields.
2. Looks up the resolved model's `ProviderQuirks` (a new metadata layer that extends `reasoningMode`).
3. Transforms the request into the provider's exact wire shape.
4. Invokes the provider via the existing observed wrappers (no change to observability).
5. Parses the response into a normalized `ModelInteraction` with typed fields for `reasoning`, `intermediate` (tool calls + status), `finalText` / `finalStructured`, `usage`, `providerMeta`.
6. For streaming, emits typed `ModelInteractionEvent`s the UI consumes uniformly.

After Phase 2 lands, no call site outside `lib/adapters/` contains a
`if (provider === 'deepseek')` branch. The Phase 3 UI overhaul has a clean,
typed stream of events to render against.

Six sub-phases AD.0 → AD.5. Same autonomous-execution pattern as Phase 1
under `AIOPS_EXECUTION_RULES_v1_0.md`.

---

## §1 — The problem in concrete terms

Examples of what leaks today:

`platform/src/lib/models/resolver.ts`:
- `deepseekProviderOptions(modelId, mode)` — returns the DeepSeek-specific `providerOptions.deepseek.thinking.type` for V4 Pro only.
- `googleProviderOptions(modelId)` — returns Google's `safetySettings` array + `thinkingConfig.thinkingBudget`.

`platform/src/lib/synthesis/think_block_filter.ts`:
- Parses DeepSeek's `<think>…</think>` blocks out of the streamed text.

`platform/src/lib/components/consume/LiveReasoningCard.tsx`:
- Renders reasoning differently for `reasoning_via: 'markers'` (DeepSeek) vs `'native'` (Gemini SDK reasoning parts).

`platform/src/lib/models/registry.ts`:
- `reasoningMode: ReasoningMode` on every entry, used by the consume UI to gate reasoning extraction.

`platform/src/lib/synthesis/single_model_strategy.ts` and `panel/member_runner.ts`:
- Both have to thread `deepseekProviderOptions` / `googleProviderOptions` into `streamText` calls.

These knowledge points are spread across at least 8 files. Every new model
quirk requires updating call sites in lockstep. Phase 2 collapses them into
one module: `platform/src/lib/adapters/`.

---

## §2 — Design philosophy

Five principles:

1. **One boundary, one contract.** All LLM calls in the codebase go through `runAdapter()`. The function returns a `ModelInteraction` (or a stream of `ModelInteractionEvent`s). Provider details are entirely behind it.

2. **Provider quirks are data, not code.** Every model's quirks live in `registry.ts` as a structured `ProviderQuirks` object. Adapters read this data and act accordingly. Adding a new model is editing one entry, not editing five files.

3. **Streaming and non-streaming are unified.** The non-streaming path is implemented as `await streamingPath.tee().final()`. One mental model.

4. **No silent normalization loss.** Provider-specific fields the abstract contract doesn't cover (e.g., Anthropic's cache_creation token counts) are preserved verbatim in `providerMeta` so future consumers can use them.

5. **Backward-compatible during cutover.** The flag `ADAPTERS_ENABLED` gates the new path. Flag-off, the system behaves identically to today. Flip in AD.5 after stack-smoke parity is confirmed.

---

## §3 — ProviderQuirks taxonomy

Extend the `ModelMeta` interface in `platform/src/lib/models/registry.ts`:

```ts
export interface ProviderQuirks {
  // How does reasoning surface in the model output?
  reasoning_via: 'markers' | 'native' | 'none'

  // Streaming-required (e.g., NIM OpenAI-compat) or optional?
  streaming_required: boolean

  // Does this model accept tool_choice / response_format?
  tool_use_format: 'openai' | 'anthropic' | 'gemini' | 'none'
  structured_output_format: 'json_schema' | 'json_object' | 'gemini_response_schema' | 'none'

  // Caching strategy.
  cache_strategy: 'automatic' | 'explicit_headers' | 'context_caching' | 'none'

  // System prompt placement.
  system_prompt_shape: 'inline' | 'system_message' | 'system_block_array'

  // Provider-specific request transforms keyed by purpose.
  // e.g., DeepSeek V4 Pro: { thinking_mode: 'toggle' }
  //       Gemini 2.5:      { safety_filter: 'block_none_required', thinking_budget: 'cap' }
  //       Anthropic:       { cache_headers: 'required_for_repeated_prompts' }
  request_transforms?: Record<string, unknown>
}
```

For each existing model, fill in the `quirks` field. Examples:

```ts
// claude-haiku-4-5
quirks: {
  reasoning_via: 'none',
  streaming_required: false,
  tool_use_format: 'anthropic',
  structured_output_format: 'json_schema',
  cache_strategy: 'explicit_headers',
  system_prompt_shape: 'system_block_array',
}

// deepseek-v4-pro
quirks: {
  reasoning_via: 'markers',
  streaming_required: false,
  tool_use_format: 'openai',
  structured_output_format: 'json_object',
  cache_strategy: 'none',
  system_prompt_shape: 'system_message',
  request_transforms: { thinking_mode: 'toggle' },
}

// gemini-2.5-pro
quirks: {
  reasoning_via: 'native',
  streaming_required: false,
  tool_use_format: 'gemini',
  structured_output_format: 'gemini_response_schema',
  cache_strategy: 'context_caching',
  system_prompt_shape: 'system_message',
  request_transforms: { safety_filter: 'block_none', thinking_budget: 32768 },
}
```

The `reasoningMode` field is preserved (it's already in use); `quirks.reasoning_via` carries the same value redundantly until Phase 2's call-site migration deletes the old field in AD.4.

---

## §4 — Abstract shapes

`platform/src/lib/adapters/types.ts`:

```ts
export interface QueryRequest {
  // What model serves this call?
  callType: CallType
  stack?: ModelStack                        // optional override; defaults to active stack
  modelOverride?: { modelId: string }       // for probes + tests

  // Content
  systemPrompt: string
  messages: Array<{ role: 'user' | 'assistant'; content: string }>

  // Optional capabilities
  tools?: ToolDefinition[]                  // tool-use functions
  responseSchema?: JSONSchema               // structured output

  // Knobs
  maxOutputTokens?: number                  // overrides default
  temperature?: number
  reasoning?: 'auto' | 'enable' | 'disable' // 'auto' = whatever model wants
  timeoutMs?: number

  // Pass-through metadata for observability
  traceId?: string
  userId?: string
  parentEventId?: string
}

export interface ToolDefinition {
  name: string
  description: string
  parameters: JSONSchema
}

export interface ModelInteraction {
  modelId: string
  provider: Provider

  reasoning?: { text: string; tokens: number }
  intermediate: Array<IntermediateEvent>
  finalText?: string
  finalStructured?: unknown

  finishReason: 'stop' | 'length' | 'tool_calls' | 'content_filter' | 'error'
  usage: {
    inputTokens: number
    outputTokens: number
    reasoningTokens?: number
    cacheReadTokens?: number
    cacheWriteTokens?: number
    costUsd: number
    latencyMs: number
  }
  providerMeta: {
    requestId?: string
    raw?: unknown    // verbatim provider response for debugging
  }
}

export interface IntermediateEvent {
  type: 'tool_call' | 'tool_result' | 'status'
  ts: number
  payload: unknown
}

export type ModelInteractionEvent =
  | { type: 'status'; ts: number; status: 'queued' | 'planning' | 'retrieving' | 'reasoning' | 'tool_calling' | 'composing' | 'complete' }
  | { type: 'reasoning_delta'; ts: number; text: string }
  | { type: 'tool_call'; ts: number; name: string; args: unknown; callId: string }
  | { type: 'tool_result'; ts: number; callId: string; result: unknown }
  | { type: 'text_delta'; ts: number; text: string }
  | { type: 'finish'; ts: number; interaction: ModelInteraction }
  | { type: 'error'; ts: number; error: { message: string; code?: string } }
```

Note: `IntermediateEvent` is the *aggregated* in-memory shape (used by
non-streaming consumers). `ModelInteractionEvent` is the *streaming* shape
(emitted by the adapter's stream variant).

---

## §5 — Streaming model

Two functions exposed by `lib/adapters/`:

```ts
// Non-streaming: collects the stream and returns the final interaction.
export async function runAdapter(req: QueryRequest): Promise<ModelInteraction>

// Streaming: returns a ReadableStream of typed events.
export function streamAdapter(req: QueryRequest): ReadableStream<ModelInteractionEvent>
```

Internally `runAdapter` calls `streamAdapter` and collects events. The
streaming path is the authoritative implementation; the non-streaming path
is a thin convenience wrapper.

**Event emission rules:**

- `status: 'queued'` emitted on stream open.
- `status: 'reasoning'` emitted when the adapter detects the model has started reasoning (e.g., first `<think>` tag in DeepSeek; first `type:'reasoning'` part in Gemini).
- `reasoning_delta` emitted progressively as reasoning text accumulates.
- `status: 'composing'` emitted when text-out begins.
- `text_delta` emitted progressively.
- `tool_call` + `tool_result` emitted as they happen.
- `status: 'complete'` + `finish` emitted at stream end with the assembled `ModelInteraction`.

For models with `reasoning_via: 'none'`, no `reasoning_delta` events are
emitted (no false-positive empty reasoning panels in the UI).

---

## §6 — Provider-specific adapters

Five files under `platform/src/lib/adapters/providers/`:

### §6.1 — `adapter_anthropic.ts`

- Transforms `QueryRequest` into Anthropic Messages API shape: `system: <string>` becomes `system: [{ type: 'text', text: <string>, cache_control: { type: 'ephemeral' } }]` when `cache_strategy === 'explicit_headers'`.
- Tools transformed into Anthropic's tool format.
- Reasoning: Anthropic models (Sonnet, Opus, Haiku) don't surface reasoning today. `reasoning_via: 'none'` → no reasoning emission.
- Note: hidden behind cost-confirmation modal in production per standing rule.

### §6.2 — `adapter_deepseek.ts`

- Transforms into DeepSeek's chat completions shape.
- For `deepseek-v4-pro` with `reasoning: 'auto' | 'enable'`: sets `providerOptions.deepseek.thinking.type = 'enabled'`. With `'disable'`: sets `'disabled'`.
- Reasoning parsing: V4 Pro emits `<think>…</think>` markers in the stream. Adapter buffers from `<think>` to `</think>` and emits as `reasoning_delta` events; flush remainder as text_delta after `</think>`.
- Edge: model never emits `</think>` (we've seen this). Finalizer flushes the buffered reasoning at stream end with a `reasoning_unclosed: true` flag in `providerMeta`.

### §6.3 — `adapter_gemini.ts`

- Transforms into Gemini's content shape (system as `systemInstruction`).
- Always sets `providerOptions.google.safetySettings` with all categories `BLOCK_NONE` (Jyotish content triggers default filters; not negotiable).
- For 2.5 Pro/Flash with `reasoning: 'auto' | 'enable'`: sets `thinkingConfig.thinkingBudget` from registry quirks (32768 default).
- Reasoning parsing: Gemini SDK emits `type: 'reasoning'` UIMessage parts. Adapter maps these directly to `reasoning_delta` events.
- Structured output: Gemini's `responseSchema` is set when `request.responseSchema` is present.

### §6.4 — `adapter_openai.ts`

- Transforms into OpenAI Chat Completions shape.
- Structured output: sets `response_format: { type: 'json_schema', json_schema: ... }` when applicable.
- Caching: automatic on the OpenAI side; no headers needed.
- Reasoning: GPT-4.1 has `reasoning_via: 'none'` today. (Future o-series models may have `'native'` — leave a TODO comment with reference to ProviderQuirks extension.)

### §6.5 — `adapter_nim.ts`

- OpenAI-compatible endpoint at `https://integrate.api.nvidia.com/v1`. Reuses OpenAI request shaping with NIM-specific overrides.
- Always sets `stream: true` (NIM requires it on the managed catalog endpoint).
- Tool-use rejection patterns: if NIM returns "does not support tool_choice / response_format", surface as `PlannerCompatibilityError` (already defined in `nvidia.ts`).
- Reasoning: most NIM models have `reasoning_via: 'none'`. Nemotron variants and DeepSeek-V4-on-NIM (if it returns to active) have `'markers'` — same `<think>` buffer logic as direct DeepSeek.

### Dispatcher (`platform/src/lib/adapters/index.ts`)

```ts
export function streamAdapter(req: QueryRequest): ReadableStream<ModelInteractionEvent> {
  const modelId = req.modelOverride?.modelId ?? resolveModelForCallType(req.callType, req.stack)
  const meta = getModelMeta(modelId)
  if (!meta) throw new Error(`Unknown model: ${modelId}`)
  const adapter = adapterFor(meta.provider)
  return adapter.stream(req, meta)
}

function adapterFor(provider: Provider): Adapter {
  switch (provider) {
    case 'anthropic': return adapterAnthropic
    case 'deepseek':  return adapterDeepseek
    case 'google':    return adapterGemini
    case 'openai':    return adapterOpenai
    case 'nvidia':    return adapterNim
  }
}
```

---

## §7 — MARSYS handling

MARSYS stack lets users mix providers per call type. The adapter dispatcher
already routes based on the *model's* provider (looked up via `getModelMeta`),
not the *stack's* provider. So MARSYS works automatically — the only
constraint is that `runtime_config.ts` (Phase 1) correctly resolves a model
for the MARSYS call type before the adapter is invoked.

Tests: parametrize across all 6 stacks × 11 call types × {primary, fallback}
= 132 dispatches; assert the correct adapter is selected each time.

---

## §8 — Call-site migration plan

Migrate every direct call to `streamText` or `generateText` (from `ai` SDK)
to use `runAdapter` / `streamAdapter` instead. Inventory before migration:

```
platform/src/lib/synthesis/single_model_strategy.ts
platform/src/lib/synthesis/panel/member_runner.ts
platform/src/lib/synthesis/panel/adjudicator.ts
platform/src/lib/synthesis/orchestrator.ts
platform/src/app/api/chat/consume/route.ts
platform/src/lib/aiops/probe/runner.ts
platform/scripts/aiops/cutover_smoke.ts
platform/scripts/aiops/probe_health_cron.ts
platform/scripts/eval/* (answer_eval.ts and friends)
platform/scripts/checkpoint/*
```

Plus delete (or thin to ID-only):
- `deepseekProviderOptions` in `resolver.ts`
- `googleProviderOptions` in `resolver.ts`
- `think_block_filter.ts` (functionality moved into `adapter_deepseek.ts`)

Migration is mechanical. Each site goes from:

```ts
// before
const meta = getModelMeta(modelId)
const model = resolveModel(modelId)
const providerOpts = deepseekProviderOptions(modelId, 'synthesis')
const result = await streamText({
  model,
  system: systemPrompt,
  messages,
  providerOptions: providerOpts,
  ...
})
```

To:

```ts
// after
const interaction = await runAdapter({
  callType: 'synthesis',
  systemPrompt,
  messages,
  reasoning: 'auto',
  // ... knobs as needed
})
// or for streaming:
const stream = streamAdapter({ ... })
```

---

## §9 — Feature flag

`ADAPTERS_ENABLED` (default false through AD.4; flipped in AD.5 after
stack-smoke parity confirms behavior is unchanged).

Flag-off path: every `runAdapter` / `streamAdapter` call short-circuits to
the legacy `streamText`-with-providerOptions path. The legacy code is
preserved in a `legacy_runAdapter.ts` module during the cutover window;
removed in the flag-removal PR scheduled 2 weeks after flip.

---

## §10 — Sub-phase arc

| Phase | Scope | Brief |
|---|---|---|
| **AD.0** | Branch + design doc + skeleton module + types | `phase_2/briefs/PHASE_AD_0_BRIEF.md` |
| **AD.1** | ProviderQuirks registry extension (every model entry) + tests | `phase_2/briefs/PHASE_AD_1_BRIEF.md` |
| **AD.2** | Abstract shapes + dispatcher + non-streaming wrapper | `phase_2/briefs/PHASE_AD_2_BRIEF.md` |
| **AD.3** | Five provider adapters + streaming buffer logic + finalizer | `phase_2/briefs/PHASE_AD_3_BRIEF.md` |
| **AD.4** | Call-site migration + legacy-path preservation + flag-off equivalence | `phase_2/briefs/PHASE_AD_4_BRIEF.md` |
| **AD.5** | Cutover smoke + flag flip + 48h watch + flag-removal scheduled | `phase_2/briefs/PHASE_AD_5_BRIEF.md` |

Each brief is self-contained and machine-executable. Same loop pattern as
Phase 1: brief rotates `CLAUDECODE_BRIEF.md` on close to point at the next
phase; Claude Code re-launches with the trigger prompt and continues.

---

## §11 — Branch + scope boundaries

**Branch:** `feature/aiops-phase-2-adapters`, cut from `main`.

```yaml
may_touch:
  - platform/src/lib/adapters/**                          # NEW module
  - platform/src/lib/models/registry.ts                   # add quirks field
  - platform/src/lib/models/resolver.ts                   # thin to ID-only after AD.4
  - platform/src/lib/synthesis/**                         # call-site migration
  - platform/src/app/api/chat/consume/**                  # call-site migration
  - platform/src/app/api/admin/aiops/probe/**             # call-site migration
  - platform/src/lib/aiops/probe/**                       # call-site migration
  - platform/scripts/aiops/**                             # call-site migration
  - platform/scripts/eval/**                              # call-site migration
  - platform/scripts/checkpoint/**                        # call-site migration
  - platform/src/lib/config/feature_flags.ts              # add ADAPTERS_ENABLED
  - .github/workflows/deploy.yml                          # add ADAPTERS_ENABLED env var (AD.5)
  - 00_ARCHITECTURE/aiops/phase_2/**                      # docs
  - CLAUDECODE_BRIEF.md                                   # session-handoff updates

must_not_touch:
  - 01_FACTS_LAYER/**
  - 025_HOLISTIC_SYNTHESIS/**
  - 06_LEARNING_LAYER/**
  - platform/src/components/consume/**                    # Phase 3 territory
  - platform/src/app/api/admin/observatory/**             # sealed
  - platform/src/lib/components/observatory/**            # sealed
  - 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
  - 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md
  - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md
  - 00_ARCHITECTURE/OBSERVATORY_PLAN_v1_0.md
  - 00_ARCHITECTURE/aiops/AIOPS_MASTER_PLAN_v1_0.md       # Phase 1 — sealed
  - 00_ARCHITECTURE/aiops/phase_briefs/**                 # Phase 1 — sealed
```

---

## §12 — Definition of done

Phase 2 is **DONE** when, after AD.5 closes:

- [ ] All six AD briefs CLOSED.
- [ ] `ADAPTERS_ENABLED=true` in production.
- [ ] Every model in registry has a populated `quirks: ProviderQuirks` field.
- [ ] Every LLM call site outside `lib/adapters/` and `legacy_runAdapter.ts` goes through `runAdapter` / `streamAdapter`.
- [ ] Flag-off equivalence tests: 35+ snapshots match exactly.
- [ ] Stack smoke (post-flip): pass rate within 1 probe of pre-flip baseline.
- [ ] `think_block_filter.ts`, `deepseekProviderOptions`, `googleProviderOptions` deleted or marked deprecated.
- [ ] 48h watch on `/consume` latency + error rate + cost: no regressions.
- [ ] Flag-removal PR scheduled 2 weeks post-flip.

---

## §13 — Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Streaming buffer eats long reasoning blocks | HIGH | Adapter buffers in chunks of ≤4096 chars; flushes early on `</think>` detection OR when buffer overflows; finalizer at stream end |
| `</think>` never arrives (DeepSeek bug) | MED | Finalizer flushes buffered content as reasoning with `reasoning_unclosed: true` flag |
| MARSYS routes through wrong adapter | MED | Parametrized test across 132 (stack × call_type × role) combos; CI gate |
| Panel mode (3 LLMs in parallel) breaks under streaming | HIGH | Each panel member gets its own `streamAdapter` invocation; adjudicator also uses streamAdapter; tested in AD.4 with panel-mode fixture |
| `resolver.ts` migration breaks an unrelated caller | MED | AD.4 keeps `resolveModel(id)` (ID → LanguageModel) intact for any caller that hasn't migrated; only delete provider-options helpers |
| Observability changes / regressions | HIGH | Observed wrappers are NOT touched by Phase 2. Adapters call them; their behavior is identical |
| Flag flip causes production regression | HIGH | Flag-off path preserved through AD.5; 48h watch; one-command rollback `gcloud run services update --remove-env-vars ADAPTERS_ENABLED` |

---

## §14 — Forward compatibility with Phase 3

Phase 3 consumes Phase 2's `ModelInteractionEvent` stream. Specific
commitments Phase 2 makes to keep Phase 3 unblocked:

- The `ModelInteractionEvent` type union is the public contract. Phase 3
  components subscribe to it. Phase 2 will not change the type union once
  AD.5 lands.
- `reasoning_via: 'none'` → no `reasoning_delta` events. Phase 3 uses this
  invariant to hide the reasoning slot for non-reasoning models.
- `status` events are emitted in canonical order: `queued → planning →
  retrieving → reasoning → tool_calling → composing → complete`. Some
  states are skipped if not relevant (e.g., no `reasoning` for non-reasoning
  models). Phase 3 builds a state machine on this ordering.
- Per-message metadata (model, cost, latency, tokens) arrives in
  `ModelInteraction.usage`. Phase 3's per-message badges read these.

---

## §15 — Trigger protocol

Same as Phase 1's:

1. Native approves this master plan + the six AD briefs.
2. Native copies `00_ARCHITECTURE/aiops/phase_2/briefs/PHASE_AD_0_BRIEF.md` to project root as `CLAUDECODE_BRIEF.md`.
3. Native triggers Claude Code in `../madhav-phase-2-tmp` (a new transient worktree) with `--dangerously-skip-permissions`.
4. Claude Code executes the AD.0 → AD.5 loop, rotating `CLAUDECODE_BRIEF.md` on each phase close.
5. Final acceptance gate at AD.5 close — same checklist pattern as Phase 1's `CP5_NATIVE_ACCEPTANCE.md`.

---

## §16 — Native acceptance checklist (review before triggering AD.0)

- [ ] Six stacks + 11 call types + ProviderQuirks taxonomy as specified are correct
- [ ] ModelInteractionEvent type union is the right surface (additions OK; removals after AD.5 are forbidden)
- [ ] Branch name `feature/aiops-phase-2-adapters` is acceptable
- [ ] Autonomous execution via bypass-permissions Claude Code is the right approach
- [ ] No M5, 01_FACTS_LAYER, 06_LEARNING_LAYER, or Phase 3 component touchpoints
- [ ] I have read at least PHASE_AD_0_BRIEF and PHASE_AD_1_BRIEF and confirm the execution detail is sufficient

When checked, native gives "go" and the trigger protocol in §15 runs.

---

*End of AIOPS_PHASE_2_MASTER_PLAN_v1_0.md*
