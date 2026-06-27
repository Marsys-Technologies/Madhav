/**
 * D2 Query Router — Types
 * ========================
 * Defines RouteResult, RouteClass, and all supporting types
 * for the MARSYS retrieval router.
 *
 * Design principles (per D2 brief + RETRIEVAL_SYSTEM_DESIGN_APPROACH):
 * - Five route classes: numeric_exact | relational | narrative | simple | multi_hop
 * - Each class maps to a traversal level and target tool pattern
 * - chart_id is ALWAYS explicit; the router NEVER injects a default
 * - Rule-driven core; model fallback only for genuinely ambiguous queries
 * - Trajectory logged for D8 eval harness
 * - No native identifiers in any field or comment
 */

import type {
  CapabilityUri,
  TraversalLevel,
  RetrievalArchetype,
  ToolRole,
} from '../registry/types'

// ── Route classes (D2 brief §0 / §1) ─────────────────────────────────────────

/**
 * The five route classes the router classifies into.
 *
 * numeric_exact  — Requires a deterministic exact lookup (grounding spine, D3).
 *                  Examples: "what is the longitude of a planet?", "strength of a lord"
 *
 * relational     — Cross-everything / contradictions / graph paths (graph tool, D4).
 *                  Examples: "contradictions between two domains", "CGM subgraph paths"
 *
 * narrative      — Hybrid vector retrieval over prose corpora (BM25+dense+rerank).
 *                  Examples: "what does Brihat Parashara say about…", classical citations
 *
 * simple         — Cheap single-shot: one umbrella tool call is sufficient.
 *                  Examples: "give me the chart orientation", "what are the top signals?"
 *
 * multi_hop      — Requires agentic loop; cannot be answered by a single call.
 *                  Examples: "compare career and health domains, resolve contradictions"
 */
export type RouteClass =
  | 'numeric_exact'
  | 'relational'
  | 'narrative'
  | 'simple'
  | 'multi_hop'

// ── Routing hints (caller-supplied) ──────────────────────────────────────────

/**
 * Optional hints the grounding spine (D3) or caller can supply
 * to bias routing without overriding the rule-driven core.
 */
export interface RoutingHints {
  /**
   * Explicit preferred route class — skips classifier when set.
   * Use only when the caller has strong domain knowledge (e.g. D3 dispatching).
   */
  force_route_class?: RouteClass

  /**
   * Preferred traversal level — overrides the classifier's level inference when set.
   */
  preferred_traversal_level?: TraversalLevel

  /**
   * Set of tool URIs the caller considers already loaded / cached.
   * Router avoids re-calling them for simple/single-shot routes.
   */
  already_loaded?: CapabilityUri[]

  /**
   * Budget ceiling for this query in USD.
   * The router selects a tool path that fits within this budget.
   */
  budget_usd?: number

  /**
   * Whether LEL (Life Event Log) signals are enabled for this query.
   * Passed through to every tool call if true.
   * Default: false — must be explicitly set by caller; never inferred.
   */
  lel_enabled?: boolean
}

// ── Budget + termination ──────────────────────────────────────────────────────

/**
 * Per-route cost/latency budget enforced by the agentic loop for multi_hop routes.
 */
export interface RouteBudget {
  /** Maximum USD spend for this route */
  max_usd: number
  /** Soft iteration limit for agentic routes */
  soft_iteration_limit: number
  /** Estimated latency category */
  latency_class: 'fast' | 'medium' | 'slow'
}

// ── Planned tool call ─────────────────────────────────────────────────────────

/**
 * A single tool call in the planned execution sequence.
 */
export interface PlannedToolCall {
  /** The capability URI to call */
  uri: CapabilityUri
  /** Why this tool was selected — readable rationale for trajectory logs */
  rationale: string
  /** Whether this is a mandatory first call or optional drill */
  mandatory: boolean
  /** Extra args to merge with context at call time */
  args?: Record<string, unknown>
}

