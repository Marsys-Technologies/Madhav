// Observatory backend API — response shape types.
//
// Authored by USTAD_S1_3_OBSERVATORY_BACKEND_API for the five read-only
// `/api/admin/observatory/*` GET endpoints. Consumed by the route handlers
// in `platform/src/app/api/admin/observatory/**` and re-exported for the
// frontend sessions S1.9–S1.13.
//
// Scope: response shapes + filter inputs only. Row types live in
// `@/lib/db/schema/observatory` and are mirrored 1:1 from migration 038.
// Nothing here describes the LLM observability shim (S1.2 owns those types).

import type {
  LlmCallStatus,
  LlmPipelineStage,
  LlmProvider,
  LlmUsageEventRow,
} from '../db/schema/observatory'

// ---------------------------------------------------------------------------
// Filters — repeated across multiple endpoints; keep one shape.
// ---------------------------------------------------------------------------

export interface ObservatoryFilters {
  provider?: string[]
  model?: string[]
  pipeline_stage?: string[]
}

// ---------------------------------------------------------------------------
// /api/admin/observatory/summary
// ---------------------------------------------------------------------------

/** KPI rollup for one date range (the "current" or "previous" window). */
export interface SummaryWindowMetrics {
  total_cost_usd: number
  total_requests: number
  total_input_tokens: number
  total_output_tokens: number
  total_cache_tokens: number
  avg_cost_per_request: number
  p50_latency_ms: number
  p95_latency_ms: number
  reconciliation_variance_pct: number | null
  reconciliation_through_date: string | null
}

/** When `compare_to_previous=true`, every numeric metric also has a `_delta`
 *  field (current minus previous). Reconciliation deltas omitted; they
 *  aren't time-deltas in the same sense. */
export interface SummaryDeltas {
  total_cost_usd_delta: number
  total_requests_delta: number
  total_input_tokens_delta: number
  total_output_tokens_delta: number
  total_cache_tokens_delta: number
  avg_cost_per_request_delta: number
  p50_latency_ms_delta: number
  p95_latency_ms_delta: number
}

export type SummaryResponse = SummaryWindowMetrics & Partial<SummaryDeltas>

export interface SummaryQueryInput {
  from: string
  to: string
  compare_to_previous?: boolean
  filters?: ObservatoryFilters
}

// ---------------------------------------------------------------------------
// /api/admin/observatory/timeseries
// ---------------------------------------------------------------------------

export type TimeseriesGranularity = 'hour' | 'day' | 'week'
export type TimeseriesDimension = 'provider' | 'model' | 'pipeline_stage'

export interface TimeseriesBucket {
  /** ISO timestamp at the start of the bucket. */
  time: string
  /** Map of `dimension_value -> total_cost_usd` for that bucket. */
  series: Record<string, number>
}

export interface TimeseriesResponse {
  buckets: TimeseriesBucket[]
}

export interface TimeseriesQueryInput {
  from: string
  to: string
  granularity: TimeseriesGranularity
  dimension: TimeseriesDimension
  filters?: ObservatoryFilters
}

// ---------------------------------------------------------------------------
// /api/admin/observatory/breakdowns
// ---------------------------------------------------------------------------

export type BreakdownDimension =
  | 'provider'
  | 'model'
  | 'pipeline_stage'
  | 'conversation'

export interface BreakdownRow {
  dim_value: string
  cost_usd: number
  request_count: number
  input_tokens: number
  output_tokens: number
  cache_tokens: number
  avg_latency_ms: number
}

export interface BreakdownsResponse {
  rows: BreakdownRow[]
}

export interface BreakdownsQueryInput {
  from: string
  to: string
  dimension: BreakdownDimension
  filters?: ObservatoryFilters
}

// ---------------------------------------------------------------------------
// /api/admin/observatory/events
// ---------------------------------------------------------------------------

/** Row shape returned by the events list endpoint. Subset of the full
 *  `llm_usage_events` row — prompt/response text excluded for list responses
 *  (large payloads). The single-event endpoint returns the full row. */
export interface ObservatoryEventListRow {
  event_id: string
  conversation_id: string | null
  conversation_name: string | null
  prompt_id: string
  user_id: string
  provider: LlmProvider | string
  model: string
  pipeline_stage: LlmPipelineStage | string
  input_tokens: number | null
  output_tokens: number | null
  cache_read_tokens: number | null
  cache_write_tokens: number | null
  computed_cost_usd: number | null
  latency_ms: number | null
  status: LlmCallStatus | string
  error_code: string | null
  started_at: string
  finished_at: string | null
}

export interface EventsResponse {
  events: ObservatoryEventListRow[]
  /** Opaque cursor to pass back as `cursor` for the next page; null when no more. */
  next_cursor: string | null
  /** Total matching rows for this filter set (computed once via COUNT(*)). */
  total_count: number
}

export interface EventsQueryInput {
  from: string
  to: string
  provider?: string[]
  model?: string[]
  pipeline_stage?: string[]
  conversation_id?: string
  user_id?: string
  status?: LlmCallStatus | string
  min_cost?: number
  max_cost?: number
  min_latency?: number
  max_latency?: number
  /** ILIKE substring against (prompt_text, response_text). */
  search?: string
  limit?: number
  /** Keyset cursor token: `<started_at_iso>|<event_id>` from a prior page. */
  cursor?: string
}

// ---------------------------------------------------------------------------
// /api/admin/observatory/event/[id]
// ---------------------------------------------------------------------------

export type EventDetailResponse = LlmUsageEventRow

// ---------------------------------------------------------------------------
// Limits / defaults — shared across endpoints
// ---------------------------------------------------------------------------

export const EVENTS_DEFAULT_LIMIT = 50
export const EVENTS_MAX_LIMIT = 200
