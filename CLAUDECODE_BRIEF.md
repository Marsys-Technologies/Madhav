---
status: OPEN
session_id: AIOPS_AD_3
phase: AD.3
phase_name: "Five provider adapters — full implementations + streaming buffers"
next_session: AIOPS_AD_4
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_2_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_AD_3
## AIOps Phase 2, Step 3 — Implement all 5 provider adapters

---

## §0 — Executor orientation

AD.3 is the heaviest sub-phase. Replaces the 5 stub adapters with full
implementations: input transform, provider invocation, output normalization,
streaming buffer logic. After AD.3, calling `streamAdapter` with real
credentials produces actual streaming `ModelInteractionEvent`s end-to-end
for every provider.

Master plan §6 has the per-provider spec for each adapter. Read it fully
before starting.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_2/AIOPS_PHASE_2_MASTER_PLAN_v1_0.md §6 (FULL)
3. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
4. platform/src/lib/adapters/types.ts
5. platform/src/lib/adapters/dispatcher.ts
6. platform/src/lib/models/registry.ts (quirks per model)
7. platform/src/lib/models/resolver.ts (current deepseekProviderOptions, googleProviderOptions — copy patterns)
8. platform/src/lib/synthesis/think_block_filter.ts (existing DeepSeek marker parsing — will be replaced)
9. platform/src/lib/llm/providers/*_observed.ts (observed wrappers — adapters CALL these)
10. existing usage in platform/src/lib/synthesis/single_model_strategy.ts (the most heavyweight current consumer)
```

---

## §2 — Scope

### may_touch
```
platform/src/lib/adapters/providers/*.ts      # replace stubs with implementations
platform/src/lib/adapters/buffer.ts           # NEW — marker buffer for <think> parsing
platform/src/lib/adapters/__tests__/providers/* # NEW — per-provider tests
CLAUDECODE_BRIEF.md
```

### must_not_touch
- platform/src/lib/llm/providers/*_observed.ts — observed wrappers stay untouched
- platform/src/lib/models/resolver.ts — kept intact until AD.4
- platform/src/lib/synthesis/** — call sites migrate in AD.4
- platform/src/lib/synthesis/think_block_filter.ts — deleted in AD.4, not here

---

## §3 — Work plan

### 3.1 — Shared streaming-marker buffer

`platform/src/lib/adapters/buffer.ts`:

A reusable utility for parsing `<think>…</think>` (or any open/close marker
pair) from a streaming text source and emitting two channels: pre-marker /
in-marker / post-marker.

```ts
export class MarkerBuffer {
  private state: 'before' | 'inside' | 'after' = 'before'
  private buffer = ''
  private readonly openTag: string
  private readonly closeTag: string

  constructor(openTag = '<think>', closeTag = '</think>') {
    this.openTag = openTag
    this.closeTag = closeTag
  }

  /** Feed a chunk and get back emitted segments. */
  feed(chunk: string): { reasoning?: string; text?: string } {
    // Append to buffer, scan for tags, advance state, emit appropriate segments.
    // Returns whatever portion is now safe to emit (i.e., we've passed the tag
    // we were looking for, or we know for sure no tag is in the buffered range).
  }

  /** Flush at end-of-stream. If still 'inside', emit remaining buffer as reasoning. */
  flush(): { reasoning?: string; text?: string; unclosed?: boolean } { ... }
}
```

≥15 tests covering edge cases: no markers, markers split across chunks,
back-to-back markers, unclosed markers, malformed markers, empty stream.

### 3.2 — adapter_deepseek.ts

```ts
import { deepseek } from '@ai-sdk/deepseek'
import { streamText } from 'ai'
import type { Adapter } from './base'
import type { QueryRequest, ModelInteractionEvent } from '../types'
import type { ModelMeta } from '@/lib/models/registry'
import { MarkerBuffer } from '../buffer'

export const adapterDeepseek: Adapter = {
  providerId: 'deepseek',
  stream(req: QueryRequest, meta: ModelMeta): ReadableStream<ModelInteractionEvent> {
    return new ReadableStream({
      async start(controller) {
        const ts = () => Date.now()
        controller.enqueue({ type: 'status', ts: ts(), status: 'queued' })

        // Build providerOptions per quirks
        const wantsThinking = req.reasoning !== 'disable'
          && meta.quirks.request_transforms?.thinking_mode === 'toggle'
        const providerOptions = wantsThinking
          ? { deepseek: { thinking: { type: 'enabled' as const } } }
          : undefined

        controller.enqueue({ type: 'status', ts: ts(), status: 'reasoning' })

        const buffer = new MarkerBuffer('<think>', '</think>')
        const startTime = ts()
        let inputTokens = 0
        let outputTokens = 0
        let reasoningTokens = 0

        try {
          const result = await streamText({
            model: deepseek(meta.id),
            system: req.systemPrompt,
            messages: req.messages,
            providerOptions,
            maxOutputTokens: req.maxOutputTokens ?? meta.maxOutputTokens,
            temperature: req.temperature,
            tools: req.tools as any,
          })

          let composing = false
          for await (const part of result.fullStream) {
            if (part.type === 'text-delta') {
              const out = buffer.feed(part.text)
              if (out.reasoning) {
                controller.enqueue({ type: 'reasoning_delta', ts: ts(), text: out.reasoning })
              }
              if (out.text) {
                if (!composing) {
                  controller.enqueue({ type: 'status', ts: ts(), status: 'composing' })
                  composing = true
                }
                controller.enqueue({ type: 'text_delta', ts: ts(), text: out.text })
              }
            }
            // ... handle tool-call parts, finish part, etc.
          }

          const flushed = buffer.flush()
          if (flushed.reasoning) {
            controller.enqueue({ type: 'reasoning_delta', ts: ts(), text: flushed.reasoning })
          }
          if (flushed.text) {
            controller.enqueue({ type: 'text_delta', ts: ts(), text: flushed.text })
          }

          const usage = await result.usage
          inputTokens = usage.inputTokens ?? 0
          outputTokens = usage.outputTokens ?? 0
          reasoningTokens = (usage as any).reasoningTokens ?? 0

          controller.enqueue({ type: 'status', ts: ts(), status: 'complete' })
          controller.enqueue({
            type: 'finish',
            ts: ts(),
            interaction: {
              modelId: meta.id,
              provider: meta.provider,
              reasoning: undefined,  // already emitted as deltas
              intermediate: [],       // tool calls handled in deltas above
              finalText: undefined,   // already emitted as deltas
              finishReason: 'stop',
              usage: {
                inputTokens,
                outputTokens,
                reasoningTokens,
                costUsd: computeCost(meta, inputTokens, outputTokens),
                latencyMs: ts() - startTime,
              },
              providerMeta: { requestId: result.providerMetadata?.deepseek?.requestId, raw: undefined, ...(flushed.unclosed && { reasoning_unclosed: true }) },
            },
          })
        } catch (err) {
          controller.enqueue({ type: 'error', ts: ts(), error: { message: String(err) } })
        }
        controller.close()
      },
    })
  },
}