// ── Route result ──────────────────────────────────────────────────────────────

/**
 * The full result of routing a query.
 * Returned by route() and consumed by the grounding spine (D3).
 *
 * CHART-AGNOSTIC CONTRACT: chart_id appears only in trajectory.chart_id
 * (opaque UUID) and in planned_calls[*].args when explicitly required.
 * The router never defaults chart_id to a known chart.
 */
export interface RouteResult {
  // ── Classification ────────────────────────────────────────────────────────

  /** The five-class route classification */
  route_class: RouteClass

  /** Traversal level this query operates at */
  traversal_level: TraversalLevel

  /** The retrieval archetype(s) this route targets */
  target_archetypes: RetrievalArchetype[]

  /** The tool roles this route uses */
  target_roles: ToolRole[]

  // ── Tool selection ────────────────────────────────────────────────────────

  /**
   * Ordered sequence of tool calls to execute.
   * - simple:        one umbrella entry call
   * - numeric_exact: one or more leaf calls
   * - relational:    the graph tool call (D4)
   * - narrative:     the hybrid retrieval call
   * - multi_hop:     bootstrap calls; the agentic loop extends from here
   */
  planned_calls: PlannedToolCall[]

  /**
   * Primary tool URI — the first / most important call.
   * Equals planned_calls[0].uri when non-empty; null when no tools available.
   */
  primary_tool: CapabilityUri | null

  /**
   * Whether the umbrella-then-drill pattern applies (per §3 topology doc).
   * true  → call primary_tool first, then drill using its returned drill_pointers
   * false → direct leaf/graph/hybrid call; no subsequent drill phase needed
   */
  umbrella_then_drill: boolean

  // ── Budget + termination ──────────────────────────────────────────────────

  /** Per-route budget for this classification */
  budget: RouteBudget

  /**
   * For multi_hop routes: value-based termination policy.
   * The agentic loop STOPS when marginal value drops, NOT on a hard count.
   * This is the D2 brief §2 "value-based termination" requirement.
   */
  termination_policy?: {
    strategy: 'value_based'
    /** 0..1 — stop when estimated marginal value of next call drops below this */
    marginal_value_threshold: number
    /** Soft iteration ceiling (advisory, not enforced as a hard cutoff) */
    soft_iteration_limit: number
  }

  // ── Observability (feeds D8 eval harness) ────────────────────────────────

  /** Trajectory record for D8 scoring */
  trajectory: RouteTrajectory
}

/**
 * Trajectory record — one entry per routed query, logged for D8 scoring.
 *
 * PRIVACY RULE: no PII, no native-specific data.
 * chart_id is an opaque UUID only; never log birth date, name, or location.
 */
export interface RouteTrajectory {
  /** Opaque chart UUID — no native name or birth data */
  chart_id: string

  /** The route class that was chosen */
  route_class: RouteClass

  /** How the routing decision was made */
  routing_method: 'rule' | 'model_fallback' | 'forced'

  /** Which rule fired (for rule-driven routing) */
  rule_fired?: string

  /** Traversal level selected */
  traversal_level: TraversalLevel

  /** Tool URIs in the planned sequence */
  planned_tool_uris: CapabilityUri[]

  /** ISO 8601 timestamp; UTC only — no locale-revealing offset */
  routed_at: string

  /** Budget ceiling applied */
  budget_usd: number

  /** Whether LEL was enabled for this query */
  lel_enabled: boolean

  /** Latency to produce the RouteResult (not including tool execution) */
  routing_latency_ms?: number
}

// ── Internal classifier result ────────────────────────────────────────────────

/**
 * Internal result from the rule-driven classifier.
 * Not exported — used only within the router implementation.
 */
export interface ClassifierResult {
  route_class: RouteClass
  traversal_level: TraversalLevel
  rule_fired: string
  confidence: 'high' | 'low'
}
