'use client'

/**
 * CacheMetricsTile.tsx — D-S6 R11.D
 *
 * Observatory dashboard tile: cache hit rate × provider × per-day.
 *
 * Displays:
 *   - Hit rate per provider (explicit_4bp / cached_content_api / automatic / implicit / n/a)
 *   - Cost savings estimate per provider
 *   - NVIDIA shows "n/a" (null promptCaching in manifest)
 *
 * Data is provided by the parent via the `summaries` prop (computed by
 * cache_aggregation.ts::computeProviderSummaries). The tile is a pure
 * display component — no data fetching.
 *
 * Click-path: Observatory Overview → "Cache Metrics" tile → provider row
 * expands to show per-day time series (per-day detail is post-D-S6 scope).
 */

import type { CacheProviderSummary } from '@/lib/observatory/cache_aggregation'
import { formatHitRate, formatCostSavings } from '@/lib/observatory/cache_aggregation'

interface CacheMetricsTileProps {
  summaries: CacheProviderSummary[]
  /** ISO date range for the displayed window, e.g. "2026-05-15 → 2026-05-22". */
  dateRange?: string
  className?: string
}

/** Provider display names. */
const PROVIDER_DISPLAY: Record<string, string> = {
  anthropic: 'Anthropic',
  google: 'Google',
  openai: 'OpenAI',
  deepseek: 'DeepSeek',
  nvidia: 'NVIDIA',
}

/** Cache mode display labels. */
const CACHE_MODE_LABEL: Record<string, string> = {
  explicit_4bp: '4-breakpoint',
  cached_content_api: 'cachedContent',
  automatic: 'automatic',
  implicit: 'implicit',
}

export function CacheMetricsTile({
  summaries,
  dateRange,
  className = '',
}: CacheMetricsTileProps) {
  return (
    <div
      className={`rounded-lg border border-border bg-card p-4 ${className}`}
      data-testid="cache-metrics-tile"
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground" data-testid="cache-tile-title">
          Cache Hit Rates
        </h3>
        {dateRange && (
          <span className="text-xs text-muted-foreground" data-testid="cache-tile-date-range">
            {dateRange}
          </span>
        )}
      </div>

      <table className="w-full text-xs" data-testid="cache-metrics-table">
        <thead>
          <tr className="border-b border-border text-muted-foreground">
            <th className="pb-2 text-left font-medium">Provider</th>
            <th className="pb-2 text-left font-medium">Mode</th>
            <th className="pb-2 text-right font-medium">Hit Rate</th>
            <th className="pb-2 text-right font-medium">Cost Δ</th>
            <th className="pb-2 text-right font-medium">Requests</th>
          </tr>
        </thead>
        <tbody>
          {summaries.map((row) => (
            <CacheMetricsRow key={row.provider} row={row} />
          ))}
        </tbody>
      </table>

      <p className="mt-3 text-[10px] text-muted-foreground">
        Hit Rate = requests with ≥1 cached token / total. Cost Δ = estimated savings vs. no-cache
        baseline. NVIDIA: no caching in Marsys NIM config.
      </p>
    </div>
  )
}

function CacheMetricsRow({ row }: { row: CacheProviderSummary }) {
  const providerName = PROVIDER_DISPLAY[row.provider] ?? row.provider
  const modeLabel = row.cacheMode ? (CACHE_MODE_LABEL[row.cacheMode] ?? row.cacheMode) : 'n/a'
  const hitRateStr = row.supported ? formatHitRate(row.overallHitRate) : 'n/a'
  const costStr = formatCostSavings(row.avgCostSavingsRatio, row.supported)

  return (
    <tr
      className="border-b border-border/50 last:border-0"
      data-testid={`cache-metrics-row-${row.provider}`}
    >
      <td className="py-1.5 font-medium text-foreground">{providerName}</td>
      <td className="py-1.5 text-muted-foreground">
        <span
          className={`rounded px-1 py-0.5 text-[10px] ${
            row.supported
              ? 'bg-brand-gold/10 text-brand-gold'
              : 'bg-muted text-muted-foreground'
          }`}
          data-testid={`cache-mode-badge-${row.provider}`}
        >
          {modeLabel}
        </span>
      </td>
      <td
        className="py-1.5 text-right tabular-nums text-foreground"
        data-testid={`hit-rate-${row.provider}`}
      >
        {hitRateStr}
      </td>
      <td
        className={`py-1.5 text-right tabular-nums ${
          row.supported && row.avgCostSavingsRatio < 0
            ? 'text-green-600 dark:text-green-400'
            : 'text-muted-foreground'
        }`}
        data-testid={`cost-savings-${row.provider}`}
      >
        {costStr}
      </td>
      <td className="py-1.5 text-right tabular-nums text-muted-foreground">
        {row.supported ? row.totalRequests.toLocaleString() : '—'}
      </td>
    </tr>
  )
}
