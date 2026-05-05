import 'server-only'

import { generateText } from 'ai'
import { resolveModel, resolveWorkerModel } from '@/lib/models/resolver'
import { getModelMeta } from '@/lib/models/registry'
import { validate } from '@/lib/schemas/index'
import { telemetry } from '@/lib/telemetry/index'
import { configService } from '@/lib/config/index'
import {
  ROUTER_SYSTEM_PROMPT,
  buildRouterUserMessage,
  buildStrictRetryMessage,
} from './prompt'
import type { QueryPlan } from './types'
import { PipelineError } from './errors'

export type { QueryPlan }
export { PipelineError } from './errors'

// ---------------------------------------------------------------------------
// Public interfaces
// ---------------------------------------------------------------------------

export interface RouterConfig {
  model_id: string
  temperature: number
  max_tokens: number
}

export interface RouterContext {
  conversation_history?: Array<{ role: 'user' | 'assistant'; content: string }>
  audience_tier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
  manifest_fingerprint: string
  /**
   * BHISMA-B1 §3.2 — the synthesis model the user picked. The router uses
   * this to pick the same family's worker model (e.g. user picks gpt-4o →
   * router uses gpt-4o-mini for classification). Optional for backward
   * compatibility; absent value falls back to ROUTER_MODEL_OVERRIDE / haiku.
   */
  synthesis_model_id?: string
  /**
   * Optional pre-allocated query_plan_id so the route handler can correlate
   * trace events even if classify throws before producing a plan. When
   * present, applyCallerFields uses this id rather than generating a fresh one.
   */
  query_plan_id?: string
}

// ---------------------------------------------------------------------------
// Known root-level properties in query_plan.schema.json.
// Used to strip LLM-invented extra fields before schema validation so that
// complex queries (nakshatra, yoga, Sade Sati, eclipse, remedial) that cause
// the model to add tool-parameter keys at root level don't trip additionalProperties:false.
// Update this set whenever query_plan.schema.json gains a new root property.
// ---------------------------------------------------------------------------
const QUERY_PLAN_KNOWN_PROPS = new Set([
  'query_plan_id', 'query_text', 'query_class', 'domains', 'forward_looking',
  'audience_tier', 'tools_authorized', 'history_mode', 'panel_mode',
  'expected_output_shape', 'manifest_fingerprint', 'schema_version',
  'planets', 'houses', 'dasha_context_required', 'graph_seed_hints',
  'edge_type_filter', 'vector_search_filter', 'bundle_directives',
  'adjudicator_model_id', 'router_confidence', 'router_model_id',
  'chart_facts_query', 'time_window', 'sade_sati_query', 'eclipse_query',
  'retrograde_query', 'retrograde_planet',
])

function stripUnknownRootProps(obj: unknown): unknown {
  if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) return obj
  const stripped: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    if (QUERY_PLAN_KNOWN_PROPS.has(k)) stripped[k] = v
  }
  return stripped
}

