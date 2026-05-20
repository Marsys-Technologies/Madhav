---
session_id: OBS-S1
title: Observatory — Data Pipeline Wiring
status: COMPLETE
phase: OBS-S1
executor: Anti-Gravity (Claude Code, claude-sonnet-4-6)
created_date: 2026-05-05
reference_plan: 00_ARCHITECTURE/OBSERVATORY_REDESIGN_PLAN_v1_0.md §3.1
---

# OBS-S1 — Observatory Data Pipeline Wiring

## Objective

Wire the two live LLM hot paths (synthesis + planner) so every AI SDK call emits one
row into `llm_usage_events`. After this session the Observatory Overview page shows
real token counts, call counts, and computed cost for every query sent through the portal.

Today neither path writes to `llm_usage_events`. The synthesis `onFinish` has an explicit
`// TODO(G.2): cost_usd is null` comment. The planner success path only writes to
`llm_call_log`. The Observatory queries exclusively from `llm_usage_events` and therefore
always shows zeros.

---

## Scope

```
may_touch:
  - platform/src/lib/llm/observability/types.ts
  - platform/src/lib/synthesis/single_model_strategy.ts
  - platform/src/lib/pipeline/manifest_planner.ts

must_not_touch:
  - platform/src/lib/llm/observability/persist.ts       # already correct — do not change
  - platform/src/lib/llm/observability/cost.ts          # already correct — do not change
  - platform/src/lib/llm/observability/observe.ts       # already correct — do not change
  - platform/src/lib/db/monitoring-write.ts             # existing monitoring — do not change
  - platform/src/lib/observatory/                       # query layer — do not change
  - platform/src/lib/components/observatory/           # UI — not this session
  - platform/src/app/(super-admin)/observatory/        # routes — not this session
  - platform/src/app/api/admin/observatory/            # API — not this session
  - any migration files
```

---

## Task 1 — Add 'planner' to PipelineStage union

**File:** `platform/src/lib/llm/observability/types.ts`

Find:
```typescript
export type PipelineStage =
  | 'classify'
  | 'compose'
  | 'retrieve'
  | 'synthesize'
  | 'audit'
  | 'other'
```

Replace with:
```typescript
export type PipelineStage =
  | 'classify'
  | 'compose'
  | 'retrieve'
  | 'synthesize'
  | 'planner'
  | 'audit'
  | 'other'
```

No other changes to `types.ts`.

---

## Task 2 — Wire synthesis onFinish to persistObservation

**File:** `platform/src/lib/synthesis/single_model_strategy.ts`

### 2a — Add imports at the top of the file

After the existing import from `@/lib/db/monitoring-write`, add:

```typescript
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'
```

### 2b — Inside the `onFinish` callback, after the existing `void writeLlmCallLog(...)` block

Locate the `void writeLlmCallLog({...})` call (around line 531). Immediately **after** the closing `})` of that call, insert the following block. Keep it as fire-and-forget (`void`). Never `await` it on the critical path.

```typescript
        // OBS-S1: Observatory per-call telemetry (synthesis stage)
        // Fire-and-forget — must not block the response stream.
        {
          const obsStartedAt = new Date(synthesisStartMs)
          const obsFinishedAt = new Date(synthesisStartMs + synthesisLatencyMs)
          const obsUsage: TokenUsage = {
            input_tokens: usage?.inputTokens ?? 0,
            output_tokens: usage?.outputTokens ?? 0,
            cache_read_tokens: (usage as { cacheReadInputTokens?: number })?.cacheReadInputTokens ?? 0,
            cache_write_tokens: (usage as { cacheCreationInputTokens?: number })?.cacheCreationInputTokens ?? 0,
            reasoning_tokens: isThinkingModel && r1Reasoning ? Math.ceil(r1Reasoning.length / 4) : 0,
          }
          const obsProvider = (resolveProvider(selected_model_id) ?? 'unknown') as ProviderName
          const obsDb = getStorageClient()
          void (async () => {
            const costResult = await computeCost(
              obsProvider,
              selected_model_id,
              obsUsage,
              obsStartedAt,
              obsDb,
            ).catch(() => null)
            await persistObservation(
              {
                provider: obsProvider,
                model: selected_model_id,
                prompt_text: null,
                system_prompt: null,
                parameters: { model: selected_model_id, temperature: synthesisTemperature },
                conversation_id: conversation_id ?? query_plan.query_plan_id,
                conversation_name: null,
                prompt_id: `${query_plan.query_plan_id}:synthesis`,
                user_id: 'native',
                pipeline_stage: 'synthesize',
              },
              {
                response_text: null,
                usage: obsUsage,
                status: finishReason === 'error' ? 'error' : 'success',
                error_code: finishReason === 'error' ? finishReason : undefined,
                started_at: obsStartedAt,
                finished_at: obsFinishedAt,
              },
              costResult,
              obsDb,
            )
          })()
        }
```

**Important:** `synthesisTemperature` is already in scope. `synthesisLatencyMs` is already computed at the top of `onFinish`. `synthesisStartMs` is a closure variable from the outer `synthesize()` scope. `conversation_id` is also in closure scope.

---

## Task 3 — Wire planner success path to persistObservation

**File:** `platform/src/lib/pipeline/manifest_planner.ts`

### 3a — Add imports at the top of the file

