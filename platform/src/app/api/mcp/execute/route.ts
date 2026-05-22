/**
 * /api/mcp/execute — MCP orchestrator HTTP entry point.
 *
 * Accepts POST requests from the platform-mcp sidecar service (MCP-2-S1).
 * Auth model: two-layer.
 *   Layer 1 (service-to-service): X-MCP-Internal-Token header (a shared
 *     secret or OIDC token from Cloud Run; validates that the caller is
 *     the trusted amjis-mcp service, not an arbitrary internet client).
 *   Layer 2 (resolved principal): X-MCP-User, X-MCP-Audience-Tier,
 *     X-MCP-Key-Id headers (set by the MCP server after its own Bearer
 *     key validation against mcp_api_keys).
 *
 * Supported tools:
 *   ask_madhav  — full pipeline (planner → tools → synthesis → envelope)
 *   plan_query  — planner only; returns PipelinePlan without executing
 *   execute_plan — run from arbitration onward given an explicit plan
 *
 * Design: single-shot only (D10). No conversation history is loaded or
 * written. The host chat owns the thread; MCP calls are stateless.
 *
 * Singleton chart (D11): always Abhisek's chart, resolved from
 * MARSYS_MCP_CHART_ID env var, with DB fallback if not set.
 *
 * Returns: McpEnvelope JSON (never a streaming response).
 */

import 'server-only'
import { NextResponse } from 'next/server'
import { query } from '@/lib/db/client'
import { callPipelinePlanner as runPlanner, PlannerFault } from '@/lib/pipeline/pipeline_planner'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { PipelinePlanSchema } from '@/lib/pipeline/types'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import { getTool } from '@/lib/retrieve/index'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { createOrchestrator } from '@/lib/synthesis/index'
import { traceEmitter } from '@/lib/trace/emitter'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { DEFAULT_STACK_ID } from '@/lib/models/registry'
import { configService } from '@/lib/config/index'
import {
  buildEnvelope,
  buildErrorEnvelope,
  buildEpistemicsBlock,
  buildSynthesisAudit,
} from '@/lib/mcp/epistemics'
import { generateSuggestedFollowups } from '@/lib/mcp/suggested_followups'
import { checkRateLimit, buildRateLimitErrorEnvelope } from '@/lib/mcp/rate_limiter'
import { logPrediction } from '@/lib/mcp/ppl_writer'
import type { McpCitation, PplEntry } from '@/lib/mcp/types'
import type { ToolBundle } from '@/lib/retrieve/index'

export const maxDuration = 120

// ── L2.5 tool set (mirrors B.11 enforcement in consume/route.ts) ──────────────

const L2_5_TOOLS = ['msr_sql', 'query_msr_aggregate', 'pattern_register',
  'resonance_register', 'cluster_atlas', 'contradiction_register', 'cgm_graph_walk']

// ── Service-to-service token validation ───────────────────────────────────────

function validateServiceToken(req: Request): boolean {
  const token = req.headers.get('x-mcp-internal-token')
  const expected = process.env.MCP_INTERNAL_TOKEN
  if (!expected) {
    // In development (no env var set), allow all internal calls for easier local testing.
    // Production must set MCP_INTERNAL_TOKEN.
    if (process.env.NODE_ENV === 'development') return true
    console.error('[mcp:execute] MCP_INTERNAL_TOKEN not set in production')
    return false
  }
  return token === expected
}

// ── Singleton chart resolution ─────────────────────────────────────────────────

interface ChartRow {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
}

async function resolveSingletonChart(): Promise<ChartRow | null> {
  // Prefer the env override (fastest path, avoids a DB round-trip).
  const envChartId = process.env.MARSYS_MCP_CHART_ID
  if (envChartId) {
    try {
      const { rows } = await query<ChartRow>(
        'SELECT id, name, birth_date, birth_time, birth_place FROM charts WHERE id=$1',
        [envChartId]
      )
      return rows[0] ?? null
    } catch (err) {
      console.error('[mcp:execute] chart lookup by MARSYS_MCP_CHART_ID failed', err)
    }
  }
  // Fallback: pick the first chart in the DB (singleton assumption).
  try {
    const { rows } = await query<ChartRow>(
      'SELECT id, name, birth_date, birth_time, birth_place FROM charts ORDER BY created_at ASC LIMIT 1'
    )
    return rows[0] ?? null
  } catch (err) {
    console.error('[mcp:execute] singleton chart fallback lookup failed', err)
    return null
  }
}

// ── Legacy QueryPlan adapter (mirrors consume/route.ts) ───────────────────────

