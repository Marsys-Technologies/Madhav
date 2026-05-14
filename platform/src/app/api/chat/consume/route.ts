import {
  stepCountIs,
  convertToModelMessages,
  createIdGenerator,
  smoothStream,
} from 'ai'
import type { ModelMessage, UIMessage } from 'ai'
import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { consumeSystemPrompt, type ConsumeStyle } from '@/lib/claude/system-prompts'
import {
  getConversation,
  insertConversationWithId,
  replaceConversationMessages,
  updateConversationTitle,
} from '@/lib/conversations'
import { generateConversationTitle } from '@/lib/conversations/title'
import { assembleProvenance, type ToolBundleLike } from '@/lib/consume/provenance_assembler'
import type { ContextUsageEvent, ContextUsageMode, ProvenanceEvent } from '@/types/sse_events'
import {
  DEFAULT_MODEL_ID,
  DEFAULT_STACK_ID,
  TITLE_MODEL_ID,
  STACK_ROUTING,
  getModelMeta,
  isValidModelId,
  supports,
  type ModelStack,
} from '@/lib/models/registry'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { configService } from '@/lib/config/index'
import { callPipelinePlanner as runPlanner, PlannerFault } from '@/lib/pipeline/pipeline_planner'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import { getTool } from '@/lib/retrieve/index'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { runAll, summarize } from '@/lib/validators/index'
import type { ValidationResult } from '@/lib/validators/types'
import { createOrchestrator } from '@/lib/synthesis/index'
import { validateCitations } from '@/lib/synthesis/citation_check'
// PipelineError import removed — citation gate no longer throws post-stream (see citation_error trace event)
import { createAuditConsumer } from '@/lib/audit/consumer'
import { traceEmitter } from '@/lib/trace/emitter'
import type { TraceStep, TraceChunkItem, TraceDataSummary, TracePayload, TraceQueryPlan, TraceToolCallSpec } from '@/lib/trace/types'
import type { ToolBundle, ToolBundleResult } from '@/lib/retrieve/index'
import { res } from '@/lib/errors'
import {
  writeLlmCallLog,
  writeQueryPlanLog,
  writeToolExecutionLog,
  writeContextAssemblyLog,
  resolveProvider,
} from '@/lib/db/monitoring-write'
import { persistObservation, computeCost } from '@/lib/llm/observability'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { getStorageClient } from '@/lib/storage'
import type { ProviderName, TokenUsage } from '@/lib/llm/observability/types'

// ── Trace helpers ─────────────────────────────────────────────────────────────

function toolStepType(toolName: string): TraceStep['step_type'] {
  if (toolName === 'vector_search') return 'vector'
  if (['msr_sql', 'query_msr_aggregate'].includes(toolName)) return 'sql'
  if (['classical_text_search', 'classical_attribution_lookup'].includes(toolName)) return 'sql'
  return 'gcs'
}

function inferLayer(toolName: string): 'L1' | 'L2.5' {
  if (['msr_sql', 'query_msr_aggregate', 'pattern_register', 'resonance_register',
       'cluster_atlas', 'contradiction_register', 'temporal', 'cgm_graph_walk'].includes(toolName)) {
    return 'L2.5'
  }
  return 'L1'
}

function buildToolSummary(toolName: string, result: ToolBundle): TraceDataSummary {
  const totalChars = result.results.reduce((s: number, r: ToolBundleResult) => s + r.content.length, 0)
  const token_estimate = Math.ceil(totalChars / 4)
  if (toolName === 'vector_search') {
    const top_score = result.results[0]?.significance ?? result.results[0]?.confidence ?? 0
    return { chunks_returned: result.results.length, top_score, token_estimate }
  }
  return { rows_returned: result.results.length, tool_name: toolName, token_estimate }
}

function buildToolPayload(toolName: string, result: ToolBundle): TracePayload {
  const layer = inferLayer(toolName)
  const items: TraceChunkItem[] = result.results.map((r: ToolBundleResult) => ({
    id: r.signal_id ?? r.source_canonical_id ?? toolName,
    source: r.source_canonical_id ?? toolName,
    layer,
    token_estimate: Math.ceil(r.content.length / 4),
    text: r.content,
  }))
  return { items }
}

export const maxDuration = 120

const ALLOWED_STYLES: ConsumeStyle[] = ['acharya', 'brief', 'client']

interface RequestBody {
  chartId?: string
  conversationId?: string
  messages?: UIMessage[]
  /** Stack name from ModelStack — replaces the legacy `model` field. */
  stack?: string
  /** @deprecated Kept for backward compat with in-flight requests; ignored when `stack` is provided. */
  model?: string
  style?: string
  panel_opt_in?: boolean
  lel_context_enabled?: boolean
}

