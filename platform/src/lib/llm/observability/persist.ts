// persistObservation — apply the active redaction policy, then INSERT one row
// into llm_usage_events. NEVER throws: observability errors must not break
// the caller (the chat path keeps working even when telemetry can't write).
//
// OD.S1.3.1 — RESOLVED 2026-05-03 (USTAD_S1_13). No separate
// `llm_provider_raw_responses` table. Request parameter snapshots live in the
// `parameters` jsonb column of llm_usage_events (all five S1.4–S1.8 adapters
// already populate it). Raw provider response bodies are not persisted at v1;
// the Meta tab of EventSidePanel surfaces this as a documented note. Capture
// can be added in a future release without schema migration (the column is
// jsonb).
//
// OD.S1.7.1 — RESOLVED 2026-05-03 (USTAD_S1_13) via Option B (no API change).
// observe()/observeStream() classify all thrown errors as status='error'.
// Adapters that detect a provider timeout call persistObservation() directly
// with status='timeout' before re-throwing. This function is therefore the
// timeout escape hatch — see the JSDoc on the export below.

import { getActivePolicy } from './redaction'
import type {
  CostResult,
  ObservatoryDb,
  ObservedLLMRequest,
  ObservedLLMResponse,
  PersistedObservation,
} from './types'

const INSERT_SQL = `
  INSERT INTO llm_usage_events (
    conversation_id,
    conversation_name,
    prompt_id,
    parent_prompt_id,
    user_id,
    provider,
    model,
    pipeline_stage,
    prompt_text,
    response_text,
    system_prompt,
    parameters,
    input_tokens,
    output_tokens,
    cache_read_tokens,
    cache_write_tokens,
    reasoning_tokens,
    computed_cost_usd,
    pricing_version_id,
    latency_ms,
    status,
    error_code,
    provider_request_id,
    started_at,
    finished_at,
    channel
  ) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
    $21, $22, $23, $24, $25, $26
  )
  RETURNING *
`

/**
 * INSERT one llm_usage_events row from an observed request/response pair.
 *
 * Provider adapters (S1.4–S1.8) call this directly — bypassing observe() — when
 * they need to record a status the wrapper can't produce on its own. Today
 * the only such status is `timeout`: observe()/observeStream() classify every
 * thrown error as `error`, so an adapter that detects a provider timeout (e.g.
 * AbortError from a per-request deadline) must build the ObservedLLMResponse
 * itself with `status: 'timeout'` and call this function before re-throwing.
 *
 * Use observe() in the success/error case; use this function as the timeout
 * escape hatch and for any other adapter-classified terminal status.
 */
export async function persistObservation(
  req: ObservedLLMRequest,
  res: ObservedLLMResponse,
  costResult: CostResult | null,
  db: ObservatoryDb,
): Promise<PersistedObservation | null> {
  try {
    const policy = getActivePolicy()
    const { request, response } = policy(req, res)

    const latencyMs = Math.max(
      0,
      response.finished_at.getTime() - response.started_at.getTime(),
    )

    const params: unknown[] = [
      request.conversation_id,
      request.conversation_name,
      request.prompt_id,
      request.parent_prompt_id ?? null,
      request.user_id,
      request.provider,
      request.model,
      request.pipeline_stage,
      request.prompt_text,
      response.response_text,
      request.system_prompt,
      request.parameters === undefined ? null : JSON.stringify(request.parameters),
      response.usage.input_tokens,
      response.usage.output_tokens,
      response.usage.cache_read_tokens,
      response.usage.cache_write_tokens,
      response.usage.reasoning_tokens,
      costResult?.computed_cost_usd ?? null,
      costResult?.pricing_version_id ?? null,
      latencyMs,
      response.status,
      response.error_code ?? null,
      response.provider_request_id ?? null,
      response.started_at.toISOString(),
      response.finished_at.toISOString(),
      // NCD-8 (migration 574): the serving door, for per-(user, channel, model)
      // cost attribution. `?? null` is the honest absence, not a default — an
      // adapter that never declared a door must not have one invented for it.
      request.channel ?? null,
    ]

    const result = await db.query<PersistedObservation>(INSERT_SQL, params)
    return result.rows[0] ?? null
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('[observability] persistObservation failed:', err)
    return null
  }
}
