import {
  stepCountIs,
  convertToModelMessages,
  createIdGenerator,
  smoothStream,
  createUIMessageStream,
  createUIMessageStreamResponse,
} from 'ai'
import type { ModelMessage, UIMessage } from 'ai'
import { stagePart, toolPart, costPart, observabilityPart, citationGatePart, citationPart, persistencePart, predictionCandidatePart, correctionPart, outOfDomainPart, titlePart, clarificationPart } from '@/lib/streams/data_parts'
import { parseMarkers } from '@/lib/consume/marker_parser'
import { detectPredictionCandidates } from '@/lib/ppl/prediction_detector'
import { extractCitations } from '@/lib/citations/citation_data_part'

/** Fetch signal headline + summary from bodha_msr_signals for a list of signal IDs.
 *  Returns a map signal_id → snippet string. Missing IDs get empty string. */
async function fetchMsrSnippets(signalIds: string[]): Promise<Map<string, string>> {
  if (signalIds.length === 0) return new Map()
  try {
    const placeholders = signalIds.map((_, i) => `$${i + 1}`).join(', ')
    const { rows } = await query<{ signal_id: string; name: string; description: string }>(
      `SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signals WHERE signal_id::text IN (${placeholders})`,
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
import { callPipelinePlanner as runPlanner } from '@/lib/pipeline/pipeline_planner'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import {
  compileFloorForPlan,
  ensureB11WholeChartReadFloor,
  ensureDashaContextFloor,
} from '@/lib/pipeline/compiled_floor_adapter'
import { buildWebCompletenessReceipt, type WebCompletenessReceipt } from '@/lib/pipeline/completeness_wiring'
import { buildChartOrientation, type ChartOrientation } from '@/lib/retrieval/orientation'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
// D7 Step 4: getTool() replaced with registry-backed getToolByName(); tool_catalogue RETIRED
// DO NOT restore lib/retrieve imports — see RETRIEVAL_D7_CALLER_MAP_v1_0.md §2.1
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { buildChatToolsFromNames } from '@/lib/retrieval/registry/schema_utils'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { getSharedQosDispatchQueue } from '@/lib/retrieval/qos/dispatch_queue'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { runAll, summarize } from '@/lib/validators/index'
import type { ValidationResult } from '@/lib/validators/types'
import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'
import { compressHistory } from '@/lib/synthesis/history_compression'
// PipelineError import removed — citation gate no longer throws post-stream (see citation_error trace event)
import { createAuditConsumer } from '@/lib/audit/consumer'
import { traceEmitter } from '@/lib/trace/emitter'
import type { TraceStep, TraceChunkItem, TraceDataSummary, TracePayload, TraceQueryPlan, TraceToolCallSpec } from '@/lib/trace/types'
// D7 migration: ToolBundle/ToolBundleResult types sourced from lib/retrieve/types
// (canonical location until lib/retrieve is retired in Step 4).
import type { ToolBundle, ToolBundleResult } from '@/lib/retrieval/shared_types'
import { res, errorResponse } from '@/lib/errors'
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
// stages substrate; unit 4.refactor_pipeline_shim (this commit) moved the
// inline pipeline body out of route.ts into `@/lib/pipelines/shared/
// run_adapter_dispatch.ts`. The route is now a thin selector: auth + chart
// resolution + planner-context + dispatch().
import { runAdapterDispatch } from '@/lib/pipelines/shared'

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

/**
 * LCA-2 / WP-1.1 — honest error classification.
 *
 * True when a Postgres error is a *permanent* schema/relation fault — a missing
 * table/column, invalid schema name, or malformed SQL. None of these can be
 * fixed by repeating the identical request, so they MUST NOT be mapped to the
 * transient `SYSTEM_DB_UNAVAILABLE {retry:true}` class (that mislabelling is the
 * exact bug this WP fixes: the retired `reports` relation raised 42P01 =
 * undefined_table, which was dishonestly reported as retryable).
 *
 * SQLSTATE class 42 = syntax error / access-rule violation (undefined_table
 * 42P01, undefined_column 42703, undefined_function 42883, …). Class 3F =
 * invalid_schema_name. Both are structural and permanent.
 */
function isPermanentSchemaError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false
  const code = (err as { code?: unknown }).code
  return typeof code === 'string' && (code.startsWith('42') || code.startsWith('3F'))
}

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

  // LCA-2 / WP-1.1 — the legacy `reports` relation was RETIRED; its DDL survives
  // only in platform/migrations/_archive and it is ABSENT from deployed Cloud SQL.
  // The prior code unconditionally SELECTed `domain, title, version FROM reports`
  // here inside this Promise.all, so every consult request raised a permanent
  // 42P01 (undefined_table) — for EVERY chart — which the catch below dishonestly
  // mapped to SYSTEM_DB_UNAVAILABLE {retry:true}, killing the flagship consult
  // surface. `reportsResult` was declared but never consumed downstream; consult
  // content is sourced entirely from the planner + retrieval tool path
  // (bodha_* signals, CGM graph traversal, vector search) — the same live
  // surfaces the working MCP tools use. The `reports` lookup is removed, not
  // re-pointed. DO NOT resurrect the `reports` table.
  let chartResult: Awaited<ReturnType<typeof query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string; client_id: string }>>>
  let profileResult: Awaited<ReturnType<typeof query<{ role: string }>>>
  try {
    ;[chartResult, profileResult] = await Promise.all([
      query<{ id: string; name: string; birth_date: string; birth_time: string; birth_place: string; client_id: string }>(
        'SELECT id, name, birth_date, birth_time, birth_place, client_id FROM charts WHERE id=$1',
        [chartId]
      ),
      query<{ role: string }>(
        'SELECT role FROM profiles WHERE id=$1',
        [user.uid]
      ),
    ])
  } catch (err) {
    // Honest classification: a permanent missing-relation / schema fault cannot
    // succeed on retry, so it must NOT carry the transient retry:true class.
    if (isPermanentSchemaError(err)) {
      console.error('[consume:v2] permanent schema error on chart/profile lookup:', err)
      return res.internal('A required database relation is missing or malformed.')
    }
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
  type DbLike = import('@/lib/auth/authorizeChartAccess').DbLike
  const principalRole: 'guest' | 'super_admin' =
    isSuperAdmin ? 'super_admin' : 'guest'
  const permission = await authorizeChartAccess({
    principal: { uid: user.uid, role: principalRole },
    chartId,
    db: { query: (sql: string, params?: unknown[]) => query(sql, params).then(r => ({ rows: r.rows })) } as DbLike,
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

  // ── W4 core step 5 — S-1 orientation front-door ────────────────────────────
  // Kick off the ≤2000-token orientation block (chart frame + structural facts +
  // notable gestalt findings + dasha context + category/drill map) EARLY, concurrently
  // with the planner + tool-fetch latency. Non-throwing (degrades to header+inventory on
  // any failure). Awaited just before adapter dispatch and delivered as a data-orientation
  // SSE event near the start of the stream. See @/lib/retrieval/orientation.
  const orientationPromise: Promise<ChartOrientation | null> = buildChartOrientation(chartId)
    .catch((err: unknown) => {
      console.error('[consume:v2] orientation build failed (non-fatal):', err)
      return null
    })

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
  // W4 "One Planner": the planner now returns a 3-way typed outcome
  // (plan | clarification_needed | fault) and NEVER throws for an expected
  // failure. Each outcome is rendered through a clean, typed response path —
  // the old raw `HTTP 422 {"error":"planner_failed", ...}` leak is gone.
  const plannerOutcome = await runPlanner(
    queryText,
    plannerHistory,
    plannerModelId,
    chartId,
    emit,
    preAllocatedQueryId,
    plannerFallbackModelId,
  )

  if (plannerOutcome.outcome === 'clarification_needed') {
    // Genuinely ambiguous query — stream a clarification the client renders as a
    // question, via the same UIMessage-stream SSE surface the rest of the chat
    // uses (data-clarification custom part). No plan is built; no LLM synthesis runs.
    const clarStream = createUIMessageStream({
      execute: ({ writer }) => {
        writer.write({ type: 'start', messageId: crypto.randomUUID() } as never)
        writer.write({
          type: 'data-clarification',
          data: clarificationPart({
            question: plannerOutcome.question,
            missing_scope_dims: plannerOutcome.missing_scope_dims,
            suggested_options: plannerOutcome.suggested_options,
          }),
        } as never)
        writer.write({ type: 'finish', finishReason: 'stop' } as never)
      },
    })
    return createUIMessageStreamResponse({ stream: clarStream })
  }

  if (plannerOutcome.outcome === 'fault') {
    // Typed, honest planner fault. Log the real reason server-side; the client
    // sees a clean canonical error envelope (NEVER the raw internal parse error).
    console.error('[consume:v2] planner fault:', plannerOutcome.reason, 'retryable=', plannerOutcome.retryable)
    return plannerOutcome.retryable
      // Transient (provider) fault — the same request may succeed on retry.
      ? errorResponse('SYSTEM_LLM_ERROR', 'The planner service is temporarily unavailable. Please retry.', 503, { retry: true })
      // The model could not produce a valid plan even after a repair-retry —
      // repeating won't help; the caller should rephrase.
      : res.validationFailed('The planner could not produce a valid plan for this request. Please rephrase and try again.')
  }

  const plan: PipelinePlan = plannerOutcome.plan
  const plannerLatencyMs = Date.now() - plannerStartedAt

  // Stamp route-controlled fields — never LLM output
  plan.query_plan_id = preAllocatedQueryId
  plan.query_text = queryText
  // audience_tier excised (C-2, tier_excision / DG1 ruling): it never
  // differentiated behavior. Disclosure is stamped separately as
  // `audienceTier` → audit `disclosure_tier` further down.
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

  // ── W4 core step 3 — floor adoption ────────────────────────────────────────
  // The B.11 floor is now COMPILED from the plan's deterministic scope_tuple via
  // the Vidhi compiler (compileFloorForPlan), replacing the former hardcoded
  // literal tool lists. The compiled floor's retrieval-executable tools are pushed
  // first (they vary by intent class); the two invariants the compiler does not
  // express in web-executable form — the B.11 whole-chart-read floor (≥1 L2.5
  // tool, incl. the predictive special-casing) and the dasha context floor — are
  // then enforced as orthogonal, idempotent guarantees. See
  // @/lib/pipeline/compiled_floor_adapter for the classifier→compiler tuple mapping
  // and the MCP-live_tool→retrieval-name bridge.
  //
  // NOTE (documented gap, W4 step-3 report): the compiler's floor is MCP-native, so
  // only a small subset of floor primitives currently map to web-executable retrieval
  // tools. The B.11 + dasha guarantees below preserve production behavior regardless.
  if (plan.scope_tuple) {
    const compiledFloor = compileFloorForPlan(plan.scope_tuple, chartId)
    for (const tc of compiledFloor.toolCalls) {
      if (!toolsAuthorized.includes(tc.tool_name)) {
        plan.tool_calls.push(tc)
        toolsAuthorized.push(tc.tool_name)
      }
    }
  }
  // else: no scope_tuple on the plan (defensive — callPipelinePlanner always attaches
  // one for a resolved plan). Fall through to the guarantees below, which reproduce
  // the legacy hardcoded floor exactly — a safe, maximally-conservative default.

  // B.11 Whole-Chart-Read enforcement — at least one L2.5 tool required. Idempotent:
  // no-ops if the compiled floor already yielded an L2.5 tool (e.g. mechanism_read →
  // cgm_graph_walk). Preserves the predictive-class special-casing.
  ensureB11WholeChartReadFloor(plan, toolsAuthorized)

  // Dasha context floor: predictive and holistic queries always need the canonical
  // Vimshottari dasha sequence so synthesis can anchor phase-based predictions to
  // correct dates (data lives in chart_facts.dasha_vimshottari).
  ensureDashaContextFloor(plan, toolsAuthorized)

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
      // D7: registry-backed lookup — no audience_tier forwarded (DG1 ruling).
      // Cast to RetrievalTool for executeWithCache compatibility: the bridge's
      // retrieve() accepts Record<string,unknown> which is a structural superset
      // of QueryPlan at runtime; the cast is safe because QueryPlan satisfies
      // Record<string,unknown> at the value level.
      const t = getToolByName(toolName) as import('@/lib/retrieval/shared_types').RetrievalTool | undefined
      if (!t) return null
      const toolStart = Date.now()
      try {
        // W5 L7 (QoS priority classes + fairness): every live tool-fetch dispatch
        // goes through the process-wide QoS queue as 'interactive' priority (the
        // safe default — a human is waiting on this stream right now), keyed by
        // user.uid for the per-principal fairness guarantee. This does not change
        // behavior for a single in-flight request (default concurrency comfortably
        // exceeds any one request's own tool count) — it bounds and fair-shares
        // capacity ACROSS concurrent requests from different users. See
        // platform/src/lib/retrieval/qos/dispatch_queue.ts for the full design.
        const result = await getSharedQosDispatchQueue().submit({
          principalId: user.uid,
          priorityClass: 'interactive',
          run: () => executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName)),
        })
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
  const validToolResults = toolResults.filter((r: ToolBundle | null): r is ToolBundle => r !== null)
  const toolFetchMs = Date.now() - toolFetchWallStart

  // ── W4 core step 4 — completeness receipt (web channel) ────────────────────
  // Now that the floor tools have actually executed, emit a TRUTHFUL served/empty/dark
  // receipt for the compiled B.11 floor, mapping each floor primitive to its real
  // per-tool outcome (toolEventLog). Most floor items are dark/empty today because
  // only a small subset of MCP floor primitives map to web-executable retrieval tools
  // (the MCP↔web namespace gap) — the receipt's channel_note states that honestly.
  // Delivered as a data-completeness SSE event near the end of the stream.
  let completenessReceipt: WebCompletenessReceipt | null = null
  if (plan.scope_tuple) {
    completenessReceipt = buildWebCompletenessReceipt(
      plan.scope_tuple,
      chartId,
      toolEventLog.map(e => ({ name: e.name, status: e.status, ok_count: e.ok_count })),
    )
  }

  // Await the orientation front-door (kicked off at request open, overlapping planner +
  // tool-fetch latency). Null on failure — the dispatch path simply omits the event.
  const orientation = await orientationPromise

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
  if (true && body.persona_id) {
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
  if (true && finalConversationId) {
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

  // [PHASE-D-06] Data-readiness context injection.
  // Queries build_checkpoints to determine which chart data assets are ready.
  // Injects a NOTE into the system prompt so the model avoids hallucinating
  // data for unbuilt domains. Non-fatal — synthesis proceeds on any error.
  let dataReadinessNote: string | undefined
  try {
    const latestBuildRes = await query<{ build_id: string }>(
      `SELECT build_id FROM build_events WHERE chart_id = $1 ORDER BY emitted_at DESC LIMIT 1`,
      [chartId],
    )
    const latestBuildId = latestBuildRes.rows[0]?.build_id
    if (latestBuildId) {
      const checkpointsRes = await query<{ asset_id: string; status: string }>(
        `SELECT DISTINCT ON (asset_id) asset_id, status
           FROM build_checkpoints
          WHERE build_id = $1
          ORDER BY asset_id, completed_at DESC NULLS LAST`,
        [latestBuildId],
      )
      if (checkpointsRes.rows.length > 0) {
        const readyAssets = checkpointsRes.rows
          .filter(r => r.status === 'success')
          .map(r => r.asset_id)
        const missingAssets = checkpointsRes.rows
          .filter(r => r.status !== 'success')
          .map(r => r.asset_id)
        const total = checkpointsRes.rows.length
        if (missingAssets.length > 0) {
          dataReadinessNote = [
            `NOTE: Chart data partially built.`,
            `Assets ready: [${readyAssets.join(', ')}].`,
            `Assets not yet built: [${missingAssets.join(', ')}].`,
            `Do NOT hallucinate data for unbuilt assets — say "data not yet available" for those domains.`,
            `(${readyAssets.length} of ${total} assets complete)`,
          ].join(' ')
        } else {
          dataReadinessNote = `NOTE: All ${total} chart assets fully built. All data domains available.`
        }
      }
    }
  } catch {
    // Non-fatal: readiness check failure does not block synthesis
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
  // Unit 4.refactor_pipeline_shim — adapter dispatch body now lives in
  // `lib/pipelines/shared/run_adapter_dispatch.ts`. The route is a thin
  // selector: auth + chart resolution + planner-context + dispatch().
  return await runAdapterDispatch({
    userUid: user.uid,
    finalConversationId,
    chartId,
    audienceTier,
    selectedStack,
    isFirstTurn,
    lelContextEnabled,
    style,
    modelId,
    modelMeta,
    plannerModelId,
    plan,
    bundle,
    queryPlan,
    validToolResults,
    toolEventLog,
    plannerLatencyMs,
    composeBundleMs,
    toolFetchMs,
    queryId,
    trimmedConversationHistory,
    queryText,
    messages,
    emit,
    nextSeq,
    pendingStreamWriter,
    fetchMsrSnippets,
    dataReadinessNote,
    orientation,
    completenessReceipt,
  })
  // (formerly route.ts L899–1319: STACK_TO_ADAPTER mapping → adapter chat
  // request assembly → Gemini cache → createUIMessageStream → B.11 citation
  // gate → shared onFinish write-through → finish marker. Moved verbatim,
  // behaviour byte-identical.)

} catch (pipelineError) {
  const msg = pipelineError instanceof Error ? pipelineError.message : String(pipelineError)
  console.error('[consume:v2] pre-stream error:', msg)
  return res.internal(msg)
}
}


