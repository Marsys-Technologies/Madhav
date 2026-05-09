/**
 * MARSYS-JIS Query Trace Panel — shared types
 * schema_version: 1.1
 *
 * v1.1 (BHISMA-B3, 2026-05-01): additive extensions for the Trace Command
 * Center. New fields are all OPTIONAL; existing emit sites continue to satisfy
 * the schema. Stream B2 will populate the new fields on context_assembly +
 * synthesis_done + plan emit; B3 panels guard every read with null checks.
 */

export type StepType = 'deterministic' | 'llm' | 'sql' | 'vector' | 'gcs'
export type StepStatus = 'pending' | 'running' | 'done' | 'error'

/** A single retrieved chunk or signal row, with layer classification */
export interface TraceChunkItem {
  id: string                  // chunk_id / signal_id
  source: string              // canonical_id or tool_name
  layer: 'L1' | 'L2.5' | 'system'
  token_estimate: number
  text: string                // full raw text
  /** Optional similarity / relevance score, when the source tool emits one. */
  score?: number
  /** Optional doc_type for vector_search results (l1_fact|ucn_section|msr_signal|cdlm_cell|domain_report|rm_element). */
  doc_type?: string
}

/**
 * Per-tool plan call, produced by the planner step. Mirrors
 * BHISMA_PLAN §4.2 ToolCallSpec without coupling to the router module.
 */
export interface TraceToolCallSpec {
  tool_name: string
  params: Record<string, unknown>
  priority: 1 | 2 | 3
  reason?: string
}

/**
 * Compact mirror of QueryPlan / RichQueryPlan attached to the planning step's
 * payload. Defined locally to avoid pulling router types into trace types
 * (router is must_not_touch in B3 scope; trace stays a pure consumer).
 */
export interface TraceQueryPlan {
  query_plan_id?: string
  query_class?: string
  domains?: string[]
  tools_authorized?: string[]
  forward_looking?: boolean
  dasha_context_required?: boolean
  graph_seed_hints?: string[]
  planets?: string[]
  houses?: number[]
  time_window?: { start: string; end: string }
  expected_output_shape?: string
  router_confidence?: number
  // RichQueryPlan additions (BHISMA-B2, may be absent pre-B2)
  query_intent_summary?: string
  planning_rationale?: string
  synthesis_guidance?: string
  tool_calls?: TraceToolCallSpec[]
  planning_model_id?: string
  planning_latency_ms?: number
}

/** Lightweight statistics stored in data_summary column */
export interface TraceDataSummary {
  // deterministic
  result?: string
  confidence?: number
  // llm
  model?: string
  input_tokens?: number
  output_tokens?: number
  // sql / vector / gcs — shared
  token_estimate?: number
  // sql
  rows_returned?: number
  tool_name?: string
  // vector
  chunks_returned?: number
  top_score?: number
  // gcs
  source_path?: string
  bytes?: number
  // plan (per_tool_planner / unified planner)
  planner_active?: boolean
  tools_refined?: number
  tool_count?: number
  // ── BHISMA-B3 additive (all optional) ──────────────────────────────────────
  /** synthesis_done: number of SIG.MSR.NNN citations detected in response. */
  citation_count?: number
  /** synthesis_done: temperature passed to streamText (W2-BUGS UQE-2). */
  temperature?: number
  /** synthesis_done: did the response match expected_output_shape (heuristic). */
  output_shape_compliant?: boolean
  /** plan: query_class promoted to data_summary for compact list-row rendering. */
  query_class?: string
  /** plan: planner confidence (0.0 = fallback). */
  planning_confidence?: number
  /** Provider family of the model used for this LLM step. */
  provider?: string
  /** Whether this step's LLM call produced a reasoning trace (DeepSeek R1 only). */
  reasoning_path?: boolean
  /** step_error step: machine-readable failure reason from PipelineError. */
  error_reason?: string
  /** step_error step: which pipeline stage failed (classify|compose|tool_fetch|synthesis). */
  error_stage?: string
  // ── P5 D.5.1 additive (context_assembly short-circuit) ─────────────────────
  /** context_assembly: true when the LLM call was skipped. */
  short_circuited?: boolean
  /** context_assembly: short-circuit reason ('token_threshold' | 'flag_off'). */
  reason?: string
  /** context_assembly: estimated total tokens of the bundle examined. */
  total_token_estimate?: number
  /** context_assembly: token threshold used for the short-circuit decision. */
  threshold?: number
}

