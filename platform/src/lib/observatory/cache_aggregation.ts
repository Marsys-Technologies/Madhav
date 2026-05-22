import 'server-only'

/**
 * cache_aggregation.ts — D-S6 R11.D
 *
 * Aggregation logic for the Observatory Cache Metrics Tile.
 *
 * Aggregates per-request cache telemetry from D-S1..D-S4 into:
 *   - Cache hit rate per provider per day
 *   - Cost savings estimate per provider
 *   - Provider-level summary (null caching → "n/a")
 *
 * Source data: structured log records tagged with `marsys_event_type: cache_metrics`
 * or `marsys_event_type: gemini_cache_metrics` (D-S1 + D-S2 emitters).
 * In production these flow through Cloud Run → Cloud Logging → BigQuery.
 *
 * For the D-S6 Observatory tile, the aggregation runs against the in-memory
 * telemetry accumulated during the current session (full BigQuery pipeline is
 * a post-D-S6 operator item).
 */

/** All 5 provider IDs in the Marsys capability matrix. */
export const ALL_PROVIDER_IDS = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia'] as const
export type ProviderIdAll = typeof ALL_PROVIDER_IDS[number]

/**
 * Per-provider caching mode, mirroring the manifest promptCaching field.
 * Used by the tile to render appropriate labels and "n/a" rows.
 */
export const PROVIDER_CACHE_MODE: Record<ProviderIdAll, string | null> = {
  anthropic: 'explicit_4bp',
  google: 'cached_content_api',
  openai: 'automatic',
  deepseek: 'implicit',
  nvidia: null,
}

/**
 * A single aggregated cache metrics record for one provider × one date bucket.
 */
export interface CacheAggregationRow {
  provider: ProviderIdAll
  /** ISO date string (YYYY-MM-DD). */
  date: string
  /** Total requests in this bucket. */
  totalRequests: number
  /** Requests with cache hit. */
  hitRequests: number
  /** Hit rate: hitRequests / totalRequests. */
  hitRate: number
  /** Estimated token-units saved (sum of negative estimatedTokenDeltaRatio from D-S1). */
  estimatedTokenSavings: number
  /** Cost saving ratio (provider-specific). */
  estimatedCostSavingsRatio: number
  /** Cache mode for this provider (from manifest). */
  cacheMode: string | null
}

/**
 * Summary row for the tile's per-provider totals.
 */
export interface CacheProviderSummary {
  provider: ProviderIdAll
  cacheMode: string | null
  /** "n/a" when cacheMode is null (NVIDIA). */
  supported: boolean
  totalRequests: number
  totalHitRequests: number
  overallHitRate: number
  /** Estimated fraction of input cost saved across all hits. */
  avgCostSavingsRatio: number
}

/**
 * Compute per-provider cache summaries from an array of raw row data.
 * This is the primary function called by the tile component.
 *
 * Input rows can come from in-memory accumulation or a BigQuery query result.
 * Each row must have: provider, hitRequests, totalRequests, estimatedCostSavingsRatio.
 */
export function computeProviderSummaries(
  rows: Array<{
    provider: string
    hitRequests: number
    totalRequests: number
    estimatedCostSavingsRatio: number
  }>,
): CacheProviderSummary[] {
  // Group by provider
  const grouped: Record<string, { hits: number; total: number; savingsSum: number }> = {}

  for (const row of rows) {
    if (!grouped[row.provider]) {
      grouped[row.provider] = { hits: 0, total: 0, savingsSum: 0 }
    }
    grouped[row.provider].hits += row.hitRequests
    grouped[row.provider].total += row.totalRequests
    grouped[row.provider].savingsSum += row.estimatedCostSavingsRatio
  }

  return ALL_PROVIDER_IDS.map((provider): CacheProviderSummary => {
    const cacheMode = PROVIDER_CACHE_MODE[provider]
    const grp = grouped[provider] ?? { hits: 0, total: 0, savingsSum: 0 }

    return {
      provider,
      cacheMode,
      supported: cacheMode !== null,
      totalRequests: grp.total,
      totalHitRequests: grp.hits,
      overallHitRate: grp.total > 0 ? grp.hits / grp.total : 0,
      avgCostSavingsRatio: grp.total > 0 ? grp.savingsSum / grp.total : 0,
    }
  })
}

/**
 * Formats a cache hit rate as a percentage string (e.g. "84.3%").
 */
export function formatHitRate(rate: number): string {
  if (rate === 0) return '0%'
  return `${(rate * 100).toFixed(1)}%`
}

/**
 * Formats an estimated cost savings ratio as a "–X%" string (negative = savings).
 * Returns "n/a" for unsupported providers.
 */
export function formatCostSavings(ratio: number, supported: boolean): string {
  if (!supported) return 'n/a'
  if (ratio === 0) return '0%'
  const pct = (ratio * 100).toFixed(1)
  return ratio < 0 ? `–${Math.abs(Number(pct)).toFixed(1)}%` : `+${pct}%`
}
