import {
  stepCountIs,
  convertToModelMessages,
  createIdGenerator,
  smoothStream,
  createUIMessageStream,
  createUIMessageStreamResponse,
} from 'ai'
import type { ModelMessage, UIMessage } from 'ai'
import { stagePart, toolPart, costPart, observabilityPart, citationGatePart, citationPart, persistencePart, predictionCandidatePart, correctionPart, outOfDomainPart, titlePart } from '@/lib/streams/data_parts'
import { parseMarkers } from '@/lib/consume/marker_parser'
import { detectPredictionCandidates } from '@/lib/ppl/prediction_detector'
import { extractCitations } from '@/lib/citations/citation_data_part'

/** Fetch signal name + description from l25_msr_signals for a list of signal IDs.
 *  Returns a map signal_id → snippet string. Missing IDs get empty string. */
async function fetchMsrSnippets(signalIds: string[]): Promise<Map<string, string>> {
  if (signalIds.length === 0) return new Map()
  try {
    const placeholders = signalIds.map((_, i) => `$${i + 1}`).join(', ')
    const { rows } = await query<{ signal_id: string; name: string; description: string }>(
      `SELECT signal_id, name, description FROM l25_msr_signals WHERE signal_id IN (${placeholders})`,
      signalIds,
    )
    return new Map(rows.map(r => {
      const full = r.name
        ? (r.description ? `${r.name} — ${r.description}` : r.name)
        : (r.description ?? '')
      return [r.signal_id, full.length > 295 ? full.slice(0, 294) + '…' : full]
    }))
  } catch {
    return new Map()
  }
}
import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { consumeSystemPrompt, type ConsumeStyle } from '@/lib/claude/system-prompts'
import {
  getConversation,
  insertConversationWithId,
  updateConversationTitle,
} from '@/lib/conversations'
import { writeConversationMessages } from '@/lib/persistence/conversation_writer'
import { createPendingStreamWriter } from '@/lib/persistence/pending_streams_writer'
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
// R11 v2 — Multi-Provider Parity: capability dispatcher (A-S7)
// Gated by MARSYS_FLAG_R11V2_USE_ADAPTERS (server-side, default false).
// When true, chat calls route through the dispatcher to the per-provider adapter.
// When false (default for R11.A), legacy single-shot pipeline is used unchanged.
import type { StackId } from '@/lib/providers/dispatcher'
import { getAdapter } from '@/lib/providers/dispatcher'
import type { ChatRequest } from '@/lib/providers/types'
import { buildAdapterMessages, buildAdapterChatRequest } from '@/lib/providers/adapter-dispatch-helpers'
import { runAgenticLoop, LOOP_CONFIG_BY_PROVIDER } from '@/lib/synthesis/agentic_loop'
import { executeMCPTool } from '@/lib/synthesis/mcp_tool_executor'
import { buildCacheCreatePayload, GEMINI_CACHE_MIN_TOKENS } from '@/lib/providers/google/cached_content'
import { callPipelinePlanner as runPlanner, PlannerFault } from '@/lib/pipeline/pipeline_planner'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import { getTool } from '@/lib/retrieve/index'
import { buildChatToolsFromNames } from '@/lib/retrieve/tool_catalogue'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { runAll, summarize } from '@/lib/validators/index'
import type { ValidationResult } from '@/lib/validators/types'
import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'
import { compressHistory } from '@/lib/synthesis/history_compression'
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
import { fakeGcsRetrieve } from '@/lib/multimodal/fake_gcs_store'
import { extractPdf } from '@/lib/multimodal/pdf_extractor'
import { getProjectForConversation } from '@/lib/projects'
import { getPersonaForSynthesis } from '@/lib/personas'

// Unit 3.gateway_pipeline_isolation built the QueryPipeline selector + shared
// stages substrate (selectPipelineForRequest / isPipelineSelectorEnabled);
// 3.legacy_delete retired the MARSYS_FLAG_PIPELINE_SELECTOR flag — the
// selector + per-kind QueryPipeline modules remain at `@/lib/pipelines` as
// infrastructure for the next refactor wave that will move dispatch out of
// this file. Only the onFinish write-through helper is consumed by the
// inline dispatch body today.
import { runOnFinishWriteThrough } from '@/lib/pipelines/shared'

