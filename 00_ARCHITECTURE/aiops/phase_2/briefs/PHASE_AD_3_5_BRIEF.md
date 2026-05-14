---
status: OPEN
session_id: AIOPS_AD_3_5
phase: AD.3.5
phase_name: "Adapter capability extension — multi-step, toolChoice, smoothStream, callbacks, raw entry point"
next_session: AIOPS_AD_4
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0 (remediation after AD.4 HALTED at d83e792)
predecessor: PHASE_AD_3_BRIEF.md (committed f92f898)
remediates: PHASE_AD_4_BRIEF.md (HALTED at d83e792 — AC.AD4.2 unreachable with AD.3 adapter shape)
---

# CLAUDECODE_BRIEF — AIOPS_AD_3_5
## AIOps Phase 2, Step 3.5 — Adapter capability extension

---

## §0 — Executor orientation

You are executing AD.3.5, a remediation sub-phase inserted between AD.3 and
AD.4 to address the architectural boundary surfaced by the AD.4 BAIL OUT
at commit `d83e792`. The bail-out documented that several call sites cannot
migrate to the adapter as designed in AD.0/AD.2/AD.3 because they need:

  1. **Multi-step tool use** (`stopWhen: stepCountIs(N)` + `onStepFinish`).
     Used by: `synthesis/single_model_strategy.ts`, `synthesis/panel_strategy.ts`,
     `synthesis/panel/member_runner.ts`, `synthesis/panel/adjudicator.ts`.
  2. **Tool choice** forcing (`toolChoice: 'required' | { type: 'tool', toolName }`).
     Used by: `pipeline/pipeline_planner.ts`.
  3. **Text-delta smoothing** (`smoothStream`).
     Used by: `synthesis/single_model_strategy.ts`.
  4. **Per-call audit callback** at stream end (`onFinish({ usage, ... })`).
     Used by: `synthesis/single_model_strategy.ts`.
  5. **Direct `StreamTextResult` access** for `.toUIMessageStreamResponse()`
     SSE piping to the HTTP response.
     Used by: `app/api/chat/consume/route.ts`, `app/api/chat/build/route.ts`.

AD.3.5 extends the adapter to support all five, and updates AD.4's brief
with the per-call-site migration pattern. After AD.3.5 closes, AD.4 becomes
achievable as originally specified.

The /Users/Dev/Vibe-Coding/Apps/Madhav worktree (M5 branch) is never touched.

YOU MUST NOT call any LLM provider during this session.
YOU MUST NOT migrate any call site in this session (that's AD.4's job).
YOU MUST NOT proceed past any FAIL — bail per §8.

---

## §1 — Mandatory reads

```
1.  CLAUDE.md
2.  00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md §4 (QueryRequest shape), §6 (per-adapter spec)
3.  00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4.  Current adapter implementations (AD.3 deliverables — DO NOT REWRITE; only EXTEND):
       platform/src/lib/adapters/types.ts
       platform/src/lib/adapters/providers/adapter_anthropic.ts
       platform/src/lib/adapters/providers/adapter_deepseek.ts
       platform/src/lib/adapters/providers/adapter_gemini.ts
       platform/src/lib/adapters/providers/adapter_openai.ts
       platform/src/lib/adapters/providers/adapter_nim.ts
       platform/src/lib/adapters/providers/base.ts
       platform/src/lib/adapters/run_adapter.ts
       platform/src/lib/adapters/stream_adapter.ts
       platform/src/lib/adapters/event_collector.ts
       platform/src/lib/adapters/dispatcher.ts
5.  Call site samples to validate the design works (read but do NOT migrate):
       platform/src/lib/synthesis/single_model_strategy.ts (lines 380–470)
       platform/src/app/api/chat/consume/route.ts
       platform/src/lib/pipeline/pipeline_planner.ts (lines 200–260)
6.  AI SDK 4.x documentation for: streamText return type (StreamTextResult), stopWhen, smoothStream, onStepFinish, onFinish, toolChoice
7.  HALTED CLAUDECODE_BRIEF.md (the `bail_out` block has the precise inventory)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/adapters/types.ts                 # extend QueryRequest
platform/src/lib/adapters/providers/*.ts           # extend stream() to honor new fields; expose prepareRequest()
platform/src/lib/adapters/providers/base.ts        # update Adapter interface (add prepareRequest)
platform/src/lib/adapters/raw.ts                   # NEW — streamAdapterRaw entry point
platform/src/lib/adapters/index.ts                 # export streamAdapterRaw
platform/src/lib/adapters/__tests__/**             # add tests for the new capabilities
00_ARCHITECTURE/aiops/phase_2/briefs/PHASE_AD_4_BRIEF.md  # patch §3.4 migration table at session close
CLAUDECODE_BRIEF.md                                # rotate to AD.4 at session close
```

