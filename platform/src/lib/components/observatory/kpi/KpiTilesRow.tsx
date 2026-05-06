'use client'

import type { SummaryResponse } from '@/lib/observatory/types'
import { KpiTile } from './KpiTile'
import { TokenSplitBar } from './TokenSplitBar'
import {
  deltaPct,
  formatLatencyMs,
  formatPct,
  formatRequests,
  formatTokens,
  formatUsd,
} from './format'

export interface KpiTilesRowProps {
  summary?: SummaryResponse
  loading?: boolean
  error?: boolean
  onRetry?: () => void
  mode?: 'hero3' | 'full'
}

type Tone = 'good' | 'bad' | 'neutral'

/** Build the delta pill for a metric. `lowerIsBetter=true` flips the colour
 *  semantics (cost/latency: down is good); otherwise neutral colouring. */
function buildDelta(
  current: number,
  delta: number | undefined,
  lowerIsBetter: boolean,
): { text: string; tone: Tone } | null {
  if (delta === undefined) return null
  const pct = deltaPct(current, delta)
  if (pct === null) return { text: 'new', tone: 'neutral' }
  const arrow = pct > 0 ? '↑' : pct < 0 ? '↓' : '·'
  let tone: Tone = 'neutral'
  if (lowerIsBetter && pct !== 0) tone = pct < 0 ? 'good' : 'bad'
  return { text: `${arrow} ${formatPct(pct)}`, tone }
}

export function KpiTilesRow({
  summary,
  loading = false,
  error = false,
  onRetry,
  mode = 'full',
}: KpiTilesRowProps) {
  const tileBaseProps = { loading, error, onRetry }

  // hero3 mode: 3 large tiles above the fold
  if (mode === 'hero3') {
    const costDelta = summary
      ? buildDelta(summary.total_cost_usd, summary.total_cost_usd_delta, true)
      : null
    const latencyDelta = summary
      ? buildDelta(summary.p50_latency_ms, summary.p50_latency_ms_delta, true)
      : null
    return (
      <div
        data-testid="kpi-tiles-row-hero"
        className="grid grid-cols-1 gap-4 sm:grid-cols-3"
      >
        <KpiTile
          testId="kpi-cost-hero"
          label="Total cost"
          value={summary ? formatUsd(summary.total_cost_usd) : undefined}
          delta={costDelta}
          loading={loading && !summary}
          error={error}
          onRetry={onRetry}
          title="Total computed cost across all LLM calls in the selected period"
          size="hero"
          accent
          hot
        />
        <KpiTile
          testId="kpi-requests-hero"
          label="LLM Calls"
          value={summary ? formatRequests(summary.total_requests) : undefined}
          loading={loading && !summary}
          error={error}
          onRetry={onRetry}
          title="Total number of individual LLM API calls (planner + synthesis)"
          size="hero"
        />
        <KpiTile
          testId="kpi-latency-hero"
          label="Avg latency"
          value={summary ? formatLatencyMs(summary.p50_latency_ms) : undefined}
          secondary={summary ? `p95 ${formatLatencyMs(summary.p95_latency_ms)}` : undefined}
          delta={latencyDelta}
          loading={loading && !summary}
          error={error}
          onRetry={onRetry}
          title="Median (p50) and 95th-percentile LLM call latency"
          size="hero"
        />
      </div>
    )
  }

  if (loading || error || !summary) {
    return (
      <div
        data-testid="kpi-tiles-row"
        className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6"
      >
        <KpiTile testId="kpi-cost" label="Total cost" {...tileBaseProps} />
        <KpiTile testId="kpi-requests" label="Requests" {...tileBaseProps} />
        <KpiTile testId="kpi-tokens" label="Total tokens" {...tileBaseProps} />
        <KpiTile testId="kpi-avg-cost" label="Avg cost / request" {...tileBaseProps} />
        <KpiTile testId="kpi-latency" label="Latency" {...tileBaseProps} />
        <KpiTile testId="kpi-variance" label="Reconciliation variance" {...tileBaseProps} />
      </div>
    )
  }

  const totalTokens =
    summary.total_input_tokens + summary.total_output_tokens + summary.total_cache_tokens
  const totalTokensDelta =
    summary.total_input_tokens_delta !== undefined &&
    summary.total_output_tokens_delta !== undefined &&
    summary.total_cache_tokens_delta !== undefined
      ? summary.total_input_tokens_delta +
        summary.total_output_tokens_delta +
        summary.total_cache_tokens_delta
      : undefined

  const variancePct = summary.reconciliation_variance_pct
  const variance = variancePct === null ? '—' : `${variancePct.toFixed(2)}%`
  const reconThrough = summary.reconciliation_through_date
  const varianceTitle = reconThrough
    ? `Reconciled through ${reconThrough}`
    : 'No reconciliation data yet'

  return (
    <div
      data-testid="kpi-tiles-row"
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6"
    >
      <KpiTile
        testId="kpi-cost"
        label="Total cost"
        value={formatUsd(summary.total_cost_usd)}
        delta={buildDelta(summary.total_cost_usd, summary.total_cost_usd_delta, true)}
      />
      <KpiTile
        testId="kpi-requests"
        label="Requests"
        value={formatRequests(summary.total_requests)}
        delta={buildDelta(summary.total_requests, summary.total_requests_delta, false)}
      />
      <KpiTile
        testId="kpi-tokens"
        label="Total tokens"
        value={formatTokens(totalTokens)}
        delta={buildDelta(totalTokens, totalTokensDelta, false)}
        footer={
          <TokenSplitBar
            inputTokens={summary.total_input_tokens}
            outputTokens={summary.total_output_tokens}
            cacheTokens={summary.total_cache_tokens}
          />
        }
      />
      <KpiTile
        testId="kpi-avg-cost"
        label="Avg cost / request"
        value={formatUsd(summary.avg_cost_per_request)}
        delta={buildDelta(
          summary.avg_cost_per_request,
          summary.avg_cost_per_request_delta,
          true,
        )}
      />
      <KpiTile
        testId="kpi-latency"
        label="Latency"
        value={
          <span>
            <span data-testid="kpi-latency-p50">{formatLatencyMs(summary.p50_latency_ms)}</span>
            <span className="ml-1 text-xs font-normal text-muted-foreground">p50</span>
          </span>
        }
        secondary={
          <span>
            <span data-testid="kpi-latency-p95">{formatLatencyMs(summary.p95_latency_ms)}</span>
            <span className="ml-1 text-xs">p95</span>
          </span>
        }
        delta={buildDelta(summary.p50_latency_ms, summary.p50_latency_ms_delta, true)}
      />
      <KpiTile
        testId="kpi-variance"
        label="Reconciliation variance"
        value={variance}
        title={varianceTitle}
      />
    </div>
  )
}
