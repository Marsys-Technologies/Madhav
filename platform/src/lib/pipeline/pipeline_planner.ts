/**
 * pipeline_planner.ts — LLM-first pipeline planner.
 *
 * Renamed + rewired from manifest_planner.ts. Consumes:
 *   1. PLANNER_PROMPT_v2_0.md §3 system prompt (verbatim).
 *   2. The compressed CAPABILITY_MANIFEST primary-tool view (≤3K tokens).
 *   3. The PlannerContext window (≤600 tokens) from planner_context_builder.
 *   4. The native's query and chart id (the planner is per-native).
 *
 * Emits a single `PipelinePlan` JSON object (validated via PipelinePlanSchema)
 * that lists the asset bundle, retrieval tool calls, and synthesis guidance
 * the downstream pipeline executes.
 *
 * Failure mode: any provider error or schema-validation failure is surfaced
 * as `PipelinePlannerError`. The route caller (consume/route.ts) catches it
 * and returns HTTP 422 — there is no silent fallback in the new pipeline.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'
import { generateText, jsonSchema, tool } from 'ai'
import {
  PipelinePlanSchema,
  PipelinePlanInputJsonSchema,
  PipelinePlannerError,
  type PipelinePlan,
} from './types'
import { resolveModel, googleProviderOptions } from '@/lib/models/resolver'
import {
  compressManifest,
  compressedManifestToString,
  type CapabilityManifest,
} from '@/lib/pipeline/manifest_compressor'
import { buildPlannerContext } from '@/lib/pipeline/planner_context_builder'
import type { TraceEvent } from '@/lib/trace/types'
import { writeLlmCallLog, resolveProvider } from '@/lib/db/monitoring-write'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { writePlanAlternatives } from '@/lib/db/trace/plan_alternatives_writer'
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'

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

function isServerError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false
  const e = err as { status?: number; statusCode?: number; message?: string }
  if (e.status === 500 || e.statusCode === 500) return true
  if (e.status === 503 || e.statusCode === 503) return true
  if (typeof e.message === 'string' && /\b(500|503|internal server error|service unavailable)\b/i.test(e.message)) return true
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
// System prompt — loaded lazily on first call from PLANNER_PROMPT_v2_0.md
// §3 + §4. Lazy because module-init readFileSync breaks Cloud Build: the
// builder runs `next build` with cwd=/app, where path.join(cwd,'..',
// '00_ARCHITECTURE',…) resolves to the filesystem root and ENOENTs.
// ────────────────────────────────────────────────────────────────────────────

function repoRoot(): string {
  return process.env.MARSYS_REPO_ROOT ?? path.join(process.cwd(), '..')
}

function extractSystemPromptBody(md: string): string {
  const headerIdx = md.indexOf('## 3. System prompt')
  if (headerIdx < 0) {
    throw new Error('PLANNER_PROMPT_v2_0.md: §3 header not found')
  }
  const fenceOpen = md.indexOf('```', headerIdx)
  if (fenceOpen < 0) {
    throw new Error('PLANNER_PROMPT_v2_0.md: §3 opening fence not found')
  }
  const bodyStart = md.indexOf('\n', fenceOpen) + 1
  const fenceClose = md.indexOf('```', bodyStart)
  if (fenceClose < 0) {
    throw new Error('PLANNER_PROMPT_v2_0.md: §3 closing fence not found')
  }
  return md.slice(bodyStart, fenceClose).trimEnd()
}

function extractFewShotSection(md: string): string {
  const startIdx = md.indexOf('## 4. Few-shot examples')
  if (startIdx < 0) {
    throw new Error('PLANNER_PROMPT_v2_0.md: §4 header not found')
  }
  const endIdx = md.indexOf('\n## 5.', startIdx)
  if (endIdx < 0) {
    throw new Error('PLANNER_PROMPT_v2_0.md: §5 boundary not found')
  }
  return md.slice(startIdx, endIdx).trimEnd()
}

let _systemPromptCache: string | null = null

function getSystemPrompt(): string {
  if (_systemPromptCache !== null) return _systemPromptCache
  const promptPath = path.join(repoRoot(), '00_ARCHITECTURE', 'PLANNER_PROMPT_v2_0.md')
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

export async function callPipelinePlanner(
  query: string,
  conversationHistory: Array<{ role: string; content: string }>,
  plannerModelId: string,
  nativeId: string,
  emitTrace?: (event: TraceEvent) => void,
  queryId?: string,
  fallbackModelId?: string,
): Promise<PipelinePlan> {
  const manifest = loadManifest()
  const compressed = compressManifest(manifest)
  const compressedManifestStr = compressedManifestToString(compressed)

  const ctx = await buildPlannerContext(query, conversationHistory, plannerModelId, queryId)

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

  emitTrace?.({
    event: 'planning_start',
    query_id: nativeId,
    planner_model_id: plannerModelId,
    manifest_tool_count: compressed.length,
  })

  const start = Date.now()
  let result
  let lastErr: unknown
  let activeModelId = plannerModelId
  let fallbackWasUsed = false
  for (let attempt = 0; attempt <= MAX_PLANNER_RETRIES; attempt++) {
    activeModelId = (attempt > 0 && fallbackModelId && (isRateLimitError(lastErr) || isServerError(lastErr)))
      ? fallbackModelId
      : plannerModelId
    fallbackWasUsed = activeModelId !== plannerModelId
    try {
      result = await generateText({
        model: resolveModel(activeModelId),
        system: getSystemPrompt(),
        messages: [{ role: 'user', content: userMessage }],
        temperature: 0,
        maxRetries: 0,
        tools: {
          submit_plan: tool({
            description:
              'Submit the planned tool calls for the native query. Call this exactly once with the full plan; do not emit prose.',
            inputSchema: jsonSchema<PipelinePlan>(PipelinePlanInputJsonSchema),
          }),
        },
        toolChoice: 'required',
        ...(googleProviderOptions(activeModelId) && {
          providerOptions: googleProviderOptions(activeModelId),
        }),
      })
      break
    } catch (err) {
      lastErr = err
      if ((isRateLimitError(err) || isServerError(err)) && attempt === 0 && fallbackModelId) {
        console.warn(
          `[pipeline_planner] ${isRateLimitError(err) ? '429' : '500/503'} on primary ${plannerModelId}, retrying with fallback ${fallbackModelId}`,
        )
        continue
      }
      if (isTimeoutError(err) && attempt < MAX_PLANNER_RETRIES) {
        console.warn(
          `[pipeline_planner] timeout on attempt ${attempt + 1}, retrying...`,
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
      throw new PipelinePlannerError(
        `LLM planner call failed: ${err instanceof Error ? err.message : String(err)}`,
        err,
      )
    }
  }
  if (!result) {
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
    throw new PipelinePlannerError(
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
    throw new PipelinePlannerError(errMsg)
  }
  const parsed = PipelinePlanSchema.safeParse(submitCall.input)
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
    throw new PipelinePlannerError(errMsg, parsed.error)
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
      `[pipeline_planner] callPipelinePlanner ok model=${plannerModelId} ` +
        `latency_ms=${latency_ms} tool_calls=${parsed.data.tool_calls.length} ` +
        `query_class=${parsed.data.query_class}`,
    )
  }

  return parsed.data
}

// Exported for tests only.
export function __resetManifestCacheForTests(): void {
  _manifestCache = null
}

export function __resetSystemPromptForTests(): void {
  _systemPromptCache = null
}

export { PipelinePlannerError } from './types'
export { PipelinePlannerError as PlannerFault } from './types'