type LegacyQueryPlan = {
  query_plan_id: string
  query_text: string
  query_class: PipelinePlan['query_class']
  domains: string[]
  forward_looking: boolean
  audience_tier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
  tools_authorized: string[]
  history_mode: 'synthesized' | 'research'
  panel_mode: boolean
  expected_output_shape: 'single_answer' | 'three_interpretation' | 'time_indexed_prediction' | 'structured_data'
  manifest_fingerprint: string
  schema_version: '1.0'
  planets?: string[]
  houses?: number[]
  dasha_context_required?: boolean
  graph_seed_hints?: string[]
  vector_search_filter?: { doc_type?: string[]; layer?: string }
  time_window?: { start: string; end: string }
  tool_calls?: PipelinePlan['tool_calls']
}

function planToLegacy(plan: PipelinePlan, queryId: string, manifestFingerprint: string): LegacyQueryPlan {
  const toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))
  return {
    query_plan_id: queryId,
    query_text: plan.query_text ?? '',
    query_class: plan.query_class,
    domains: plan.domains ?? [],
    forward_looking: plan.forward_looking ?? false,
    audience_tier: plan.audience_tier ?? 'client',
    tools_authorized: toolsAuthorized,
    history_mode: plan.history_mode ?? 'synthesized',
    panel_mode: plan.panel_mode ?? false,
    expected_output_shape: plan.expected_output_shape ?? 'three_interpretation',
    manifest_fingerprint: manifestFingerprint,
    schema_version: '1.0',
    planets: plan.planets,
    houses: plan.houses,
    dasha_context_required: plan.dasha_context_required,
    graph_seed_hints: plan.graph_seed_hints,
    vector_search_filter: plan.vector_search_filter,
    time_window: plan.time_window,
    tool_calls: plan.tool_calls,
  }
}

// ── B.11 floor enforcement (mirrors consume/route.ts) ─────────────────────────

function enforceB11Floor(plan: PipelinePlan, toolsAuthorized: string[]): { plan: PipelinePlan; toolsAuthorized: string[]; warnings: string[] } {
  const warnings: string[] = []
  const hasL25 = toolsAuthorized.some(t => L2_5_TOOLS.includes(t))
  if (!hasL25) {
    if (plan.query_class === 'predictive') {
      const domainSearchQuery = (plan.domains ?? []).join(' ') || 'relationships family marriage'
      plan.tool_calls.push(
        { tool_name: 'msr_sql', params: { forward_looking: true }, token_budget: 600, priority: 1 as const, reason: 'B.11 predictive floor' },
        { tool_name: 'vector_search', params: { query_text: domainSearchQuery, doc_type: ['domain_report'], top_k: 6 }, token_budget: 500, priority: 1 as const, reason: 'B.11 predictive floor' },
        { tool_name: 'pattern_register', params: { forward_looking: true }, token_budget: 400, priority: 2 as const, reason: 'B.11 floor R7a' },
      )
      toolsAuthorized.push('msr_sql', 'vector_search', 'pattern_register')
    } else {
      plan.tool_calls.push(
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'B.11 floor enforcement' },
        { tool_name: 'cgm_graph_walk', params: {}, token_budget: 400, priority: 2 as const, reason: 'B.11 floor enforcement' },
      )
      toolsAuthorized.push('msr_sql', 'cgm_graph_walk')
    }
    warnings.push('B.11 floor enforced: L2.5 tools injected into plan')
  }
  return { plan, toolsAuthorized, warnings }
}

// ── Dasha floor (mirrors consume/route.ts) ─────────────────────────────────────

function ensureDashaFloor(plan: PipelinePlan, toolsAuthorized: string[]): void {
  if (
    (plan.query_class === 'predictive' || plan.query_class === 'holistic') &&
    !toolsAuthorized.includes('chart_facts_query')
  ) {
    plan.tool_calls.push({
      tool_name: 'chart_facts_query',
      params: { category: 'dasha_vimshottari', limit: 50 },
      token_budget: 600,
      priority: 1 as const,
      reason: 'dasha context floor',
    })
    toolsAuthorized.push('chart_facts_query')
  }
}

// ── Citation extraction ────────────────────────────────────────────────────────

function extractMcpCitations(text: string, toolResults: ToolBundle[]): McpCitation[] {
  const signalIdRegex = /SIG\.MSR\.(\d+)/g
  const seen = new Set<string>()
  const citations: McpCitation[] = []

  let match: RegExpExecArray | null
  while ((match = signalIdRegex.exec(text)) !== null) {
    const id = `SIG.MSR.${match[1]}`
    if (seen.has(id)) continue
    seen.add(id)
    // Determine layer from tool results
    const layer: McpCitation['layer'] = 'L2.5'
    // Find snippet from tool results
    let snippet: string | undefined
    for (const tb of toolResults) {
      for (const r of tb.results) {
        if (r.signal_id === id && r.content) {
          snippet = r.content.slice(0, 200)
          break
        }
      }
      if (snippet) break
    }
    citations.push({ id, layer, snippet })
  }
  return citations
}

