/**
 * manifest_planner.ts — LLM-first planner (W2-PLANNER, UQE-4c).
 *
 * Consumes:
 *   1. PLANNER_PROMPT_v1_0.md §3 system prompt (verbatim).
 *   2. The compressed CAPABILITY_MANIFEST primary-tool view (≤3K tokens).
 *   3. The PlannerContext window (≤600 tokens) from planner_context_builder.
 *   4. The native's query and chart id (the planner is per-native).
 *
 * Emits a single `PlanSchema` JSON object (validated via Zod) that lists the
 * tool calls the retrieval layer should execute.
 *
 * Failure mode: any provider error or schema-validation failure is surfaced as
 * `PlannerError` with the original error attached as `cause`. The route caller
 * (consume/route.ts) catches `PlannerError`, warn-logs, and falls back silently
 * to the existing classify() + compose_bundle() path.
 *
 * Gated by `LLM_FIRST_PLANNER_ENABLED` (default false). The module is safe to
 * import unconditionally; it does no work until `callLlmPlanner()` is called.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'
import { generateText, jsonSchema, tool } from 'ai'
import type { JSONSchema7 } from 'json-schema'
import { z } from 'zod'
import { resolveModel, googleProviderOptions } from '@/lib/models/resolver'
import {
  compressManifest,
  compressedManifestToString,
  type CapabilityManifest,
} from '@/lib/pipeline/manifest_compressor'
import { buildPlannerContext } from '@/lib/pipeline/planner_context_builder'
import type { PlanningStartEvent, PlanningDoneEvent, TraceEvent } from '@/lib/trace/types'
import { writeLlmCallLog, resolveProvider } from '@/lib/db/monitoring-write'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { writePlanAlternatives } from '@/lib/db/trace/plan_alternatives_writer'
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'

// ────────────────────────────────────────────────────────────────────────────
// PlanSchema (TS) + PlannerError
// ────────────────────────────────────────────────────────────────────────────

export interface PlanSchema {
  query_class: 'remedial' | 'interpretive' | 'predictive' | 'holistic' | 'planetary' | 'single_answer'
  query_intent_summary: string
  tool_calls: Array<{
    tool_name: string
    params: Record<string, unknown>
    token_budget: number
    priority: 1 | 2 | 3
    reason: string
  }>
}

export class PlannerError extends Error {
  constructor(message: string, public readonly cause?: unknown) {
    super(message)
    this.name = 'PlannerError'
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Retry helpers — timeout + rate-limit retry gate
// ────────────────────────────────────────────────────────────────────────────

const MAX_PLANNER_RETRIES = 1
const PLANNER_RETRY_DELAY_MS = 2000

function isRateLimitError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false
  const e = err as { status?: number; statusCode?: number; message?: string }
  if (e.status === 429 || e.statusCode === 429) return true
  if (typeof e.message === 'string' && e.message.includes('429')) return true
  if (typeof e.message === 'string' && e.message.toLowerCase().includes('rate')) return true
  return false
}

function isTimeoutError(err: unknown): boolean {
  if (err instanceof Error) {
    const msg = err.message.toLowerCase()
    return (
      msg.includes('timeout') ||
      msg.includes('aborted') ||
      msg.includes('network') ||
      msg.includes('enotfound') ||
      msg.includes('econnreset') ||
      msg.includes('econnrefused') ||
      msg.includes('cannot connect') ||
      err.name === 'AbortError'
    )
  }
  return false
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ────────────────────────────────────────────────────────────────────────────
// Zod schema for generateObject() structured output
// ────────────────────────────────────────────────────────────────────────────

const ToolCallSchema = z.object({
  tool_name: z.string().min(1),
  params: z.record(z.string(), z.unknown()),
  token_budget: z.number().int().min(100).max(2000),
  priority: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  reason: z.string().min(1),
})

export const PlanSchemaZod = z.object({
  query_class: z.enum([
    'remedial',
    'interpretive',
    'predictive',
    'holistic',
    'planetary',
    'single_answer',
  ]),
  query_intent_summary: z.string().min(1),
  tool_calls: z.array(ToolCallSchema),
})

// Hand-crafted JSON Schema for the submit_plan tool input. We do NOT feed the
// Zod schema directly because Zod's translation for `z.record(z.string(),
// z.unknown())` emits the `propertyNames` JSON-Schema keyword, which NIM's
// grammar-constrained decoder rejects ("Grammar error: Unimplemented keys"),
// and `z.union([z.literal(1), z.literal(2), z.literal(3)])` emits an
// `anyOf:[{const:N}]` form that's similarly unfriendly. PlanSchemaZod is still
// applied post-call as the runtime validator (parity with prior generateObject
// behavior), so this hand-crafted schema only governs what NIM constrains the
// model to emit, not what the planner ultimately accepts.
const PlanInputJsonSchema: JSONSchema7 = {
  type: 'object',
  properties: {
    query_class: {
      type: 'string',
      enum: ['remedial', 'interpretive', 'predictive', 'holistic', 'planetary', 'single_answer'],
    },
    query_intent_summary: { type: 'string' },
    tool_calls: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          tool_name: { type: 'string' },
          params: { type: 'object' },
          token_budget: { type: 'integer', minimum: 100, maximum: 2000 },
          priority: { type: 'integer', minimum: 1, maximum: 3 },
          reason: { type: 'string' },
        },
        required: ['tool_name', 'params', 'token_budget', 'priority', 'reason'],
      },
    },
  },
  required: ['query_class', 'query_intent_summary', 'tool_calls'],
}

// ────────────────────────────────────────────────────────────────────────────
// System prompt — loaded lazily on first call from PLANNER_PROMPT_v1_0.md
// §3 + §4. Lazy because module-init readFileSync breaks Cloud Build: the
// builder runs `next build` with cwd=/app, where path.join(cwd,'..',
// '00_ARCHITECTURE',…) resolves to the filesystem root and ENOENTs. Reading
// at first call lets MARSYS_REPO_ROOT (set in Dockerfile runner stage) point
// at /app where the file actually lives.
// ────────────────────────────────────────────────────────────────────────────
//
// Why load from markdown instead of hardcoding (W2-UQE-ACTIVATE round 5):
//   Round 4 surfaced a load-bearing defect — markdown edits to R8 + the second
//   remedial few-shot (resonance_register for alignment-character remedials)
//   never reached the runtime, because SYSTEM_PROMPT was a hand-copied string
//   constant of §3 only. §4 (few-shots) had never been at runtime at all.
//   Loading from disk eliminates the drift permanently: the markdown is the
//   single source of truth.
//
// query_class is now part of §3 directly (PLANNER_PROMPT v1.1 amendment
// 2026-05-03). The old QUERY_CLASS_EXTENSION constant is removed; the
// markdown is the single source of truth for the full schema.

function repoRoot(): string {
  return process.env.MARSYS_REPO_ROOT ?? path.join(process.cwd(), '..')
}

function extractSystemPromptBody(md: string): string {
  // §3 is "## 3. System prompt (verbatim — copy into code)" followed by a
  // ```...``` fenced code block. Pull out just the fenced contents.
  const headerIdx = md.indexOf('## 3. System prompt')
  if (headerIdx < 0) {
    throw new Error('PLANNER_PROMPT_v1_0.md: §3 header not found')
  }
  const fenceOpen = md.indexOf('```', headerIdx)
  if (fenceOpen < 0) {
    throw new Error('PLANNER_PROMPT_v1_0.md: §3 opening fence not found')
  }
  const bodyStart = md.indexOf('\n', fenceOpen) + 1
  const fenceClose = md.indexOf('```', bodyStart)
  if (fenceClose < 0) {
    throw new Error('PLANNER_PROMPT_v1_0.md: §3 closing fence not found')
  }
  return md.slice(bodyStart, fenceClose).trimEnd()
}

function extractFewShotSection(md: string): string {
  // §4 is "## 4. Few-shot examples" through (but not including) "## 5.".
  const startIdx = md.indexOf('## 4. Few-shot examples')
  if (startIdx < 0) {
    throw new Error('PLANNER_PROMPT_v1_0.md: §4 header not found')
  }
  const endIdx = md.indexOf('\n## 5.', startIdx)
  if (endIdx < 0) {
    throw new Error('PLANNER_PROMPT_v1_0.md: §5 boundary not found')
  }
  return md.slice(startIdx, endIdx).trimEnd()
}

let _systemPromptCache: string | null = null

function getSystemPrompt(): string {
  if (_systemPromptCache !== null) return _systemPromptCache
  const promptPath = path.join(repoRoot(), '00_ARCHITECTURE', 'PLANNER_PROMPT_v1_0.md')
  const md = readFileSync(promptPath, 'utf-8')
  const body = extractSystemPromptBody(md)
  const fewShots = extractFewShotSection(md)
  _systemPromptCache = `${body}\n\n---\n\n${fewShots}\n`
  return _systemPromptCache
}

// ────────────────────────────────────────────────────────────────────────────
// Manifest loading (read-once, lazy)
// ────────────────────────────────────────────────────────────────────────────

let _manifestCache: CapabilityManifest | null = null

function loadManifest(): CapabilityManifest {
  if (_manifestCache) return _manifestCache
  const manifestPath = path.join(repoRoot(), '00_ARCHITECTURE', 'CAPABILITY_MANIFEST.json')
  const raw = readFileSync(manifestPath, 'utf-8')
  _manifestCache = JSON.parse(raw) as CapabilityManifest
  return _manifestCache
}

// ────────────────────────────────────────────────────────────────────────────
// Public entrypoint
// ────────────────────────────────────────────────────────────────────────────

export async function callLlmPlanner(
  query: string,
  conversationHistory: Array<{ role: string; content: string }>,
  plannerModelId: string,
  nativeId: string,
  emitTrace?: (event: TraceEvent) => void,
  queryId?: string,
  fallbackModelId?: string,
): Promise<PlanSchema> {
  const manifest = loadManifest()
  const compressed = compressManifest(manifest)
  const compressedManifestStr = compressedManifestToString(compressed)

  const ctx = await buildPlannerContext(query, conversationHistory, plannerModelId, queryId)

  // The user message is JSON the planner consumes alongside the verbatim
  // system prompt. native_id is included so the planner can keep per-native
  // context if it needs to (currently informational only — UQE-4c logs it,
  // W2-INSTRUMENT will persist it).
  const userPayload = {
    native_id: nativeId,
    manifest: JSON.parse(compressedManifestStr) as unknown,
    history: {
      turns: ctx.history_turns,
      was_summarized: ctx.history_was_summarized,
    },
    query: ctx.query,
  }
  const userMessage = JSON.stringify(userPayload)

  // Capture timing before emitting step_start so started_at is accurate.
  const plannerStepStart = new Date().toISOString()
  const plannerStartMs = Date.now()
  const stepQueryId = queryId ?? nativeId

  emitTrace?.({
    event: 'step_start',
    query_id: stepQueryId,
    step: {
      query_id: stepQueryId,
      step_seq: 0,
      step_name: 'llm_planner',
      step_type: 'llm',
      status: 'running',
      started_at: plannerStepStart,
      data_summary: {
        model: plannerModelId,
        planner_active: true,
        tool_count: compressed.length,
      },
      payload: {},
    },
  })

  // nativeId doubles as the SSE query_id for the request that owns this plan.
  emitTrace?.({
    event: 'planning_start',
    query_id: nativeId,
    planner_model_id: plannerModelId,
    manifest_tool_count: compressed.length,
  })

  // NIM (and other OpenAI-compatible providers that don't implement
  // response_format=json_schema) reject `generateObject`'s structured-output
  // path with HTTP 500. Force tool-call mode by routing through `generateText`
  // with a single submit-plan tool whose inputSchema is PlanSchemaZod and
  // toolChoice='required'. The AI SDK validates the model's tool-call args
  // against PlanSchemaZod before populating `toolCall.input`.
  const start = Date.now()
  let result
  let lastErr: unknown
  let activeModelId = plannerModelId
  let fallbackWasUsed = false
  for (let attempt = 0; attempt <= MAX_PLANNER_RETRIES; attempt++) {
    activeModelId = (attempt > 0 && fallbackModelId && isRateLimitError(lastErr))
      ? fallbackModelId
      : plannerModelId
    fallbackWasUsed = activeModelId !== plannerModelId
    try {
      result = await generateText({
        model: resolveModel(activeModelId),
        system: getSystemPrompt(),
        messages: [{ role: 'user', content: userMessage }],
        temperature: 0,
        // maxRetries: 0 — NIM free-tier is queue-based. Without this, the AI SDK
        // retries an AbortError (headers-timeout) up to 3 times; the queued-then-
        // aborted request comes back as HTTP 500 on retry, masking the real cause.
        // With 0 retries the AbortError surfaces cleanly so isTimeoutError() can
        // gate our own single retry. The 90s nimFetch timeout gives ample headroom
        // for NIM queue waits before aborting at all.
        maxRetries: 0,
        tools: {
          submit_plan: tool({
            description:
              'Submit the planned tool calls for the native query. Call this exactly once with the full plan; do not emit prose.',
            inputSchema: jsonSchema<PlanSchema>(PlanInputJsonSchema),
          }),
        },
        toolChoice: 'required',
        // Apply Google safety overrides when the planner model is a Gemini model.
        // Returns undefined for all non-Google models — spread is a no-op.
        ...(googleProviderOptions(activeModelId) && {
          providerOptions: googleProviderOptions(activeModelId),
        }),
      })
      break
    } catch (err) {
      lastErr = err
      if (isRateLimitError(err) && attempt === 0 && fallbackModelId) {
        console.warn(
          `[manifest_planner] 429 on primary ${plannerModelId}, retrying with fallback ${fallbackModelId}`,
        )
        continue
      }
      if (isTimeoutError(err) && attempt < MAX_PLANNER_RETRIES) {
        console.warn(
          `[manifest_planner] timeout on attempt ${attempt + 1}, retrying...`,
        )
        await sleep(PLANNER_RETRY_DELAY_MS)
        continue
      }
      if (queryId) {
        void writeLlmCallLog({
          query_id: queryId,
          conversation_id: null,
          call_stage: 'planner',
          model_id: activeModelId,
          provider: resolveProvider(activeModelId),
          input_tokens: null,
          output_tokens: null,
          reasoning_tokens: null,
          latency_ms: Date.now() - start,
          cost_usd: null,
          fallback_used: fallbackWasUsed,
          error_code: err instanceof Error ? err.message : String(err),
          payload: null,
        })
      }
      {
        const errMsg = err instanceof Error ? err.message : String(err)
        emitTrace?.({
          event: 'step_error',
          query_id: stepQueryId,
          step: {
            query_id: stepQueryId,
            step_seq: 0,
            step_name: 'llm_planner',
            step_type: 'llm',
            status: 'error',
            started_at: plannerStepStart,
            completed_at: new Date().toISOString(),
            latency_ms: Date.now() - plannerStartMs,
            data_summary: { model: activeModelId, planner_active: false, error_reason: errMsg },
            payload: { error_message: errMsg },
          },
        })
      }
      throw new PlannerError(
        `LLM planner call failed: ${err instanceof Error ? err.message : String(err)}`,
        err,
      )
    }
  }
  if (!result) {
    // Exhausted retries on timeout/rate-limit errors — log and throw
    if (queryId) {
      void writeLlmCallLog({
        query_id: queryId,
        conversation_id: null,
        call_stage: 'planner',
        model_id: activeModelId,
        provider: resolveProvider(activeModelId),
        input_tokens: null,
        output_tokens: null,
        reasoning_tokens: null,
        latency_ms: Date.now() - start,
        cost_usd: null,
        fallback_used: fallbackWasUsed,
        error_code: lastErr instanceof Error ? lastErr.message : String(lastErr),
        payload: null,
      })
    }
    {
      const errMsg = lastErr instanceof Error ? lastErr.message : String(lastErr)
      emitTrace?.({
        event: 'step_error',
        query_id: stepQueryId,
        step: {
          query_id: stepQueryId,
          step_seq: 0,
          step_name: 'llm_planner',
          step_type: 'llm',
          status: 'error',
          started_at: plannerStepStart,
          completed_at: new Date().toISOString(),
          latency_ms: Date.now() - plannerStartMs,
          data_summary: { model: activeModelId, planner_active: false, error_reason: errMsg },
          payload: { error_message: errMsg },
        },
      })
    }
    throw new PlannerError(
      `LLM planner call failed: ${lastErr instanceof Error ? lastErr.message : String(lastErr)}`,
      lastErr,
    )
  }
  const latency_ms = Date.now() - start

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
      cost_usd: computeCostUsd(getModelPricingSync(activeModelId), {
        input_tokens: result.usage?.inputTokens ?? null,
        output_tokens: result.usage?.outputTokens ?? null,
      }),
      fallback_used: fallbackWasUsed,
      error_code: null,
      payload: null,
    })
  }

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

  const submitCall = result.toolCalls.find(tc => tc.toolName === 'submit_plan')
  if (!submitCall) {
    const errMsg = `LLM planner did not produce a submit_plan tool call (toolCalls=${result.toolCalls.length}, finishReason=${result.finishReason})`
    emitTrace?.({
      event: 'step_error',
      query_id: stepQueryId,
      step: {
        query_id: stepQueryId,
        step_seq: 0,
        step_name: 'llm_planner',
        step_type: 'llm',
        status: 'error',
        started_at: plannerStepStart,
        completed_at: new Date().toISOString(),
        latency_ms: Date.now() - plannerStartMs,
        data_summary: { model: activeModelId, planner_active: false, error_reason: errMsg },
        payload: { error_message: errMsg },
      },
    })
    throw new PlannerError(errMsg)
  }
  const parsed = PlanSchemaZod.safeParse(submitCall.input)
  if (!parsed.success) {
    const errMsg = `LLM planner returned schema-invalid output: ${parsed.error.message}`
    emitTrace?.({
      event: 'step_error',
      query_id: stepQueryId,
      step: {
        query_id: stepQueryId,
        step_seq: 0,
        step_name: 'llm_planner',
        step_type: 'llm',
        status: 'error',
        started_at: plannerStepStart,
        completed_at: new Date().toISOString(),
        latency_ms: Date.now() - plannerStartMs,
        data_summary: { model: activeModelId, planner_active: false, error_reason: errMsg },
        payload: { error_message: errMsg },
      },
    })
    throw new PlannerError(errMsg, parsed.error)
  }

  emitTrace?.({
    event: 'step_done',
    query_id: stepQueryId,
    step: {
      query_id: stepQueryId,
      step_seq: 0,
      step_name: 'llm_planner',
      step_type: 'llm',
      status: 'done',
      started_at: plannerStepStart,
      completed_at: new Date().toISOString(),
      latency_ms: Date.now() - plannerStartMs,
      data_summary: {
        model: activeModelId,
        planner_active: true,
        tool_count: parsed.data.tool_calls.length,
        query_class: parsed.data.query_class,
      },
      payload: {
        query_plan: {
          query_class: parsed.data.query_class,
          tools_authorized: parsed.data.tool_calls.map(tc => tc.tool_name),
          tool_calls: parsed.data.tool_calls.map(tc => ({
            tool_name: tc.tool_name,
            params: tc.params,
            priority: tc.priority,
            reason: tc.reason,
          })),
          query_intent_summary: parsed.data.query_intent_summary,
          planning_model_id: activeModelId,
          planning_latency_ms: latency_ms,
        },
        tool_calls: parsed.data.tool_calls.map(tc => ({
          tool_name: tc.tool_name,
          params: tc.params,
          priority: tc.priority,
          reason: tc.reason,
        })),
      },
    },
  })

  emitTrace?.({
    event: 'planning_done',
    query_id: nativeId,
    tool_count_planned: parsed.data.tool_calls.length,
    tools_selected: Array.from(new Set(parsed.data.tool_calls.map(tc => tc.tool_name))),
    query_intent_summary: parsed.data.query_intent_summary,
    planner_latency_ms: latency_ms,
  })

  // TRACE-T1: Emit plan alternatives for selected tool_calls.
  // PlanSchema only carries selected tools (tool_calls[]); there is no
  // excluded_bundles field in the current schema.
  // TODO(TRACE-T2): when the planner prompt is extended to return rejected bundles,
  // add excluded_bundles here.
  if (queryId) {
    const obsDb = getStorageClient()
    writePlanAlternatives(
      parsed.data.tool_calls.map(tc => ({
        query_id: queryId,
        bundle_name: tc.tool_name,
        was_selected: true,
        rationale: tc.reason,
      })),
      obsDb,
    )
  }

  if (process.env.NODE_ENV !== 'production') {
    console.log(
      `[planner] callLlmPlanner ok model=${plannerModelId} ` +
        `latency_ms=${latency_ms} tool_calls=${parsed.data.tool_calls.length} ` +
        `query_class=${parsed.data.query_class}`,
    )
  }

  return parsed.data
}

// Exported for tests only — lets the suite reset the manifest cache between
// runs without hitting the filesystem twice in a row.
export function __resetManifestCacheForTests(): void {
  _manifestCache = null
}

// Exported for tests only — same purpose as __resetManifestCacheForTests, for
// the lazy system-prompt cache.
export function __resetSystemPromptForTests(): void {
  _systemPromptCache = null
}
