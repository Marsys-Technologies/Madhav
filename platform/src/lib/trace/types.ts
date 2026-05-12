/**
 * MARSYS-JIS Query Trace — single source of truth for trace UI and assembler.
 * schema_version: 1.2
 *
 * This module is the authoritative schema for the trace surface. Renderers,
 * the assembler, the SSE stream, and the admin endpoint all import their
 * stage names, step discriminants, and per-stage metadata interfaces from
 * here. Hard-coded string literals for stage names anywhere in the trace UI
 * are a regression — point them at `PipelineStage` instead.
 *
 * History:
 *  - v1.0 — initial schema (TraceStep / TraceEvent).
 *  - v1.1 (BHISMA-B3, 2026-05-01) — additive Trace Command Center fields.
 *  - v1.2 (Gate II, 2026-05-12) — adds `PipelineStage`, `AssembledTrace`, and
 *    per-stage metadata interfaces. The emitter writes legacy `step_name`
 *    values (e.g. `'classify'` for the planner); `STAGE_FROM_STEP_NAME`
 *    projects them onto canonical stages.
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

// ── Gate II v1.2 — canonical stage model ──────────────────────────────────────

/**
 * Canonical pipeline stages, as the trace UI presents them.
 *
 * The emitter's `step_name` values are LEGACY in places (e.g. `'classify'` is
 * really the planner — see `STAGE_FROM_STEP_NAME` below). Renderers should
 * key off `PipelineStage`, not raw `step_name`.
 */
export type PipelineStage =
  | 'planner'
  | 'retrieval'
  | 'synthesis'
  | 'audit'
  | 'checkpoint_4_5'
  | 'checkpoint_5_5'
  | 'checkpoint_8_5'

/**
 * Map a raw emitted `step_name` to its canonical pipeline stage.
 *
 * `'classify'` → planner is a renamed-but-not-yet-migrated emitter literal
 * (route.ts:393 carries the inline reason).
 *
 * `'compose_bundle'` → planner sub-step.
 *
 * `'context_assembly'` is a vestigial short-circuit marker (the legacy stage
 * was retired in Pipeline-Transform-S1) — surfaced inside the Synthesis
 * step-detail, not as its own canonical stage.
 *
 * Steps whose `parallel_group === 'tool_fetch'` map to `retrieval` regardless
 * of their `step_name`. Use `mapStepToStage()` for the parallel-group aware
 * resolver.
 */
export const STAGE_FROM_STEP_NAME: Record<string, PipelineStage> = {
  classify: 'planner',
  compose_bundle: 'planner',
  context_assembly: 'synthesis',
  synthesis: 'synthesis',
  synthesis_done: 'synthesis',
  citation_warn: 'audit',
  citation_error: 'audit',
}

/**
 * Resolve a step row to its canonical pipeline stage, honoring the
 * `parallel_group === 'tool_fetch'` rule (any tool fetch belongs to the
 * Retrieval stage regardless of its tool name).
 */
export function mapStepToStage(step: Pick<TraceStep, 'step_name' | 'parallel_group'>): PipelineStage | null {
  if (step.parallel_group === 'tool_fetch') return 'retrieval'
  return STAGE_FROM_STEP_NAME[step.step_name] ?? null
}

/** One tool's run inside the Retrieval group (D5). */
export interface RetrievalSubToolRun {
  /** Manifest tool_name (e.g. 'vector_search', 'cgm_graph_walk', 'chart_facts_query', etc.). */
  tool_name: string
  step_seq: number
  step_type: StepType
  status: StepStatus
  latency_ms: number | null
  data_summary: TraceDataSummary
  payload: TracePayload
}

/** Planner stage metadata (D3). */
export interface PlannerStepMetadata {
  step_seq: number
  status: StepStatus
  latency_ms: number | null
  query_plan: TraceQueryPlan | null
  tool_calls: TraceToolCallSpec[]
  /** From the `compose_bundle` sub-step, if present. */
  bundle_summary: string | null
}

/**
 * Synthesis stage metadata (D6).
 *
 * Discriminated by `mode`. The emitter does not yet write a `mode` field
 * (§J.4 in GAP_ANALYSIS); the assembler infers it from query-plan / message
 * metadata and defaults to `single_model` when ambiguous (§4.5 R1).
 */