/** Full drill-down content stored in payload column */
export interface TracePayload {
  // sql / vector / gcs steps
  items?: TraceChunkItem[]
  // context_assembly step
  l1_tokens?: number
  l2_tokens?: number
  system_tokens?: number
  total_tokens?: number
  l1_items?: TraceChunkItem[]
  l2_items?: TraceChunkItem[]
  // llm steps
  prompt_preview?: string
  // ── BHISMA-B3 additive (all optional) ──────────────────────────────────────
  /** Planning step: full QueryPlan / RichQueryPlan emitted for QueryDNAPanel. */
  query_plan?: TraceQueryPlan
  /** Planning step: per-tool calls with priorities (subsumes plan_per_tool overrides). */
  tool_calls?: TraceToolCallSpec[]
  /** DeepSeek R1: extracted think-block reasoning trace (optional, hidden by default). */
  reasoning_trace?: string
  /** step_error step: human-readable detail for inline display. */
  error_message?: string
}

/** One pipeline step record (maps 1:1 to a query_trace_steps row) */
export interface TraceStep {
  query_id: string
  conversation_id?: string
  step_seq: number
  step_name: string
  step_type: StepType
  status: StepStatus
  started_at: string          // ISO 8601
  completed_at?: string       // ISO 8601, set on done/error
  latency_ms?: number
  parallel_group?: string     // e.g. 'tool_fetch' — marks concurrent siblings
  data_summary: TraceDataSummary
  payload: TracePayload
}

/**
 * Planning lifecycle events (W2-TRACE-A, UQE-5b). Emitted by manifest_planner
 * before/after the LLM-first planner runs so the UI can show a planning
 * indicator + materialise the plan as soon as it's available.
 */
export interface PlanningStartEvent {
  event: 'planning_start'
  query_id: string
  planner_model_id: string
  manifest_tool_count: number
}

export interface PlanningDoneEvent {
  event: 'planning_done'
  query_id: string
  tool_count_planned: number
  tools_selected: string[]
  query_intent_summary: string
  planner_latency_ms: number
}

/**
 * Event sent over SSE and through the in-process emitter.
 *
 * Modeled as a single open shape (not a discriminated union) so existing
 * consumers — notably useTraceStream which checks `event.step` directly —
 * keep type-checking. Variant-specific fields are optional and only
 * populated for the matching `event` value.
 */
export interface TraceEvent {
  event:
    | 'step_start'
    | 'step_done'
    | 'step_error'
    | 'done'
    | 'planning_start'
    | 'planning_done'
  query_id: string
  step?: TraceStep
  // ── planning_start fields (W2-TRACE-A) ─────────────────────────────────────
  planner_model_id?: string
  manifest_tool_count?: number
  // ── planning_done fields (W2-TRACE-A) ──────────────────────────────────────
  tool_count_planned?: number
  tools_selected?: string[]
  query_intent_summary?: string
  planner_latency_ms?: number
}

// ── BHISMA-B3 analytics types ─────────────────────────────────────────────────

/** Single-row summary returned by /api/trace/history (default mode). */
export interface TraceHistoryRow {
  query_id: string
  query_text: string | null
  created_at: string
  step_count: number
  total_latency_ms: number | null
  // ── analytics-mode additions (all optional; populated when ?mode=analytics) ─
  query_class?: string | null
  plan_latency_ms?: number | null
  synthesis_latency_ms?: number | null
  tool_fetch_latency_ms?: number | null
  citation_count?: number | null
  planning_confidence?: number | null
  has_error?: boolean
  tools_used?: string[]
}
