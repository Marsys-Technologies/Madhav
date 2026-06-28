/**
 * D2 Query Router — Tool Selector
 * =================================
 * Given a route class + traversal level, selects the appropriate tool(s)
 * from the registry by inspecting capability descriptors
 * (archetype, tool_role, traversal_level fields — frozen D1 contract).
 *
 * Selection policy:
 * - simple / L-ORIENT    → umbrella tool with traversal_level='L-ORIENT'
 * - numeric_exact        → leaf tools with traversal_level matching signal level
 * - relational           → graph tools (tool_role='graph')
 * - narrative            → hybrid_retrieval tools (tool_role='hybrid_retrieval')
 * - multi_hop            → orientation umbrella as bootstrap; loop extends from there
 *
 * GATE A: This file does NOT import from registry/index.ts or registry/types.ts
 * in a way that would modify the registry. It READS the registry via the
 * exported query functions. Gate A is honoured.
 */

import { listCapabilities } from '../registry'
import type {
  CapabilityDescriptor,
  CapabilityUri,
  TraversalLevel,
  ToolRole,
} from '../registry/types'
import type { RouteClass, PlannedToolCall, RouteBudget } from './types'

// ── Budget table ──────────────────────────────────────────────────────────────

/**
 * Per-route-class default budgets.
 * Callers can override via RoutingHints.budget_usd.
 */
const ROUTE_BUDGETS: Record<RouteClass, RouteBudget> = {
  simple: {
    max_usd: 0.005,
    soft_iteration_limit: 1,
    latency_class: 'fast',
  },
  numeric_exact: {
    max_usd: 0.01,
    soft_iteration_limit: 2,
    latency_class: 'fast',
  },
  relational: {
    max_usd: 0.05,
    soft_iteration_limit: 3,
    latency_class: 'medium',
  },
  narrative: {
    max_usd: 0.05,
    soft_iteration_limit: 2,
    latency_class: 'medium',
  },
  multi_hop: {
    max_usd: 0.50,
    soft_iteration_limit: 12,
    latency_class: 'slow',
  },
}

// ── Per-route tool role preferences ──────────────────────────────────────────

const ROUTE_PREFERRED_ROLES: Record<RouteClass, ToolRole[]> = {
  simple: ['umbrella', 'drill'],
  numeric_exact: ['leaf'],
  relational: ['graph'],
  narrative: ['hybrid_retrieval'],
  multi_hop: ['umbrella', 'drill', 'leaf', 'graph'],
}

// ── Traversal level priority order ───────────────────────────────────────────
// When searching for tools at a given traversal level, also accept the next
// level up if nothing is found at the exact level.

const TRAVERSAL_FALLBACKS: Record<TraversalLevel, TraversalLevel[]> = {
  'L-ORIENT':   ['L-ORIENT', 'L-OVERVIEW'],
  'L-OVERVIEW': ['L-OVERVIEW', 'L-ORIENT'],
  'L-DOMAIN':   ['L-DOMAIN', 'L-OVERVIEW'],
  'L-SIGNAL':   ['L-SIGNAL', 'L-DOMAIN'],
  'L-SOURCE':   ['L-SOURCE'],
  'L-SYNTH':    ['L-SYNTH'],
}

// ── Selection algorithm ───────────────────────────────────────────────────────

/**
 * Select tools from the registry for a given route classification.
 *
 * @param route_class    - The classified route class
 * @param traversal_level - The classified traversal level
 * @param chart_id       - The explicit chart UUID (REQUIRED; never defaulted here)
 * @param lel_enabled    - Whether LEL signals are enabled
 * @param already_loaded - Tool URIs already in context (skip for simple routes)
 * @param budget_usd     - Optional budget override
 *
 * @returns PlannedToolCall[] ordered by priority; may be empty if no tools registered yet
 */
