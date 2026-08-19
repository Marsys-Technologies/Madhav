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
import type { SafetyDecision } from '@/lib/pariprashna/safety'
import { isInjectionContainmentEnabled } from '@/lib/pariprashna/injection/flag'
import { isHonestControlsEnabled } from '@/lib/pariprashna/honest_controls/flag'

import { halt, proceed, type StageResult, type TurnIdentity, type TurnParams } from './stage_context'

/**
 * Lane P2-C (PPR-09/16) — honest depth disclosure. Maps the CLASSIFIER's own
 * `scope_tuple.depth` ('shallow' | 'standard' | 'deep', from
 * `@/lib/vidhi/scope_classifier`) to the reader-facing label emitted as the
 * `reading_depth_received` grade. Mirrors `compiled_floor_adapter.ts`'s
 * private `DEPTH_MAP` (shallow→retrieval, standard→structure, deep→deepdive)
 * one-for-one by design — that module's map is not exported and this lane's
 * `may_touch` does not include `lib/pipeline/**`, so this is a second,
 * intentionally-identical mapping rather than a shared import. If the
 * classifier's depth enum changes, both sites need updating; a mismatch here
 * would show the reader the wrong depth, which is exactly the defect this
 * lane exists to remove, so keep this in lockstep with `DEPTH_MAP`.
 */
const READING_DEPTH_RECEIVED_LABEL: Readonly<Record<'shallow' | 'standard' | 'deep', string>> = {
  shallow: 'quick',
  standard: 'standard',
  deep: 'deep_dive',
}

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
  /**
   * The safety decision AFTER the plan-time pass (lane G1-A). May carry a
   * STRONGER action than the pre-plan decision — a plan that reveals a health
   * or longevity domain the question's wording hid escalates the turn. Never
   * weaker: `reclassifyAfterPlan` is a monotone join.
   */
  safetyDecision: SafetyDecision
  /**
   * Capabilities this stage DELIBERATELY removed from the plan — NO-LEAKAGE
   * strips plus HS-1/HS-4 mortality exclusions (lane G1-G).
   *
   * Carried forward rather than discarded because "a capability that was
   * considered and then taken away is later asked for anyway" is the single
   * highest-signal tool-sequence anomaly there is, and the monitor in the
   * synthesis stage cannot reconstruct this set on its own.
   */
  removedCapabilities: string[]
}