// ---------------------------------------------------------------------------
// JSON extraction helper — strips any accidental markdown fences
// ---------------------------------------------------------------------------
function extractJson(raw: string): string {
  const stripped = raw.trim()
  // Handle ```json ... ``` or ``` ... ```
  const fenceMatch = stripped.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```\s*$/)
  if (fenceMatch) return fenceMatch[1].trim()
  return stripped
}

function resolveModelId(context: RouterContext, configModelId: string | undefined): string {
  // Precedence: explicit config override → family worker for chosen synthesis
  // model → ROUTER_MODEL_OVERRIDE env → claude-haiku-4-5.
  if (configModelId) return configModelId
  if (context.synthesis_model_id) return resolveWorkerModel(context.synthesis_model_id)
  return configService.getValue<string>('ROUTER_MODEL_OVERRIDE', 'claude-haiku-4-5')
}

// ---------------------------------------------------------------------------
// Core classify function
// ---------------------------------------------------------------------------
export async function classify(
  query: string,
  context: RouterContext,
  config?: Partial<RouterConfig>
): Promise<QueryPlan> {
  const modelId = resolveModelId(context, config?.model_id)
  const provider = getModelMeta(modelId)?.provider
  const temperature =
    config?.temperature ??
    configService.getValue<number>('ROUTER_TEMPERATURE', 0.0)
  const maxTokens =
    config?.max_tokens ??
    configService.getValue<number>('ROUTER_MAX_TOKENS', 1024)

  const model = resolveModel(modelId)

  const promptInputs = {
    query,
    conversationHistory: context.conversation_history,
    audienceTier: context.audience_tier,
  }

  // ---------------------------------------------------------------------------
  // Attempt 1 — standard classification prompt
  // ---------------------------------------------------------------------------
  const attempt1Start = Date.now()
  let rawText1 = ''
  let inputTokens1 = 0
  let outputTokens1 = 0

  try {
    const result1 = await generateText({
      model,
      system: ROUTER_SYSTEM_PROMPT,
      messages: [{ role: 'user', content: buildRouterUserMessage(promptInputs) }],
      temperature,
      maxOutputTokens: maxTokens,
    })

    rawText1 = result1.text
    inputTokens1 = result1.usage?.inputTokens ?? 0
    outputTokens1 = result1.usage?.outputTokens ?? 0
  } catch (err) {
    telemetry.recordError('router', 'llm_call_1_failed', err instanceof Error ? err : new Error(String(err)))
    throw new PipelineError({
      stage: 'classify',
      reason: `Planning LLM call failed: ${err instanceof Error ? err.message : String(err)}`,
      model_id: modelId,
      provider,
      cause: err,
    })
  } finally {
    telemetry.recordLatency('router', 'classify', Date.now() - attempt1Start)
    telemetry.recordCost('router', modelId, inputTokens1, outputTokens1, 0)
  }

  // Try to parse attempt 1
  let parsed1: unknown
  let parseError1: string | null = null
  try {
    parsed1 = JSON.parse(extractJson(rawText1))
  } catch (e) {
    parseError1 = e instanceof Error ? e.message : String(e)
  }

  if (parsed1 !== undefined) {
    const result = applyCallerFields(stripUnknownRootProps(parsed1), query, context, modelId)
    const validation = validate<QueryPlan>('query_plan', result)
    if (validation.valid && validation.data) {
      return { ...validation.data, router_confidence: 1.0, router_model_id: modelId }
    }
    // Schema invalid — fall through to retry
    parseError1 = validation.errors?.map(e => `${e.path}: ${e.message}`).join('; ') ?? 'schema validation failed'
  }

  // ---------------------------------------------------------------------------
  // Attempt 2 — strict retry with error feedback
  // ---------------------------------------------------------------------------
  const attempt2Start = Date.now()
  let rawText2 = ''
  let inputTokens2 = 0
  let outputTokens2 = 0

  try {
    const result2 = await generateText({
      model,
      system: ROUTER_SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: buildStrictRetryMessage(promptInputs, parseError1 ?? 'unknown error'),
        },
      ],
      temperature: 0.0, // force deterministic on retry
      maxOutputTokens: maxTokens,
    })

    rawText2 = result2.text
    inputTokens2 = result2.usage?.inputTokens ?? 0
    outputTokens2 = result2.usage?.outputTokens ?? 0
  } catch (err) {
    telemetry.recordError('router', 'llm_call_2_failed', err instanceof Error ? err : new Error(String(err)))
    throw new PipelineError({
      stage: 'classify',
      reason: `Planning LLM retry failed: ${err instanceof Error ? err.message : String(err)}`,
      model_id: modelId,
      provider,
      cause: err,
    })
  } finally {
    telemetry.recordLatency('router', 'classify_retry', Date.now() - attempt2Start)
    telemetry.recordCost('router', modelId, inputTokens2, outputTokens2, 0)
  }

  // Try to parse attempt 2
  let parsed2: unknown
  try {
    parsed2 = JSON.parse(extractJson(rawText2))
  } catch (e) {
    throw new PipelineError({
      stage: 'classify',
      reason: `Planning LLM returned invalid JSON after 2 attempts: ${e instanceof Error ? e.message : String(e)}`,
      model_id: modelId,
      provider,
    })
  }

  const result2 = applyCallerFields(stripUnknownRootProps(parsed2), query, context, modelId)
  const validation2 = validate<QueryPlan>('query_plan', result2)
  if (validation2.valid && validation2.data) {
    return { ...validation2.data, router_confidence: 1.0, router_model_id: modelId }
  }

  // Both attempts failed schema validation — surface the structured error.
  const reasonDetail =
    validation2.errors?.map(e => `${e.path}: ${e.message}`).join('; ') ??
    'unknown schema validation error'
  throw new PipelineError({
    stage: 'classify',
    reason: `Planning output failed schema validation after 2 attempts: ${reasonDetail}`,
    model_id: modelId,
    provider,
  })
}

// ---------------------------------------------------------------------------
// applyCallerFields — overlay the caller-controlled fields onto the LLM output
// so the LLM can never override audience_tier or manifest_fingerprint.
// ---------------------------------------------------------------------------
function applyCallerFields(
  llmOutput: unknown,
  query: string,
  context: RouterContext,
  modelId: string
): unknown {
  if (typeof llmOutput !== 'object' || llmOutput === null) {
    return llmOutput
  }
  return {
    ...(llmOutput as Record<string, unknown>),
    query_plan_id: context.query_plan_id ?? crypto.randomUUID(),
    query_text: query,
    audience_tier: context.audience_tier,
    manifest_fingerprint: context.manifest_fingerprint,
    schema_version: '1.0',
    router_model_id: modelId,
  }
}
