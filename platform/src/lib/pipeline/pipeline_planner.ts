/**
 * pipeline_planner.ts — LLM-first pipeline planner.
 *
 * Renamed + rewired from manifest_planner.ts. Consumes:
 *   1. PLANNER_PROMPT_v2_0.md §3 system prompt (verbatim).
 *   2. The compressed CAPABILITY_MANIFEST primary-tool view (≤3K tokens).
 *   3. The PlannerContext window (≤600 tokens) from planner_context_builder.
 *   4. The native's query and chart id (the planner is per-native).
 *
 * Emits a `PlannerOutcome` — the 3-way discriminated union (W4 "One Planner"):
 *   'plan'                → PlanReceipt          (a validated PipelinePlan + scope_tuple)
 *   'clarification_needed' → ClarificationRequest (the query was too ambiguous to plan)
 *   'fault'               → PlannerFaultResult    (a typed, honest error — never a throw)
 *
 * The plan lists the asset bundle, retrieval tool calls, and synthesis guidance
 * the downstream pipeline executes. Every incoming query is first run through the
 * DETERMINISTIC scope-tuple classifier (`classifyScope`); low-confidence queries
 * short-circuit to a clarification (no LLM cost), and the resulting `scope_tuple`
 * is attached to a successful plan.
 *
 * Failure mode: the planner NEVER throws for an expected failure. Unparseable /
 * schema-invalid LLM output gets exactly ONE structured repair-retry; if that
 * also fails it is returned as `{ outcome: 'fault', retryable: false }`. Provider
 * errors that exhaust the retry budget return `{ outcome: 'fault', retryable: true }`.
 * route.ts branches on the outcome and renders a clean typed response for each —
 * there is no longer a raw HTTP 422 with an internal error message leaking out.
 */

import { readFileSync } from 'node:fs'
import path from 'node:path'
import { runAdapter } from '@/lib/adapters'
import {
  PipelinePlanSchema,
  PipelinePlanInputJsonSchema,
  type PipelinePlan,
  type PlannerOutcome,
  type ClarificationRequest,
} from './types'
import { classifyScope, type ScopeClassification, type ScopeTuple } from '@/lib/vidhi/scope_classifier'
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
// M9 multi-school few-shot injection
//
// gemini-2.5-flash with thinkingBudget=0 ignores system-prompt rules for
// novel tool names not in its training distribution. Message-turn examples
// are the reliable fix: the model treats them as conversation continuation
// and directly mirrors the demonstrated tool selection pattern.
//
// Injected only when the query matches M9 patterns (Pattern A/B/C from
// PLANNER_PROMPT_v2_0.md STEP 0) — zero overhead for non-M9 queries.
// ────────────────────────────────────────────────────────────────────────────

function detectM9Query(query: string): boolean {
  const q = query.toLowerCase()
  // Pattern A: school count keywords
  if (/all\s+7\s+jyotish\s+school/.test(q)) return true
  if (/\b(all|each|every)\s+jyotish\s+school/.test(q)) return true
  if (/all\s+7\s+school/.test(q)) return true
  if (/all\s+schools?\b/.test(q)) return true
  // Pattern C: convergence keywords
  if (q.includes('convergence score') || q.includes('convergence level') ||
      q.includes('convergence metrics') || q.includes('inter-school') ||
      q.includes('school agreement') || q.includes('divergent school') ||
      q.includes('schools agree') || q.includes('schools diverge')) return true
  // Pattern B: 2+ Jyotish school names present in query
  const schools = ['parashari', 'jaimini', 'tajika', 'nadi', 'yogini']
  const shortSchools = ['kp', 'bnn']
  let hits = schools.filter(s => q.includes(s)).length
  hits += shortSchools.filter(s => new RegExp(`\\b${s}\\b`).test(q)).length
  return hits >= 2
}