### must_not_touch
```
platform/src/lib/synthesis/**                      # AD.4 territory
platform/src/app/api/chat/**                       # AD.4 territory
platform/src/lib/pipeline/**                       # AD.4 territory
platform/src/lib/aiops/**                          # AD.4 territory
platform/src/lib/components/**                     # Phase 3 territory
platform/src/lib/models/registry.ts                # AD.1 territory — DO NOT MODIFY
platform/src/lib/llm/providers/*_observed.ts       # adapters call these; do not modify
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**
```

---

## §3 — Work plan

### 3.1 — Extend QueryRequest

Edit `platform/src/lib/adapters/types.ts`. Add the following fields to
`QueryRequest` (all optional, additive — no breaking changes to AD.0–AD.3
callers):

```ts
export interface QueryRequest {
  // ... all existing fields preserved ...

  /**
   * Multi-step agentic loop. When set, the adapter calls streamText with
   * stopWhen: stepCountIs(maxSteps). Each tool round-trip emits a
   * tool_call event followed by a tool_result event; intermediate text
   * deltas emit between rounds as the model interleaves reasoning with
   * tool calls.
   *
   * Used by synthesis/single_model_strategy.ts and the panel_strategy +
   * panel/member_runner + panel/adjudicator agentic loops.
   */
  multiStep?: {
    maxSteps: number
  }

  /**
   * Tool choice forcing. Passed through to streamText.toolChoice.
   * Provider-specific shape is handled by the adapter's prepareRequest.
   *
   * Used by pipeline/pipeline_planner.ts.
   */
  toolChoice?: 'auto' | 'none' | 'required' | { type: 'tool'; toolName: string }

  /**
   * Enable AI SDK text-delta smoothing. Passed through to streamText
   * experimental_transform: smoothStream(). Makes streamed text feel more
   * natural in real-time UIs.
   *
   * Used by synthesis/single_model_strategy.ts.
   */
  smoothStream?: boolean

  /**
   * Per-step callback for multi-step loops. Adapter wires this to
   * streamText.onStepFinish. Called after each tool round-trip with
   * step-level usage and metadata.
   *
   * Synthesis path uses this for per-step audit event capture.
   */
  onStepFinish?: (step: {
    text: string
    toolCalls: unknown[]
    toolResults: unknown[]
    usage: { inputTokens: number; outputTokens: number; totalTokens: number }
    finishReason: string
    stepType: string
  }) => Promise<void> | void

  /**
   * Final callback called once at stream end with the assembled
   * ModelInteraction. Adapter wires this AFTER the finish event is
   * emitted on the stream.
   *
   * Synthesis path uses this for end-of-call audit event capture.
   */
  onFinish?: (interaction: ModelInteraction) => Promise<void> | void
}
```