function computeCost(meta: ModelMeta, inp: number, out: number): number {
  return (inp / 1_000_000) * meta.costPer1MInput + (out / 1_000_000) * meta.costPer1MOutput
}
```

### 3.3 — adapter_gemini.ts

Similar shape. Key differences:
- Always set `providerOptions.google.safetySettings` (all 5 categories `BLOCK_NONE`).
- Set `thinkingConfig.thinkingBudget` from `meta.quirks.request_transforms.thinking_budget`.
- Reasoning arrives via `fullStream` parts of `type: 'reasoning'` (or wherever the Gemini SDK exposes thinking). Map those directly to `reasoning_delta` events — no marker buffer needed.
- Handle structured output via `request.responseSchema` → `responseSchema` provider option.

### 3.4 — adapter_anthropic.ts

- `system` becomes `[{ type: 'text', text: req.systemPrompt, cache_control: { type: 'ephemeral' } }]` when `meta.quirks.cache_strategy === 'explicit_headers'`.
- No reasoning emission (`reasoning_via: 'none'`).
- Tools transformed to Anthropic tool format.

### 3.5 — adapter_openai.ts

- Standard OpenAI Chat Completions shape.
- Structured output via `response_format: { type: 'json_schema', ... }` when `request.responseSchema` is present.
- No reasoning emission today; TODO comment for future o-series.

### 3.6 — adapter_nim.ts

- OpenAI-compat endpoint. Reuse OpenAI request shaping with NIM-specific overrides:
  - Always set `stream: true` (NIM requires).
  - Catch `PlannerCompatibilityError` from `nvidia.ts` and re-throw inside the stream as an `error` event.
  - For NIM models with `reasoning_via: 'markers'` (DeepSeek-on-NIM), use the same MarkerBuffer as direct DeepSeek.

### 3.7 — Per-provider tests

For each adapter, `platform/src/lib/adapters/__tests__/providers/adapter_<provider>.test.ts`:

- Mock the provider SDK using vitest's mocking facilities (no real LLM calls in unit tests).
- Test that the input is transformed correctly (e.g., DeepSeek thinking enabled → providerOptions.deepseek.thinking.type='enabled').
- Test that the output stream emits the right event sequence: queued → reasoning → reasoning_delta(s) → composing → text_delta(s) → complete → finish.
- Test that reasoning models actually emit `reasoning_delta`; non-reasoning models do NOT.
- Test error paths: provider error → `error` event emitted; stream closes.
- ≥8 cases per adapter = ≥40 total.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.AD3.1 | All 5 adapter stubs replaced with implementations | grep `not yet implemented` in providers/*.ts returns 0 |
| AC.AD3.2 | MarkerBuffer tests pass | ≥15 cases |
| AC.AD3.3 | Per-adapter tests pass | ≥40 cases (≥8 each × 5) |
| AC.AD3.4 | Reasoning emission matches reasoning_via | parametrized test: emit iff quirks.reasoning_via !== 'none' |
| AC.AD3.5 | Error path emits `error` event and closes stream | per-adapter assertion |
| AC.AD3.6 | typecheck + lint + full test suite green | exit 0 each |
| AC.AD3.7 | scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Final commit:
```
feat(aiops-AD.3): implement all 5 provider adapters

- adapter_deepseek: <think> marker buffer, thinking-mode toggle, native usage
- adapter_gemini: safety BLOCK_NONE, thinkingBudget, native reasoning parts
- adapter_anthropic: system block array, cache_control headers, no reasoning
- adapter_openai: structured output via json_schema, automatic caching
- adapter_nim: OpenAI-compat with stream:true required, PlannerCompatibilityError handling
- MarkerBuffer utility (shared between deepseek + nim DeepSeek-on-NIM)
- 55+ new tests; all 5 adapters mocked + asserted

AC summary: 7/7 PASS
```

Rotate brief → AD.4.

---

## §7 — BAIL OUT triggers

- Provider SDK shape changed since registry comments were written (e.g., Gemini SDK no longer exposes `type: 'reasoning'` parts) — bail and let native investigate.
- MarkerBuffer logic has an irreducible ambiguity (e.g., `<think>` appears inside a code block in the model's output) — bail and let native shape the rule.

---

*End of PHASE_AD_3_BRIEF.md*