After the existing `import { writeLlmCallLog, resolveProvider } from '@/lib/db/monitoring-write'`, add:

```typescript
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'
```

### 3b — In the planner success path, after the existing writeLlmCallLog block

Find the success-path `writeLlmCallLog` block. It looks like:

```typescript
  if (queryId) {
    void writeLlmCallLog({
      query_id: queryId,
      conversation_id: null,
      call_stage: 'planner',
      model_id: activeModelId,
      provider: resolveProvider(activeModelId),
      input_tokens: result.usage?.inputTokens ?? null,
      output_tokens: result.usage?.outputTokens ?? null,
      reasoning_tokens: null,
      latency_ms,
      cost_usd: null,
      fallback_used: fallbackWasUsed,
      error_code: null,
      payload: null,
    })
  }
```

Immediately **after** the closing `}` of that `if (queryId)` block, insert:

```typescript
  // OBS-S1: Observatory per-call telemetry (planner stage)
  // Fire-and-forget — must not add latency to the planning path.
  {
    const obsStartedAt = new Date(start)
    const obsFinishedAt = new Date(start + latency_ms)
    const obsUsage: TokenUsage = {
      input_tokens: result.usage?.inputTokens ?? 0,
      output_tokens: result.usage?.outputTokens ?? 0,
      cache_read_tokens: 0,
      cache_write_tokens: 0,
      reasoning_tokens: 0,
    }
    const obsProvider = (resolveProvider(activeModelId) ?? 'unknown') as ProviderName
    const obsDb = getStorageClient()
    void (async () => {
      const costResult = await computeCost(
        obsProvider,
        activeModelId,
        obsUsage,
        obsStartedAt,
        obsDb,
      ).catch(() => null)
      await persistObservation(
        {
          provider: obsProvider,
          model: activeModelId,
          prompt_text: null,
          system_prompt: null,
          parameters: { model: activeModelId, temperature: 0, fallback_used: fallbackWasUsed },
          conversation_id: queryId ?? nativeId,
          conversation_name: null,
          prompt_id: `${queryId ?? nativeId}:planner`,
          user_id: 'native',
          pipeline_stage: 'planner',
        },
        {
          response_text: null,
          usage: obsUsage,
          status: 'success',
          started_at: obsStartedAt,
          finished_at: obsFinishedAt,
        },
        costResult,
        obsDb,
      )
    })()
  }
```

**Important:** `start` is the `const start = Date.now()` declared at the top of the retry loop, already in scope. `latency_ms` is `const latency_ms = Date.now() - start` already computed. `nativeId` is in scope from the outer `callLlmPlanner` function parameters.

---

## Task 4 — Verify pricing seed

Check whether `llm_pricing_versions` has been seeded in production by looking at the seed file path. Do NOT run the seed automatically — just confirm the seed script exists and print the command the native should run manually if needed.

**File to check:** `platform/src/lib/db/seed/observatory_pricing/seed_v1.ts`

At the end of your work, output a clearly marked block:

```
═══════════════════════════════════════════════════════
PRICING SEED COMMAND (run once against production DB):
  cd platform
  NEXT_PUBLIC_DATABASE_URL=$DATABASE_URL npx tsx src/lib/db/seed/observatory_pricing/seed_v1.ts
═══════════════════════════════════════════════════════
```

---

## Task 5 — TypeScript check

Run `cd platform && npx tsc --noEmit 2>&1 | tail -30`. All synthesis and planner related type errors must be zero. If you see type errors in the files you touched, fix them. Pre-existing errors in unrelated files are acceptable.

---

## Task 6 — Run affected tests

```bash
cd platform && npx vitest run \
  src/lib/llm/__tests__/observability_persist.test.ts \
  src/lib/llm/__tests__/observability_cost.test.ts \
  --reporter=verbose 2>&1 | tail -40
```

These tests must still pass. Do not modify the test files.

---

## Acceptance Criteria

All must be confirmed before this session closes.

| AC | Check |
|---|---|
| AC.S1.1 | `platform/src/lib/llm/observability/types.ts` — PipelineStage union includes `'planner'` |
| AC.S1.2 | `single_model_strategy.ts` `onFinish` — contains `persistObservation` call after `writeLlmCallLog` |
| AC.S1.3 | `manifest_planner.ts` success path — contains `persistObservation` call after the success `writeLlmCallLog` block |
| AC.S1.4 | Both new Observatory blocks are `void (async () => { ... })()` — fire-and-forget, never blocking |
| AC.S1.5 | `tsc --noEmit` exits 0 (or only pre-existing errors in unrelated files) |
| AC.S1.6 | `observability_persist.test.ts` and `observability_cost.test.ts` still pass |
| AC.S1.7 | Pricing seed command printed for native to run |

---

## Do NOT do

- Do not modify any Observatory query files (`lib/observatory/queries.ts` or anything under `lib/observatory/`)
- Do not modify `persist.ts`, `cost.ts`, or `observe.ts` in the observability layer
- Do not add any migrations
- Do not modify any test files
- Do not change the existing `writeLlmCallLog` calls — add the Observatory calls alongside them, not instead of them

---

## How to start

Open the Madhav project (`/Users/Dev/Vibe-Coding/Apps/Madhav/`) in Anti-Gravity.
Run: **"Read CLAUDECODE_BRIEF_OBS_S1.md and execute it."**