export function selectTools(options: {
  route_class: RouteClass
  traversal_level: TraversalLevel
  chart_id: string
  lel_enabled: boolean
  already_loaded?: CapabilityUri[]
  budget_usd?: number
}): {
  planned_calls: PlannedToolCall[]
  budget: RouteBudget
  umbrella_then_drill: boolean
} {
  const {
    route_class,
    traversal_level,
    chart_id,
    lel_enabled,
    already_loaded = [],
    budget_usd,
  } = options

  const budget: RouteBudget = {
    ...ROUTE_BUDGETS[route_class],
    ...(budget_usd !== undefined ? { max_usd: budget_usd } : {}),
  }

  const preferredRoles = ROUTE_PREFERRED_ROLES[route_class]
  const levelCandidates = TRAVERSAL_FALLBACKS[traversal_level]

  // Get all registered capabilities
  const allCaps = listCapabilities()

  // Filter to per_chart capabilities (all chart queries need chart_id)
  // plus global caps for narrative routes (classical text corpora are global)
  const scopeFilter = route_class === 'narrative'
    ? allCaps
    : allCaps.filter((c) => c.scope === 'per_chart')

  // Select by preferred roles first, then widen if nothing found
  let selected: CapabilityDescriptor[] = []

  // Try preferred roles at the target traversal level(s)
  for (const level of levelCandidates) {
    selected = scopeFilter.filter(
      (c) =>
        preferredRoles.includes(c.tool_role) &&
        c.traversal_level === level
    )
    if (selected.length > 0) break
  }

  // Widen: if still empty, pick any capability at the traversal level
  if (selected.length === 0) {
    for (const level of levelCandidates) {
      selected = allCaps.filter((c) => c.traversal_level === level)
      if (selected.length > 0) break
    }
  }

  // For simple routes: skip already-loaded tools (they're in context)
  if (route_class === 'simple') {
    const filtered = selected.filter((c) => !already_loaded.includes(c.uri))
    if (filtered.length > 0) selected = filtered
    // If all are already loaded, return empty (caller knows they're in context)
    else return { planned_calls: [], budget, umbrella_then_drill: false }
  }

  // Sort: umbrella/drill first, then by emits_references (reference tools preferred)
  selected.sort((a, b) => {
    const roleOrder = (r: ToolRole) =>
      r === 'umbrella' ? 0 : r === 'drill' ? 1 : r === 'leaf' ? 2 : 3
    const ra = roleOrder(a.tool_role)
    const rb = roleOrder(b.tool_role)
    if (ra !== rb) return ra - rb
    // Prefer reference-emitting tools
    if (a.emits_references && !b.emits_references) return -1
    if (!a.emits_references && b.emits_references) return 1
    return 0
  })

  // Build planned calls
  const planned_calls: PlannedToolCall[] = selected.map((cap, idx) => {
    const args: Record<string, unknown> = {}

    // Inject chart_id for per_chart capabilities
    if (cap.scope === 'per_chart') {
      args['chart_id'] = chart_id
    }

    // Inject lel_enabled when the capability supports LEL
    if (cap.lel_capable) {
      args['lel_enabled'] = lel_enabled
    }

    // Umbrella tools get a concise response format
    if (cap.tool_role === 'umbrella') {
      args['response_format'] = 'concise'
    }

    const rationale = buildRationale(cap, route_class, idx)

    return {
      uri: cap.uri,
      rationale,
      mandatory: idx === 0,  // First call is mandatory; drills are opportunistic
      args,
    }
  })

  // Determine if umbrella-then-drill pattern applies
  const umbrella_then_drill =
    planned_calls.length > 0 &&
    (route_class === 'simple' || route_class === 'multi_hop') &&
    selected[0]?.tool_role === 'umbrella'

  return { planned_calls, budget, umbrella_then_drill }
}

// ── Rationale builder ─────────────────────────────────────────────────────────

function buildRationale(
  cap: CapabilityDescriptor,
  route_class: RouteClass,
  position: number
): string {
  if (position === 0) {
    return `Primary tool for ${route_class} route: ${cap.tool_role} at ${cap.traversal_level} (archetype: ${cap.archetype})`
  }
  return `Supporting ${cap.tool_role} at ${cap.traversal_level} (archetype: ${cap.archetype})`
}

// ── Budget accessor ───────────────────────────────────────────────────────────

/**
 * Get the default budget for a route class without running tool selection.
 * Used by tests and the agentic loop when setting up termination policy.
 */
export function getBudget(route_class: RouteClass, budget_override?: number): RouteBudget {
  return {
    ...ROUTE_BUDGETS[route_class],
    ...(budget_override !== undefined ? { max_usd: budget_override } : {}),
  }
}

// ── Termination policy factory ────────────────────────────────────────────────

/**
 * Build a value-based termination policy for multi_hop routes.
 * Per D2 brief §2: "stop when marginal retrieved value drops, not a hard count."
 */
export function buildTerminationPolicy(budget: RouteBudget): {
  strategy: 'value_based'
  marginal_value_threshold: number
  soft_iteration_limit: number
} {
  return {
    strategy: 'value_based',
    marginal_value_threshold: 0.15,  // Stop when next call adds <15% marginal value
    soft_iteration_limit: budget.soft_iteration_limit,
  }
}
