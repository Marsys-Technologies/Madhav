/**
 * QueryPlan — the structured plan produced by the Router (C2.1) that drives
 * every downstream pipeline stage. Derived from query_plan.schema.json v1.0.
 * Exported for shared use by Bundle Composer and other downstream consumers.
 */
export interface QueryPlan {
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
  // audience_tier excised (C-2, tier_excision / DG1 ruling): no downstream
  // consumer reads query_plan.audience_tier. Panel synthesis reads the
  // separate SynthesisRequest.audience_tier instead.
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
  /**
   * RC-11 (CR-118 fast-fail root cause, W5 residual closure): the chart the plan
   * is scoped to. `tool_name_bridge.ts`'s `getToolByName().retrieve()` reads this
   * dynamically (`plan['chart_id']`) to populate `args.chart_id` for every
   * `scope: 'per_chart'` capability. Never defaulted — undefined for
   * chart-agnostic tools. A QueryPlan literal that omits this silently sends NO
   * chart_id to a per-chart tool, which fails fast (a few ms, before any DB
   * round-trip) with a `chart_id is required` validation error — CR-118's
   * observed symptom on msr_sql/get_yoga_firings/cgm_graph_walk. Confirmed
   * offender: `/api/mcp/primitives/[tool]/route.ts`'s queryPlan builder (fixed
   * alongside this).
   */
  chart_id?: string
  // Optional fields
  planets?: string[]
  houses?: number[]
  dasha_context_required?: boolean
  graph_seed_hints?: string[]
  /** Edge types the classifier wants cgm_graph_walk to traverse. Empty/undefined = all edge types. */
  edge_type_filter?: string[]
  graph_traversal_depth?: number
  /** Filter applied to vector_search retrieval — narrows by doc_type and/or layer. */
  vector_search_filter?: {
    doc_type?: string[]
    layer?: string
  }
  bundle_directives?: {
    floor_overrides?: string[]
    conditional_overrides?: object
  }
  adjudicator_model_id?: string
  router_confidence?: number
  router_model_id?: string
  /** Params for chart_facts_query retrieval tool (M2-C1). */
  chart_facts_query?: {
    category?: string | string[]
    planet?: string
    house?: number
    sign?: string
    nakshatra?: string
    divisional_chart?: string
    keyword?: string
    limit?: number
    as_of_date?: string
    from_date?: string
    to_date?: string
    [key: string]: unknown
  }
  // Temporal extension flags (W5-R1)
  time_window?: { start: string; end: string }
  sade_sati_query?: boolean
  eclipse_query?: boolean
  retrograde_query?: boolean
  retrograde_planet?: string
  // Tool-param sidecar objects (mirrors schema properties; prevents additionalProperties failures)
  kp_query?: { cusp?: number; planet?: string }
  saham_query?: { saham_name?: string }
  divisional_query?: { varga?: string; planet?: string }
  domain_report_query?: { domains?: string[]; keyword?: string }
  remedial_codex_query?: { planet?: string; practice_type?: string }
  timeline_query?: { dasha_name?: string }
  // M8-G classical tools sidecar params
  classical_text_search?: { query?: string; schools?: string[]; tier_max?: number; limit?: number }
  classical_attribution_lookup?: {
    signal_ids?: string[]
    attribution_type?: 'confirms' | 'contradicts' | 'partial' | 'extends' | 'silent'
    confidence_tier?: 'HIGH' | 'MEDIUM' | 'LOW'
  }
}

// ────────────────────────────────────────────────────────────────────────────
// BHISMA Stream 2 — LLM-first planner types (§4.2)
//
// `RichQueryPlan` was returned by the legacy unified `plan()` when the
// LLM planner was flag-gated. It is a strict superset of `QueryPlan`,
// so every downstream consumer that already accepts a `QueryPlan` continues
// to work without change. Only the planner-aware code paths (route.ts when
// the flag is on, single_model_strategy synthesis_guidance reader) need to
// know about the extra fields.
// ────────────────────────────────────────────────────────────────────────────

/** Planning priority for a tool call. 1 = critical (never drop), 3 = nice-to-have. */
export type ToolCallPriority = 1 | 2 | 3

/**
 * Per-tool parameter spec produced by the planning LLM. The `params` object
 * is opaque from the planner's POV — each retrieval tool validates its own
 * param shape via Zod when called. Planner-supplied params are merged on
 * top of the QueryPlan defaults at retrieval time, exactly the same way
 * `per_tool_planner.ts` overrides work today.
 */
export interface ToolCallSpec {
  tool_name: string
  params: Record<string, unknown>
  priority: ToolCallPriority
  reason: string
}

/**
 * The richer plan emitted by the LLM-first planner. Extends QueryPlan; all
 * legacy consumers (rule_composer, retrieval pipeline) read only QueryPlan
 * fields and ignore the extras.
 */
export interface RichQueryPlan extends QueryPlan {
  /** One-sentence summary of what the user actually wants. */
  query_intent_summary: string
  /** Why these tools were selected (plan-level rationale). */
  planning_rationale: string
  /** Instruction to the synthesis LLM on angle, depth, and emphasis. */
  synthesis_guidance: string
  /** Per-tool parameter specs produced by the planning LLM. */
  tool_calls: ToolCallSpec[]
  /** Worker model that produced this plan. */
  planning_model_id: string
  /** Wall-clock latency of the planning LLM call. */
  planning_latency_ms: number
}

/** Minimal chart context the planning LLM needs to make sane tool selections. */
export interface ChartContext {
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
  /** Active mahadasha at current_date, e.g. "Mercury MD (2010–2027)". Optional. */
  active_dasha?: string
}

/** Conversation turn the planner consumes for short-term context. */
export interface ConversationTurn {
  role: 'user' | 'assistant'
  content: string
}

/**
 * Full input to `plan()`. The caller is responsible for resolving the
 * synthesis-model family (so the planner knows which worker family to use
 * per ADR-1) and for stamping current_date — never let the LLM guess time.
 */
export interface PlanContext {
  query: string
  conversation_history: ConversationTurn[]
  chart_context: ChartContext
  /** ISO date — the planner uses this for any temporal reasoning, never `new Date()` inside the prompt. */
  current_date: string
  manifest_fingerprint: string
  /** The user-selected synthesis model; planner resolves its worker family from this. */
  synthesis_model_id: string
}