All five fields are optional. Existing callers (probe/runner.ts,
checkpoints/*.ts, etc.) need no changes — they'll continue to work because
they don't set these fields.

### 3.2 — Refactor each provider adapter

Goal: extract a `prepareRequest(req, meta)` method on each adapter that
returns the streamText options object. The existing `stream()` method
continues to work — it calls `prepareRequest` internally to build options.
This refactor enables a new `streamAdapterRaw` entry point (§3.3) that
needs access to the same streamText options to construct a raw call.

In `platform/src/lib/adapters/providers/base.ts`, extend the Adapter
interface:

```ts
import type { StreamTextResult } from 'ai'
import type { ModelMeta } from '@/lib/models/registry'
import type { QueryRequest, ModelInteractionEvent } from '../types'

export interface StreamTextOptions {
  model: unknown  // LanguageModel from ai
  system?: string
  messages: unknown[]
  tools?: unknown
  toolChoice?: unknown
  providerOptions?: Record<string, unknown>
  maxOutputTokens?: number
  temperature?: number
  stopWhen?: unknown
  experimental_transform?: unknown
  onStepFinish?: (step: unknown) => Promise<void> | void
  onFinish?: (info: unknown) => Promise<void> | void
}

export interface Adapter {
  readonly providerId: string

  /** Build the streamText options object for this provider + request. */
  prepareRequest(req: QueryRequest, meta: ModelMeta): StreamTextOptions

  /** Stream the model's response as ModelInteractionEvents (existing AD.3 behavior). */
  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent>
}
```

For each of the 5 adapters (anthropic, deepseek, gemini, openai, nim):

1. **Extract the existing streamText options-building code into a new
   `prepareRequest(req, meta)` method.** The method returns the
   `StreamTextOptions` object — model, system, messages, providerOptions,
   maxOutputTokens, temperature, tools.

2. **Extend `prepareRequest` to honor the new fields:**
   - `req.multiStep` → set `stopWhen: stepCountIs(req.multiStep.maxSteps)`. Import `stepCountIs` from `ai`.
   - `req.toolChoice` → set `toolChoice` per the provider's tool_use_format quirks:
     - `'openai'` / `'nim'`: pass through directly
     - `'anthropic'`: map `'required'` → `{ type: 'any' }`, etc. (per Anthropic Messages API)
     - `'gemini'`: map per Google's toolConfig
     - `'none'` providers: throw error if toolChoice provided
   - `req.smoothStream` → set `experimental_transform: smoothStream()`. Import from `ai`.
   - `req.onStepFinish` → wire as `onStepFinish` callback. Type-cast as needed.
   - `req.onFinish` → store on a side-channel for the adapter's stream() to invoke after emitting the `finish` event. (Not passed directly to streamText — the adapter calls it after collecting the ModelInteraction so the callback receives the typed `ModelInteraction`, not AI SDK's raw `onFinish` arg.)

3. **Update the existing `stream()` method to use `prepareRequest`:** instead of inlining the options-building, call `prepareRequest(req, meta)` to get the options object, then pass to streamText. Preserves all AD.3 behavior.

4. **Update `stream()` to honor the new fields where applicable in the event stream:**
   - For `multiStep`: emit `tool_call` + `tool_result` events as they arrive (existing logic from AD.3 may already do this via `fullStream`; verify).
   - For `onStepFinish`: the AI SDK invokes the callback during streamText execution; nothing for the adapter to do beyond passing it through in §2.
   - For `onFinish`: after the `finish` event is enqueued on the stream, call `req.onFinish(interaction)` if provided. Await before closing the controller.

### 3.3 — New entry point: `streamAdapterRaw`

Create `platform/src/lib/adapters/raw.ts`:

```ts
import 'server-only'
import { streamText, type StreamTextResult } from 'ai'
import type { QueryRequest } from './types'
import type { ModelMeta } from '@/lib/models/registry'
import { getModelMeta } from '@/lib/models/registry'
import { resolveModel } from '@/lib/models/resolver'
import { adapterFor } from './dispatcher'

export interface RawAdapterResult {
  /** AI SDK StreamTextResult — caller can use .toUIMessageStreamResponse(), .fullStream, etc. */
  result: StreamTextResult<any, any>
  /** Model meta for cost/usage attribution. */
  meta: ModelMeta
}

/**
 * Low-level adapter entry point. Builds provider-correct streamText options
 * for the requested call type + model, invokes streamText, and returns the
 * AI SDK result directly to the caller. The caller is responsible for
 * consuming the result (e.g., via result.toUIMessageStreamResponse() for
 * SSE piping to consume/route, or by reading result.fullStream for custom
 * event handling in synthesis's stopWhen loop).
 *
 * The adapter's provider-quirk transforms (DeepSeek thinking, Gemini
 * safety, Anthropic system blocks, NIM stream:true, etc.) are still
 * applied — the caller never has to touch providerOptions directly.
 */
export function streamAdapterRaw(req: QueryRequest): RawAdapterResult {
  const modelId = req.modelOverride?.modelId
    ?? resolveModelForCallType(req.callType, req.stack)
  const meta = getModelMeta(modelId)
  if (!meta) throw new Error(`streamAdapterRaw: unknown model ${modelId}`)

  const adapter = adapterFor(meta.provider)
  const options = adapter.prepareRequest(req, meta)

  const result = streamText({
    ...options,
    model: resolveModel(meta.id),  // ensure model is resolved with the right SDK
  } as Parameters<typeof streamText>[0])

  return { result, meta }
}