function buildM9FewShotMessages(manifestStr: string): Array<{ role: 'user' | 'assistant'; content: string }> {
  const manifest = JSON.parse(manifestStr) as unknown
  const emptyHistory = { turns: [], was_summarized: false }

  // Example 1: all-schools career query → R31 (multi_school_signal_lookup) + R32 (convergence_score_lookup)
  const ex1User = JSON.stringify({
    native_id: 'example', manifest, history: emptyHistory,
    query: 'How do all 7 Jyotish schools read my career prospects?',
  })
  const ex1Assistant = JSON.stringify({
    query_class: 'multi_school_triangulation',
    query_intent_summary: 'Multi-school career signal coverage and convergence metrics.',
    asset_bundle: [
      { asset_id: 'FORENSIC', priority: 1, reason: 'Floor: career-significator placements.' },
      { asset_id: 'MSR', priority: 1, reason: 'Floor: signal list for coverage lookup.' },
    ],
    tool_calls: [
      { tool_name: 'multi_school_signal_lookup', params: { topic: 'career', domains: ['CAREER'] }, token_budget: 800, priority: 1, reason: 'R31: all 7 schools signal coverage for career.' },
      { tool_name: 'convergence_score_lookup', params: { domain: 'CAREER' }, token_budget: 400, priority: 1, reason: 'R32: inter-school convergence score for CAREER.' },
    ],
    synthesis_guidance: 'Lead with convergence level for CAREER. Enumerate schools by coverage type. Flag divergent schools.',
    forward_looking: false, dasha_context_required: false,
    expected_output_shape: 'structured_data', domains: ['career'], history_mode: 'research',
    prior_turn_relevance: { used: 0, reason: 'No prior turns relevant.', mode: 'independent' },
  })

  // Example 2: convergence-only query → R32 alone (convergence_score_lookup)
  const ex2User = JSON.stringify({
    native_id: 'example', manifest, history: emptyHistory,
    query: 'What is the inter-school convergence score for my spiritual domain? Are there any divergent schools?',
  })
  const ex2Assistant = JSON.stringify({
    query_class: 'multi_school_triangulation',
    query_intent_summary: 'Convergence score for SPIRITUAL domain plus divergence analysis.',
    asset_bundle: [
      { asset_id: 'FORENSIC', priority: 1, reason: 'Floor: spiritual-domain significators.' },
    ],
    tool_calls: [
      { tool_name: 'convergence_score_lookup', params: { domain: 'SPIRITUAL' }, token_budget: 400, priority: 1, reason: 'R32: inter-school convergence score for SPIRITUAL.' },
    ],
    synthesis_guidance: 'State convergence level and overall agreement. Identify any divergent school.',
    forward_looking: false, dasha_context_required: false,
    expected_output_shape: 'single_answer', domains: ['spiritual'], history_mode: 'research',
    prior_turn_relevance: { used: 0, reason: 'No prior turns relevant.', mode: 'independent' },
  })

  return [
    { role: 'user' as const, content: ex1User },
    { role: 'assistant' as const, content: ex1Assistant },
    { role: 'user' as const, content: ex2User },
    { role: 'assistant' as const, content: ex2Assistant },
  ]
}

// ────────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────────

/** Extract the first balanced JSON object `{...}` from a string.
 *  Returns the original string unchanged if no object is found. */
function extractFirstJsonObject(text: string): string {
  const start = text.indexOf('{')
  if (start === -1) return text
  let depth = 0
  let inString = false
  let escaped = false
  for (let i = start; i < text.length; i++) {
    const ch = text[i]
    if (escaped) { escaped = false; continue }
    if (ch === '\\' && inString) { escaped = true; continue }
    if (ch === '"') { inString = !inString; continue }
    if (inString) continue
    if (ch === '{') depth++
    else if (ch === '}') { depth--; if (depth === 0) return text.slice(start, i + 1) }
  }
  return text
}

// ────────────────────────────────────────────────────────────────────────────
// Parse-attempt helper — used for both the primary LLM output and the single
// repair-retry output. Never throws; returns a discriminated result so the
// caller can decide whether to repair (first failure) or fault (second failure).
// ────────────────────────────────────────────────────────────────────────────

type ParseAttempt =
  | { ok: true; data: PipelinePlan; rawArgs: unknown }
  | { ok: false; reason: string }

function tryBuildPlan(rawText: string): ParseAttempt {
  if (!rawText || !rawText.trim()) {
    return { ok: false, reason: 'LLM planner returned no text output' }
  }
  // Strip optional ```json ... ``` fences and extract the first balanced JSON object.
  // Some LLMs (including sonnet-4.x) append explanatory text after the closing }
  // which causes "Unexpected non-whitespace character after JSON at position N".
  const fenceStripped = rawText.replace(/^```(?:json)?\s*/im, '').replace(/\s*```\s*$/m, '').trim()
  const jsonText = extractFirstJsonObject(fenceStripped)
  let rawArgs: unknown
  try {
    rawArgs = JSON.parse(jsonText)
  } catch (parseErr) {
    return { ok: false, reason: `LLM planner returned non-JSON text output: ${String(parseErr)}` }
  }
  const parsed = PipelinePlanSchema.safeParse(rawArgs)
  if (!parsed.success) {
    return { ok: false, reason: `LLM planner returned schema-invalid output: ${parsed.error.message}` }
  }
  return { ok: true, data: parsed.data, rawArgs }
}