export async function POST(request: Request) {
  const setupStart = Date.now()

  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: RequestBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('Invalid JSON body')
  }

  const { chartId, messages } = body
  let { conversationId } = body

  if (!chartId || !messages) {
    return res.badRequest('chartId and messages are required')
  }

  // Resolve synthesis model from stack. Stack takes precedence over the legacy
  // `model` field. Unknown/missing stacks fall back to the default NIM stack.
  const VALID_STACKS = Object.keys(STACK_ROUTING) as ModelStack[]
  const selectedStack: ModelStack = VALID_STACKS.includes(body.stack as ModelStack)
    ? (body.stack as ModelStack)
    : DEFAULT_STACK_ID
  const stackSynthPrimary = await getEffectiveModel(selectedStack, 'synthesis', 'primary', request)
  // Backward-compat: if the legacy `model` field is a known model ID AND no
  // stack was sent (old client), honour it directly so sessions mid-upgrade
  // don't silently switch models on the user.
  const modelId =
    !body.stack && isValidModelId(body.model ?? '')
      ? (body.model as string)
      : stackSynthPrimary
  const modelMeta = getModelMeta(modelId) ?? getModelMeta(DEFAULT_MODEL_ID)!
  const style: ConsumeStyle = ALLOWED_STYLES.includes(body.style as ConsumeStyle)
    ? (body.style as ConsumeStyle)
    : 'acharya'

  // LEL context toggle. Undefined or true = informed mode (LEL included).
  // False = blind mode (LEL excluded; query logged as prospective prediction).
  const lelContextEnabled = body.lel_context_enabled !== false

  let chartResult: Awaited<ReturnType<typeof query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string; client_id: string }>>>
  let profileResult: Awaited<ReturnType<typeof query<{ role: string }>>>
  let reportsResult: Awaited<ReturnType<typeof query<{ domain: string; title: string; version: string }>>>
  try {
    ;[chartResult, profileResult, reportsResult] = await Promise.all([
      query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string; client_id: string }>(
        'SELECT id, name, birth_date, birth_time, birth_place, client_id FROM charts WHERE id=$1',
        [chartId]
      ),
      query<{ role: string }>(
        'SELECT role FROM profiles WHERE id=$1',
        [user.uid]
      ),
      query<{ domain: string; title: string; version: string }>(
        'SELECT domain, title, version FROM reports WHERE chart_id=$1 ORDER BY domain',
        [chartId]
      ),
    ])
  } catch {
    return res.dbError()
  }

  if (!chartResult.rows[0]) return res.notFound('chart')
  const chart = chartResult.rows[0]
  const role = profileResult.rows[0]?.role
  const isSuperAdmin = role === 'super_admin'

  if (!isSuperAdmin && chart.client_id !== user.uid) {
    return res.forbidden()
  }

  let isFirstTurn = false

  if (conversationId) {
    const existing = await getConversation({ id: conversationId, userId: user.uid, isSuperAdmin })
    if (!existing || existing.chart_id !== chartId) {
      return res.notFound('conversation')
    }
  } else {
    conversationId = crypto.randomUUID()
    isFirstTurn = true
    // BUG-1: eager insert before streaming so turn-2 can always find the row.
    // ON CONFLICT DO NOTHING makes this idempotent on retry.
    try {
      await insertConversationWithId({
        id: conversationId,
        chartId,
        userId: user.uid,
        module: 'consume',
      })
    } catch (err) {
      const msg = String(err).toLowerCase()
      if (!msg.includes('duplicate') && !msg.includes('unique') && !msg.includes('conflict')) {
        return res.internal('Failed to initialize conversation. Please retry.')
      }
      // duplicate key = row already exists from a retry → safe to continue
    }
  }

  const finalConversationId = conversationId

  try {
  const lastUserMessage = messages.filter(m => m.role === 'user').at(-1)
  const queryText = extractText(lastUserMessage?.parts ?? [])

  const manifest = await loadManifest('00_ARCHITECTURE/CAPABILITY_MANIFEST.json', '00_ARCHITECTURE/manifest_overrides.yaml')

  // ── Single-path LLM-first planner ─────────────────────────────────────────
  // No flag guard. No circuit breaker. No fallback. The planner produces
  // the single PipelinePlan that drives every downstream stage.
  // PlannerFault → HTTP 422 (caller must retry or degrade gracefully).
  const plannerHistory = messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(-2)
    .map(m => ({
      role: m.role as 'user' | 'assistant',
      content: extractText(m.parts ?? []),
    }))
    .filter(m => m.content.length > 0)

  const preAllocatedQueryId = crypto.randomUUID()
  const [plannerModelId, plannerFallbackModelId] = await Promise.all([
    getEffectiveModel(selectedStack, 'planner_fast', 'primary', request),
    getEffectiveModel(selectedStack, 'planner_fast', 'fallback', request),
  ])

  // UQE-9 — atomic per-request step_seq counter. Declared before the planner
  // emits its trace step so all subsequent stages share one counter.
  let stepSeq = 0
  const nextSeq = () => ++stepSeq

  const plannerStartedAt = Date.now()
  let plan: PipelinePlan
  try {
    plan = await runPlanner(
      queryText,
      plannerHistory,
      plannerModelId,
      chartId,
      (event) => traceEmitter.emitStep(event),
      preAllocatedQueryId,
      plannerFallbackModelId,
    )
  } catch (err) {
    if (err instanceof PlannerFault) {
      return NextResponse.json(
        { error: 'planner_failed', message: err.message },
        { status: 422 },
      )
    }
    throw err
  }
  const plannerLatencyMs = Date.now() - plannerStartedAt

  // Stamp route-controlled fields — never LLM output
  plan.query_plan_id = preAllocatedQueryId
  plan.query_text = queryText
  plan.audience_tier = isSuperAdmin ? 'super_admin' : 'client'
  plan.manifest_fingerprint = manifest.fingerprint
  plan.schema_version = '2.0'
  plan.planning_model_id = plannerModelId
  plan.planning_latency_ms = plannerLatencyMs

  const queryId = preAllocatedQueryId

  // Budget arbitration — proportional trim p3 → p2 → p1 with floor on p1.
  const arbitrated = arbitrateBudgets(
    plan.tool_calls.map(tc => ({
      tool_name: tc.tool_name,
      priority: tc.priority,
      token_budget: tc.token_budget,
    })),
    {
      synthesis_model_max_context: modelMeta.maxInputTokens ?? 128_000,
      system_prompt_reserve: 800,
      synthesis_guidance_reserve: plan.synthesis_guidance ? 200 : 0,
      safety_margin: 0.85,
      min_tokens_per_tool: 200,
    },
  )
  for (let i = 0; i < plan.tool_calls.length; i++) {
    plan.tool_calls[i].token_budget = arbitrated[i].token_budget
  }

  // Derive toolsAuthorized from plan.tool_calls.
  const toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))

  // B.11 Whole-Chart-Read enforcement — at least one L2.5 tool required.
  const L2_5_TOOLS = ['msr_sql', 'query_msr_aggregate', 'pattern_register',
    'resonance_register', 'cluster_atlas', 'contradiction_register', 'cgm_graph_walk']
  if (!toolsAuthorized.some(t => L2_5_TOOLS.includes(t))) {
    // Predictive class: cgm_graph_walk is banned (R14c); pattern_register is
    // required (R7a). Inject msr_sql + vector_search + pattern_register so the
    // synthesis model receives the domain narrative it needs.
    if (plan.query_class === 'predictive') {
      const domainSearchQuery = (plan.domains ?? []).length > 0
        ? (plan.domains ?? []).join(' ')
        : 'relationships family marriage children'
      plan.tool_calls.push(
        { tool_name: 'msr_sql', params: { forward_looking: true }, token_budget: 600, priority: 1 as const, reason: 'B.11 predictive floor: signal foundation' },
        { tool_name: 'vector_search', params: { query_text: domainSearchQuery, doc_type: ['domain_report'], top_k: 6 }, token_budget: 500, priority: 1 as const, reason: 'B.11 predictive floor: domain narrative' },
        { tool_name: 'pattern_register', params: { forward_looking: true }, token_budget: 400, priority: 2 as const, reason: 'B.11 predictive floor: R7a requirement' },
      )
      toolsAuthorized.push('msr_sql', 'vector_search', 'pattern_register')
    } else {
      plan.tool_calls.push(
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'B.11 floor enforcement' },
        { tool_name: 'cgm_graph_walk', params: {}, token_budget: 400, priority: 2 as const, reason: 'B.11 floor enforcement' },
      )
      toolsAuthorized.push('msr_sql', 'cgm_graph_walk')
    }
  }

  // Dasha context floor: predictive and holistic queries always need the
  // canonical Vimshottari dasha sequence so synthesis can anchor phase-based
  // predictions to correct dates (data lives in chart_facts.dasha_vimshottari).
  if (
    (plan.query_class === 'predictive' || plan.query_class === 'holistic') &&
    !toolsAuthorized.includes('chart_facts_query')
  ) {
    plan.tool_calls.push({
      tool_name: 'chart_facts_query',
      // limit:50 required — there are 50 AD records (V.001–V.050). Default limit:20
      // only covers through Mercury-Mars AD (ends 2020), cutting off the current
      // Mercury-Saturn AD and all future Ketu MD + Venus MD periods.
      params: { category: 'dasha_vimshottari', limit: 50 },
      token_budget: 600,
      priority: 1 as const,
      reason: 'dasha context floor: synthesis requires canonical MD/AD sequence for phase-anchored predictions',
    })
    toolsAuthorized.push('chart_facts_query')
  }

  // Adapter: PipelinePlan → legacy-shaped object for retrieval tools,
  // validators, audit, the orchestrator. Carries plan.tool_calls as an extra
  // field so single_model_strategy can read planner-supplied per-tool params.
  interface LegacyQueryPlanShape {
    query_plan_id: string
    query_text: string
    query_class:
      | 'factual'
      | 'interpretive'
      | 'predictive'
      | 'cross_domain'
      | 'discovery'
      | 'holistic'
      | 'remedial'
      | 'cross_native'
      | 'classical_grounding'
    domains: string[]
    forward_looking: boolean
    audience_tier:
      | 'super_admin'
      | 'acharya_reviewer'
      | 'client'
      | 'public_redacted'
    tools_authorized: string[]
    history_mode: 'synthesized' | 'research'
    panel_mode: boolean
    expected_output_shape:
      | 'single_answer'
      | 'three_interpretation'
      | 'time_indexed_prediction'
      | 'structured_data'
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
  const queryPlan: LegacyQueryPlanShape = {
    query_plan_id: queryId,
    query_text: queryText,
    query_class: plan.query_class,
    domains: plan.domains ?? [],
    forward_looking: plan.forward_looking ?? false,
    audience_tier: plan.audience_tier ?? (isSuperAdmin ? 'super_admin' : 'client'),
    tools_authorized: toolsAuthorized,
    history_mode: plan.history_mode ?? 'synthesized',
    panel_mode: plan.panel_mode ?? false,
    expected_output_shape: plan.expected_output_shape ?? 'three_interpretation',
    manifest_fingerprint: manifest.fingerprint,
    schema_version: '1.0',
    planets: plan.planets,
    houses: plan.houses,
    dasha_context_required: plan.dasha_context_required,
    graph_seed_hints: plan.graph_seed_hints,
    vector_search_filter: plan.vector_search_filter,
    time_window: plan.time_window,
    tool_calls: plan.tool_calls,
  }

  // ── MON-6: query_plan_log write ────────────────────────────────────────
  void writeQueryPlanLog({
    query_id: queryId,
    conversation_id: finalConversationId ?? null,
    chart_id: chartId ?? null,
    planner_model_id: plannerModelId,
    query_text: queryText,
    query_class: plan.query_class,
    tool_count: plan.tool_calls.length,
    plan_json: plan as unknown as Record<string, unknown>,
    parsing_success: true,
    parse_error: null,
    fallback_used: false,
    planner_latency_ms: plannerLatencyMs,
  })

  // Step 1 — emit plan trace step (step_name 'classify' preserved for trace UI compat)
  const classifyStart = plannerStartedAt
  traceEmitter.emitStep({
    event: 'step_done',
    query_id: queryId,
    step: {
      query_id: queryId,
      conversation_id: finalConversationId,
      step_seq: nextSeq(),
      step_name: 'classify',
      step_type: 'llm',
      status: 'done',
      started_at: new Date(classifyStart).toISOString(),
      completed_at: new Date().toISOString(),
      latency_ms: plannerLatencyMs,
      data_summary: {
        result: plan.query_class,
        query_class: plan.query_class,
        confidence: 1.0,
        planning_confidence: 1.0,
      },
      payload: {
        query_plan: {
          ...(queryPlan as unknown as TraceQueryPlan),
          query_intent_summary: plan.query_intent_summary,
          planning_rationale: plan.planning_rationale,
          synthesis_guidance: plan.synthesis_guidance,
          planning_model_id: plan.planning_model_id,
          planning_latency_ms: plan.planning_latency_ms,
        } as TraceQueryPlan,
        tool_calls: plan.tool_calls as unknown as TraceToolCallSpec[],
      },
    },
  })

  // Per-tool params map for retrieval layer.
  const plannerParamsMap = new Map<string, Record<string, unknown>>(
    plan.tool_calls.map(tc => [tc.tool_name, tc.params]),
  )

  const composeStart = Date.now()
  const bundle = await hydrateBundle(plan, manifest)
  // Step 2 — hydrate bundle
  traceEmitter.emitStep({
    event: 'step_done',
    query_id: queryId,
    step: {
      query_id: queryId,
      conversation_id: finalConversationId,
      step_seq: nextSeq(),
      step_name: 'compose_bundle',
      step_type: 'deterministic',
      status: 'done',
      started_at: new Date(composeStart).toISOString(),
      completed_at: new Date().toISOString(),
      latency_ms: Date.now() - composeStart,
      data_summary: {
        result: `${bundle.assets.length} assets · ${toolsAuthorized.length} tools${bundle.floor_enforced ? ' · floor_enforced' : ''}`,
      },
      payload: {},
    },
  })

  const cache = createToolCache()
  const toolFetchWallStart = Date.now()
  // UQE-9: pre-allocate one seq per tool BEFORE the parallel emissions so
  // the running event and the eventual done/error event for the same logical
  // tool step share a single step_seq.
  const toolSeqs: number[] = toolsAuthorized.map(() => nextSeq())
  // Steps 3…N — emit 'running' for all tools simultaneously (they fire in parallel)
  toolsAuthorized.forEach((toolName: string, idx: number) => {
    traceEmitter.emitStep({
      event: 'step_start',
      query_id: queryId,
      step: {
        query_id: queryId,
        conversation_id: finalConversationId,
        step_seq: toolSeqs[idx],
        step_name: toolName,
        step_type: toolStepType(toolName),
        status: 'running',
        started_at: new Date(toolFetchWallStart).toISOString(),
        parallel_group: 'tool_fetch',
        data_summary: {},
        payload: {},
      },
    })
  })

  const toolResults = await Promise.all(
    toolsAuthorized.map(async (toolName: string, idx: number) => {
      const t = getTool(toolName)
      if (!t) return null
      const toolStart = Date.now()
      try {
        const result = await executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName))
        traceEmitter.emitStep({
          event: 'step_done',
          query_id: queryId,
          step: {
            query_id: queryId,
            conversation_id: finalConversationId,
            step_seq: toolSeqs[idx],
            step_name: toolName,
            step_type: toolStepType(toolName),
            status: 'done',
            started_at: new Date(toolFetchWallStart).toISOString(),
            completed_at: new Date().toISOString(),
            latency_ms: Date.now() - toolStart,
            parallel_group: 'tool_fetch',
            data_summary: buildToolSummary(toolName, result),
            payload: buildToolPayload(toolName, result),
          },
        })
        return result
      } catch (err) {
        traceEmitter.emitStep({
          event: 'step_error',
          query_id: queryId,
          step: {
            query_id: queryId,
            conversation_id: finalConversationId,
            step_seq: toolSeqs[idx],
            step_name: toolName,
            step_type: toolStepType(toolName),
            status: 'error',
            started_at: new Date(toolFetchWallStart).toISOString(),
            completed_at: new Date().toISOString(),
            latency_ms: Date.now() - toolStart,
            parallel_group: 'tool_fetch',
            data_summary: { result: String(err) },
            payload: {},
          },
        })
        return null
      }
    })
  )
  const validToolResults = toolResults.filter((r): r is NonNullable<typeof r> => r !== null)

  const bundleValidations = await runAll(bundle, 'bundle', { query_plan: queryPlan, bundle, manifest_fingerprint: manifest.fingerprint })
  const bundleSummary = summarize(bundleValidations)
  if (bundleSummary.overall === 'fail' && configService.getFlag('VALIDATOR_FAILURE_HALT')) {
    return NextResponse.json(
      { error: 'bundle_validation_failed', failures: bundleSummary.failures },
      { status: 422 }
    )
  }

  const audienceTier = isSuperAdmin ? 'super_admin' as const : 'client' as const
  const panelOptIn = body.panel_opt_in === true

  // No LLM context assembler. plan.synthesis_guidance from the planner
  // serves the framing role; per-tool token budgets from arbitrateBudgets
  // serve the size role.
  const synthesisToolResults: ToolBundle[] = validToolResults

  // UQE-9: pre-allocate context_assembly seq (single_model_strategy emits
  // a deterministic context_assembly trace step before synthesis_done), then
  // the synthesis seq shared by start (here) and done (in onFinish inside
  // the orchestrator).
  const contextAssemblySeq = nextSeq()
  const synthesisSeq = nextSeq()
  const synthesisStart = Date.now()
  traceEmitter.emitStep({
    event: 'step_start',
    query_id: queryId,
    step: {
      query_id: queryId,
      conversation_id: finalConversationId,
      step_seq: synthesisSeq,
      step_name: 'synthesis',
      step_type: 'llm',
      status: 'running',
      started_at: new Date(synthesisStart).toISOString(),
      data_summary: { model: modelId },
      payload: {},
    },
  })

  // BUG-2: mutable holder populated by onValidatorResults callback (fires from
  // single_model_strategy onFinish, BEFORE onAuditEvent fires). The audit
  // consumer closes over the same array reference, so validators_run is non-empty.
  const validatorResultsHolder: ValidationResult[] = []

  // ── Gate III: smart context selection ─────────────────────────────────────
  // Trim conversation_history according to planner.prior_turn_relevance.used.
  // When the planner has not (yet) emitted prior_turn_relevance, fall back to
  // the legacy 2-pair window (= 4 prior messages + current user message).
  const ptr = plan.prior_turn_relevance
  const ptrUsedPairs = ptr ? ptr.used : 2
  // 2 pairs = 4 prior messages; +1 to include current user message which is
  // then dropped below.
  const historyMessageCap = ptrUsedPairs * 2 + 1
  const trimmedConversationHistory = messages
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .slice(-historyMessageCap)
    .slice(0, -1) // drop current user message (appended via `query`)
    .map(m => ({
      role: m.role as 'user' | 'assistant',
      content: extractText(m.parts ?? []),
    }))
    .filter(m => m.content.length > 0)

  const contextUsageMeta: ContextUsageEvent = ptr
    ? {
        type: 'context_usage',
        prior_turns_used: ptr.used,
        mode: ptr.mode as ContextUsageMode,
        reason: ptr.reason,
      }
    : {
        type: 'context_usage',
        prior_turns_used: Math.min(2, Math.floor(trimmedConversationHistory.length / 2)),
        mode: 'narrative_context',
        reason: 'Default 2-turn window — planner did not specify.',
      }

  const orchestrator = createOrchestrator({ panel_opt_in: panelOptIn })
  const { result, methodologyBlockHolder } = await orchestrator.synthesize({
    query: queryText,
    query_plan: queryPlan,
    bundle,
    tool_results: synthesisToolResults,
    conversation_history: trimmedConversationHistory,
    selected_model_id: modelId,
    style,
    audience_tier: audienceTier,
    cache,
    chart_context: {
      name: chart.name ?? 'the native',
      birth_date: chart.birth_date,
      birth_time: chart.birth_time,
      birth_place: chart.birth_place,
    },
    conversation_id: finalConversationId,
    panel_opt_in: panelOptIn,
    context_assembly_seq: contextAssemblySeq,
    synthesis_seq: synthesisSeq,
    // BUG-2: callback fires from single_model_strategy onFinish before onAuditEvent.
    onValidatorResults: (r) => { validatorResultsHolder.push(...r) },
    synthesis_guidance: plan.synthesis_guidance,
    // AUDIT_ENABLED retired BHISMA-B1 §6.2: always-on; flag removed from type union.
    onAuditEvent: createAuditConsumer({
      query_text: queryText,
      query_plan: queryPlan,
      bundle,
      tool_results: validToolResults,
      validator_results: validatorResultsHolder,
      disclosure_tier: audienceTier,
    }),
  })

  result.consumeStream()

  // ── Gate III: title for first turn (eager so it lands in start metadata)
  let gateIIITitle: string | null = null
  if (isFirstTurn) {
    try {
      // Use only the latest user message (first user message in this turn = same).
      const titleMessages = [lastUserMessage].filter(Boolean) as typeof messages
      gateIIITitle = await generateConversationTitle(titleMessages, {
        queryId,
        conversationId: finalConversationId,
        userId: user.uid,
      })
      if (gateIIITitle) {
        try { await updateConversationTitle(finalConversationId, gateIIITitle) } catch { /* non-fatal */ }
      }
    } catch {
      // non-fatal; UI falls back to the conversation list refresh path
    }
  }

  // ── Gate III: assemble provenance shell that will be finalized at finish.
  // The deepest information (synthesis tokens/latency) lands in onFinish; the
  // holder pattern lets messageMetadata.finish read the most-recent snapshot.
  const provenanceHolder: { value: ProvenanceEvent | null } = { value: null }
  const finishGuard = () => {
    if (provenanceHolder.value) return
    const topVectorScore = validToolResults
      .filter(t => t.tool_name === 'vector_search')
      .flatMap(t => t.results)
      .map(r => r.significance ?? r.confidence ?? 0)
      .reduce((max, v) => (v > max ? v : max), 0)
    provenanceHolder.value = assembleProvenance({
      models: [
        { stage: 'planner', model_id: plannerModelId, latency_ms: plannerLatencyMs },
        { stage: 'synthesis', model_id: modelId },
      ],
      toolResults: validToolResults as unknown as ToolBundleLike[],
      totalLatencyMs: Date.now() - setupStart,
      topVectorScore: topVectorScore > 0 ? topVectorScore : undefined,
    })
  }

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    generateMessageId: createIdGenerator({ prefix: 'msg', size: 16 }),
    messageMetadata: ({ part }: { part: { type: string } }) => {
      if (part.type === 'start' && isFirstTurn) {
        return {
          conversationId: finalConversationId,
          model: modelId,
          stack: selectedStack,
          style,
          disclosure_tier: audienceTier,
          pipeline: 'v2',
          queryId,
          planning_model_id: plannerModelId,
          planning_latency_ms: plannerLatencyMs,
          // F014 fix: emit planner_active into SSE body so runner.py regex can detect it
          planner_active: true,
          // Gate III additions
          query_class: plan.query_class,
          context_usage: contextUsageMeta,
          conversation_title: gateIIITitle ?? undefined,
        }
      }
      if (part.type === 'start') {
        return {
          model: modelId,
          stack: selectedStack,
          style,
          disclosure_tier: audienceTier,
          pipeline: 'v2',
          queryId,
          planning_model_id: plannerModelId,
          planning_latency_ms: plannerLatencyMs,
          planner_active: true,
          query_class: plan.query_class,
          context_usage: contextUsageMeta,
        }
      }
      if (part.type === 'finish') {
        finishGuard()
        return {
          methodology_block: methodologyBlockHolder?.value ?? null,
          provenance: provenanceHolder.value,
        }
      }
    },
    onFinish: async ({ messages: finalMessages }: { messages: UIMessage[] }) => {
      // ── W2-EVAL-A: Layer-2 citation gate (post-synthesis) ─────────────
      // Cross-reference SIG.MSR.NNN ids in the assistant's final text against
      // the assembled context (bundle + tool results). Suspected training-data
      // leaks WARN; ungrounded prescriptive answers ERROR (unless override).
      // Field destination context_assembly_log.verified_citations lands with
      // W2-SCHEMA; until then we keep the result local and log.
      //
      // Gate errors are logged + traced but never thrown post-stream.
      // Throwing inside onFinish propagates into the HTTP pipe machinery,
      // causing "failed to pipe response" not a clean stream error.
      try {
        const assistantMsg = finalMessages.filter((m) => m.role === 'assistant').at(-1)
        const outputText = extractText(assistantMsg?.parts ?? [])
        const assembledContextJson = JSON.stringify({
          bundle,
          tool_results: validToolResults,
        })
        const citationCheck = validateCitations(outputText, assembledContextJson, plan.query_class)
        const overrideOn = configService.getFlag('CITATION_GATE_OVERRIDE')
        const effectiveResult =
          citationCheck.gate_result === 'ERROR' && overrideOn ? 'WARN' : citationCheck.gate_result

        console.log(
          `[consume:v2] citation_gate_l2 query_id=${queryId} ` +
            `result=${effectiveResult} layer1=${citationCheck.layer1_count} ` +
            `verified=${citationCheck.layer2_verified} leaked=${citationCheck.layer2_leaked}` +
            (overrideOn && citationCheck.gate_result === 'ERROR' ? ' override=on' : '') +
            ` reason="${citationCheck.gate_reason}"`
        )

        if (effectiveResult === 'WARN') {
          traceEmitter.emitStep({
            event: 'step_done',
            query_id: queryId,
            step: {
              query_id: queryId,
              conversation_id: finalConversationId,
              step_seq: nextSeq(),
              step_name: 'citation_warn',
              step_type: 'deterministic',
              status: 'done',
              started_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
              latency_ms: 0,
              data_summary: {
                result: citationCheck.gate_reason,
                citation_count: citationCheck.layer1_count,
              },
              payload: {},
            },
          })
        }

        // ── MON-8: context_assembly_log write ──────────────────────────
        // Per-layer token breakdown grouped from validToolResults by tool_name.
        // No more LLM context assembler — per-layer counts come from raw bundles.
        const tokensFor = (predicate: (toolName: string) => boolean): number => {
          let chars = 0
          for (const tb of validToolResults) {
            if (!predicate(tb.tool_name)) continue
            for (const r of tb.results) chars += r.content.length
          }
          return Math.ceil(chars / 4)
        }
        void writeContextAssemblyLog({
          query_id: queryId,
          l1_tokens: tokensFor(n => [
            'chart_facts_query', 'divisional_query', 'kp_query',
            'manifest_query', 'query_kp_ruling_planets', 'query_varshaphala',
            'saham_query', 'temporal', 'timeline_query',
          ].includes(n)),
          l2_5_signal_tokens: tokensFor(n => [
            'msr_sql', 'query_msr_aggregate', 'query_signal_state',
          ].includes(n)),
          l2_5_pattern_tokens: tokensFor(n => [
            'pattern_register', 'resonance_register',
            'contradiction_register', 'cluster_atlas',
          ].includes(n)),
          l4_tokens: tokensFor(n => ['remedial_codex_query', 'domain_report_query'].includes(n)),
          vector_tokens: tokensFor(n => n === 'vector_search'),
          cgm_tokens: tokensFor(n => n === 'cgm_graph_walk'),
          synthesis_model_id: modelId,
          model_max_context: modelMeta.maxInputTokens ?? null,
          b3_compliant: citationCheck.gate_result === 'PASS',
          citation_count: citationCheck.layer1_count ?? 0,
          verified_citations: citationCheck.layer2_verified ?? 0,
        })

        if (citationCheck.gate_result === 'ERROR' && !overrideOn) {
          // Do NOT throw — onFinish fires after the HTTP response body is
          // already being piped. Throwing here propagates into the pipe
          // machinery, not into a clean stream-error part, causing
          // "failed to pipe response" on the server and "Network error" on
          // the client. The user already received the truncated response;
          // throwing post-hoc neither retracts it nor surfaces a meaningful
          // message. Instead: hard-block log + trace event for visibility.
          // If enforcement is needed, gate pre-stream (before synthesis starts).
          console.error(
            `[consume:v2] citation_gate_l2 HARD_BLOCK (non-throwing) ` +
            `query_id=${queryId} reason="${citationCheck.gate_reason}"`
          )
          traceEmitter.emitStep({
            event: 'step_done',
            query_id: queryId,
            step: {
              query_id: queryId,
              conversation_id: finalConversationId,
              step_seq: nextSeq(),
              step_name: 'citation_error',
              step_type: 'deterministic',
              status: 'error',
              started_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
              latency_ms: 0,
              data_summary: { result: citationCheck.gate_reason, citation_count: citationCheck.layer1_count },
              payload: {},
            },
          })
        }
      } catch (err) {
        console.error('[consume:v2] citation gate error', err)
      }

      // Emit trace done sentinel so SSE endpoint closes the stream
      traceEmitter.emitStep({ event: 'done', query_id: queryId })
      try {
        await replaceConversationMessages({
          conversationId: finalConversationId,
          messages: finalMessages,
        })
        if (isFirstTurn && !gateIIITitle) {
          // Gate III: only runs if eager pre-stream title generation failed.
          generateConversationTitle(finalMessages, {
            queryId,
            conversationId: finalConversationId,
            userId: user.uid,
          }).then((title: string | null) => {
            if (title) void updateConversationTitle(finalConversationId, title)
          })
        }
      } catch (err) {
        console.error('[consume:v2] persistence failed', err)
      }
      if (!lelContextEnabled) {
        try {
          const fs = await import('fs/promises')
          const path = await import('path')
          const ledgerPath = path.join(process.cwd(), '..', '06_LEARNING_LAYER',
            'PREDICTION_LEDGER', 'prediction_ledger.jsonl')
          const entry = JSON.stringify({
            pred_id: `PRED.BLIND.${Date.now()}`,
            emitted_at: new Date().toISOString(),
            mode: 'blind',
            chart_id: chartId,
            conversation_id: conversationId,
            query: extractText(messages[messages.length - 1]?.parts ?? []),
            outcome: null,
            confidence: null,
            horizon: null,
            falsifier: null,
            note: 'Auto-logged blind-mode query. Outcome/confidence/horizon/falsifier to be filled by native.',
          }) + '\n'
          await fs.appendFile(ledgerPath, entry, 'utf8')
        } catch {
          // Non-fatal: prediction ledger write failure does not block the response.
        }
      }
      // Note: deferredGateError pattern removed — see citation_gate block above.
      // Citation gate errors are logged and traced but never thrown post-stream.
    },
    onError: (error: unknown) => {
      const msg = error instanceof Error ? error.message : String(error)
      // Surface the actual Anthropic error body (overloaded_error / api_error /
      // invalid_request_error) so Cloud Run logs can disambiguate provider outage
      // vs bad request vs per-IP throttling. Previously invisible — only the SDK
      // wrapper ("Internal Server Error") was logged.
      const errObj = error as Record<string, unknown>
      const responseBody = errObj?.responseBody ?? errObj?.cause ?? errObj?.data
      console.error(
        '[consume:v2] synthesis error:', msg,
        responseBody !== undefined ? `| responseBody=${JSON.stringify(responseBody)}` : ''
      )
      return msg
    },
  })
} catch (pipelineError) {
  const msg = pipelineError instanceof Error ? pipelineError.message : String(pipelineError)
  console.error('[consume:v2] pre-stream error:', msg)
  return res.internal(msg)
}
}


function extractText(parts: Array<{ type: string; text?: string }>): string {
  return parts.filter(p => p.type === 'text').map(p => p.text ?? '').join(' ').trim()
}