export type SynthesisStepMetadata =
  | {
      mode: 'single_model'
      step_seq: number
      status: StepStatus
      latency_ms: number | null
      model: string | null
      input_tokens: number | null
      output_tokens: number | null
      citation_count: number | null
      provider: string | null
      reasoning_path: boolean | null
      output_shape_compliant: boolean | null
      temperature: number | null
      prompt_preview: string | null
      reasoning_trace: string | null
      /** Optional short-circuit metadata from the vestigial `context_assembly` step. */
      context_assembly_short_circuit: {
        short_circuited: boolean
        total_token_estimate: number
        threshold: number
        reason: string | null
      } | null
    }
  | {
      mode: 'panel'
      step_seq: number
      status: StepStatus
      latency_ms: number | null
      /** Per-panelist rows; empty array if the emitter has not been extended yet (§J.4). */
      panelists: Array<{
        panelist_id: string
        model: string | null
        latency_ms: number | null
        input_tokens: number | null
        output_tokens: number | null
      }>
      aggregator: {
        model: string | null
        latency_ms: number | null
        input_tokens: number | null
        output_tokens: number | null
      } | null
      /** Render hint: when true, render a "panel trace shape pending follow-up gate" note. */
      panel_trace_pending: boolean
    }

/** Audit stage metadata (assembled from `audit_events` + `citation_*` trace steps). */
export interface AuditStepMetadata {
  /** Present when an `audit_events` row exists for the query_id. */
  audit_event_id: string | null
  audit_event_version: number | null
  disclosure_tier: 'super_admin' | 'client' | null
  validator_verdict: 'PASS' | 'WARN' | 'ERROR' | 'UNKNOWN'
  /** B.10 (no fabricated computation) compliance flag. `null` when not yet computed. */
  b10_compliant: boolean | null
  /** B.11 (whole-chart-read) compliance flag. */
  b11_compliant: boolean | null
  /** Inline citation-gate signal carried by `citation_warn` / `citation_error` trace steps. */
  citation_gate: {
    result: 'PASS' | 'WARN' | 'ERROR'
    reason: string | null
    layer1_count: number | null
  } | null
  /** When the assembler had no audit row, surface a placeholder note (§J.2). */
  placeholder_note: string | null
}

/** Checkpoint stage metadata (D1 — collapsible group). */
export interface CheckpointStepMetadata {
  stage: 'checkpoint_4_5' | 'checkpoint_5_5' | 'checkpoint_8_5'
  /** Flag-driven; `null` until the assembler resolves the config. */
  enabled: boolean | null
  /** `true` if a corresponding trace step exists; `false` if the checkpoint did not run. */
  ran: boolean
  status: StepStatus | null
  latency_ms: number | null
  verdict: 'PASS' | 'WARN' | 'ERROR' | 'SKIPPED' | null
  notes: string | null
}

/**
 * Type alias for the brief's `QueryPlan` interface; this surface uses the
 * existing `TraceQueryPlan` to avoid duplicating the source of truth.
 */
export type QueryPlan = TraceQueryPlan

/**
 * Assembled view of a single query's trace — the shape returned by
 * `/api/admin/trace/[query_id]` and consumed by every renderer that reads
 * the full trace (not the live SSE stream).
 *
 * `steps` retains the raw `TraceStep[]` for renderers that scan/group
 * themselves (e.g. RetrievalScorecard); `grouped` is the canonical view
 * keyed by pipeline stage.
 */
export interface AssembledTrace {
  query_id: string
  query_text: string | null
  total_latency_ms: number | null
  /** Top-line QueryPlan for the header banner (D3). */
  query_plan: TraceQueryPlan | null
  /** Raw step rows for renderers that need everything. */
  steps: TraceStep[]
  /** Canonical per-stage projection. */
  grouped: {
    planner: PlannerStepMetadata | null
    retrieval: RetrievalSubToolRun[]
    synthesis: SynthesisStepMetadata | null
    audit: AuditStepMetadata | null
    checkpoints: CheckpointStepMetadata[]
  }
  /** Schema-version + diagnostics — true if any expected projection was missing. */
  partial: boolean
}

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
