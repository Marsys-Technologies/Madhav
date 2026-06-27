/**
 * D2 Query Router — Main Entry Point
 * =====================================
 * Implements route(): the top-level function the grounding spine (D3) calls
 * to classify a query and select a tool chain.
 *
 * Architecture (D2 brief §0):
 *   "route, don't choose" — classifies query into one of five route classes,
 *   selects the cheapest correct tool path, biases toward ERROR over fabrication.
 *
 * Routing pipeline:
 *   1. Rule-driven classifier (deterministic, auditable)
 *   2. If confidence=low AND model fallback enabled → optional LLM re-classification
 *   3. Tool selector (inspects registry descriptors)
 *   4. Budget + termination policy assembly
 *   5. Trajectory logging
 *
 * CHART-AGNOSTIC GUARANTEE:
 * - chart_id is a REQUIRED parameter; route() errors if absent
 * - No default chart UUID is ever injected at any point in the pipeline
 * - Per principle #14 of the RETRIEVAL_SYSTEM_DESIGN_APPROACH
 */

import { classifyQuery, isModelFallbackEligible } from './classifier'
import { selectTools, buildTerminationPolicy, getBudget } from './tool_selector'
import type {
  RouteResult,
  RouteTrajectory,
  RoutingHints,
  ClassifierResult,
  RouteClass,
} from './types'

// ── Route function ─────────────────────────────────────────────────────────────

export interface RouteInput {
  /** The natural-language query to route */
  query: string

  /**
   * Chart UUID — REQUIRED, never defaulted.
   * If omitted, route() throws immediately.
   */
  chart_id: string

  /** Optional caller-supplied routing hints */
  hints?: RoutingHints

  /**
   * Whether to allow model-classifier fallback for low-confidence rule results.
   * Default: false (rule-only mode; safe for all production paths).
   * Set true only when the caller has a model available and wants richer routing.
   */
  allow_model_fallback?: boolean

  /**
   * Optional model fallback function — called when allow_model_fallback=true
   * and the rule classifier returns low confidence.
   * Must return a ClassifierResult.
   * Injected by D3/D7 so the router itself has no model dependency.
   */
  model_classifier?: (query: string) => Promise<ClassifierResult>
}

/**
 * Route a query to the appropriate tool chain.
 *
 * @throws {Error} if chart_id is missing or empty
 * @returns RouteResult with planned tool calls, budget, and trajectory
 */