export async function runPlanStage(args: {
  em: PariprashnaEmitter
  request: Request
  messages: UIMessage[]
  identity: TurnIdentity
  params: TurnParams
  safetyDecision: SafetyDecision
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

  // ── INJECTION CONTAINMENT: the planner's own inputs (lane G1-G · PPR-13). ──
  // TA §14A.1 names this surface first and by line number: "`queryText` flows
  // raw into `runPlanner`; prior turns raw into `plannerHistory`". The planner
  // is the FIRST model to read the reader's text and the one whose output grants
  // capability, so it is the first place the question stops being an instruction
  // and starts being data.
  //
  // The wrap is applied to what the planner reads, NOT to `queryText` itself —
  // `plan.query_text`, the synthesis call, persistence and the safety classifier
  // all consume the plain text and must keep seeing exactly it.
  //
  // Flag-OFF (default): `containedQueryText === queryText` and
  // `containedHistory === plannerHistory`, by identity, so the planner call is
  // byte-for-byte today's.
  const injectionContained = isInjectionContainmentEnabled()
  let containedQueryText = queryText
  let containedHistory = plannerHistory
  if (injectionContained) {
    const { containUserQuestion, containPriorTurn } = await import('@/lib/pariprashna/injection')
    containedQueryText = containUserQuestion(queryText)
    containedHistory = plannerHistory.map((m) => ({
      role: m.role,
      content: containPriorTurn(m.content, m.role),
    }))
  }

  // ── Planner. Faults → in-stream `error` event (never HTTP 4xx/5xx). ────────
  // The planner emits trace steps; a no-op trace sink keeps it decoupled from
  // the Paripraśna wire (trace observability is a separate surface).
  const plannerStartedAt = Date.now()
  const plannerOutcome = await runPlanner(
    containedQueryText,
    containedHistory,
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

  // ── HONEST DEPTH DISCLOSURE (lane P2-C · PPR-09/16). ────────────────────────
  // What the reader is TOLD they got should be what the planner's own
  // `scope_tuple` actually resolved to, not the composer's pre-planning guess
  // (§N.7 item 6: an honest null beats an invented judgment). Derived, never
  // re-stated: this reads `plan.scope_tuple.depth` directly rather than
  // recomputing a depth signal, so it cannot drift from what actually drove
  // the B.11/floor composition a few lines below. Omitted entirely — no grade
  // emitted — when the planner produced no scope_tuple, which is the honest
  // behavior (no invented depth for a turn the classifier didn't score).
  if (isHonestControlsEnabled() && plan.scope_tuple) {
    const receivedLabel = READING_DEPTH_RECEIVED_LABEL[plan.scope_tuple.depth]
    em.grade({
      subject: 'reading_depth_received',
      grade: receivedLabel,
      detail: `scope_tuple: intent=${plan.scope_tuple.intent} width=${plan.scope_tuple.width} depth=${plan.scope_tuple.depth}`,
    })
  }

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
  const removedCapabilities: string[] = []
  const noLeakageFiltered = filterLeakedCapabilities(toolsAuthorized)
  if (noLeakageFiltered.length !== toolsAuthorized.length) {
    const stripped = toolsAuthorized.filter((t) => !noLeakageFiltered.includes(t))
    removedCapabilities.push(...stripped)
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

  // ── SAFETY: plan-time enforcement (lane G1-A · HS-1 point (a) · PPR-12). ───
  // Two acts, in this order and not the other:
  //   1. RE-CLASSIFY against the produced plan. The pre-plan pass could only
  //      read the question; the plan is where a longevity or health domain the
  //      wording hid becomes visible. The merge is monotone — the decision can
  //      only get stronger.
  //   2. EXCLUDE the mortality capabilities the (possibly escalated) decision
  //      names, AFTER the floors have run, so a floor cannot smuggle one back
  //      in. "The query never gets a capability that could compute a specific
  //      death date" is a statement about what the tool broker receives, and
  //      the tool broker receives what is left after this line.
  let safetyDecision = args.safetyDecision
  if (safetyDecision.enforced) {
    const { reclassifyAfterPlan, applyCapabilityExclusion } = await import('@/lib/pariprashna/safety')
    safetyDecision = await reclassifyAfterPlan({
      decision: safetyDecision,
      queryText,
      domains: plan.domains ?? [],
      capabilities: toolsAuthorized,
    })
    const { kept, stripped } = applyCapabilityExclusion(toolsAuthorized, safetyDecision.excluded_capabilities)
    if (stripped.length > 0) {
      // Raw capability names are server-log-only (gate 11 [integrity]); the wire
      // flag carries a count and the REASON, never the identifiers.
      console.warn('[pariprashna/safety] HS-1/HS-4 stripped mortality capabilities:', stripped)
      removedCapabilities.push(...stripped)
      judgmentFlags.push('safety_mortality_capabilities_excluded')
      em.flag({
        code: 'safety_mortality_capabilities_excluded',
        level: 'warn',
        detail: `${stripped.length} longevity capabilit${stripped.length === 1 ? 'y' : 'ies'} excluded (no individualized mortality window)`,
      })
      plan.tool_calls = plan.tool_calls.filter((tc) => kept.includes(tc.tool_name))
      toolsAuthorized.splice(0, toolsAuthorized.length, ...kept)
    }
  }

  // ── INJECTION CONTAINMENT: plan closure (lane G1-G · PPR-13). ─────────────
  // LAST, after every floor and every exclusion, for the same reason the safety
  // capability exclusion runs last: what matters is what the TOOL BROKER
  // receives, and the tool broker receives what is left after this line.
  //
  // Closes the plan's two open surfaces (see `injection/plan_closure.ts` for
  // why the schema itself is NOT switched to `.strict()`): a planner-supplied
  // identity param naming any chart other than the authenticated one is
  // REJECTED from the tool call, and an unregistered tool name is FLAGGED.
  if (injectionContained) {
    const { closePlanAgainstInjection } = await import('@/lib/pariprashna/injection')
    const { getToolByName } = await import('@/lib/retrieval/registry/tool_name_bridge')
    const closure = closePlanAgainstInjection({
      plan,
      authenticatedChartId: chartId,
      isRegisteredTool: (name) => getToolByName(name) !== undefined,
    })
    if (closure.rejected_param_count > 0) {
      // Loud on the server WITH the key names; the wire gets a count only
      // (gate 11 [integrity]) — a rejected `chart_id` value is precisely the
      // identifier this lane exists to keep off the wire.
      console.error(
        '[pariprashna/injection] plan closure REJECTED identity params from tool calls:',
        closure.findings.filter((f) => f.code === 'plan_identity_param_rejected'),
      )
      judgmentFlags.push('injection_plan_identity_param_rejected')
      em.flag({
        code: 'injection_plan_identity_param_rejected',
        level: 'error',
        detail: `${closure.rejected_param_count} planner-supplied identity parameter(s) rejected (identity comes from the authenticated call)`,
      })
    }
    if (closure.depth_exceeded_count > 0) {
      // A DIFFERENT fact from the line above: nothing was found in these
      // subtrees, they were never inspected. They are removed rather than
      // allowed (fail closed), and reported as what they are rather than
      // folded into the identity-rejection count (§N.8).
      console.warn(
        '[pariprashna/injection] plan closure removed param subtrees past the depth cap:',
        closure.findings.filter((f) => f.code === 'plan_param_depth_exceeded'),
      )
      judgmentFlags.push('injection_plan_param_depth_exceeded')
      em.flag({
        code: 'injection_plan_param_depth_exceeded',
        level: 'warn',
        detail: `${closure.depth_exceeded_count} tool parameter subtree(s) removed unexamined for nesting past the inspection depth cap`,
      })
    }
    if (closure.flagged_tool_count > 0) {
      console.warn(
        '[pariprashna/injection] plan closure flagged unregistered tool names:',
        closure.findings.filter((f) => f.code === 'plan_unregistered_tool_flagged'),
      )
      judgmentFlags.push('injection_plan_unregistered_tool')
      em.flag({
        code: 'injection_plan_unregistered_tool',
        level: 'warn',
        detail: `${closure.flagged_tool_count} planned tool name(s) resolve to no registered capability`,
      })
    }
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
    safetyDecision,
    removedCapabilities,
  })
}
