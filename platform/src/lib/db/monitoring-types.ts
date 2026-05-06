// Row types for the monitoring log tables created in migrations 032-035.
// Field names and nullability mirror the SQL columns 1:1; consumed by the
// W2-INSTRUMENT (Round 3) write helpers and the v_* analytics views.

export type LlmCallStage =
  | 'planner'
  | 'synthesis'
  | 'title'
  | 'history_summary'
  | 'context_assembly'

export type ToolExecutionStatus = 'ok' | 'zero_rows' | 'error' | 'cache_hit'

export interface LlmCallLogRow {
  id: string
  query_id: string
  conversation_id: string | null
  call_stage: LlmCallStage | string
  model_id: string
  provider: string
  input_tokens: number | null
  output_tokens: number | null
  reasoning_tokens: number | null
  latency_ms: number | null
  cost_usd: string | number | null
  fallback_used: boolean | null
  error_code: string | null
  payload: unknown | null
  // TRACE-T1 additions (migration 040) — all optional/nullable for backward compat
  decision_alternatives?: unknown | null
  decision_reasoning?: string | null
  prompt_template_id?: string | null
  prompt_template_version?: string | null
  parent_call_id?: string | null
  created_at: string
}

export interface QueryPlanLogRow {
  id: string
  query_id: string
  conversation_id: string | null
  chart_id: string | null
  planner_model_id: string | null
  query_text: string | null
  query_class: string | null
  tool_count: number | null
  plan_json: unknown | null
  parsing_success: boolean
  parse_error: string | null
  fallback_used: boolean | null
  planner_latency_ms: number | null
  created_at: string
}

export type ToolExecutionErrorClass = 'OK' | 'TIMEOUT' | 'AUTH' | 'MALFORMED_RESPONSE' | 'EMPTY'

export interface ToolExecutionLogRow {
  id: string
  query_id: string
  tool_name: string
  params_json: unknown | null
  status: ToolExecutionStatus | string
  rows_returned: number | null
  latency_ms: number | null
  token_estimate: number | null
  data_asset_id: string | null
  error_code: string | null
  served_from_cache: boolean | null
  fallback_used: boolean | null
  // TRACE-T1 additions (migration 040) — all optional/nullable for backward compat
  raw_result_count?: number | null
  kept_result_count?: number | null
  dropped_items?: unknown | null
  kept_items?: unknown | null
  tool_input_payload?: unknown | null
  tool_output_summary?: unknown | null
  error_class?: ToolExecutionErrorClass | null
  created_at: string
}

export interface ContextAssemblyLogRow {
  id: string
  query_id: string
  l1_tokens: number | null
  l2_5_signal_tokens: number | null
  l2_5_pattern_tokens: number | null
  l4_tokens: number | null
  vector_tokens: number | null
  cgm_tokens: number | null
  total_tokens: number
  synthesis_model_id: string | null
  model_max_context: number | null
  b3_compliant: boolean | null
  citation_count: number | null
  verified_citations: number | null
  created_at: string
}

export interface ObservatoryQueryEventInput {
  queryId: string
  conversationId: string | null
  userId: string
  modelId: string
  queryClass: string
  stack: string
  queryText: string
  responseText: string | null
  setupStart: Date
  /** Token counts from the AI SDK response — optional; pass when available. */
  inputTokens?: number | null
  outputTokens?: number | null
  cacheReadTokens?: number | null
  cacheWriteTokens?: number | null
  reasoningTokens?: number | null
}
