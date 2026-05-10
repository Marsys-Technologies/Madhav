import {
  streamText,
  stepCountIs,
  convertToModelMessages,
  createIdGenerator,
  generateText,
  smoothStream,
} from 'ai'
import type { ModelMessage, UIMessage } from 'ai'
import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { consumeTools, buildConsumeTools } from '@/lib/claude/consume-tools'
import { consumeSystemPrompt, type ConsumeStyle } from '@/lib/claude/system-prompts'
import {
  getConversation,
  insertConversationWithId,
  replaceConversationMessages,
  updateConversationTitle,
} from '@/lib/conversations'
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
import { resolveModel, googleProviderOptions, deepseekProviderOptions } from '@/lib/models/resolver'
import { configService } from '@/lib/config/index'
import { classify } from '@/lib/router/router'
import { callLlmPlanner, PlannerError, type PlanSchema } from '@/lib/pipeline/manifest_planner'
import { plannerCircuit, PlannerCircuitOpenError } from '@/lib/pipeline/planner_circuit_breaker'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import { compose } from '@/lib/bundle/rule_composer'
import { getTool } from '@/lib/retrieve/index'
import { createToolCache, executeWithCache } from '@/lib/cache/index'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { runAll, summarize } from '@/lib/validators/index'
import type { ValidationResult } from '@/lib/validators/types'
import { createOrchestrator } from '@/lib/synthesis/index'
import {
  contextAssembler,
  CONTEXT_ASSEMBLY_TOKEN_THRESHOLD,
  estimateBundleTokens,
} from '@/lib/synthesis/context_assembler'
import type { ContextBundle } from '@/lib/synthesis/types'
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
  const stackSynthPrimary = STACK_ROUTING[selectedStack].synthesis.primary
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

  if (configService.getFlag('NEW_QUERY_PIPELINE_ENABLED')) {
    try {
    const lastUserMessage = messages.filter(m => m.role === 'user').at(-1)
    const queryText = extractText(lastUserMessage?.parts ?? [])

    const manifest = await loadManifest('00_ARCHITECTURE/CAPABILITY_MANIFEST.json', '00_ARCHITECTURE/manifest_overrides.yaml')

    // ── W2-PLANNER: LLM-first planner branch ──────────────────────────────
    // When LLM_FIRST_PLANNER_ENABLED is true, the planner runs BEFORE classify
    // and produces a PlanSchema that drives tool execution. On any failure
    // (provider error, schema invalid), we fall back silently to the existing
    // classify() + compose_bundle() path. The flag stays false in DEFAULT_FLAGS
    // — the native controls activation.
    // CTX-GAP-S1: Explicitly pass last 2 turns (= the effective window that
    // planner_context_builder will actually use after its internal slice(-MAX_TURNS=2)).
    // Previous slice(-4) created a silent mismatch — caller believed planner saw 4
    // turns, but planner_context_builder re-sliced to 2 internally.
    // Also used by classify() — both stages now see the same explicit 2-turn window.
    const plannerHistory = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-2)
      .map(m => ({
        role: m.role as 'user' | 'assistant',
        content: extractText(m.parts ?? []),
      }))
      .filter(m => m.content.length > 0)
    // Pre-allocate query_id so it's stable across planner + classify and can be
    // used by all monitoring write helpers, even when the planner runs before
    // classify() generates the QueryPlan.
    const preAllocatedQueryId = crypto.randomUUID()
    let planSchema: PlanSchema | null = null
    let plannerLatencyMs: number | null = null
    let plannerModelIdUsed: string | null = null
    let plannerErrorMsg: string | null = null
    let plannerFallbackUsed = false
    if (configService.getFlag('LLM_FIRST_PLANNER_ENABLED')) {
      const plannerModelId = STACK_ROUTING[selectedStack].planner_fast.primary
      const plannerFallbackModelId = STACK_ROUTING[selectedStack].planner_fast.fallback
      plannerModelIdUsed = plannerModelId
      const plannerStartedAt = Date.now()
      try {
        planSchema = await plannerCircuit.call(() =>
          callLlmPlanner(
            queryText,
            plannerHistory,
            plannerModelId,
            chartId,
            (event) => traceEmitter.emitStep(event),
            preAllocatedQueryId,
            plannerFallbackModelId,
          ),
        )
        plannerLatencyMs = Date.now() - plannerStartedAt
      } catch (err) {
        plannerLatencyMs = Date.now() - plannerStartedAt
        plannerFallbackUsed = true
        if (err instanceof PlannerCircuitOpenError) {
          console.warn('[planner] circuit open — skipping planner, using classify() fallback')
          plannerErrorMsg = 'circuit_open'
        } else if (err instanceof PlannerError) {
          console.warn('[planner] LLM planner failed, falling back to classify()', err.message)
          plannerErrorMsg = err.message
        } else {
          console.warn('[planner] unexpected planner error, falling back to classify()', err)
          plannerErrorMsg = err instanceof Error ? err.message : String(err)
        }
        planSchema = null
      }
    }

    const classifyStart = Date.now()
    const queryPlan = await classify(queryText, {
      audience_tier: isSuperAdmin ? 'super_admin' : 'client',
      manifest_fingerprint: manifest.fingerprint,
      conversation_history: plannerHistory,
      query_plan_id: preAllocatedQueryId,
    })
    const queryId = queryPlan.query_plan_id

    // ── MON-6: query_plan_log write ────────────────────────────────────────
    // Only emit when the planner actually ran. Successful planner → full plan
    // payload; PlannerError fallback → parsing_success=false + parse_error.
    if (plannerModelIdUsed) {
      void writeQueryPlanLog({
        query_id: queryId,
        conversation_id: finalConversationId ?? null,
        chart_id: chartId ?? null,
        planner_model_id: plannerModelIdUsed,
        query_text: queryText,
        query_class: planSchema?.query_class ?? queryPlan.query_class,
        tool_count: planSchema
          ? planSchema.tool_calls.length
          : queryPlan.tools_authorized.length,
        plan_json: planSchema
          ? (planSchema as unknown as Record<string, unknown>)
          : null,
        parsing_success: planSchema !== null,
        parse_error: plannerErrorMsg,
        fallback_used: plannerFallbackUsed,
        planner_latency_ms: plannerLatencyMs,
      })
    }

    // When the planner produced a plan, its tool list overrides classify()'s
    // tools_authorized. classify() + compose() still run so the bundle and the
    // rest of queryPlan (audience_tier, query_class, panel_mode, …) remain
    // available for downstream consumers (validators, synthesis, citation
    // gate, audit). Per-tool param threading from planSchema.tool_calls into
    // each retrieval tool is W2-TRACE-A scope.
    if (planSchema) {
      // UQE-5a: enforce a hard cap on the sum of per-tool token_budgets so
      // retrieval cannot blow past the synthesis model's effective context
      // window. Pure proportional trim p3 → p2 → p1, with a floor on p1 tools.
      const arbitrated = arbitrateBudgets(
        planSchema.tool_calls.map(tc => ({
          tool_name: tc.tool_name,
          priority: tc.priority,
          token_budget: tc.token_budget,
        })),
        {
          synthesis_model_max_context: modelMeta.maxInputTokens ?? 128_000,
          system_prompt_reserve: 800,
          synthesis_guidance_reserve: 200,
          safety_margin: 0.85,
          min_tokens_per_tool: 200,
        },
      )
      for (let i = 0; i < planSchema.tool_calls.length; i++) {
        planSchema.tool_calls[i].token_budget = arbitrated[i].token_budget
      }
      const plannerTools = Array.from(new Set(planSchema.tool_calls.map(tc => tc.tool_name)))
      queryPlan.tools_authorized = plannerTools
    }

    // W2-TRACE-A: map from tool_name → planner-supplied params.
    // When the LLM planner is active, these narrow the retrieve call
    // (e.g. msr_sql gets { planet:'SATURN', valence:'negative' }).
    // When planSchema is null (classify() fallback), map is empty and
    // executeWithCache receives undefined — no behaviour change.
    const plannerParamsMap = new Map<string, Record<string, unknown>>(
      planSchema?.tool_calls.map(tc => [tc.tool_name, tc.params]) ?? []
    )

    // UQE-9 (W2-BUGS B2W-7) — atomic per-request step_seq counter. Replaces
    // every hard-coded `step_seq: N` and `step_seq: 3 + idx` arithmetic so
    // parallel tools and synthesis can never collide on the same logical seq.
    // Single-thread async context, so no locks needed.
    let stepSeq = 0
    const nextSeq = () => ++stepSeq

    // Step 1 — classify (emit done immediately; query_id now known)
    traceEmitter.emitStep({
      event: 'step_done',
      query_id: queryId,
      step: {
        query_id: queryId,
        conversation_id: finalConversationId,
        step_seq: nextSeq(),
        step_name: 'classify',
        step_type: 'deterministic',
        status: 'done',
        started_at: new Date(classifyStart).toISOString(),
        completed_at: new Date().toISOString(),
        latency_ms: Date.now() - classifyStart,
        data_summary: {
          result: queryPlan.query_class,
          query_class: queryPlan.query_class,
          confidence: queryPlan.router_confidence,
          planning_confidence: queryPlan.router_confidence,
        },
        // G.1: wire plan_json tool calls + full query plan to QueryDNAPanel
        payload: {
          query_plan: {
            ...(queryPlan as unknown as TraceQueryPlan),
            query_intent_summary: (planSchema as unknown as Record<string, unknown> | null)?.query_intent_summary as string | undefined,
            planning_rationale: (planSchema as unknown as Record<string, unknown> | null)?.planning_rationale as string | undefined,
            synthesis_guidance: (planSchema as unknown as Record<string, unknown> | null)?.synthesis_guidance as string | undefined,
            planning_model_id: plannerModelIdUsed ?? undefined,
            planning_latency_ms: plannerLatencyMs ?? undefined,
          } as TraceQueryPlan,
          tool_calls: planSchema?.tool_calls as unknown as TraceToolCallSpec[] | undefined,
        },
      },
    })

    const composeStart = Date.now()
    const bundle = await compose(queryPlan)
    // Step 2 — compose bundle
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
          result: `${bundle.mandatory_context.length} bundles · ${queryPlan.tools_authorized.length} tools`,
        },
        payload: {},
      },
    })

    // BUG-9: B.11 Whole-Chart-Read enforcement — ensure at least one L2.5 tool
    // is in tools_authorized. A query that only selects L1 tools violates B.11.
    // These are the canonical L2.5 retrieval tool names per inferLayer().
    {
      const L2_5_TOOLS = ['msr_sql', 'query_msr_aggregate', 'pattern_register',
        'resonance_register', 'cluster_atlas', 'contradiction_register', 'cgm_graph_walk']
      const hasL2_5 = queryPlan.tools_authorized.some(t => L2_5_TOOLS.includes(t))
      if (!hasL2_5) {
        queryPlan.tools_authorized.push('msr_sql', 'cgm_graph_walk')
        console.log('[consume:v2] B.11 enforcement: added msr_sql + cgm_graph_walk to tools_authorized')
      }
    }

    const cache = createToolCache()
    const toolFetchWallStart = Date.now()
    // UQE-9: pre-allocate one seq per tool BEFORE the parallel emissions so
    // the running event and the eventual done/error event for the same logical
    // tool step share a single step_seq.
    const toolSeqs: number[] = queryPlan.tools_authorized.map(() => nextSeq())
    // Steps 3…N — emit 'running' for all tools simultaneously (they fire in parallel)
    queryPlan.tools_authorized.forEach((toolName: string, idx: number) => {
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
      queryPlan.tools_authorized.map(async (toolName: string, idx: number) => {
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

    // W2-CTX-ASSEMBLY: optional LLM-based context compression step. When the
    // flag is OFF (default) we forward validToolResults to synthesis unchanged
    // — zero behaviour change. When ON, the assembler model compresses /
    // reorders the bundle and returns a ContextBundle whose tool_bundles are
    // passed downstream in place of validToolResults.
    // BUG-8: NIM stack bypasses context assembly — assembler model has empty
    // capabilities and degrades signal IDs. Force off for NIM regardless of flag.
    const effectiveContextAssembly =
      configService.getFlag('CONTEXT_ASSEMBLY_ENABLED') && selectedStack !== 'nim'

    let assembledBundle: ContextBundle | null = null
    let synthesisToolResults: ToolBundle[] = validToolResults
    // P5 D.5.1 — short-circuit when tool-result bundle is already small.
    const totalToolTokens = estimateBundleTokens(validToolResults)
    const belowThreshold = totalToolTokens < CONTEXT_ASSEMBLY_TOKEN_THRESHOLD
    if (effectiveContextAssembly && !belowThreshold) {
      const ctxLlmSeq = nextSeq()
      const assemblerModelId = STACK_ROUTING[selectedStack].context_assembly.primary
      assembledBundle = await contextAssembler(
        validToolResults,
        queryPlan,
        assemblerModelId,
        {
          queryId,
          conversationId: finalConversationId,
          stepSeq: ctxLlmSeq,
        },
      )
      synthesisToolResults = assembledBundle.tool_bundles
    } else if (effectiveContextAssembly && belowThreshold) {
      // Emit a trace event so the lifecycle view can show "skipped — token
      // threshold met". synthesisToolResults stays as validToolResults; the
      // downstream synthesis path already handles a null assembledBundle.
      const ctxLlmSeq = nextSeq()
      traceEmitter.emitStep({
        event: 'step_done',
        query_id: queryId,
        step: {
          query_id: queryId,
          conversation_id: finalConversationId,
          step_seq: ctxLlmSeq,
          step_name: 'context_assembly',
          step_type: 'llm',
          status: 'done',
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          latency_ms: 0,
          data_summary: {
            short_circuited: true,
            reason: 'token_threshold',
            total_token_estimate: totalToolTokens,
            threshold: CONTEXT_ASSEMBLY_TOKEN_THRESHOLD,
          },
          payload: {},
        },
      })
    }

    // UQE-9: pre-allocate context_assembly seq first (single_model_strategy
    // emits context_assembly before synthesis_done), then the synthesis seq
    // shared by start (here) and done (in onFinish inside the orchestrator).
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

    const orchestrator = createOrchestrator({ panel_opt_in: panelOptIn })
    const { result, methodologyBlockHolder } = await orchestrator.synthesize({
      query: queryText,
      query_plan: queryPlan,
      bundle,
      tool_results: synthesisToolResults,
      // CTX-GAP-S1: Cap synthesis history to the last 4 messages (= 2 prior user+assistant
      // exchange pairs) to prevent prior conversation narrative from contaminating the
      // corpus-grounded synthesis response. Aligns with planner_context_builder's
      // effective 2-turn window. Unbounded history (.slice(0,-1)) was the primary
      // vector for context contamination, especially on Gemini stack.
      conversation_history: messages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .slice(-5)       // last 5 = 2 prior pairs + current user message
        .slice(0, -1)    // drop current user message (appended via `query`)
        .map(m => ({
          role: m.role as 'user' | 'assistant',
          content: extractText(m.parts ?? []),
        }))
        .filter(m => m.content.length > 0),
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
            // P4 D.4.3: planner attribution propagation. context_assembler not
            // currently surfaced as a separate model in this route — left null.
            planning_model_id: plannerModelIdUsed ?? null,
            planning_latency_ms: plannerLatencyMs ?? null,
            // F014 fix: emit planner_active into SSE body so runner.py regex can detect it
            planner_active: planSchema !== null && !plannerFallbackUsed,
            context_assembler_model_id: null,
            context_assembler_latency_ms: null,
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
            planning_model_id: plannerModelIdUsed ?? null,
            planning_latency_ms: plannerLatencyMs ?? null,
            planner_active: planSchema !== null && !plannerFallbackUsed,
            context_assembler_model_id: null,
            context_assembler_latency_ms: null,
          }
        }
        if (part.type === 'finish') {
          return { methodology_block: methodologyBlockHolder?.value ?? null }
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
          // BUG-6: prefer assembled bundle when context assembly ran, so citation
          // verification checks against the signal IDs synthesis actually saw.
          const assembledContextJson = JSON.stringify({
            bundle,
            tool_results: assembledBundle?.tool_bundles ?? validToolResults,
          })
          const citationCheck = validateCitations(outputText, assembledContextJson, queryPlan.query_class)
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
          // Per-layer token breakdown. When CONTEXT_ASSEMBLY_ENABLED ran, the
          // ContextBundle returned by contextAssembler already carries per-
          // layer counts on the (possibly compressed) bundle — prefer those
          // so the log reflects what synthesis actually saw. Otherwise group
          // validToolResults inline by source-canonical-id (B.10:
          // Math.ceil(str.length / 4) when no SDK-side count is available).
          const sourceBundles = assembledBundle?.tool_bundles ?? validToolResults
          const tokensFor = (predicate: (toolName: string) => boolean): number => {
            let chars = 0
            for (const tb of sourceBundles) {
              if (!predicate(tb.tool_name)) continue
              for (const r of tb.results) chars += r.content.length
            }
            return Math.ceil(chars / 4)
          }
          void writeContextAssemblyLog({
            query_id: queryId,
            l1_tokens: assembledBundle?.l1_tokens ?? tokensFor(n => [
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
            l4_tokens: assembledBundle?.l4_tokens ?? tokensFor(n => ['remedial_codex_query', 'domain_report_query'].includes(n)),
            vector_tokens: assembledBundle?.vector_tokens ?? tokensFor(n => n === 'vector_search'),
            cgm_tokens: assembledBundle?.cgm_tokens ?? tokensFor(n => n === 'cgm_graph_walk'),
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
          if (isFirstTurn) {
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

  const systemPrompt = consumeSystemPrompt(chart, reportsResult.rows, style, !lelContextEnabled)

  console.log(`[consume] pre-stream setup: ${Date.now() - setupStart}ms  stack=${selectedStack}  model=${modelId}  style=${style}`)

  // Provider-specific system message handling. Anthropic supports ephemeral
  // prompt caching on the stable prefix; Gemini does not. Attach cache control
  // only where it's supported so other providers see a plain system message.
  const systemMessage: ModelMessage = supports(modelId, 'prompt-caching')
    ? {
        role: 'system',
        content: systemPrompt,
        providerOptions: {
          anthropic: { cacheControl: { type: 'ephemeral' } },
        },
      }
    : {
        role: 'system',
        content: systemPrompt,
      }

  const modelMessages: ModelMessage[] = [
    systemMessage,
    ...(await convertToModelMessages(messages)),
  ]

  let finishReason: string | undefined

  // Some models (e.g. DeepSeek R1) don't support tool-use reliably; omit tools
  // entirely for those so the model answers from conversation context alone
  // rather than emitting malformed tool calls.
  const toolsForModel = supports(modelId, 'tool-use') ? buildConsumeTools(lelContextEnabled) : undefined

  // Synthesis-time tool calls (consumeTools / buildConsumeTools) need a stable
  // query_id to land in tool_execution_log. The v2 pipeline pre-allocates one;
  // the legacy path mints its own here so onStepFinish can correlate rows.
  const queryId = crypto.randomUUID()

  const result = streamText({
    model: resolveModel(modelId),
    messages: modelMessages,
    tools: toolsForModel,
    stopWhen: stepCountIs(5),
    maxOutputTokens: modelMeta.maxOutputTokens,
    experimental_transform: smoothStream({ delayInMs: 20, chunking: 'word' }),
    // NIM retry guard — same as single_model_strategy. maxRetries: 0 prevents
    // the 3-attempt cycle (AI_RetryError after 3× headers-timeout ≈ 5+ min).
    // nimFetch in nvidia.ts enforces a 30 s hard abort, so worst-case hang
    // for a dead NIM endpoint is ~30 s, not 5+ minutes.
    ...(modelMeta.provider === 'nvidia' && { maxRetries: 0 }),
    // Google-specific: disable safety filters + cap thinking budget.
    // DeepSeek V4 Pro: activate thinking=enabled for synthesis CoT.
    // Merge at the top-level provider key — no model is both google and deepseek.
    ...((googleProviderOptions(modelId) || deepseekProviderOptions(modelId, 'synthesis')) && {
      providerOptions: {
        ...(googleProviderOptions(modelId)?.google && { google: googleProviderOptions(modelId)!.google }),
        ...(deepseekProviderOptions(modelId, 'synthesis')?.deepseek && { deepseek: deepseekProviderOptions(modelId, 'synthesis')!.deepseek }),
      },
    }),
    onStepFinish: ({ toolCalls, toolResults }) => {
      // Log each tool call that happened during this synthesis step.
      // The retrieve-tools path (executeWithCache) logs itself — this hook
      // only fires for consumeTools (structured tools + chart tools called
      // during streamText). Fire-and-forget: never throw to the caller.
      if (!toolCalls?.length) return
      for (let i = 0; i < toolCalls.length; i++) {
        const tc = toolCalls[i]
        const tr = toolResults?.[i] as { result?: unknown } | undefined
        const result = tr?.result
        const rowsReturned =
          result != null
            ? Array.isArray(result)
              ? result.length
              : 1
            : 0
        void writeToolExecutionLog({
          query_id: queryId,
          tool_name: tc.toolName,
          params_json: (tc as { args?: Record<string, unknown> }).args ?? {},
          status: result != null ? 'success' : 'error',
          rows_returned: rowsReturned,
          latency_ms: null,
          token_estimate: null,
          data_asset_id: null,
          error_code: null,
          served_from_cache: false,
          fallback_used: false,
        })
      }
    },
    onFinish: ({ finishReason: reason, providerMetadata, usage }) => {
      finishReason = reason
      const meta = providerMetadata?.anthropic as
        | { cacheReadInputTokens?: number; cacheCreationInputTokens?: number }
        | undefined
      console.log(
        `[consume] stream finish: model=${modelId} finishReason=${reason} ` +
          `cacheRead=${meta?.cacheReadInputTokens ?? 0} ` +
          `cacheCreate=${meta?.cacheCreationInputTokens ?? 0} ` +
          `inputTokens=${usage?.inputTokens ?? 0} ` +
          `outputTokens=${usage?.outputTokens ?? 0}`
      )
      if (reason === 'length') {
        console.warn('[consume] OUTPUT TRUNCATED: hit maxOutputTokens cap', {
          model: modelId,
          cap: modelMeta.maxOutputTokens,
        })
      }
    },
  })

  // Keep the server stream alive even if the client disconnects, so onFinish
  // still fires and we persist the full assistant turn.
  result.consumeStream()

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    generateMessageId: createIdGenerator({ prefix: 'msg', size: 16 }),
    messageMetadata: ({ part }) => {
      if (part.type === 'start' && isFirstTurn) {
        return { conversationId: finalConversationId, model: modelId, stack: selectedStack, queryId }
      }
      if (part.type === 'start') {
        return { model: modelId, stack: selectedStack, queryId }
      }
      // Emitted after streamText.onFinish has run, so finishReason is set.
      if (part.type === 'finish' && finishReason === 'length') {
        return { truncated: true }
      }
    },
    onFinish: async ({ messages: finalMessages }) => {
      try {
        await replaceConversationMessages({
          conversationId: finalConversationId,
          messages: finalMessages,
        })
        if (isFirstTurn) {
          generateConversationTitle(finalMessages).then(title => {
            if (title) void updateConversationTitle(finalConversationId, title)
          })
        }
      } catch (err) {
        console.error('[consume] persistence failed', err)
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
    },
    onError: error => {
      if (error instanceof Error) return error.message
      return 'Something went wrong while generating a response.'
    },
  })
}

async function generateConversationTitle(
  messages: UIMessage[],
  monCtx?: { queryId?: string; conversationId?: string | null; userId?: string },
): Promise<string | null> {
  const firstUser = messages.find(m => m.role === 'user')
  if (!firstUser) return null
  const text = firstUser.parts
    .filter(p => p.type === 'text')
    .map(p => (p as { text: string }).text)
    .join(' ')
    .trim()
  if (!text) return null

  const start = Date.now()
  let usage: { inputTokens?: number; outputTokens?: number } | undefined
  let errorCode: string | null = null
  try {
    // Pinned to the cheapest fast model regardless of the user's picked chat
    // model — titles are short and latency-sensitive.
    const result = await generateText({
      model: resolveModel(TITLE_MODEL_ID),
      system:
        'Summarize the user question as a concise 3-6 word chat title. No quotes, no trailing punctuation, Title Case.',
      prompt: text.slice(0, 500),
      maxOutputTokens: 40,
    })
    usage = result.usage
    const cleaned = result.text.replace(/^["']|["']$/g, '').trim().slice(0, 80)
    return cleaned || fallbackTitle(text)
  } catch (err) {
    errorCode = err instanceof Error ? err.message : String(err)
    return fallbackTitle(text)
  } finally {
    if (monCtx?.queryId) {
      const latency_ms = Date.now() - start
      void writeLlmCallLog({
        query_id: monCtx.queryId,
        conversation_id: monCtx.conversationId ?? null,
        call_stage: 'title',
        model_id: TITLE_MODEL_ID,
        provider: resolveProvider(TITLE_MODEL_ID),
        input_tokens: usage?.inputTokens ?? null,
        output_tokens: usage?.outputTokens ?? null,
        reasoning_tokens: null,
        latency_ms,
        cost_usd: computeCostUsd(getModelPricingSync(TITLE_MODEL_ID), {
          input_tokens: usage?.inputTokens ?? null,
          output_tokens: usage?.outputTokens ?? null,
        }),
        fallback_used: false,
        error_code: errorCode,
        payload: null,
      })
      // OBS-S1: Observatory per-call telemetry (title stage)
      {
        const obsStartedAt = new Date(start)
        const obsFinishedAt = new Date(start + latency_ms)
        const obsUsage: TokenUsage = {
          input_tokens: usage?.inputTokens ?? 0,
          output_tokens: usage?.outputTokens ?? 0,
          cache_read_tokens: 0,
          cache_write_tokens: 0,
          reasoning_tokens: 0,
        }
        const obsProvider = (resolveProvider(TITLE_MODEL_ID) ?? 'unknown') as ProviderName
        const obsDb = getStorageClient()
        void (async () => {
          const costResult = await computeCost(obsProvider, TITLE_MODEL_ID, obsUsage, obsStartedAt, obsDb).catch(() => null)
          await persistObservation(
            {
              provider: obsProvider,
              model: TITLE_MODEL_ID,
              prompt_text: null,
              system_prompt: null,
              parameters: { model: TITLE_MODEL_ID },
              conversation_id: monCtx.conversationId ?? monCtx.queryId ?? 'unknown',
              conversation_name: null,
              prompt_id: `${monCtx.queryId}:title`,
              user_id: monCtx.userId ?? 'native',
              pipeline_stage: 'title',
            },
            {
              response_text: null,
              usage: obsUsage,
              status: errorCode ? 'error' : 'success',
              error_code: errorCode ?? undefined,
              started_at: obsStartedAt,
              finished_at: obsFinishedAt,
            },
            costResult,
            obsDb,
          )
        })()
      }
    }
  }
}

function fallbackTitle(text: string): string {
  const firstLine = text.split('\n')[0].trim()
  if (firstLine.length <= 60) return firstLine
  const slice = firstLine.slice(0, 60)
  const lastSpace = slice.lastIndexOf(' ')
  return (lastSpace > 20 ? slice.slice(0, lastSpace) : slice) + '…'
}

function extractText(parts: Array<{ type: string; text?: string }>): string {
  return parts.filter(p => p.type === 'text').map(p => p.text ?? '').join(' ').trim()
}
