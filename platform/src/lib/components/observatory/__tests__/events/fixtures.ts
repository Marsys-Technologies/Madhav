import type {
  EventDetailResponse,
  EventsResponse,
  ObservatoryEventListRow,
} from '@/lib/observatory/types'

export function makeRow(
  i: number,
  overrides: Partial<ObservatoryEventListRow> = {},
): ObservatoryEventListRow {
  const base: ObservatoryEventListRow = {
    event_id: `evt-${String(i).padStart(4, '0')}`,
    conversation_id: 'conv-A',
    conversation_name: 'Conversation A',
    prompt_id: `pmt-${i}`,
    user_id: 'user-1',
    provider: 'anthropic',
    model: 'claude-opus-4-7',
    pipeline_stage: 'synthesize',
    input_tokens: 100 + i,
    output_tokens: 50 + i,
    cache_read_tokens: 0,
    cache_write_tokens: 0,
    computed_cost_usd: 0.000123 + i * 0.000001,
    latency_ms: 1000 + i * 10,
    status: 'success',
    error_code: null,
    started_at: new Date(2026, 4, 1, 10, 0, i).toISOString(),
    finished_at: new Date(2026, 4, 1, 10, 0, i, 500).toISOString(),
  }
  return { ...base, ...overrides }
}

export function makeRows(n: number): ObservatoryEventListRow[] {
  return Array.from({ length: n }, (_, i) => makeRow(i))
}

export function makeEventsResponse(
  rows: ObservatoryEventListRow[],
  next_cursor: string | null = null,
  total_count?: number,
): EventsResponse {
  return {
    events: rows,
    next_cursor,
    total_count: total_count ?? rows.length,
  }
}

export function makeDetail(
  i: number,
  overrides: Partial<EventDetailResponse> = {},
): EventDetailResponse {
  const base: EventDetailResponse = {
    event_id: `evt-${String(i).padStart(4, '0')}`,
    conversation_id: 'conv-A',
    conversation_name: 'Conversation A',
    prompt_id: `pmt-${i}`,
    parent_prompt_id: null,
    user_id: 'user-1',
    provider: 'anthropic',
    model: 'claude-opus-4-7',
    pipeline_stage: 'synthesize',
    prompt_text: `prompt body for ${i}`,
    response_text: `response body for ${i}`,
    system_prompt: `system prompt ${i}`,
    parameters: { temperature: 0.7, max_tokens: 1024 },
    input_tokens: 100 + i,
    output_tokens: 50 + i,
    cache_read_tokens: 0,
    cache_write_tokens: 0,
    reasoning_tokens: 0,
    computed_cost_usd: 0.000123 + i * 0.000001,
    pricing_version_id: 'pricing-v1',
    latency_ms: 1000 + i * 10,
    status: 'success',
    error_code: null,
    provider_request_id: `req-${i}`,
    started_at: new Date(2026, 4, 1, 10, 0, i).toISOString(),
    finished_at: new Date(2026, 4, 1, 10, 0, i, 500).toISOString(),
    feature_flag_state: {},
    client_ip_hash: null,
    created_at: new Date(2026, 4, 1, 10, 0, i, 600).toISOString(),
    // NCD-8 / migration 574. null is the accurate value for a row whose call site
    // declared no serving door — the state every pre-574 row is in.
    channel: null,
  }
  return { ...base, ...overrides }
}
