/**
 * /api/pariprashna — Paripraśna consult route (lane PB-1/S-1, wave DHĀRĀ).
 *
 * A FORK (never an edit) of `/api/chat/consult/route.ts`. The consult route
 * runs the whole planner → tool-fetch → bundle pipeline BEFORE opening its
 * stream (inside `runAdapterDispatch`), so its first bytes only arrive after
 * the planner (an LLM call, seconds) completes, and a planner fault surfaces as
 * a post-nothing HTTP 4xx/5xx.
 *
 * Paripraśna INVERTS that ordering: the SSE stream opens and writes `turn.open`
 * + `phase{plan,start}` as its FIRST bytes, BEFORE the planner runs. Everything
 * heavy (chart resolution, planner, retrieval, synthesis, persistence) then runs
 * INSIDE the stream, and every fault — planner, chart, adapter — becomes an
 * in-stream `error` event, never a post-headers HTTP status.
 *
 * What it SHARES with consult (in-process, no forking of engine internals):
 *   • the SAME in-process retrieval registry (`getToolByName` → `getCapability`
 *     → `cap.handler(...)` — a direct function call, ZERO HTTP to any MCP edge);
 *   • the SAME planner (`callPipelinePlanner`), floor compiler, budget arbiter,
 *     NO-LEAKAGE filter, agentic loop (`runAgenticLoop` + `executeMCPTool`);
 *   • the SAME persistence path (`runOnFinishWriteThrough` → the existing
 *     `writeConversationMessages`), with the prediction-candidate detector left
 *     wired exactly as it fires today (it lives inside that shared helper).
 *
 * What differs: the wire format. Instead of AI-SDK UIMessage data-parts, this
 * route emits the typed Paripraśna vocabulary (`@/lib/pariprashna/protocol`),
 * Zod-validated end-to-end with ZERO `as any` in the writer path.
 *
 * Lane scope (PB-1/S-1): protocol + route only. The existing consult route is
 * byte-identical (must_not_touch). Verbosity binding is stubbed — see TODO(PB-4).
 */

import type { ModelMessage, UIMessage } from 'ai'
import { convertToModelMessages } from 'ai'

import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import {
  getConversation,
  insertConversationWithId,
  updateConversationTitle,
} from '@/lib/conversations'
import { writeConversationMessages } from '@/lib/persistence/conversation_writer'
import { extractCitations } from '@/lib/citations/citation_data_part'
import { detectPredictionCandidates } from '@/lib/ppl/prediction_detector'
import { createPendingStreamWriter } from '@/lib/persistence/pending_streams_writer'
import { generateConversationTitle } from '@/lib/conversations/title'
import {
  DEFAULT_MODEL_ID,
  DEFAULT_STACK_ID,
  STACK_ROUTING,
  getModelMeta,
  isValidModelId,
  type ModelStack,
} from '@/lib/models/registry'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import { configService } from '@/lib/config/index'
import { callPipelinePlanner as runPlanner } from '@/lib/pipeline/pipeline_planner'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import {
  compileFloorForPlan,
  ensureB11WholeChartReadFloor,
  ensureDashaContextFloor,
} from '@/lib/pipeline/compiled_floor_adapter'
import { filterLeakedCapabilities } from '@/lib/pipeline/no_leakage_filter'
import {
  buildWebCompletenessReceipt,
  type WebCompletenessReceipt,
} from '@/lib/pipeline/completeness_wiring'
import { buildChartOrientation, type ChartOrientation } from '@/lib/retrieval/orientation'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { getToolByName } from '@/lib/retrieval/registry/tool_name_bridge'
import { buildChatToolsFromNames } from '@/lib/retrieval/registry/schema_utils'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { getSharedQosDispatchQueue } from '@/lib/retrieval/qos/dispatch_queue'
import type { ToolBundle, RetrievalTool } from '@/lib/retrieval/shared_types'
import type { StackId } from '@/lib/providers/dispatcher'
import { getAdapter } from '@/lib/providers/dispatcher'
import type { ChatRequest } from '@/lib/providers/types'
import {
  buildAdapterMessages,
  buildAdapterChatRequest,
} from '@/lib/providers/adapter-dispatch-helpers'
import {
  runAgenticLoop,
  LOOP_CONFIG_BY_PROVIDER,
  type AgenticLoopConfig,
} from '@/lib/synthesis/agentic_loop'
import { executeMCPTool } from '@/lib/synthesis/mcp_tool_executor'
import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'
import { buildConsultSystemContent } from '@/lib/pipelines/shared/run_adapter_dispatch'
import {
  runOnFinishWriteThrough,
  type WriteThroughWriter,
} from '@/lib/pipelines/shared/onfinish_writethrough'
import { computeCostUsd, getModelPricingSync } from '@/lib/llm/pricing'
import { writeContextAssemblyLog } from '@/lib/db/monitoring-write'

import { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import {
  ReadingDepthSchema,
  LengthTierSchema,
  type ReadingDepth,
  type LengthTier,
} from '@/lib/pariprashna/protocol/events'
import { getCapability } from '@/lib/retrieval/registry'
import { TOOL_NAME_TO_URI } from '@/lib/retrieval/registry/tool_name_bridge'
import { resolveReaderLabel, FALLBACK_READER_LABEL } from '@/lib/pariprashna/lexicon'
import { writeTurn } from '@/lib/pariprashna/store/writer'
import { CANONICAL_SCHEMA_VERSION, type CanonicalMessage, type MessagePartInput } from '@/lib/pariprashna/store/schema'
import {
  textPartFromBlock,
  citationPartFromDetection,
  predictionCandidatePartFromDetection,
} from '@/lib/pariprashna/store/route_writer_adapter'

export const maxDuration = 120

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

// Gate 11 [integrity]: `label_key`/`detail` on activity.upsert are CLIENT-VISIBLE
// wire content (design plan §7.8/§8.4.4 — server resolves label_key -> display
// string; the client renders verbatim). Never pass a raw tool name / registry
// URI / layer name through to either field — resolve via S-2's closed-lexicon
// reader_label mapping, falling back to FALLBACK_READER_LABEL + a CI warning
// exactly like the registry's own resolveReaderLabel() contract.
function resolveActivityLabel(toolNameOrUri: string): string {
  const uri = toolNameOrUri.startsWith('marsys://') ? toolNameOrUri : TOOL_NAME_TO_URI[toolNameOrUri]
  const capability = uri ? getCapability(uri) : undefined
  if (!capability) {
    console.warn(
      `[pariprashna] activity label: no registry capability resolved for "${toolNameOrUri}" — using fallback reader label`,
    )
    return FALLBACK_READER_LABEL
  }
  return resolveReaderLabel(capability)
}

// deep_dive raises the agentic-loop iteration cap so the model can retrieve
// exhaustively across adaptive passes — the web engine's "dossier / maximal
// chart coverage" lever (the deterministic B.11 + dasha floors always run; this
// widens the ADAPTIVE re-entry budget on top of them).
const DEEP_DIVE_MAX_ITERATIONS = 16

interface RequestBody {
  chartId?: string
  conversationId?: string
  messages?: UIMessage[]
  /** Adapter stack (anthropic | gemini | gpt | deepseek | nim | marsys). */
  stack?: string
  /** PB-1/S-1 param: explicit synthesis model id. Binds directly when valid. */
  model_id?: string
  /** PB-1/S-1 param: 'auto' | 'deep_dive'. deep_dive forces the completeness path. */
  reading_depth?: string
  /** PB-1/S-1 param: verbosity/length tier — see TODO(PB-4) (no live web binding). */
  length_tier?: string
  style?: string
  lel_context_enabled?: boolean
}

/** MSR snippet resolver (read-only). Copy of the consult route's helper — this
 *  is a retrieval read, NOT the message-write path (that is shared, below). */
async function fetchMsrSnippets(signalIds: string[]): Promise<Map<string, string>> {
  if (signalIds.length === 0) return new Map()
  try {
    const placeholders = signalIds.map((_, i) => `$${i + 1}`).join(', ')
    const { rows } = await query<{ signal_id: string; name: string; description: string }>(
      `SELECT signal_id::text, signal_headline_text AS name, signal_summary_text AS description FROM bodha_msr_signals WHERE signal_id::text IN (${placeholders})`,
      signalIds,
    )
    return new Map(
      rows.map((r) => {
        const full = r.name
          ? r.description
            ? `${r.name} — ${r.description}`
            : r.name
          : r.description ?? ''
        return [r.signal_id, full.length > 295 ? full.slice(0, 294) + '…' : full]
      }),
    )
  } catch {
    return new Map()
  }
}

// Minimal, specific shapes for the AI-SDK data-parts the write-through helper
// emits — narrow interfaces (NOT `any`) so the adapter-writer can map them onto
// the Paripraśna vocabulary with full type safety.
interface CitationDataPart {
  index: number
  signal_id: string
  layer: string
  snippet: string
}
interface PersistenceDataPart {
  conversation_id: string
  message_id: string
  status: 'ok' | 'error'
}
interface PredictionCandidateDataPart {
  text: string
  score: number
  horizon: string | null
}
interface WriteThroughEvent {
  type: string
  data?: unknown
}

export async function POST(request: Request): Promise<Response> {
  const requestStartedAt = Date.now()

  // ── Pre-stream: auth + validation only (fast; real HTTP responses). ────────
  // Everything DB/LLM-bound runs INSIDE the stream so `turn.open` is the first
  // byte and every downstream fault is an in-stream `error` event.
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  // PB-1 rollback gate — the whole wave's rollback design IS this flag.
  // Off means this route does not exist for this deploy: a deliberate 404,
  // never silent processing of a half-wired surface.
  if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
    return res.notFound('Paripraśna is not enabled.')
  }

  let body: RequestBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('Invalid JSON body')
  }

  const { chartId, messages } = body
  if (!chartId || !messages) {
    return res.badRequest('chartId and messages are required')
  }
  if (!UUID_RE.test(chartId)) {
    return res.badRequest('INVALID_CHART_ID: chartId must be a valid UUID')
  }

  // ── Bind request params (pure — no DB/LLM). ────────────────────────────────
  const VALID_STACKS = Object.keys(STACK_ROUTING) as ModelStack[]
  const selectedStack: ModelStack = VALID_STACKS.includes(body.stack as ModelStack)
    ? (body.stack as ModelStack)
    : DEFAULT_STACK_ID

  // model_id (PB-1/S-1) binds DIRECTLY to the synthesis model when it names a
  // known model; otherwise fall back to the stack's synthesis primary.
  const stackSynthPrimary = await getEffectiveModel(selectedStack, 'synthesis', 'primary', request)
  const modelId = isValidModelId(body.model_id ?? '') ? (body.model_id as string) : stackSynthPrimary
  const modelMeta = getModelMeta(modelId) ?? getModelMeta(DEFAULT_MODEL_ID)!

  // reading_depth: 'auto' | 'deep_dive'. Unknown → 'auto'.
  const readingDepth: ReadingDepth = ReadingDepthSchema.safeParse(body.reading_depth).success
    ? (body.reading_depth as ReadingDepth)
    : 'auto'
  const deepDive = readingDepth === 'deep_dive'

  // TODO(PB-4): verbosity/length tier has NO live behavioral contract in the web
  // synthesis path — the adapter dispatch builds systemContent from the bundle +
  // synthesis_guidance only and never applies a ConsumeStyle/verbosity suffix
  // (the `reading_depth:deep_dive` + `exhaustive` verbosity contract landed
  // MCP-side, out of scope for this Next.js app). We accept + echo the tier on
  // `turn.open` and stamp it into persistence metadata, but it does NOT yet
  // change synthesis length. Wire the real length lever in wave PB-4.
  const lengthTier: LengthTier = LengthTierSchema.safeParse(body.length_tier).success
    ? (body.length_tier as LengthTier)
    : 'standard'

  const lelContextEnabled = body.lel_context_enabled !== false
  const style = body.style ?? 'acharya'

  // Conversation identity is resolvable synchronously (generated for a first
  // turn) so `turn.open` can carry it before any DB round-trip.
  const clientConversationId = body.conversationId
  const isFirstTurn = !clientConversationId
  const conversationId = clientConversationId ?? crypto.randomUUID()

  const turnId = crypto.randomUUID()
  const queryId = crypto.randomUUID()

  // ── Open the stream. `turn.open` + `phase{plan,start}` are the FIRST bytes. ─
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const em = new PariprashnaEmitter(controller)

      // FIRST BYTES — before the planner, before any DB/LLM work.
      em.turnOpen({
        turn_id: turnId,
        conversation_id: conversationId,
        chart_id: chartId,
        model_id: modelId,
        reading_depth: readingDepth,
        length_tier: lengthTier,
      })
      em.phase({ phase: 'plan', status: 'start' })

      const finish = (status: 'ok' | 'error' | 'aborted'): void => {
        em.turnClose({ turn_id: turnId, status, ms: Date.now() - requestStartedAt })
        em.close()
      }

      try {
        // ── Chart resolution + authorization (in-stream faults → error event). ─
        const chartResult = await query<{ id: string; name: string; client_id: string }>(
          'SELECT id, name, client_id FROM charts WHERE id=$1',
          [chartId],
        )
        if (!chartResult.rows[0]) {
          em.error({ code: 'CHART_NOT_FOUND', message: 'Chart not found.', retryable: false, phase: 'plan' })
          return finish('error')
        }
        const profileResult = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
        const isSuperAdmin = profileResult.rows[0]?.role === 'super_admin'

        const { authorizeChartAccess } = await import('@/lib/auth/authorizeChartAccess')
        type DbLike = import('@/lib/auth/authorizeChartAccess').DbLike
        const permission = await authorizeChartAccess({
          principal: { uid: user.uid, role: isSuperAdmin ? 'super_admin' : 'guest' },
          chartId,
          db: { query: (sql: string, params?: unknown[]) => query(sql, params).then((r) => ({ rows: r.rows })) } as DbLike,
        })
        if (permission === 'deny') {
          em.error({ code: 'FORBIDDEN', message: 'Not authorized for this chart.', retryable: false, phase: 'plan' })
          return finish('error')
        }

        // ── Conversation resolution / eager insert (mirrors consult). ──────────
        if (clientConversationId) {
          const existing = await getConversation({ id: clientConversationId, userId: user.uid, isSuperAdmin })
          if (!existing || existing.chart_id !== chartId) {
            em.error({ code: 'CONVERSATION_NOT_FOUND', message: 'Conversation not found.', retryable: false, phase: 'plan' })
            return finish('error')
          }
        } else {
          try {
            await insertConversationWithId({ id: conversationId, chartId, userId: user.uid, module: 'consume' })
          } catch (err) {
            const msg = String(err).toLowerCase()
            if (!msg.includes('duplicate') && !msg.includes('unique') && !msg.includes('conflict')) {
              em.error({ code: 'CONVERSATION_INIT_FAILED', message: 'Failed to initialize conversation.', retryable: true, phase: 'plan' })
              return finish('error')
            }
          }
        }

        // ── Query text + planner context. ──────────────────────────────────────
        const lastUserMessage = messages.filter((m) => m.role === 'user').at(-1)
        const queryText = (lastUserMessage?.parts ?? [])
          .filter((p) => p.type === 'text')
          .map((p) => (p as { type: string; text?: string }).text ?? '')
          .join(' ')
          .trim()

        const manifest = await loadManifest(
          '00_ARCHITECTURE/CAPABILITY_MANIFEST.json',
          '00_ARCHITECTURE/manifest_overrides.yaml',
        )

        // Orientation front-door — kicked off concurrently with the planner.
        const orientationPromise: Promise<ChartOrientation | null> = buildChartOrientation(chartId).catch(
          (err: unknown) => {
            console.error('[pariprashna] orientation build failed (non-fatal):', err)
            return null
          },
        )

        const plannerHistory = messages
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .slice(-2)
          .map((m) => ({
            role: m.role as 'user' | 'assistant',
            content: (m.parts ?? [])
              .filter((p) => p.type === 'text')
              .map((p) => (p as { type: string; text?: string }).text ?? '')
              .join(' ')
              .trim(),
          }))
          .filter((m) => m.content.length > 0)

        const [plannerModelId, plannerFallbackModelId] = await Promise.all([
          getEffectiveModel(selectedStack, 'planner_fast', 'primary', request),
          getEffectiveModel(selectedStack, 'planner_fast', 'fallback', request),
        ])

        // ── Planner. Faults → in-stream `error` event (never HTTP 4xx/5xx). ────
        // The planner emits trace steps; a no-op trace sink keeps it decoupled
        // from the Paripraśna wire (trace observability is a separate surface).
        const plannerStartedAt = Date.now()
        const plannerOutcome = await runPlanner(
          queryText,
          plannerHistory,
          plannerModelId,
          chartId,
          () => {
            /* trace sink — Paripraśna surfaces planner state via phase/activity, not trace steps */
          },
          queryId,
          plannerFallbackModelId,
        )

        if (plannerOutcome.outcome === 'clarification_needed') {
          em.flag({ code: 'clarification_needed', level: 'info', detail: plannerOutcome.question })
          em.blockOpen({ block_id: 'clar-0', pass_id: 1, role: 'prose' })
          em.blockDelta({ block_id: 'clar-0', delta: plannerOutcome.question })
          em.blockCommit({ block_id: 'clar-0', text: plannerOutcome.question })
          em.phase({ phase: 'plan', status: 'end', ms: Date.now() - plannerStartedAt })
          return finish('ok')
        }
        if (plannerOutcome.outcome === 'fault') {
          console.error('[pariprashna] planner fault:', plannerOutcome.reason, 'retryable=', plannerOutcome.retryable)
          em.error({
            code: plannerOutcome.retryable ? 'PLANNER_TRANSIENT' : 'PLANNER_INVALID_PLAN',
            message: plannerOutcome.retryable
              ? 'The planner service is temporarily unavailable. Please retry.'
              : 'The planner could not produce a valid plan. Please rephrase and try again.',
            retryable: plannerOutcome.retryable,
            phase: 'plan',
          })
          return finish('error')
        }

        const plan: PipelinePlan = plannerOutcome.plan
        const plannerLatencyMs = Date.now() - plannerStartedAt
        plan.query_plan_id = queryId
        plan.query_text = queryText
        plan.manifest_fingerprint = manifest.fingerprint
        plan.schema_version = '2.0'
        plan.planning_model_id = plannerModelId
        plan.planning_latency_ms = plannerLatencyMs
        // deep_dive → force the dasha-context floor so the completeness path has
        // the full Vimshottari sequence for maximal coverage.
        if (deepDive) plan.dasha_context_required = true

        em.phase({ phase: 'plan', status: 'end', ms: plannerLatencyMs })
        em.grade({ subject: 'query_class', grade: String(plan.query_class), detail: `${plan.tool_calls.length} planned tools` })

        // ── Budget arbitration + floor composition (identical to consult). ─────
        const arbitrated = arbitrateBudgets(
          plan.tool_calls.map((tc) => ({ tool_name: tc.tool_name, priority: tc.priority, token_budget: tc.token_budget })),
          {
            synthesis_model_max_context: modelMeta.maxInputTokens ?? 128_000,
            system_prompt_reserve: 800,
            synthesis_guidance_reserve: plan.synthesis_guidance ? 200 : 0,
            safety_margin: 0.85,
            min_tokens_per_tool: 200,
          },
        )
        for (let i = 0; i < plan.tool_calls.length; i++) plan.tool_calls[i].token_budget = arbitrated[i].token_budget

        const toolsAuthorized = Array.from(new Set(plan.tool_calls.map((tc) => tc.tool_name)))
        if (plan.scope_tuple) {
          const compiledFloor = compileFloorForPlan(plan.scope_tuple, chartId)
          for (const tc of compiledFloor.toolCalls) {
            if (!toolsAuthorized.includes(tc.tool_name)) {
              plan.tool_calls.push(tc)
              toolsAuthorized.push(tc.tool_name)
            }
          }
        }
        ensureB11WholeChartReadFloor(plan, toolsAuthorized)
        ensureDashaContextFloor(plan, toolsAuthorized)

        // NO-LEAKAGE enforcement (doctrine F-R7) — surfaced as a `flag`.
        const judgmentFlags: string[] = []
        const noLeakageFiltered = filterLeakedCapabilities(toolsAuthorized)
        if (noLeakageFiltered.length !== toolsAuthorized.length) {
          const stripped = toolsAuthorized.filter((t) => !noLeakageFiltered.includes(t))
          // Raw capability names are server-log-only (gate 11 [integrity]) —
          // the wire flag reports only a count, never the stripped identifiers.
          console.warn('[pariprashna] NO-LEAKAGE stripped capabilities:', stripped)
          judgmentFlags.push('no_leakage_capabilities_stripped')
          em.flag({
            code: 'no_leakage_capabilities_stripped',
            level: 'warn',
            detail: `${stripped.length} capabilit${stripped.length === 1 ? 'y' : 'ies'} excluded (calibration-context-only)`,
          })
          plan.tool_calls = plan.tool_calls.filter((tc) => noLeakageFiltered.includes(tc.tool_name))
          toolsAuthorized.splice(0, toolsAuthorized.length, ...noLeakageFiltered)
        }

        // Legacy-shaped plan object the registry bridge + tools read (chart_id is
        // the CR-118 fast-fail fix — every per_chart tool scopes off this).
        const queryPlan = {
          query_plan_id: queryId,
          query_text: queryText,
          chart_id: chartId,
          query_class: plan.query_class,
          domains: plan.domains ?? [],
          forward_looking: plan.forward_looking ?? false,
          tools_authorized: toolsAuthorized,
          history_mode: plan.history_mode ?? 'synthesized',
          panel_mode: plan.panel_mode ?? false,
          expected_output_shape: plan.expected_output_shape ?? 'three_interpretation',
          manifest_fingerprint: manifest.fingerprint,
          schema_version: '1.0' as const,
          planets: plan.planets,
          houses: plan.houses,
          dasha_context_required: plan.dasha_context_required,
          graph_seed_hints: plan.graph_seed_hints,
          vector_search_filter: plan.vector_search_filter,
          time_window: plan.time_window,
          tool_calls: plan.tool_calls,
        }

        // ── Retrieval (pass 1). SAME in-process registry as consult. ───────────
        const PASS_ONE = 1
        em.phase({ phase: 'retrieve', status: 'start', pass_id: PASS_ONE })
        const bundle = await hydrateBundle(plan, manifest)

        const plannerParamsMap = new Map<string, Record<string, unknown>>(
          plan.tool_calls.map((tc) => [tc.tool_name, tc.params]),
        )
        const cache = createToolCache()
        const toolEventLog: Array<{ name: string; status: 'done' | 'error'; ms: number; ok_count: number; err_count: number }> = []
        const retrieveStart = Date.now()

        const toolResults = await Promise.all(
          toolsAuthorized.map(async (toolName): Promise<ToolBundle | null> => {
            if (request.signal.aborted) return null
            const activityLabel = resolveActivityLabel(toolName)
            em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'running' })
            const t = getToolByName(toolName) as RetrievalTool | undefined
            if (!t) {
              em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'error' })
              return null
            }
            const toolStart = Date.now()
            try {
              const result = await getSharedQosDispatchQueue().submit({
                principalId: user.uid,
                priorityClass: 'interactive',
                run: () => executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName)),
              })
              const ms = Date.now() - toolStart
              em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'done', count: result.results.length, ms })
              toolEventLog.push({ name: toolName, status: 'done', ms, ok_count: result.results.length, err_count: 0 })
              return result
            } catch {
              const ms = Date.now() - toolStart
              em.activity({ key: `retrieve:${toolName}`, label_key: activityLabel, pass_id: PASS_ONE, status: 'error', ms })
              toolEventLog.push({ name: toolName, status: 'error', ms, ok_count: 0, err_count: 1 })
              return null
            }
          }),
        )
        const validToolResults = toolResults.filter((r): r is ToolBundle => r !== null)
        em.phase({ phase: 'retrieve', status: 'end', pass_id: PASS_ONE, ms: Date.now() - retrieveStart })

        // Completeness receipt — always built for deep_dive; otherwise when the
        // plan carried a scope_tuple. Surfaced as a `grade`.
        let completenessReceipt: WebCompletenessReceipt | null = null
        if (plan.scope_tuple) {
          completenessReceipt = buildWebCompletenessReceipt(
            plan.scope_tuple,
            chartId,
            toolEventLog.map((e) => ({ name: e.name, status: e.status, ok_count: e.ok_count })),
          )
        }

        const orientation = await orientationPromise

        // ── Synthesis system content (reuses consult's temporal-anchored builder). ─
        const trimmedConversationHistory: ModelMessage[] = await convertToModelMessages(
          messages.filter((m) => m.role === 'user' || m.role === 'assistant').slice(-5).slice(0, -1),
        )
        const bundleSystemContent = (bundle.assets as Array<{ content: string }>)
          .map((a) => a.content)
          .filter(Boolean)
          .join('\n\n')
        const currentMahaAntar =
          orientation?.chart_header?.current_maha_antar ?? orientation?.dasha_context?.current_maha_antar ?? null
        const systemContent = buildConsultSystemContent({
          bundleSystemContent,
          synthesisGuidance: plan.synthesis_guidance,
          nowContextDate: new Date().toISOString().slice(0, 10),
          currentMahaAntar,
        })

        // ── Adapter + agentic loop wiring (SAME engine as consult). ────────────
        const STACK_TO_ADAPTER: Partial<Record<string, StackId>> = {
          anthropic: 'anthropic',
          gemini: 'google',
          gpt: 'openai',
          deepseek: 'deepseek',
          nim: 'nvidia',
        }
        const adapterId: StackId | undefined =
          STACK_TO_ADAPTER[selectedStack] ?? (modelMeta.provider as StackId | undefined)
        if (!adapterId) {
          em.error({ code: 'NO_ADAPTER', message: `No adapter for stack=${selectedStack}.`, retryable: false, phase: 'synthesize' })
          return finish('error')
        }
        const adapterMessages = buildAdapterMessages(trimmedConversationHistory, queryText)
        let adapterChatReq: ChatRequest = buildAdapterChatRequest(adapterMessages, modelId, systemContent)
        const adapter = getAdapter(adapterId)
        const AGENTIC_PROVIDERS = new Set<string>(['anthropic', 'google', 'openai', 'deepseek', 'nvidia'])
        const useAgenticLoop = AGENTIC_PROVIDERS.has(adapterId)
        const loopMaxIterations = deepDive ? DEEP_DIVE_MAX_ITERATIONS : 8

        if (useAgenticLoop) {
          const providerManifest = adapter.getManifest()
          const toolsCfg = adapter.tools({
            toolLoopMode: providerManifest.adaptiveToolLoop,
            tools: buildChatToolsFromNames(queryPlan.tools_authorized ?? []),
            maxIterations: loopMaxIterations,
          })
          adapterChatReq = { ...adapterChatReq, toolsConfig: toolsCfg, tools: toolsCfg.tools }
        }

        // ── Synthesis stream → prose blocks + adaptive-pass seams. ─────────────
        em.phase({ phase: 'synthesize', status: 'start', pass_id: PASS_ONE })
        const synthesisStart = Date.now()

        // Pass/seam state — derived PURELY from the engine's own control flow
        // (tool-use events after prose), never from text/prose heuristics.
        let passId = PASS_ONE
        let proseSeenInPass = false
        let awaitingResume = false
        let lastToolInSeam = ''
        let blockCounter = 0
        let currentBlock: { id: string; role: 'prose' | 'thinking'; text: string } | null = null
        let accumulatedText = ''

        // PB-2/M-2: every committed block, role included — the SOURCE data for the
        // canonical `text` parts written via M-1's DAL (see finalize, below). Only
        // 'prose' blocks become `text` parts (`reasoning` kind is left for a future
        // lane — see route_writer_adapter.ts's header).
        const committedBlocks: Array<{ id: string; role: 'prose' | 'thinking'; text: string }> = []

        const commitBlock = (): void => {
          if (currentBlock) {
            em.blockCommit({ block_id: currentBlock.id, text: currentBlock.text })
            committedBlocks.push({ id: currentBlock.id, role: currentBlock.role, text: currentBlock.text })
            currentBlock = null
          }
        }
        const ensureBlock = (role: 'prose' | 'thinking'): { id: string; role: 'prose' | 'thinking'; text: string } => {
          if (currentBlock && currentBlock.role !== role) commitBlock()
          if (!currentBlock) {
            const id = `blk-${passId}-${++blockCounter}`
            currentBlock = { id, role, text: '' }
            em.blockOpen({ block_id: id, pass_id: passId, role })
          }
          return currentBlock
        }

        const baseLoopConfig: AgenticLoopConfig | undefined = LOOP_CONFIG_BY_PROVIDER[adapterId]
        const loopConfig: AgenticLoopConfig | undefined = baseLoopConfig
          ? { ...baseLoopConfig, maxIterations: loopMaxIterations }
          : undefined

        try {
          const chatStream =
            useAgenticLoop && loopConfig
              ? runAgenticLoop(adapter, adapterChatReq, (toolCall) => executeMCPTool(toolCall, { queryPlan }), loopConfig)
              : adapter.chat(adapterChatReq)

          for await (const event of chatStream) {
            if (request.signal.aborted) {
              commitBlock()
              return finish('aborted')
            }
            if (event.type === 'text_delta') {
              if (awaitingResume) {
                // Prose resumed after the engine re-entered retrieval → close seam.
                em.seamSet({ pass_id: passId, summary: lastToolInSeam ? `Consulted ${lastToolInSeam}` : 'Continued analysis' })
                em.phase({ phase: 'synthesize', status: 'start', pass_id: passId })
                awaitingResume = false
              }
              const blk = ensureBlock('prose')
              blk.text += event.text
              em.blockDelta({ block_id: blk.id, delta: event.text })
              accumulatedText += event.text
              proseSeenInPass = true
            } else if (event.type === 'thinking_delta') {
              const blk = ensureBlock('thinking')
              blk.text += event.thinking
              em.blockDelta({ block_id: blk.id, delta: event.thinking })
            } else if (event.type === 'tool_use_start') {
              em.activity({ key: `pass${passId}:tool:${event.id}`, label_key: resolveActivityLabel(event.name), pass_id: passId, status: 'running' })
            } else if (event.type === 'tool_use_complete') {
              // Engine re-entered retrieval. If prose was already emitted this
              // pass, THIS is a pass boundary (real control-flow truth).
              commitBlock()
              if (proseSeenInPass) {
                passId += 1
                proseSeenInPass = false
                lastToolInSeam = event.name
                em.phase({ phase: 'retrieve', status: 'start', pass_id: passId })
                em.seamOpen({ pass_id: passId, label_key: `pariprashna.pass.${passId}` })
                awaitingResume = true
              } else {
                lastToolInSeam = event.name
              }
              em.activity({ key: `pass${passId}:tool:${event.id}`, label_key: resolveActivityLabel(event.name), pass_id: passId, status: 'done' })
            } else if (event.type === 'error') {
              console.error('[pariprashna] adapter error event:', event.error)
              em.flag({ code: 'adapter_error', level: 'warn', detail: event.error })
            }
          }
        } catch (adapterErr) {
          console.error('[pariprashna] synthesis stream error:', adapterErr)
          em.flag({ code: 'synthesis_stream_error', level: 'error', detail: String(adapterErr) })
        }
        commitBlock()
        em.phase({ phase: 'synthesize', status: 'end', pass_id: passId, ms: Date.now() - synthesisStart })

        // ── B.11 citation gate (adapter-path parity) → grade + flag. ───────────
        let citationGateResult: 'PASS' | 'WARN' | 'ERROR' = 'PASS'
        let citationL1Count = 0
        let citationL2Verified = 0
        try {
          const assembledContextJson = JSON.stringify({ bundle, tool_results: validToolResults })
          const overrideOn = configService.getFlag('CITATION_GATE_OVERRIDE')
          const validation = validateCitationsForStream(
            accumulatedText,
            assembledContextJson,
            plan.query_class as Parameters<typeof validateCitationsForStream>[2],
            overrideOn,
          )
          citationGateResult = validation.gateResult
          citationL1Count = validation.layer1Count
          citationL2Verified = validation.layer2Verified
          em.grade({ subject: 'citation_gate', grade: validation.gateResult, detail: validation.gateReason })
          if (validation.gateResult === 'WARN') {
            judgmentFlags.push('citation_gate_warn')
            em.flag({ code: 'citation_gate_warn', level: 'warn', detail: validation.gateReason })
          } else if (validation.gateResult === 'ERROR') {
            judgmentFlags.push('citation_gate_error')
            em.flag({ code: 'citation_gate_error', level: 'error', detail: validation.gateReason })
          }
        } catch (err) {
          console.error('[pariprashna] citation gate error', err)
        }

        // ── Finalize: persistence. ──────────────────────────────────────────────
        // PB-2/M-2: the ASSISTANT turn's content persists via M-1's canonical
        // `writeTurn` DAL (transactional message row + kind-typed parts) — see
        // the `persistence.writeMessages` closure below. This REPLACES the
        // legacy write-through for the assistant's content; it is never run in
        // parallel with it for the same row.
        //
        // Scope decision (M-2, disclosed): conversation HISTORY (every message
        // prior to this turn, including the user's current query) still
        // persists via the pre-existing legacy `writeConversationMessages`
        // helper, UNCHANGED. Migrating user-message persistence onto a
        // canonical schema is not part of M-1's schema/DAL charter (M-1 built
        // `message_parts` for the ASSISTANT turn's kind-typed content) and is
        // well beyond "persistence seam only" scope — rearchitecting it here
        // risks a real regression (silently dropped user-message history) for
        // no requested benefit. See the M-2 report.
        em.phase({ phase: 'finalize', status: 'start' })
        const pendingStreamWriter = createPendingStreamWriter(queryId, conversationId, user.uid)

        if (accumulatedText) {
          const historyMsgs: UIMessage[] = (messages as UIMessage[]).map(
            (m) => ({ ...m, id: crypto.randomUUID() }) as UIMessage,
          )
          const assistantMessageId = crypto.randomUUID()
          // Used for onfinish's title-generation step only (needs the FULL
          // turn incl. assistant text) — NOT for persistence (see the
          // `persistence.writeMessages` closure below, which ignores
          // `args.messages` and writes history/assistant separately).
          const persistMsgs: UIMessage[] = [
            ...historyMsgs,
            { id: assistantMessageId, role: 'assistant' as const, parts: [{ type: 'text', text: accumulatedText }] } as UIMessage,
          ]
          const lastUserText = ((lastUserMessage?.parts ?? []) as Array<{ type: string; text?: string }>)
            .filter((p) => p.type === 'text')
            .map((p) => p.text ?? '')
            .join(' ')
            .trim()

          // Adapter-writer: maps the write-through's AI-SDK data-parts onto the
          // Paripraśna vocabulary. Typed with a narrow event interface (NOT
          // `any`) — assignable to WriteThroughWriter because its `write` param
          // is `any`, so no cast is needed at the boundary.
          const bridgeWriter: WriteThroughWriter = {
            write: (evt: WriteThroughEvent): void => {
              switch (evt.type) {
                case 'data-citation': {
                  const d = evt.data as CitationDataPart
                  em.citationDefine({ index: d.index, signal_id: d.signal_id, layer: d.layer, snippet: d.snippet })
                  break
                }
                case 'data-persistence': {
                  const d = evt.data as PersistenceDataPart
                  em.turnCommit({
                    turn_id: turnId,
                    conversation_id: d.conversation_id,
                    message_id: d.message_id,
                    status: d.status,
                    assistant_chars: accumulatedText.length,
                  })
                  break
                }
                case 'data-prediction-candidate': {
                  // Detector left wired exactly as it fires today (inside the
                  // shared helper); surfaced here as an info flag.
                  const d = evt.data as PredictionCandidateDataPart
                  em.flag({ code: 'prediction_candidate', level: 'info', detail: `${d.text} (score=${d.score}${d.horizon ? `, horizon=${d.horizon}` : ''})` })
                  break
                }
                case 'data-correction': {
                  em.flag({ code: 'correction', level: 'info' })
                  break
                }
                case 'data-out-of-domain': {
                  em.flag({ code: 'out_of_domain', level: 'warn' })
                  break
                }
                default:
                  // data-cost / data-title / etc — not part of the Paripraśna wire.
                  break
              }
            },
          }

          const tokensForAdapter = (predicate: (toolName: string) => boolean): number => {
            let chars = 0
            for (const tb of validToolResults) {
              if (!predicate(tb.tool_name)) continue
              for (const r of tb.results) chars += r.content.length
            }
            return Math.ceil(chars / 4)
          }

          await runOnFinishWriteThrough(
            {
              pipelineKind: 'agentic',
              queryId,
              conversationId,
              chartId,
              userUid: user.uid,
              isFirstTurn,
              lelContextEnabled,
              finalMessages: persistMsgs,
              assistantText: accumulatedText,
              lastUserQuery: lastUserText,
              lastAssistantMetadata: {
                custom: {
                  model: modelId,
                  queryId,
                  planning_model_id: plannerModelId,
                  planning_latency_ms: plannerLatencyMs,
                  disclosure_tier: isSuperAdmin ? 'super_admin' : 'client',
                  query_class: plan.query_class,
                  stack: selectedStack,
                  style,
                  reading_depth: readingDepth,
                  length_tier: lengthTier,
                  pipeline: 'pariprashna',
                  conversationId,
                },
              },
              modelId,
              modelMaxContext: modelMeta.maxInputTokens ?? null,
              synthUsage: null,
              synthesisElapsedMs: Date.now() - synthesisStart,
              citationGate: { gateResult: citationGateResult, layer1Count: citationL1Count, layer2Verified: citationL2Verified },
              contextAssembly: {
                l1_tokens: tokensForAdapter((n) => ['chart_facts_query', 'divisional_query', 'kp_query', 'manifest_query'].includes(n)),
                l2_5_signal_tokens: tokensForAdapter((n) => ['msr_sql', 'query_msr_aggregate', 'query_signal_state'].includes(n)),
                l2_5_pattern_tokens: tokensForAdapter((n) => ['pattern_register', 'resonance_register', 'contradiction_register', 'cluster_atlas'].includes(n)),
                l4_tokens: tokensForAdapter((n) => ['remedial_codex_query', 'domain_report_query'].includes(n)),
                vector_tokens: tokensForAdapter((n) => n === 'vector_search'),
                cgm_tokens: tokensForAdapter((n) => n === 'cgm_graph_walk'),
              },
              writer: bridgeWriter,
              emit: () => {
                /* trace sink — Paripraśna surfaces state via its own vocabulary */
              },
            },
            {
              persistence: {
                writeMessages: async (args) => {
                  // History rows — legacy path, UNCHANGED (see scope-decision
                  // comment above). `args.messages` (== persistMsgs, history +
                  // assistant) is deliberately NOT used here — the assistant
                  // row is written canonically below instead.
                  const historyResult = await writeConversationMessages({
                    conversationId,
                    messages: historyMsgs,
                  })

                  // Assistant row — PB-2/M-2 canonical path. Built from the
                  // route's own in-memory turn data via
                  // route_writer_adapter.ts's production mapping functions —
                  // the SAME functions lane M-2's byte-equality gate
                  // (tests/pariprashna/reducer/canonical_serialization_golden.test.ts)
                  // exercises independently against a client-reducer simulation.
                  const canonicalParts: MessagePartInput[] = []
                  let partSeq = 0
                  for (const b of committedBlocks) {
                    if (b.role === 'prose') {
                      canonicalParts.push(textPartFromBlock({ block_id: b.id, text: b.text }, partSeq++))
                    }
                  }
                  const citationsFound = extractCitations(accumulatedText)
                  if (citationsFound.length > 0) {
                    const snippets = await fetchMsrSnippets(citationsFound.map((c) => c.signal_id))
                    for (const c of citationsFound) {
                      canonicalParts.push(
                        citationPartFromDetection(
                          {
                            index: c.index,
                            signal_id: c.signal_id,
                            layer: c.layer,
                            snippet: snippets.get(c.signal_id) ?? '',
                          },
                          partSeq++,
                        ),
                      )
                    }
                  }
                  const predictionCandidatesFound = detectPredictionCandidates(accumulatedText).filter(
                    (c) => c.score >= 0.5,
                  )
                  for (const c of predictionCandidatesFound) {
                    canonicalParts.push(
                      predictionCandidatePartFromDetection(
                        { text: c.text, score: c.score, horizon: c.horizon },
                        partSeq++,
                      ),
                    )
                  }

                  const canonicalMessage: CanonicalMessage = {
                    id: assistantMessageId,
                    conversation_id: conversationId,
                    role: 'assistant',
                    schema_version: CANONICAL_SCHEMA_VERSION,
                    model_id: modelId,
                    provider: modelMeta.provider,
                    metadata: args.lastAssistantMetadata,
                  }

                  let canonicalOk = true
                  try {
                    await writeTurn(canonicalMessage, canonicalParts)
                  } catch (err) {
                    console.error('[pariprashna] canonical writeTurn failed', err)
                    canonicalOk = false
                  }

                  return {
                    verified: historyResult.verified && canonicalOk,
                    messageIds: [...historyResult.messageIds, assistantMessageId],
                  }
                },
              },
              pricing: {
                getPricing: (mid) => getModelPricingSync(mid),
                computeUsd: (pricing, tokens) => computeCostUsd(pricing as Parameters<typeof computeCostUsd>[0], tokens),
              },
              contextAssemblyLog: (entry) => {
                void writeContextAssemblyLog(entry)
              },
              fetchMsrSnippets: (ids) => fetchMsrSnippets(ids),
              pendingStreamWriter,
              title: {
                generate: (msgs, c) => generateConversationTitle(msgs, c),
                update: (cid, t) => updateConversationTitle(cid, t).then(() => undefined),
              },
              predictionLedger: async (entry) => {
                try {
                  const fs = await import('fs/promises')
                  const path = await import('path')
                  const ledgerPath = path.join(process.cwd(), '..', '06_LEARNING_LAYER', 'PREDICTION_LEDGER', 'prediction_ledger.jsonl')
                  const line =
                    JSON.stringify({
                      ...entry,
                      outcome: null,
                      confidence: null,
                      horizon: null,
                      falsifier: null,
                      note: 'Auto-logged blind-mode query (pariprashna). Outcome/confidence/horizon/falsifier to be filled by native.',
                    }) + '\n'
                  await fs.appendFile(ledgerPath, line, 'utf8')
                } catch {
                  /* non-fatal */
                }
              },
            },
          )
        } else {
          // No prose produced — persistence is skipped by the shared helper, so
          // report the honest gap rather than silently omitting turn.commit.
          em.flag({ code: 'empty_synthesis', level: 'warn', detail: 'No assistant text produced.' })
        }

        // Completeness + aggregated judgment flags (grade/flag — always emitted).
        // `coverage` is a {floor_item_total, served, empty, dark} object, never a
        // scalar — String(coverage) previously produced the literal "[object
        // Object]" on the wire. Report the served/total fraction instead.
        if (completenessReceipt) {
          const { served, floor_item_total } = completenessReceipt.coverage
          em.grade({
            subject: 'completeness',
            grade: `${served}/${floor_item_total}`,
            detail: completenessReceipt.channel_note,
          })
        }

        em.phase({ phase: 'finalize', status: 'end' })
        return finish('ok')
      } catch (fatal) {
        console.error('[pariprashna] fatal in-stream error:', fatal)
        em.error({ code: 'INTERNAL', message: fatal instanceof Error ? fatal.message : String(fatal), retryable: false })
        return finish('error')
      }
    },
  })

  return new Response(stream, {
    headers: {
      'content-type': 'text/event-stream; charset=utf-8',
      'cache-control': 'no-cache, no-transform',
      connection: 'keep-alive',
      'x-accel-buffering': 'no',
    },
  })
}