// ── Trace helpers ─────────────────────────────────────────────────────────────

function toolStepType(toolName: string): TraceStep['step_type'] {
  if (toolName === 'vector_search') return 'vector'
  if (['msr_sql', 'query_msr_aggregate'].includes(toolName)) return 'sql'
  if (['classical_text_search', 'classical_attribution_lookup'].includes(toolName)) return 'sql'
  // L1 substrate tools restored to planner visibility 2026-05-17 — all Postgres-backed.
  if (
    ['lel_query', 'query_signal_state', 'query_kp_ruling_planets', 'query_varshaphala'].includes(
      toolName
    )
  ) {
    return 'sql'
  }
  // M9 L9 tools — Postgres-backed convergence + coverage tables
  if (['multi_school_signal_lookup', 'convergence_score_lookup'].includes(toolName)) {
    return 'sql'
  }
  // COV-S4 sidecar compute tools — sidecar-backed, classified as gcs (default)
  if (['query_muhurat', 'query_jaimini_drishti', 'query_v7_additions'].includes(toolName)) {
    return 'gcs'
  }
  return 'gcs'
}

function inferLayer(toolName: string): 'L1' | 'L2.5' {
  if (['msr_sql', 'query_msr_aggregate', 'pattern_register', 'resonance_register',
       'cluster_atlas', 'contradiction_register', 'temporal', 'cgm_graph_walk',
       'multi_school_signal_lookup', 'convergence_score_lookup'].includes(toolName)) {
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

interface AttachmentRef {
  token: string
  filename: string
  contentType: string
}

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
  /** β5: file attachment tokens from the upload flow */
  attachments?: AttachmentRef[]
  /** R9-S3: Active persona ID for synthesis prompt injection. */
  persona_id?: string
}

// β5: Resolve attachment tokens to ModelMessage-compatible parts.
// Returns extra parts to append to the last user ModelMessage.
async function resolveAttachments(
  attachments: AttachmentRef[],
): Promise<Array<{ type: 'image'; image: string; mimeType: string } | { type: 'text'; text: string }>> {
  const parts: Array<{ type: 'image'; image: string; mimeType: string } | { type: 'text'; text: string }> = []

  for (const att of attachments) {
    const entry = fakeGcsRetrieve(att.token)
    if (!entry) {
      // Token expired or not found — silently skip (file already noted in client)
      continue
    }

    if (att.contentType === 'application/pdf') {
      const result = await extractPdf(att.filename, entry.bytes)
      parts.push({ type: 'text', text: `[Attached PDF: ${att.filename}]\n\n${result.text}` })
    } else if (att.contentType.startsWith('image/')) {
      const base64 = entry.bytes.toString('base64')
      parts.push({ type: 'image', image: `data:${att.contentType};base64,${base64}`, mimeType: att.contentType })
    }
  }

  return parts
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

  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  if (!UUID_RE.test(chartId)) {
    return res.badRequest('INVALID_CHART_ID: chartId must be a valid UUID')
  }

  // Resolve synthesis model from stack. Stack takes precedence over the legacy
  // `model` field. Unknown/missing stacks fall back to the default NIM stack.
  const VALID_STACKS = Object.keys(STACK_ROUTING) as ModelStack[]
  // E.3: provider override — URL param ?provider=<stack> or MARSYS_FORCE_PROVIDER env.
  // Takes lowest precedence: only applied when the client sent no explicit stack.
  const providerOverride = (
    (!body.stack && new URL(request.url).searchParams.get('provider')) ||
    (!body.stack && process.env.MARSYS_FORCE_PROVIDER) ||
    null
  )
  const selectedStack: ModelStack = VALID_STACKS.includes(body.stack as ModelStack)
    ? (body.stack as ModelStack)
    : (providerOverride && VALID_STACKS.includes(providerOverride as ModelStack)
        ? (providerOverride as ModelStack)
        : DEFAULT_STACK_ID)
  const [stackSynthPrimary, stackSynthFallback] = await Promise.all([
    getEffectiveModel(selectedStack, 'synthesis', 'primary', request),
    getEffectiveModel(selectedStack, 'synthesis', 'fallback', request),
  ])
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

  // Unit 2c (Stream B): single authorization brain. Replaces inline
  // `chart.client_id !== user.uid`. Maps to 401 on deny; 'view' is read-only
  // and rejects Build/edit/delete operations (this route is a read/consult
  // surface — no mutation — so 'view' is sufficient here).
  const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
  const principalRole: 'guest' | 'super_admin' =
    isSuperAdmin ? 'super_admin' : 'guest'
  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role: principalRole },
    chartId,
    db: { query },
  })
  if (permission === 'deny') {
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
  const queryText = (lastUserMessage?.parts ?? []).filter(p => p.type === 'text').map(p => (p as { type: string; text?: string }).text ?? '').join(' ').trim()

  // β5: resolve attachment tokens → model-ready parts
  const attachmentParts = body.attachments?.length
    ? await resolveAttachments(body.attachments)
    : []

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
      content: (m.parts ?? []).filter(p => p.type === 'text').map(p => (p as { type: string; text?: string }).text ?? '').join(' ').trim(),
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

  // Inject user_id into every trace step so /api/predictions ownership check works (O4 fix).
  const emit = (event: Parameters<typeof traceEmitter.emitStep>[0]) => {
    if (event.step) event.step.user_id = user.uid
    traceEmitter.emitStep(event)
  }

  const plannerStartedAt = Date.now()
  let plan: PipelinePlan
  try {
    plan = await runPlanner(
      queryText,
      plannerHistory,
      plannerModelId,
      chartId,
      emit,
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

  // γ7: Create per-request pending stream writer for stream-resume.
  const pendingStreamWriter = createPendingStreamWriter(queryId, finalConversationId, user.uid)

  // β3: Register abort sentinel — writes a 'cancelled' step when client disconnects mid-stream.
  request.signal.addEventListener('abort', () => {
    emit({
      event: 'step_done',
      query_id: queryId,
      step: {
        query_id: queryId,
        conversation_id: finalConversationId ?? undefined,
        step_seq: nextSeq(),
        step_name: 'cancelled',
        step_type: 'deterministic',
        status: 'cancelled',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        latency_ms: 0,
        data_summary: {},
        payload: {},
      },
    })
  }, { once: true })

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
      | 'multi_school_triangulation'
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
  emit({
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
  const composeBundleMs = Date.now() - composeStart
  // Step 2 — hydrate bundle
  emit({
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
  interface ToolEvent { name: string; status: 'done' | 'error'; ms: number; ok_count: number; err_count: number }
  const toolEventLog: ToolEvent[] = []
  const toolFetchWallStart = Date.now()
  // UQE-9: pre-allocate one seq per tool BEFORE the parallel emissions so
  // the running event and the eventual done/error event for the same logical
  // tool step share a single step_seq.
  const toolSeqs: number[] = toolsAuthorized.map(() => nextSeq())
  // Steps 3…N — emit 'running' for all tools simultaneously (they fire in parallel)
  toolsAuthorized.forEach((toolName: string, idx: number) => {
    emit({
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
      if (request.signal.aborted) return null
      const t = getTool(toolName)
      if (!t) return null
      const toolStart = Date.now()
      try {
        const result = await executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName))
        emit({
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
        toolEventLog.push({ name: toolName, status: 'done', ms: Date.now() - toolStart, ok_count: result.results.length, err_count: 0 })
        return result
      } catch (err) {
        emit({
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
        toolEventLog.push({ name: toolName, status: 'error', ms: Date.now() - toolStart, ok_count: 0, err_count: 1 })
        return null
      }
    })
  )
  const validToolResults = toolResults.filter((r): r is NonNullable<typeof r> => r !== null)
  const toolFetchMs = Date.now() - toolFetchWallStart

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
  emit({
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

  // β8: when HISTORY_COMPRESSION_ENABLED, take the full prior history and let
  // compressHistory decide whether to summarize based on the token budget.
  // Flag OFF: use the existing planner-guided hard cap (unchanged behavior).
  let trimmedConversationHistory: import('ai').ModelMessage[]
  if (configService.getFlag('HISTORY_COMPRESSION_ENABLED')) {
    const allPriorMessages = await convertToModelMessages(
      messages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .slice(0, -1), // drop current user message
    )
    trimmedConversationHistory = await compressHistory(
      allPriorMessages,
      finalConversationId,
    )
  } else {
    trimmedConversationHistory = await convertToModelMessages(
      messages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .slice(-historyMessageCap)
        .slice(0, -1), // drop current user message (appended via `query`)
    )
  }

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

  // R9-S3: Look up persona for synthesis injection (flag-gated).
  let personaId: string | undefined
  let personaSystemPrompt: string | undefined
  if (configService.getFlag('R9_PERSONAS') && body.persona_id) {
    try {
      const persona = await getPersonaForSynthesis(body.persona_id, user.uid)
      if (persona && persona.system_prompt.trim().length > 0) {
        personaId = persona.id
        personaSystemPrompt = persona.system_prompt
      }
    } catch {
      // Non-fatal: persona lookup failure does not block synthesis
    }
  }

  // R9-S1: Look up project context for prompt injection (flag-gated).
  let projectId: string | undefined
  let projectSystemPromptAddition: string | undefined
  if (configService.getFlag('R9_PROJECTS') && finalConversationId) {
    try {
      const project = await getProjectForConversation(finalConversationId)
      if (project) {
        projectId = project.id
        if (project.system_prompt_addition && project.system_prompt_addition.trim().length > 0) {
          projectSystemPromptAddition = project.system_prompt_addition
        }
        if (project.chart_id) {
          // chart_id retrieval deferred to R9-S2+
          // Trace: project_chart_retrieval deferred
          void project.chart_id // referenced to avoid lint unused-var
        }
      }
    } catch {
      // Non-fatal: project lookup failure does not block synthesis
    }
  }

  /**
   * B.11 FLOOR CONTRACT (binding for all adapter dispatch paths):
   *
   * B.11 floor tools (MSR, UCN, CGM holistic synthesis) are pre-executed
   * deterministically above this block and their results injected into
   * adapterChatReq.messages before any model call. The agentic loop receives
   * a context that already contains the holistic synthesis layer — the model
   * cannot skip or defer it.
   *
   * Loop tools are the PLANNER-AUTHORISED SUBSET only. The loop adds gap-recovery
   * and ambiguity-resolution capability. It does not replace the planner.
   */
  // R11 v2 — Capability Dispatcher (A-S7 + dispatch-wiring; unconditional
  // post-Stream A 3.legacy_delete 2026-05-28 — the legacy synthesis trio
  // (single_model_strategy / panel_strategy / orchestrator) is deleted; the
  // adapter pipeline is the only path. The MARSYS_FLAG_R11V2_USE_ADAPTERS
  // flag remains in the feature-flag catalogue (default true) as an operator
  // rollback knob, but flipping it false now throws unmapped-stack errors —
  // recovery path is `git revert`, not flag flip.
  {
    const STACK_TO_ADAPTER: Partial<Record<string, StackId>> = {
      anthropic: 'anthropic',
      gemini: 'google',
      gpt: 'openai',
      deepseek: 'deepseek',
      nim: 'nvidia',
    }
    // 'marsys' meta-stack: derive the concrete adapter from the resolved
    // model's provider field. STACK_ROUTING resolves a synthesis model_id;
    // modelMeta.provider is the concrete provider that adapter dispatch needs.
    const mappedStackAdapter = STACK_TO_ADAPTER[selectedStack] as StackId | undefined
    const adapterId: StackId | undefined =
      mappedStackAdapter ??
      (modelMeta.provider as StackId | undefined)
    if (!adapterId) {
      throw new Error(
        `[consult] no adapter mapping for stack=${selectedStack} provider=${modelMeta.provider} — ` +
        `legacy synthesis path was removed by 3.legacy_delete.`,
      )
    }
    {
      // Bug A+B fix: use helper that appends current user turn and filters empty content parts.
      const adapterMessages = buildAdapterMessages(trimmedConversationHistory, queryText)
      // Bug C fix: pass bundle assets + synthesis guidance as system context.
      const bundleSystemContent = (bundle.assets as Array<{ content: string }>)
        .map(a => a.content)
        .filter(Boolean)
        .join('\n\n')
      const systemContent = [
        bundleSystemContent,
        plan.synthesis_guidance ? `SYNTHESIS GUIDANCE:\n${plan.synthesis_guidance}` : '',
      ].filter(Boolean).join('\n\n---\n\n') || undefined
      let adapterChatReq: ChatRequest = buildAdapterChatRequest(adapterMessages, modelId, systemContent)
      const adapter = getAdapter(adapterId)
      // R11.F — S3: Per-provider agentic loop flag map
      const ADAPTER_TO_LOOP_FLAG: Record<string, string> = {
        anthropic: 'R11E_ANTHROPIC_LOOP',
        google: 'R11E_GEMINI_LOOP',
        openai: 'R11E_OPENAI_LOOP',
        deepseek: 'R11E_DEEPSEEK_LOOP',
        nvidia: 'R11E_NVIDIA_LOOP',
      }
      const loopFlagKey = ADAPTER_TO_LOOP_FLAG[adapterId]
      const useAgenticLoop = loopFlagKey ? configService.getFlag(loopFlagKey as Parameters<typeof configService.getFlag>[0]) : false

      // Unit 3.gateway_pipeline_isolation built the selector + per-kind
      // QueryPipeline modules; 3.cutover flipped the structural shadow on;
      // 3.legacy_delete removed the legacy decision path that the shadow
      // was comparing against. The selector + pipeline modules remain in
      // place (platform/src/lib/pipelines/) as infrastructure for the next
      // wave that will move the dispatch body out of route.ts. Until then,
      // the inline useAgenticLoop decision (above) is the single source of
      // truth and the MARSYS_FLAG_PIPELINE_SELECTOR flag is retired.

      if (useAgenticLoop) {
        const manifest = adapter.getManifest()
        const toolsCfg = adapter.tools({
          toolLoopMode: manifest.adaptiveToolLoop,
          tools: buildChatToolsFromNames(queryPlan.tools_authorized ?? []),
          maxIterations: 8,
        })
        adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
      }
      // R11.F — S4: Gemini cachedContent API (D.3)
      // When R11D_GEMINI_CACHE=true and provider=google, attempt to create a
      // Gemini cachedContent object for the system prompt + RAG bundle.
      // The returned resource name is passed through cacheConfig so GoogleAdapter.chat()
      // can reference it in the streamText providerOptions.google.cachedContent field.
      // Cache creation is non-fatal — any failure falls through to a standard uncached request.
      if (configService.getFlag('R11D_GEMINI_CACHE') && adapterId === 'google') {
        const cacheResponse = adapter.cache({ cacheMode: 'cached_content_api', breakpointPositions: [] })
        const estimatedTokens = Math.ceil((systemContent?.length ?? 0) / 4)
        if (estimatedTokens >= GEMINI_CACHE_MIN_TOKENS) {
          try {
            const ttlSeconds = (cacheResponse.providerPayload?.['ttlSeconds'] as number) ?? 600
            // Prefix model name with 'models/' if not already qualified — Gemini REST API requirement
            const qualifiedModel = adapterChatReq.model.startsWith('models/')
              ? adapterChatReq.model
              : `models/${adapterChatReq.model}`
            const cachePayload = buildCacheCreatePayload({
              model: qualifiedModel,
              systemPrompt: systemContent,
              ragBundle: undefined,
              ttl: `${ttlSeconds}s`,
            })
            const apiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY
            if (apiKey) {
              const cacheRes = await fetch(
                `https://generativelanguage.googleapis.com/v1beta/cachedContents?key=${apiKey}`,
                {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(cachePayload),
                }
              )
              if (cacheRes.ok) {
                const cacheJson = await cacheRes.json() as { name?: string }
                const cachedContentName = cacheJson.name
                if (cachedContentName) {
                  adapterChatReq = {
                    ...adapterChatReq,
                    cacheConfig: {
                      ...cacheResponse,
                      providerPayload: {
                        ...cacheResponse.providerPayload,
                        cachedContentName,
                      },
                    },
                  }
                  console.log(`[gemini-cache] Created cachedContent: ${cachedContentName} (~${estimatedTokens} tokens)`)
                }
              } else {
                const errText = await cacheRes.text()
                console.warn(`[gemini-cache] Cache creation failed (${cacheRes.status}): ${errText.slice(0, 200)}`)
              }
            }
          } catch (cacheErr) {
            console.warn('[gemini-cache] Cache creation error (non-fatal):', cacheErr)
          }
        } else {
          console.log(`[gemini-cache] Skipping cache: ~${estimatedTokens} tokens < ${GEMINI_CACHE_MIN_TOKENS} minimum`)
        }
      }
      const adapterMsgId = createIdGenerator({ prefix: 'msg', size: 16 })()
      const adapterStartMs = Date.now()
      const adapterStream = createUIMessageStream({
        execute: async ({ writer }) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          writer.write({ type: 'start', messageId: adapterMsgId } as any)
          writer.write({ type: 'data-stage', data: stagePart('classify', 'done', plannerLatencyMs) })
          writer.write({ type: 'data-stage', data: stagePart('compose_bundle', 'done', composeBundleMs) })
          for (const evt of toolEventLog) {
            writer.write({
              type: 'data-tool',
              data: { type: 'tool', name: evt.name, status: evt.status, ms: evt.ms, ok_count: evt.ok_count, err_count: evt.err_count },
            })
          }
          writer.write({ type: 'data-stage', data: stagePart('tool_fetch', 'done', toolFetchMs) })
          writer.write({ type: 'data-stage', data: stagePart('synthesis', 'running') })
          pendingStreamWriter.onEvent()
          // AI SDK v6 UI message stream protocol requires text-start before text-delta,
          // and text-end + finish after the last delta.
          const adapterTextPartId = 'text-0'
          let adapterTextStarted = false
          let adapterAccumulatedText = ''
          try {
            const loopConfig = LOOP_CONFIG_BY_PROVIDER[adapterId]
            const chatStream = (useAgenticLoop && loopConfig)
              ? runAgenticLoop(
                  adapter,
                  adapterChatReq,
                  (toolCall) => executeMCPTool(toolCall, { queryPlan }),
                  loopConfig,
                )
              : adapter.chat(adapterChatReq)
            for await (const event of chatStream) {
              if (event.type === 'text_delta') {
                if (!adapterTextStarted) {
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  writer.write({ type: 'text-start', id: adapterTextPartId } as any)
                  adapterTextStarted = true
                }
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                writer.write({ type: 'text-delta', id: adapterTextPartId, delta: event.text } as any)
                pendingStreamWriter.onTextDelta(event.text)
                adapterAccumulatedText += event.text
              } else if (event.type === 'thinking_delta') {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                writer.write({ type: 'reasoning', delta: event.thinking, id: adapterMsgId } as any)
              } else if (event.type === 'tool_use_start') {
                // Silently consume — loop engine handles tool execution
              } else if (event.type === 'tool_use_input_delta') {
                // Silently consume — loop engine handles accumulation
              } else if (event.type === 'tool_use_complete') {
                // Emit as a tool data event for client visibility
                writer.write({
                  type: 'data-tool',
                  data: { type: 'tool', name: event.name, status: 'done', ms: 0, ok_count: 1, err_count: 0 },
                })
              } else if (event.type === 'error') {
                console.error('[adapter-dispatch] adapter error event stack=%s error=%s', adapterId, event.error)
              }
            }
          } catch (adapterErr) {
            console.error('[adapter-dispatch] stream error stack=%s', adapterId, adapterErr)
          }
          if (adapterTextStarted) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            writer.write({ type: 'text-end', id: adapterTextPartId } as any)
          }
          // ── 0b.1: B.11 citation gate (adapter-path parity with legacy onFinish) ─
          // Mirrors the legacy gate at the wire (route.ts:1373-1475 onFinish branch).
          // Cross-references SIG.MSR.NNN ids in the adapter-streamed text against the
          // assembled context (bundle + tool results). Same MARSYS_FLAG_CITATION_GATE_OVERRIDE
          // semantics, same data-citation-gate emission, same step_done telemetry. Errors
          // are logged only — never thrown post-stream (would corrupt the HTTP pipe).
          let adapterCitationGateResult: 'PASS' | 'WARN' | 'ERROR' = 'PASS'
          let adapterCitationL1Count = 0
          let adapterCitationL2Verified = 0
          try {
            const adapterAssembledContextJson = JSON.stringify({
              bundle,
              tool_results: validToolResults,
            })
            const adapterOverrideOn = configService.getFlag('CITATION_GATE_OVERRIDE')
            const adapterCitationValidation = validateCitationsForStream(
              adapterAccumulatedText,
              adapterAssembledContextJson,
              plan.query_class,
              adapterOverrideOn,
            )
            adapterCitationGateResult = adapterCitationValidation.gateResult
            adapterCitationL1Count = adapterCitationValidation.layer1Count
            adapterCitationL2Verified = adapterCitationValidation.layer2Verified

            console.log(
              `[consume:adapter] citation_gate_l2 query_id=${queryId} ` +
                `result=${adapterCitationValidation.gateResult} layer1=${adapterCitationValidation.layer1Count} ` +
                `verified=${adapterCitationValidation.layer2Verified} leaked=${adapterCitationValidation.layer2Leaked}` +
                (adapterOverrideOn && adapterCitationValidation.gateResult === 'WARN' && adapterCitationValidation.layer1Count > 0 ? ' override=on' : '') +
                ` reason="${adapterCitationValidation.gateReason}"`
            )

            if (adapterCitationValidation.dataPart) {
              writer.write({ type: 'data-citation-gate', data: adapterCitationValidation.dataPart })
            }

            if (adapterCitationValidation.gateResult === 'WARN') {
              emit({
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
                    result: adapterCitationValidation.gateReason,
                    citation_count: adapterCitationValidation.layer1Count,
                  },
                  payload: {},
                },
              })
            } else if (adapterCitationValidation.gateResult === 'ERROR') {
              console.error(
                `[consume:adapter] citation_gate_l2 HARD_BLOCK (non-throwing) ` +
                `query_id=${queryId} reason="${adapterCitationValidation.gateReason}"`
              )
              emit({
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
                  data_summary: { result: adapterCitationValidation.gateReason, citation_count: adapterCitationValidation.layer1Count },
                  payload: {},
                },
              })
            }
          } catch (err) {
            console.error('[consume:adapter] citation gate error', err)
          }
          // ── 3.cutover (G5b_onfinish) — shared onFinish write-through ─────
          // Routes the adapter path's onFinish stage through the same helper
          // the legacy synthesis-orchestrator path uses (parity is enforced by
          // onfinish_parity.golden.test.ts). Closes the prior adapter gaps:
          //   • data-cost emit (Observatory cost tile)
          //   • lastAssistantMetadata in persistence (R10 PerMessageDetailsDrawer)
          //   • per-citation data-citation parts (β4 SIG.MSR enrichment)
          //   • data-correction / data-out-of-domain markers (D.3)
          //   • pendingStreamWriter.clear() (γ7)
          //   • blind-mode prediction-ledger append (PPL)
          if (adapterAccumulatedText) {
            // Assign fresh UUIDs for all messages — client-side message IDs
            // (e.g. "yhJSXqHyqhawY9an") are not valid UUIDs and would fail
            // the conversation_messages.id UUID column constraint.
            const persistMsgs: UIMessage[] = [
              ...(messages as UIMessage[]).map(m => ({ ...m, id: crypto.randomUUID() } as UIMessage)),
              {
                id: crypto.randomUUID(),
                role: 'assistant' as const,
                parts: [{ type: 'text', text: adapterAccumulatedText }],
              } as UIMessage,
            ]
            // Per-layer token aggregation (closure over validToolResults).
            const tokensForAdapter = (predicate: (toolName: string) => boolean): number => {
              let chars = 0
              for (const tb of validToolResults) {
                if (!predicate(tb.tool_name)) continue
                for (const r of tb.results) chars += r.content.length
              }
              return Math.ceil(chars / 4)
            }
            const lastUserAdapter = (messages as UIMessage[])
              .filter(m => m.role === 'user').at(-1)
            const lastUserAdapterText = ((lastUserAdapter?.parts ?? []) as Array<{ type: string; text?: string }>)
              .filter(p => p.type === 'text')
              .map(p => p.text ?? '')
              .join(' ')
              .trim()
            const adapterLastAssistantMetadata: Record<string, unknown> = {
              custom: {
                model: modelId,
                queryId,
                planning_model_id: plannerModelId,
                planning_latency_ms: plannerLatencyMs,
                disclosure_tier: audienceTier,
                query_class: plan.query_class,
                stack: selectedStack,
                style,
                pipeline: 'v2-adapter',
                conversationId: finalConversationId,
              },
            }
            await runOnFinishWriteThrough(
              {
                pipelineKind: 'agentic',
                queryId,
                conversationId: finalConversationId,
                chartId,
                userUid: user.uid,
                isFirstTurn,
                lelContextEnabled,
                finalMessages: persistMsgs,
                assistantText: adapterAccumulatedText,
                lastUserQuery: lastUserAdapterText,
                lastAssistantMetadata: adapterLastAssistantMetadata,
                modelId,
                modelMaxContext: modelMeta.maxInputTokens ?? null,
                // Adapter path has no usageHolder — cost emit is suppressed.
                synthUsage: null,
                synthesisElapsedMs: Date.now() - adapterStartMs,
                citationGate: {
                  gateResult: adapterCitationGateResult,
                  layer1Count: adapterCitationL1Count,
                  layer2Verified: adapterCitationL2Verified,
                },
                contextAssembly: {
                  l1_tokens: tokensForAdapter(n => [
                    'chart_facts_query', 'divisional_query', 'kp_query',
                    'manifest_query', 'query_kp_ruling_planets', 'query_varshaphala',
                    'saham_query', 'temporal', 'timeline_query',
                  ].includes(n)),
                  l2_5_signal_tokens: tokensForAdapter(n => [
                    'msr_sql', 'query_msr_aggregate', 'query_signal_state',
                  ].includes(n)),
                  l2_5_pattern_tokens: tokensForAdapter(n => [
                    'pattern_register', 'resonance_register',
                    'contradiction_register', 'cluster_atlas',
                  ].includes(n)),
                  l4_tokens: tokensForAdapter(n => ['remedial_codex_query', 'domain_report_query'].includes(n)),
                  vector_tokens: tokensForAdapter(n => n === 'vector_search'),
                  cgm_tokens: tokensForAdapter(n => n === 'cgm_graph_walk'),
                },
                writer,
                emit,
              },
              {
                persistence: {
                  writeMessages: (args) => writeConversationMessages(args),
                },
                pricing: {
                  getPricing: (mid) => getModelPricingSync(mid),
                  computeUsd: (pricing, tokens) =>
                    computeCostUsd(pricing as Parameters<typeof computeCostUsd>[0], tokens),
                },
                contextAssemblyLog: (entry) => { void writeContextAssemblyLog(entry) },
                fetchMsrSnippets: (ids) => fetchMsrSnippets(ids),
                pendingStreamWriter,
                title: {
                  generate: (msgs, ctx) => generateConversationTitle(msgs, ctx),
                  update: (cid, t) => updateConversationTitle(cid, t).then(() => undefined),
                },
                predictionLedger: async (entry) => {
                  try {
                    const fs = await import('fs/promises')
                    const path = await import('path')
                    const ledgerPath = path.join(process.cwd(), '..', '06_LEARNING_LAYER',
                      'PREDICTION_LEDGER', 'prediction_ledger.jsonl')
                    const line = JSON.stringify({
                      ...entry,
                      outcome: null,
                      confidence: null,
                      horizon: null,
                      falsifier: null,
                      note: 'Auto-logged blind-mode query. Outcome/confidence/horizon/falsifier to be filled by native.',
                    }) + '\n'
                    await fs.appendFile(ledgerPath, line, 'utf8')
                  } catch {
                    // Non-fatal — prediction ledger write failure must not block the response.
                  }
                },
              },
            )
          }
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          writer.write({ type: 'finish', finishReason: 'stop' } as any)
          writer.write({ type: 'data-stage', data: stagePart('synthesis', 'done', Date.now() - adapterStartMs) })
          writer.write({
            type: 'data-observability',
            data: observabilityPart({ query_id: queryId, trace_url: `/observatory/trace/${queryId}` }),
          })
          emit({ event: 'done', query_id: queryId })
        },
      })
      return createUIMessageStreamResponse({ stream: adapterStream })
    }
  }
  // Unreachable: adapter dispatch block always returns above. The legacy
  // synthesis fallback was deleted by 3.legacy_delete 2026-05-28.
  throw new Error('[consult] adapter dispatch did not return — unreachable')

} catch (pipelineError) {
  const msg = pipelineError instanceof Error ? pipelineError.message : String(pipelineError)
  console.error('[consume:v2] pre-stream error:', msg)
  return res.internal(msg)
}
}


