/**
 * Paripraśna pipeline — PLAN STAGE (P0-C / RF-1).
 *
 * Ports: `ScopeTuple | ClarificationRequest → AcharyaPlan`.
 *
 * Everything from "what did the user actually ask" to "here is the authorized,
 * budgeted, floor-composed, leak-filtered plan the tool broker will run":
 *   · query text + planner history extraction
 *   · manifest load and the concurrent chart-orientation front door
 *   · the planner call, with its three outcomes (plan / clarification / fault)
 *   · plan enrichment (ids, fingerprint, deep-dive dasha floor)
 *   · budget arbitration + compiled-floor composition + B.11 / dasha floors
 *   · NO-LEAKAGE enforcement (doctrine F-R7) — the REAL filter, surfaced as a
 *     wire `flag` carrying a COUNT ONLY (gate 11: never the stripped ids)
 *   · the legacy-shaped `queryPlan` object the registry bridge + tools read
 *
 * `orientationPromise` is deliberately returned UNAWAITED: it is kicked off
 * before the planner so the two run concurrently, exactly as before, and the
 * evidence stage awaits it after retrieval.
 */

import type { UIMessage } from 'ai'

import { callPipelinePlanner as runPlanner } from '@/lib/pipeline/pipeline_planner'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { arbitrateBudgets } from '@/lib/pipeline/budget_arbiter'
import {
  compileFloorForPlan,
  ensureB11WholeChartReadFloor,
  ensureDashaContextFloor,
} from '@/lib/pipeline/compiled_floor_adapter'
import { filterLeakedCapabilities } from '@/lib/pipeline/no_leakage_filter'
import { buildChartOrientation, type ChartOrientation } from '@/lib/retrieval/orientation'
import { loadManifest } from '@/lib/bundle/manifest_reader'
import { getEffectiveModel } from '@/lib/models/runtime_config'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

import { halt, proceed, type StageResult, type TurnIdentity, type TurnParams } from './stage_context'

/** The legacy-shaped plan object the registry bridge + retrieval tools read. */
export interface LegacyQueryPlan {
  query_plan_id: string
  query_text: string
  chart_id: string
  query_class: PipelinePlan['query_class']
  domains: string[]
  forward_looking: boolean
  tools_authorized: string[]
  history_mode: NonNullable<PipelinePlan['history_mode']>
  panel_mode: boolean
  expected_output_shape: NonNullable<PipelinePlan['expected_output_shape']>
  manifest_fingerprint: string
  schema_version: '1.0'
  planets: PipelinePlan['planets']
  houses: PipelinePlan['houses']
  dasha_context_required: PipelinePlan['dasha_context_required']
  graph_seed_hints: PipelinePlan['graph_seed_hints']
  vector_search_filter: PipelinePlan['vector_search_filter']
  time_window: PipelinePlan['time_window']
  tool_calls: PipelinePlan['tool_calls']
}

export interface PlanStageOutput {
  plan: PipelinePlan
  queryPlan: LegacyQueryPlan
  manifest: Awaited<ReturnType<typeof loadManifest>>
  orientationPromise: Promise<ChartOrientation | null>
  queryText: string
  lastUserMessage: UIMessage | undefined
  toolsAuthorized: string[]
  plannerModelId: string
  plannerLatencyMs: number
  /** Mutable across later stages, exactly as the single-closure route had it. */
  judgmentFlags: string[]
}

export async function runPlanStage(args: {
  em: PariprashnaEmitter
  request: Request
  messages: UIMessage[]
  identity: TurnIdentity
  params: TurnParams
}): Promise<StageResult<PlanStageOutput>> {
  const { em, request, messages, identity, params } = args
  const { chartId, queryId } = identity

  // ── Query text + planner context. ──────────────────────────────────────────
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
    getEffectiveModel(params.selectedStack, 'planner_fast', 'primary', request),
    getEffectiveModel(params.selectedStack, 'planner_fast', 'fallback', request),
  ])

  // ── Planner. Faults → in-stream `error` event (never HTTP 4xx/5xx). ────────
  // The planner emits trace steps; a no-op trace sink keeps it decoupled from
  // the Paripraśna wire (trace observability is a separate surface).
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
    return halt('ok')
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
    return halt('error')
  }

  const plan: PipelinePlan = plannerOutcome.plan
  const plannerLatencyMs = Date.now() - plannerStartedAt
  plan.query_plan_id = queryId
  plan.query_text = queryText
  plan.manifest_fingerprint = manifest.fingerprint
  plan.schema_version = '2.0'
  plan.planning_model_id = plannerModelId
  plan.planning_latency_ms = plannerLatencyMs
  // deep_dive → force the dasha-context floor so the completeness path has the
  // full Vimshottari sequence for maximal coverage.
  if (params.deepDive) plan.dasha_context_required = true

  em.phase({ phase: 'plan', status: 'end', ms: plannerLatencyMs })
  em.grade({ subject: 'query_class', grade: String(plan.query_class), detail: `${plan.tool_calls.length} planned tools` })

  // ── Budget arbitration + floor composition (identical to consult). ─────────
  const arbitrated = arbitrateBudgets(
    plan.tool_calls.map((tc) => ({ tool_name: tc.tool_name, priority: tc.priority, token_budget: tc.token_budget })),
    {
      synthesis_model_max_context: params.modelMeta.maxInputTokens ?? 128_000,
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
    // Raw capability names are server-log-only (gate 11 [integrity]) — the wire
    // flag reports only a count, never the stripped identifiers.
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

  // Legacy-shaped plan object the registry bridge + tools read (chart_id is the
  // CR-118 fast-fail fix — every per_chart tool scopes off this).
  const queryPlan: LegacyQueryPlan = {
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

  return proceed({
    plan,
    queryPlan,
    manifest,
    orientationPromise,
    queryText,
    lastUserMessage,
    toolsAuthorized,
    plannerModelId,
    plannerLatencyMs,
    judgmentFlags,
  })
}