// (resolveModelForCallType is the same helper used by streamAdapter — extract to shared util if not already)
```

Export from `platform/src/lib/adapters/index.ts`:

```ts
export { streamAdapterRaw } from './raw'
export type { RawAdapterResult } from './raw'
```

### 3.4 — Patch AD.4 brief

At session close (§7), update `00_ARCHITECTURE/aiops/phase_2/briefs/PHASE_AD_4_BRIEF.md`
§3.4 to replace the single-pattern migration example with the three-entry-point
table below. The patch must be additive — don't delete other sections.

Replacement content for AD.4 §3.4 (insert after the existing "Migration is
mechanical" paragraph, before "Migrate in this order"):

```markdown
### Three adapter entry points — choose per call site type:

| Call site pattern | Entry point | Why |
|---|---|---|
| `generateText({ ... })` — single-shot non-streaming, with or without tools | `runAdapter(req)` | Collects the stream into a `ModelInteraction`. Synchronous-feeling API. |
| `streamText({ ... })` — single-shot streaming consumed by custom event handlers (not AI SDK UI) | `streamAdapter(req)` | Returns `ReadableStream<ModelInteractionEvent>` with typed events. |
| `streamText({ ... })` — agentic loop with `stopWhen: stepCountIs(N)`, OR streaming response piped via `result.toUIMessageStreamResponse()` to SSE | `streamAdapterRaw(req)` → `{ result, meta }` | Returns the AI SDK `StreamTextResult` directly. Caller uses `.toUIMessageStreamResponse()` (SSE) or reads `.fullStream` (custom multi-step handling). Provider quirks still applied by the adapter. |

#### Per-site migration pattern map:

| Call site | Entry point | Key options to pass |
|---|---|---|
| `synthesis/single_model_strategy.ts` (multi-step + audit) | `streamAdapterRaw` | `multiStep: { maxSteps: 5 }`, `smoothStream: true`, `onStepFinish`, `onFinish` |
| `synthesis/panel_strategy.ts` (panel verbatim passthrough) | `streamAdapterRaw` | `multiStep` as needed; caller pipes `result` to its own consumer |
| `synthesis/panel/member_runner.ts` (single panel member) | `runAdapter` | tools, temperature |
| `synthesis/panel/adjudicator.ts` (final adjudication) | `runAdapter` | tools (if any), responseSchema (if structured output) |
| `pipeline/pipeline_planner.ts` (tool-choice required) | `runAdapter` | `tools`, `toolChoice: 'required'` (or `{ type: 'tool', toolName }`) |
| `pipeline/planner_context_builder.ts` (single generateText for context) | `runAdapter` | no special options |
| `app/api/chat/consume/route.ts` (SSE pipe) | `streamAdapterRaw` | `multiStep` (synthesis under it), `onStepFinish`, `onFinish` for audit; then `return result.toUIMessageStreamResponse()` |
| `app/api/chat/build/route.ts` (SSE pipe) | `streamAdapterRaw` | same SSE pattern |
| `aiops/probe/runner.ts` | `runAdapter` | minimal — single call, no tools |
| `checkpoints/checkpoint_{4_5,5_5,8_5}.ts` | `runAdapter` | minimal |
| `conversations/title.ts` | `runAdapter` | minimal |
| `models/health.ts` | `runAdapter` | minimal |
| `scripts/retrieval/test_classify.ts` | `runAdapter` | as needed |
```

This table goes into AD.4's brief as part of the AD.3.5 session-close work.

### 3.5 — Tests

Add tests under `platform/src/lib/adapters/__tests__/`:

- `multi_step.test.ts` — multi-step tool use round-trip
- `tool_choice.test.ts` — toolChoice per provider mapping
- `smooth_stream.test.ts` — smoothStream passthrough
- `callbacks.test.ts` — onStepFinish + onFinish wiring
- `raw_entry.test.ts` — streamAdapterRaw returns the expected shape
- `equivalence.test.ts` — verify that for a call with NONE of the new fields set, behavior is identical to AD.3 (regression guard for the existing 260-test suite)

Minimum new tests: ≥40.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD3.5.1 | QueryRequest has 5 new optional fields (multiStep, toolChoice, smoothStream, onStepFinish, onFinish) | grep |
| AC.AD3.5.2 | All 5 adapter implementations expose `prepareRequest(req, meta)` | grep per file |
| AC.AD3.5.3 | `prepareRequest` honors all new fields | parametrized tests pass |
| AC.AD3.5.4 | `streamAdapterRaw` exists and exports `{ result, meta }` shape | grep + types |
| AC.AD3.5.5 | New tests added (≥40) | test count |
| AC.AD3.5.6 | AD.3 regression: 260 existing tests still pass | full suite |
| AC.AD3.5.7 | AD.4 brief §3.4 patched with three-entry-points table | grep |
| AC.AD3.5.8 | typecheck + lint clean | exit 0 each |
| AC.AD3.5.9 | scope-violation grep | SCOPE_OK |

---

## §5 — Test minimums

- multi_step.test.ts: ≥8 cases (per provider × stop conditions × tool round-trips)
- tool_choice.test.ts: ≥10 cases (per provider × choice variants × validation)
- smooth_stream.test.ts: ≥4 cases (on/off × providers that support it)
- callbacks.test.ts: ≥8 cases (onStepFinish wiring + onFinish wiring + cancellation behavior + async)
- raw_entry.test.ts: ≥6 cases (per provider returns correct shape; provider quirks applied)
- equivalence.test.ts: ≥10 parametrized cases asserting AD.3-shaped requests produce identical streams

Total ≥ 46.

---

## §6 — Session close (rotation to AD.4)

Standard procedure per AIOPS_EXECUTION_RULES §R4 + §R5:

1. Final commit message:
   ```
   feat(aiops-AD.3.5): adapter capability extension — multi-step, toolChoice, smoothStream, callbacks, streamAdapterRaw

   Extends the adapter contract to cover the call-site patterns AD.4 needs:

   - QueryRequest gains 5 optional fields:
     multiStep, toolChoice, smoothStream, onStepFinish, onFinish.
   - Each provider adapter (anthropic, deepseek, gemini, openai, nim) exposes
     prepareRequest(req, meta) that builds the streamText options object,
     honoring all new fields with provider-correct quirks.
   - New entry point streamAdapterRaw(req) returns { result, meta } where
     result is the AI SDK StreamTextResult — for callers piping
     toUIMessageStreamResponse() to SSE or running multi-step loops over
     result.fullStream.
   - AD.4 brief §3.4 patched with the three-entry-points migration table.
   - 46+ new tests; AD.3's 260 tests still pass.

   AC summary: 9/9 PASS
   ```

2. Update `00_ARCHITECTURE/aiops/phase_2/briefs/PHASE_AD_4_BRIEF.md` with
   the patch from §3.4 above (insert before the existing "Migrate in this
   order" list).

3. Rotate `CLAUDECODE_BRIEF.md`: copy the patched PHASE_AD_4_BRIEF.md
   contents (with `status: OPEN` at the top) into the root
   `CLAUDECODE_BRIEF.md`.

4. Commit the rotation:
   ```
   chore(aiops): rotate brief — AIOPS_AD_4 ready (post-3.5)
   ```

5. Report: `[AIOPS-CLOSE] phase=AD.3.5 status=CLOSED next_phase=AD.4`

---

## §7 — BAIL OUT triggers (AD.3.5 specific)

- The AI SDK version pinned in `platform/package.json` doesn't expose
  `smoothStream` or `stepCountIs` — bail and let native upgrade the SDK
  first.
- A provider's tool_choice format isn't documented or our `quirks`
  metadata is wrong (e.g., we say `tool_use_format: 'anthropic'` but the
  Anthropic API has changed) — bail and let native verify.
- The `prepareRequest` refactor causes a regression in any of AD.3's 260
  tests that can't be fixed by mechanical re-wiring (i.e., the refactor
  reveals a hidden contract mismatch) — bail and let native investigate.

---

## §8 — Hard constraints

  - Additive only. Every change to QueryRequest is a new optional field.
    AD.3's existing callers (probe, etc.) must continue to work unchanged.
  - No call site migration in this session. AD.4 does that.
  - Provider-quirk metadata (`quirks` field on each ModelMeta from AD.1)
    is the source of truth for per-provider transforms. Don't hardcode
    new switch statements; consult quirks.
  - LLM stack discipline: Gemini → DeepSeek → NIM. No Anthropic API calls
    during execution.

Begin with §3.1.

*End of PHASE_AD_3_5_BRIEF.md*