// ── POST handler ───────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  // Layer 1: service-to-service auth
  if (!validateServiceToken(request)) {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'auth', message: 'Invalid service token', remediation: 'MCP server must pass MCP_INTERNAL_TOKEN header' }),
      { status: 401 }
    )
  }

  // Read resolved principal from headers (set by MCP server after Bearer validation)
  const userUid = request.headers.get('x-mcp-user')
  const audienceTierHeader = request.headers.get('x-mcp-audience-tier') as 'client' | 'super_admin' | null
  const keyId = request.headers.get('x-mcp-key-id')

  if (!userUid || !audienceTierHeader || !keyId) {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'auth', message: 'Missing principal headers' }),
      { status: 401 }
    )
  }

  const audienceTier: 'client' | 'super_admin' = audienceTierHeader === 'super_admin' ? 'super_admin' : 'client'

  // Rate limiting: conservative 4000-token estimate for ask_madhav/execute_plan (actual deducted post-synthesis via trace logger).
  const rateLimitResult = await checkRateLimit(keyId, 4000)
  if (!rateLimitResult.allowed) {
    return NextResponse.json(
      buildRateLimitErrorEnvelope(rateLimitResult.reason ?? 'rate_limit'),
      { status: 429, headers: { 'Retry-After': String(rateLimitResult.retry_after_seconds ?? 60) } }
    )
  }

  // Parse body
  let body: { tool: string; params: Record<string, unknown> }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'validation', message: 'Invalid JSON body' }),
      { status: 400 }
    )
  }

  const { tool, params } = body
  if (!tool || typeof tool !== 'string') {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'validation', message: 'tool field is required' }),
      { status: 400 }
    )
  }

  // Resolve singleton chart (D11)
  const chart = await resolveSingletonChart()
  if (!chart) {
    return NextResponse.json(
      buildErrorEnvelope({ error_class: 'internal', message: 'Singleton chart not found', remediation: 'Set MARSYS_MCP_CHART_ID env var' }),
      { status: 503 }
    )
  }

  const queryId = crypto.randomUUID()

  // Noop trace emitter (MCP calls don't need the same real-time event fan-out
  // as the chat route, but they DO write to query_trace_steps via traceEmitter).
  let stepSeq = 0
  const nextSeq = () => ++stepSeq
  const emit = (event: Parameters<typeof traceEmitter.emitStep>[0]) => {
    if (event.step) event.step.user_id = userUid
    traceEmitter.emitStep(event)
  }

  // ── plan_query — planner only ────────────────────────────────────────────────
  if (tool === 'plan_query') {
    const queryText = String(params?.query ?? '')
    if (!queryText.trim()) {
      return NextResponse.json(
        buildErrorEnvelope({ trace_id: queryId, error_class: 'validation', message: 'query param is required' }),
        { status: 400 }
      )
    }

    const [plannerModelId] = await Promise.all([
      getEffectiveModel(DEFAULT_STACK_ID, 'planner_fast', 'primary', request),
    ])

    let plan: PipelinePlan
    try {
      plan = await runPlanner(queryText, [], plannerModelId, chart.id, emit, queryId, undefined)
    } catch (err) {
      if (err instanceof PlannerFault) {
        return NextResponse.json(
          buildErrorEnvelope({ trace_id: queryId, error_class: 'planner_error', message: err.message }),
          { status: 422 }
        )
      }
      throw err
    }
    plan.query_plan_id = queryId
    plan.query_text = queryText
    plan.audience_tier = audienceTier

    return NextResponse.json(
      buildEnvelope({
        trace_id: queryId,
        audience_tier: audienceTier,
        epistemics: buildEpistemicsBlock({ surgical: false }),
        result: plan,
        plan,
        synthesis_audit: null,
        suggested_followups: [],
      })
    )
  }

  // ── ask_madhav or execute_plan — full pipeline ───────────────────────────────

  let queryText: string
  let plan: PipelinePlan

  if (tool === 'ask_madhav') {
    queryText = String(params?.query ?? '')
    if (!queryText.trim()) {
      return NextResponse.json(
        buildErrorEnvelope({ trace_id: queryId, error_class: 'validation', message: 'query param is required' }),
        { status: 400 }
      )
    }
    const contextHint = params?.context_hint ? `\n\n[Context from prior turns: ${String(params.context_hint)}]` : ''
    const effectiveQuery = contextHint ? `${queryText}${contextHint}` : queryText

    const [plannerModelId] = await Promise.all([
      getEffectiveModel(DEFAULT_STACK_ID, 'planner_fast', 'primary', request),
    ])

    try {
      plan = await runPlanner(effectiveQuery, [], plannerModelId, chart.id, emit, queryId, undefined)
    } catch (err) {
      if (err instanceof PlannerFault) {
        return NextResponse.json(
          buildErrorEnvelope({ trace_id: queryId, error_class: 'planner_error', message: err.message }),
          { status: 422 }
        )
      }
      throw err
    }
  } else if (tool === 'execute_plan') {
    // Validate the provided plan
    const planInput = params?.plan
    const parsed = PipelinePlanSchema.safeParse(planInput)
    if (!parsed.success) {
      return NextResponse.json(
        buildErrorEnvelope({ trace_id: queryId, error_class: 'validation', message: 'Invalid PipelinePlan', remediation: parsed.error.message }),
        { status: 400 }
      )
    }
    plan = parsed.data
    queryText = plan.query_text ?? String(params?.query ?? 'execute_plan')
  } else {
    return NextResponse.json(
      buildErrorEnvelope({ trace_id: queryId, error_class: 'validation', message: `Unknown tool: ${tool}`, remediation: 'Supported tools: ask_madhav, plan_query, execute_plan' }),
      { status: 400 }
    )
  }

  // Stamp route-controlled fields
  plan.query_plan_id = queryId
  plan.query_text = queryText
  plan.audience_tier = audienceTier

  try {
    const manifest = await loadManifest('00_ARCHITECTURE/CAPABILITY_MANIFEST.json', '00_ARCHITECTURE/manifest_overrides.yaml')
    plan.manifest_fingerprint = manifest.fingerprint

    // Resolve synthesis model ID (still needed for orchestrator.synthesize).
    const modelId = await getEffectiveModel(DEFAULT_STACK_ID, 'synthesis', 'primary', request)

    // F.7 fix (MCPT v3.1.0-S1): token-budget allocation call removed from MCP path.
    // Token budgets are passed through as-is from the planner plan.
    // The allocation helper is retained for the /consume (web) path only.

    let toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))

    // B.11 floor enforcement
    const b11Result = enforceB11Floor(plan, toolsAuthorized)
    plan = b11Result.plan
    toolsAuthorized = b11Result.toolsAuthorized
    const warnings = b11Result.warnings

    // Dasha floor
    ensureDashaFloor(plan, toolsAuthorized)
    toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))

    // Hydrate bundle
    const bundle = await hydrateBundle(plan, manifest)
    const queryPlan = planToLegacy(plan, queryId, manifest.fingerprint)

    // Execute tools in parallel
    const cache = createToolCache()
    const plannerParamsMap = new Map<string, Record<string, unknown>>(
      plan.tool_calls.map(tc => [tc.tool_name, tc.params])
    )
    const toolResults = await Promise.all(
      toolsAuthorized.map(async (toolName) => {
        const t = getTool(toolName)
        if (!t) return null
        try {
          return await executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName))
        } catch {
          return null
        }
      })
    )
    const validToolResults = toolResults.filter((r): r is NonNullable<typeof r> => r !== null)

    // Mode override from ask_madhav params
    const modeParam = String(params?.mode ?? 'auto')
    const isSurgical = modeParam === 'factual'

    // Synthesis
    const orchestrator = createOrchestrator({ panel_opt_in: false })
    const { result } = await orchestrator.synthesize({
      query: queryText,
      query_plan: queryPlan,
      bundle,
      tool_results: validToolResults,
      conversation_history: [],  // D10: single-shot, no history
      selected_model_id: modelId,
      style: audienceTier === 'super_admin' ? 'acharya' : 'client',
      audience_tier: audienceTier,
      cache,
      chart_context: {
        name: chart.name ?? 'Abhisek Mohanty',
        birth_date: chart.birth_date,
        birth_time: chart.birth_time,
        birth_place: chart.birth_place,
      },
      synthesis_guidance: plan.synthesis_guidance,
    })

    // Collect the full text output from the stream.
    const answerText = await result.text

    // Extract citations
    const citations = extractMcpCitations(answerText, validToolResults)

    // Build synthesis audit
    const toolsFired = validToolResults.map(r => r.tool_name)
    const dominantSignals = citations.slice(0, 3).map(c => c.id)
    const domainsTouched = plan.domains ?? []
    const synthesisAudit = buildSynthesisAudit({
      tools_fired: toolsFired,
      dominant_signals: dominantSignals,
      domains_touched: domainsTouched,
    })

    // Warn if B.11 floor was bypassed (should not happen in normal operation)
    if (!synthesisAudit.holistic_read_passed && !isSurgical) {
      warnings.push('synthesis_audit.holistic_read_passed=false: no L2.5 tool fired despite non-surgical mode')
    }

    // Build epistemics
    const epistemics = buildEpistemicsBlock({
      surgical: isSurgical,
      confidence_band: 'medium',
      horizon_days: plan.forward_looking ? 90 : null,
      falsifier: plan.forward_looking ? 'Native circumstances change materially from current state' : null,
    })

    // Suggested follow-ups
    const suggestedFollowups = generateSuggestedFollowups(plan, domainsTouched)

    // ── PPL auto-logging for predictive calls (G4 / MCP_BRIEF §4.1) ───────────
    //
    // Per PPL discipline rule #4: "held-out prospective data is sacrosanct;
    // the model never sees outcome before prediction." Logging happens here,
    // SERVER-SIDE, before the response is returned to the caller. This ensures
    // governance compliance regardless of what the MCP client does with the result.
    //
    // Auto-logging criteria:
    //   1. mode === "predictive" (explicit predictive mode from caller), OR
    //   2. plan.forward_looking === true (planner classified as forward-looking)
    //
    // Each forward-looking domain covered by the synthesis gets one PPL entry.
    // Confidence derives from epistemics. horizon_days from plan if available.
    // falsifier is set to "[AUTO_LOGGED — native to specify falsifier]" as a
    // placeholder: the caller should call log_prediction() directly with a
    // proper falsifier for governance quality.
    //
    // Auto-logged entries are included in predictions_logged[] so the caller
    // can surface them and prompt the native to supply proper falsifiers.

    const predictionsLogged: PplEntry[] = []

    const isExplicitPredictive = modeParam === 'predictive'
    const isPlanForwardLooking = plan.forward_looking === true

    if ((isExplicitPredictive || isPlanForwardLooking) && !isSurgical) {
      // Determine which domains to log (use plan.domains; fall back to one generic entry).
      const logDomains = domainsTouched.length > 0 ? domainsTouched : ['general']

      // Derive horizon from plan.time_window.end or from horizon_days.
      const horizonStr =
        plan.time_window?.end ??
        (epistemics.horizon_days
          ? new Date(Date.now() + epistemics.horizon_days * 86_400_000)
              .toISOString()
              .slice(0, 10)
          : null)

      const emittedAt = new Date().toISOString()

      for (const domain of logDomains) {
        try {
          const predictionId = await logPrediction({
            horizon: horizonStr ?? '[horizon_unspecified — native to fill]',
            domain,
            prediction_text: answerText.slice(0, 500),
            confidence: epistemics.confidence_band ?? 'medium',
            falsifier: '[AUTO_LOGGED — native to specify falsifier]',
            source: {
              key_id: keyId,
              trace_id: queryId,
              caller_context: `auto_logged; mode=${modeParam}; query_class=${plan.query_class}`,
            },
          })
          // Build a PplEntry for the envelope so the caller can surface it.
          predictionsLogged.push({
            pred_id: predictionId,
            emitted_at: emittedAt,
            mode: 'predictive',
            query: queryText.slice(0, 500),
            confidence: epistemics.confidence_band === 'high' ? 0.8
              : epistemics.confidence_band === 'medium' ? 0.6 : 0.4,
            horizon_days: epistemics.horizon_days,
            falsifier: '[AUTO_LOGGED — native to specify falsifier]',
            trace_id: queryId,
          })
        } catch (pplErr) {
          // Non-fatal: PPL write failure logged but does not block the response.
          console.error('[mcp:execute] PPL auto-log failed for domain', domain, pplErr)
        }
      }
    }

    emit({ event: 'done', query_id: queryId })

    return NextResponse.json(
      buildEnvelope({
        trace_id: queryId,
        audience_tier: audienceTier,
        epistemics,
        result: { answer_markdown: answerText },
        citations,
        plan,
        predictions_logged: predictionsLogged,
        synthesis_audit: synthesisAudit,
        suggested_followups: suggestedFollowups,
        warnings,
      })
    )
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    console.error('[mcp:execute] pipeline error', msg)
    return NextResponse.json(
      buildErrorEnvelope({ trace_id: queryId, error_class: 'orchestrator_error', message: msg }),
      { status: 500 }
    )
  }
}
