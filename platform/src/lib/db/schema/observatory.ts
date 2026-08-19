// Observatory schema row types — mirrors migration 038_observatory_schema.sql
// 1:1 by column name and nullability. Consumed by the instrumentation shim
// (S1.2), the dashboard backend (S1.3), the per-provider adapters (S1.4–S1.8),
// the reconciliation framework (S2.1+), the budget evaluator (S3.2), and the
// replay/re-cost engine (S4.5). NUMERIC columns surface as `number` because
// db/client.ts registers a parseFloat type-parser for OID 1700.

export type LlmProvider =
  | 'anthropic'
  | 'openai'
  | 'gemini'
  | 'deepseek'
  | 'nim'

export type LlmPipelineStage =
  | 'classify'
  | 'compose'
  | 'retrieve'
  | 'synthesize'
  | 'audit'
  | 'other'
  | 'planner'
  | 'title'
  | 'history_summary'

export type LlmCallStatus = 'success' | 'error' | 'timeout'

export type LlmTokenClass =
  | 'input'
  | 'output'
  | 'cache_read'
  | 'cache_write'
  | 'reasoning'

export type LlmReconciliationStatus =
  | 'matched'
  | 'variance_within_tolerance'
  | 'variance_alert'
  | 'missing_authoritative'

export type LlmBudgetScope =
  | 'total'
  | 'provider'
  | 'model'
  | 'pipeline_stage'

export type LlmBudgetPeriod = 'daily' | 'weekly' | 'monthly'

export interface LlmPricingVersionRow {
  pricing_version_id: string
  provider: LlmProvider | string
  model: string
  token_class: LlmTokenClass | string
  price_per_million_usd: number
  effective_from: string
  effective_to: string | null
  source_url: string | null
  recorded_at: string
}

export interface LlmUsageEventRow {
  event_id: string
  conversation_id: string
  conversation_name: string | null
  prompt_id: string
  parent_prompt_id: string | null
  user_id: string
  provider: LlmProvider | string
  model: string
  pipeline_stage: LlmPipelineStage | string
  prompt_text: string | null
  response_text: string | null
  system_prompt: string | null
  parameters: unknown | null
  input_tokens: number | null
  output_tokens: number | null
  cache_read_tokens: number | null
  cache_write_tokens: number | null
  reasoning_tokens: number | null
  computed_cost_usd: number | null
  pricing_version_id: string | null
  latency_ms: number | null
  status: LlmCallStatus | string
  error_code: string | null
  provider_request_id: string | null
  started_at: string
  finished_at: string | null
  feature_flag_state: unknown | null
  client_ip_hash: string | null
  created_at: string
  /**
   * Serving door this call came through — 'web' | 'mcp' | 'other'. Added by
   * migration 574 (NCD-8) for per-(user_id, channel, model) cost attribution.
   * NULL for every row written before the door was recorded, and for any call
   * site that does not declare one.
   */
  channel: string | null
}

export interface LlmProviderCostReportRow {
  report_id: string
  provider: LlmProvider | string
  model: string | null
  time_bucket_start: string
  time_bucket_end: string
  workspace_id: string | null
  authoritative_cost_usd: number
  authoritative_input_tokens: number | null
  authoritative_output_tokens: number | null
  raw_payload: unknown | null
  pulled_at: string
}

export interface LlmCostReconciliationRow {
  reconciliation_id: string
  reconciliation_date: string
  provider: LlmProvider | string
  model: string | null
  computed_total_usd: number
  authoritative_total_usd: number | null
  variance_usd: number | null
  variance_pct: number | null
  event_count: number
  status: LlmReconciliationStatus | string
  notes: string | null
  reconciled_at: string
}

export interface LlmBudgetAlertThreshold {
  pct: number
  channel: string
}

export interface LlmBudgetRuleRow {
  budget_rule_id: string
  name: string
  scope: LlmBudgetScope | string
  scope_value: string | null
  period: LlmBudgetPeriod | string
  amount_usd: number
  alert_thresholds: LlmBudgetAlertThreshold[] | unknown
  created_by_user_id: string | null
  active: boolean
  created_at: string
  updated_at: string
}