// ────────────────────────────────────────────────────────────────────────────
// Clarification builder — turns the deterministic classifier's low-confidence
// signal into a user-facing ClarificationRequest. NOTE: the classifier's
// `fallback_prompt` is an LLM-classification PROMPT (the full INTENT_CLASSIFY
// template), not something a user should read — so we synthesize a concise,
// user-facing question here and use the tuple's unknown/default dimensions to
// populate `missing_scope_dims`. (Judgment call documented in the W4 report.)
// ────────────────────────────────────────────────────────────────────────────

function buildClarificationFromScope(classification: ScopeClassification): ClarificationRequest {
  const t = classification.scope_tuple
  const missing_scope_dims: string[] = []
  if (t.intent === 'unknown') missing_scope_dims.push('intent')
  if (t.domains.length === 1 && t.domains[0] === 'general') missing_scope_dims.push('domain')

  const question =
    'I want to make sure I read the right part of the chart. Could you clarify what ' +
    "you'd like to know — a specific life area (career, wealth, marriage, health, " +
    'children, education, spirituality), the timing of events, a remedy, or an overall ' +
    'chart reading?'

  return {
    outcome: 'clarification_needed',
    question,
    missing_scope_dims,
    suggested_options: [
      'Career & profession',
      'Wealth & finances',
      'Marriage & relationships',
      'Health',
      'Timing of a specific event',
      'Remedies',
      'Overall chart reading',
    ],
  }
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
  suppliedScopeTuple?: ScopeTuple,
): Promise<PlannerOutcome> {
  // ── Step 1: deterministic scope classification (BEFORE the LLM call) ────────
  // W4 core step 1. Runs on the raw incoming query text. A low-confidence /
  // unmatched classification (the classifier's own `fallback_recommended` signal)
  // short-circuits to a ClarificationRequest so genuinely ambiguous queries ask a
  // question instead of silently guessing a plan — and we skip the LLM cost.
  const classification = classifyScope(query)
  let scopeTuple: ScopeTuple = classification.scope_tuple
  let fallbackRecommended = classification.fallback_recommended

  // W6.1 fix-cycle (native-directed, trace c332bf16-1641-4f70-b15c-65ea33b589ee):
  // a caller-supplied scope_tuple with a resolved intent (C-1 signature's
  // `scope_tuple?` param) is an explicit, out-of-band scope declaration — it must
  // be trusted over the deterministic text classifier's own guess, and it must be
  // able to bypass a clarification_needed the classifier would otherwise produce.
  // Domains fall back to the classifier's own result only when the caller didn't
  // supply any (an empty/['general']-only array is treated as "not supplied").
  if (suppliedScopeTuple && suppliedScopeTuple.intent !== 'unknown') {
    const suppliedDomains =
      suppliedScopeTuple.domains.length > 0 &&
      !(suppliedScopeTuple.domains.length === 1 && suppliedScopeTuple.domains[0] === 'general')
        ? suppliedScopeTuple.domains
        : scopeTuple.domains
    scopeTuple = { ...suppliedScopeTuple, domains: suppliedDomains }
    fallbackRecommended = false
  }

  if (fallbackRecommended) {
    emitTrace?.({
      event: 'step_done',
      query_id: queryId ?? nativeId,
      step: {
        query_id: queryId ?? nativeId,
        step_seq: 0,
        step_name: 'scope_clarification',
        step_type: 'deterministic',
        status: 'done',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        latency_ms: 0,
        data_summary: {
          result: scopeTuple.intent,
          query_class: scopeTuple.intent,
          planning_confidence: classification.confidence,
          reason: 'fallback_recommended',
        },
        payload: { prompt_preview: classification.matched_rules.join(', ') },
      },
    })
    return buildClarificationFromScope(classification)
  }

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
  let interaction: Awaited<ReturnType<typeof runAdapter>> | undefined
  let lastErr: unknown
  let activeModelId = plannerModelId
  let fallbackWasUsed = false
  for (let attempt = 0; attempt <= MAX_PLANNER_RETRIES; attempt++) {
    activeModelId = (attempt > 0 && fallbackModelId && (isRateLimitError(lastErr) || isServerError(lastErr)))
      ? fallbackModelId
      : plannerModelId
    fallbackWasUsed = activeModelId !== plannerModelId
    try {
      interaction = await runAdapter({
        callType: 'planner_fast',
        modelOverride: { modelId: activeModelId },
        systemPrompt: getSystemPrompt(),
        messages: [
          ...(detectM9Query(query) ? buildM9FewShotMessages(compressedManifestStr) : []),
          { role: 'user', content: userMessage },
        ],
        temperature: 0,
        disableSdkRetry: true,
        reasoning: 'disable',
        responseSchema: PipelinePlanInputJsonSchema,
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
      // W4 fault contract: a provider error that exhausted the retry budget is a
      // TYPED fault return, not a throw. Provider errors are transient in class, so
      // retryable:true — the caller may retry or degrade.
      return {
        outcome: 'fault',
        reason: `LLM planner call failed: ${err instanceof Error ? err.message : String(err)}`,
        retryable: true,
      }
    }
  }
  if (!interaction) {
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
    return {
      outcome: 'fault',
      reason: `LLM planner call failed: ${lastErr instanceof Error ? lastErr.message : String(lastErr)}`,
      retryable: true,
    }
  }
  const latency_ms = Date.now() - start

  if (queryId) {
    void writeLlmCallLog({
      query_id: queryId,
      conversation_id: null,
      call_stage: 'planner',
      model_id: activeModelId,
      provider: resolveProvider(activeModelId),
      input_tokens: interaction!.usage.inputTokens ?? null,
      output_tokens: interaction!.usage.outputTokens ?? null,
      reasoning_tokens: null,
      latency_ms,
      cost_usd: computeCostUsd(getModelPricingSync(activeModelId), {
        input_tokens: interaction!.usage.inputTokens ?? null,
        output_tokens: interaction!.usage.outputTokens ?? null,
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
      input_tokens: interaction!.usage.inputTokens ?? 0,
      output_tokens: interaction!.usage.outputTokens ?? 0,
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

  const rawText = interaction!.finalText ?? ''

  // ── Parse + validate, with exactly ONE structured repair-retry ──────────────
  // W4 core step 2 / the live HTTP-422 bug fix. When the LLM returns non-JSON or
  // schema-invalid output, we re-issue the SAME client/model call once with the
  // model's own bad output attached and an explicit corrective instruction to
  // return ONLY valid JSON matching the schema. If the repair ALSO fails, we
  // return a TYPED `fault` — never a throw — so route.ts renders a clean,
  // honest error instead of a raw 422 leaking the internal parse error.
  const primaryAttempt = tryBuildPlan(rawText)
  // SAMĀPTI A7-N8-AUDIT F-23: capture whether the FIRST attempt actually parsed, and the
  // reason if it did not. Previously this was known only inside this function and lost at
  // the return, so the consult route wrote the constant `parsing_success: true` / a null
  // parse_error for every request — a value that could never go red.
  const parsedOnFirstAttempt = primaryAttempt.ok
  const firstParseError = primaryAttempt.ok ? null : primaryAttempt.reason
  let okData: PipelinePlan
  let rawPlannerArgs: unknown
  if (primaryAttempt.ok) {
    okData = primaryAttempt.data
    rawPlannerArgs = primaryAttempt.rawArgs
  } else {
    console.warn(
      '[pipeline_planner] primary planner output unparseable — attempting ONE repair-retry.' +
      ' reason=%s model=%s query_id=%s',
      primaryAttempt.reason, activeModelId, queryId ?? 'unknown',
    )
    emitTrace?.({
      event: 'step_start',
      query_id: stepQueryId,
      step: {
        query_id: stepQueryId,
        step_seq: 0,
        step_name: 'llm_planner_repair',
        step_type: 'llm',
        status: 'running',
        started_at: new Date().toISOString(),
        data_summary: { model: activeModelId, reason: primaryAttempt.reason },
        payload: {},
      },
    })

    const REPAIR_INSTRUCTION =
      'Your previous response was not valid JSON matching the required planner schema ' +
      `(${primaryAttempt.reason}). Return ONLY a single valid JSON object matching the ` +
      'planner schema — no prose, no markdown code fences, and nothing before or after ' +
      'the JSON object.'

    let repairInteraction: Awaited<ReturnType<typeof runAdapter>> | undefined
    try {
      repairInteraction = await runAdapter({
        callType: 'planner_fast',
        modelOverride: { modelId: activeModelId },
        systemPrompt: getSystemPrompt(),
        messages: [
          ...(detectM9Query(query) ? buildM9FewShotMessages(compressedManifestStr) : []),
          { role: 'user', content: userMessage },
          { role: 'assistant', content: rawText || '(empty response)' },
          { role: 'user', content: REPAIR_INSTRUCTION },
        ],
        temperature: 0,
        disableSdkRetry: true,
        reasoning: 'disable',
        responseSchema: PipelinePlanInputJsonSchema,
      })
    } catch (repairErr) {
      const reason = `LLM planner repair-retry call failed: ${repairErr instanceof Error ? repairErr.message : String(repairErr)}`
      emitTrace?.({
        event: 'step_error',
        query_id: stepQueryId,
        step: {
          query_id: stepQueryId,
          step_seq: 0,
          step_name: 'llm_planner_repair',
          step_type: 'llm',
          status: 'error',
          started_at: plannerStepStart,
          completed_at: new Date().toISOString(),
          latency_ms: Date.now() - plannerStartMs,
          data_summary: { model: activeModelId, planner_active: false, error_reason: reason },
          payload: { error_message: reason },
        },
      })
      // The repair CALL itself failed (provider error) — transient class → retryable.
      return { outcome: 'fault', reason, retryable: true }
    }

    const repairAttempt = tryBuildPlan(repairInteraction.finalText ?? '')
    if (!repairAttempt.ok) {
      const reason = `LLM planner returned unparseable output after one repair-retry: ${repairAttempt.reason}`
      emitTrace?.({
        event: 'step_error',
        query_id: stepQueryId,
        step: {
          query_id: stepQueryId,
          step_seq: 0,
          step_name: 'llm_planner_repair',
          step_type: 'llm',
          status: 'error',
          started_at: plannerStepStart,
          completed_at: new Date().toISOString(),
          latency_ms: Date.now() - plannerStartMs,
          data_summary: { model: activeModelId, planner_active: false, error_reason: reason },
          payload: { error_message: reason },
        },
      })
      // The model keeps returning malformed output — repeating won't help → NOT retryable.
      return { outcome: 'fault', reason, retryable: false }
    }
    okData = repairAttempt.data
    rawPlannerArgs = repairAttempt.rawArgs
  }

  const parsed = { data: okData }

  // Detect soft-optional string fields that the LLM returned as null (before coercion).
  // PipelinePlanSchema coerces null → undefined for these fields so parsing succeeds,
  // but we capture the original null here for audit emission below.
  const SOFT_OPTIONAL_STRING_FIELDS = ['synthesis_guidance', 'planning_rationale'] as const
  const coercedFields = new Set<string>()
  if (rawPlannerArgs !== null && typeof rawPlannerArgs === 'object') {
    const raw = rawPlannerArgs as Record<string, unknown>
    for (const field of SOFT_OPTIONAL_STRING_FIELDS) {
      if (raw[field] === null) coercedFields.add(field)
    }
  }

  // Emit audit trace for any soft-optional null coercions so they appear in
  // query_trace_steps and are visible in Cloud Run logs. A silent coercion
  // would mask systemic model non-compliance across providers.
  if (coercedFields.size > 0) {
    console.warn(
      '[pipeline_planner] soft-optional null fields coerced to undefined — fields=%s model=%s query_id=%s',
      [...coercedFields].join(','),
      activeModelId,
      queryId ?? 'unknown',
    )
    emitTrace?.({
      event: 'step_done',
      query_id: stepQueryId,
      step: {
        query_id: stepQueryId,
        step_seq: 0,
        step_name: 'planner_field_coerced',
        step_type: 'llm',
        status: 'done',
        started_at: plannerStepStart,
        completed_at: new Date().toISOString(),
        latency_ms: 0,
        data_summary: {
          model: activeModelId,
          coercion_count: coercedFields.size,
        },
        payload: {
          coerced_fields: [...coercedFields],
        },
      },
    })
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

  // Attach the deterministic scope tuple (W4 core step 1) and return the
  // successful 'plan' variant of the PlannerOutcome union.
  parsed.data.scope_tuple = scopeTuple
  // SAMĀPTI A7-N8-AUDIT F-23: carry the planner's REAL observability values across the
  // boundary. Each is already computed above; none is new work, none is estimated. The
  // consult route consumes these instead of the constants it used to write.
  return {
    outcome: 'plan',
    plan: parsed.data,
    metrics: {
      planning_confidence: classification.confidence,
      fallback_used: fallbackWasUsed,
      active_model_id: activeModelId,
      parsed_on_first_attempt: parsedOnFirstAttempt,
      first_parse_error: firstParseError,
    },
  }
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
