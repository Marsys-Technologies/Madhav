import 'server-only'

/**
 * cache_metrics.ts — D-S1 R11.D
 *
 * Observatory-side logging for Anthropic prompt-cache hit/miss metrics.
 *
 * Called from the /api/chat/consume route (or synthesis layer) after every
 * Anthropic API call that returns usage with cache token fields. Appends a
 * structured record to the telemetry stream already consumed by the Observatory.
 *
 * Anthropic's cache token fields (from SDK usage object):
 *   cache_creation_input_tokens  — tokens written to the 5-min ephemeral cache
 *   cache_read_input_tokens      — tokens served from cache (0.1x cost)
 *
 * Cost model (at time of D-S1, 2026-05-22):
 *   cache write  = 1.25x base input token price
 *   cache read   = 0.10x base input token price
 *   savings      = (1 − 0.10) × cache_read_input_tokens × base_price
 */

export interface CacheUsage {
  /** Tokens written to cache (cache-miss path). 1.25x cost. */
  cacheCreationTokens: number
  /** Tokens read from cache (cache-hit path). 0.1x cost. */
  cacheReadTokens: number
  /** Standard input tokens (non-cached). 1.0x cost. */
  inputTokens: number
  /** Output tokens. Standard output price. */
  outputTokens: number
}

export interface CacheMetricsRecord {
  provider: 'anthropic'
  /** ISO-8601 timestamp. */
  timestamp: string
  /** The conversation/query identifier for correlation. */
  conversationId?: string
  /** The current model string (e.g. "claude-opus-4-5-20251101"). */
  model: string
  usage: CacheUsage
  /** Derived: true when cacheReadTokens > 0. */
  cacheHit: boolean
  /** Derived: true when cacheCreationTokens > 0. */
  cacheWrite: boolean
  /**
   * Estimated cost delta vs. no-cache: negative means cheaper.
   * Formula: (cacheRead × 0.10 + cacheWrite × 1.25 + input) − (cacheRead + cacheWrite + input)
   *        = cacheRead × (0.10 − 1) + cacheWrite × (1.25 − 1)
   *        = −0.90 × cacheRead + 0.25 × cacheWrite  (in token units; caller scales by per-token price)
   */
  estimatedTokenDeltaRatio: number
}

/**
 * Builds a CacheMetricsRecord from an Anthropic SDK usage object.
 * Returns null when the provider is not Anthropic or when cache data is absent.
 */
export function buildCacheMetricsRecord(params: {
  model: string
  conversationId?: string
  /** Raw usage from Anthropic SDK response (typed loosely to avoid SDK version coupling). */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  usage: Record<string, any>
}): CacheMetricsRecord | null {
  const { model, conversationId, usage } = params

  // Guard: only proceed when cache fields are present
  const cacheCreationTokens: number = usage?.cache_creation_input_tokens ?? 0
  const cacheReadTokens: number = usage?.cache_read_input_tokens ?? 0
  const inputTokens: number = usage?.input_tokens ?? 0
  const outputTokens: number = usage?.output_tokens ?? 0

  // If there's no cache activity at all, skip (avoids polluting Observatory with
  // every non-caching request)
  if (cacheCreationTokens === 0 && cacheReadTokens === 0) {
    return null
  }

  const estimatedTokenDeltaRatio =
    -0.9 * cacheReadTokens + 0.25 * cacheCreationTokens

  return {
    provider: 'anthropic',
    timestamp: new Date().toISOString(),
    conversationId,
    model,
    usage: {
      cacheCreationTokens,
      cacheReadTokens,
      inputTokens,
      outputTokens,
    },
    cacheHit: cacheReadTokens > 0,
    cacheWrite: cacheCreationTokens > 0,
    estimatedTokenDeltaRatio,
  }
}

/**
 * Emits a CacheMetricsRecord to console in structured JSON form.
 * In production this is picked up by Cloud Run log sink → BigQuery → Observatory.
 *
 * Tagged with `marsys_event_type: cache_metrics` for log-filter routing.
 */
export function emitCacheMetrics(record: CacheMetricsRecord): void {
  console.log(
    JSON.stringify({
      marsys_event_type: 'cache_metrics',
      ...record,
    }),
  )
}

/**
 * Convenience: build + emit in one call from a route handler.
 * Silently no-ops when cache fields are absent (non-caching requests).
 */
export function logCacheMetrics(params: {
  model: string
  conversationId?: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  usage: Record<string, any>
}): void {
  const record = buildCacheMetricsRecord(params)
  if (record) {
    emitCacheMetrics(record)
  }
}