export async function route(input: RouteInput): Promise<RouteResult> {
  const startMs = Date.now()

  const {
    query,
    chart_id,
    hints = {},
    allow_model_fallback = false,
    model_classifier,
  } = input

  // ── CHART-AGNOSTIC GATE ────────────────────────────────────────────────────
  if (!chart_id || chart_id.trim() === '') {
    throw new Error(
      '[D2-router] chart_id is required and must not be empty. ' +
      'The router never injects a default chart UUID.'
    )
  }

  const lel_enabled = hints.lel_enabled ?? false
  const budget_usd = hints.budget_usd

  // ── STEP 1: Classify the query ─────────────────────────────────────────────

  let classifierResult: ClassifierResult
  let routing_method: RouteTrajectory['routing_method']

  if (hints.force_route_class) {
    // Forced override — skip classifier entirely
    classifierResult = {
      route_class: hints.force_route_class,
      traversal_level: hints.preferred_traversal_level ?? 'L-ORIENT',
      rule_fired: 'FORCED_by_caller',
      confidence: 'high',
    }
    routing_method = 'forced'
  } else {
    // Rule-driven classification
    classifierResult = classifyQuery(query)
    routing_method = 'rule'

    // Override traversal level if hinted
    if (hints.preferred_traversal_level) {
      classifierResult = {
        ...classifierResult,
        traversal_level: hints.preferred_traversal_level,
      }
    }

    // ── STEP 1b: Optional model fallback for low-confidence results ───────────
    if (
      allow_model_fallback &&
      model_classifier &&
      isModelFallbackEligible(classifierResult)
    ) {
      try {
        const modelResult = await model_classifier(query)
        classifierResult = modelResult
        routing_method = 'model_fallback'
      } catch {
        // Model fallback failed — keep rule result (fail-safe, not fail-open)
        // routing_method stays 'rule'
      }
    }
  }

  const { route_class, traversal_level, rule_fired } = classifierResult

  // ── STEP 2: Select tools from registry ────────────────────────────────────

  const { planned_calls, budget, umbrella_then_drill } = selectTools({
    route_class,
    traversal_level,
    chart_id,
    lel_enabled,
    already_loaded: hints.already_loaded,
    budget_usd,
  })

  // ── STEP 3: Derive archetype + role metadata from selected tools ────────────
  // Look up capabilities from the registry to extract their D1 metadata.

  const { listCapabilities } = await import('../registry')
  const allCaps = listCapabilities()
  const capMap = new Map(allCaps.map((c) => [c.uri, c]))

  const resolvedArchetypes = [
    ...new Set(
      planned_calls
        .map((pc) => capMap.get(pc.uri)?.archetype)
        .filter((a): a is NonNullable<typeof a> => a !== undefined)
    ),
  ]
  const resolvedRoles = [
    ...new Set(
      planned_calls
        .map((pc) => capMap.get(pc.uri)?.tool_role)
        .filter((r): r is NonNullable<typeof r> => r !== undefined)
    ),
  ]

  // ── STEP 4: Build termination policy for multi_hop ─────────────────────────

  const termination_policy =
    route_class === 'multi_hop'
      ? buildTerminationPolicy(budget)
      : undefined

  // ── STEP 5: Build trajectory record ───────────────────────────────────────

  const routing_latency_ms = Date.now() - startMs

  const trajectory: RouteTrajectory = {
    chart_id,  // Opaque UUID — no native data
    route_class,
    routing_method,
    rule_fired,
    traversal_level,
    planned_tool_uris: planned_calls.map((pc) => pc.uri),
    routed_at: new Date().toISOString(),
    budget_usd: budget.max_usd,
    lel_enabled,
    routing_latency_ms,
  }

  // ── STEP 6: Assemble RouteResult ───────────────────────────────────────────

  return {
    route_class,
    traversal_level,
    target_archetypes: resolvedArchetypes as RouteResult['target_archetypes'],
    target_roles: resolvedRoles as RouteResult['target_roles'],
    planned_calls,
    primary_tool: planned_calls[0]?.uri ?? null,
    umbrella_then_drill,
    budget,
    termination_policy,
    trajectory,
  }
}

// ── Convenience: route + immediately execute the first call ──────────────────

/**
 * Route a query and execute the primary tool call.
 * Returns both the RouteResult and the primary tool's result.
 *
 * For simple/single-shot queries — avoids the caller having to assemble args.
 * For multi_hop/relational — use route() directly and pass to the agentic loop.
 */
export async function routeAndExecutePrimary(
  input: RouteInput
): Promise<{
  route: RouteResult
  result: unknown
  is_error: boolean
}> {
  const routeResult = await route(input)

  if (!routeResult.primary_tool || routeResult.planned_calls.length === 0) {
    return {
      route: routeResult,
      result: null,
      is_error: false,
    }
  }

  const { listCapabilities } = await import('../registry')
  const allCaps = listCapabilities()
  const capMap = new Map(allCaps.map((c) => [c.uri, c]))

  const primaryCall = routeResult.planned_calls[0]
  const cap = capMap.get(primaryCall.uri)

  if (!cap) {
    return {
      route: routeResult,
      result: { error: `Tool not found: ${primaryCall.uri}` },
      is_error: true,
    }
  }

  try {
    const toolResult = await cap.handler(primaryCall.args ?? {}, {
      chart_id: input.chart_id,
    })
    return {
      route: routeResult,
      result: toolResult.content,
      is_error: toolResult.is_error ?? false,
    }
  } catch (err) {
    return {
      route: routeResult,
      result: { error: String(err) },
      is_error: true,
    }
  }
}
