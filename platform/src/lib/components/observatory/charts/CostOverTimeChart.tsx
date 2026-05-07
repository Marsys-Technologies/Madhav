'use client'

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { TimeseriesResponse } from '@/lib/observatory/types'

import {
  colorForDimension,
  formatBucketTime,
  formatCostUSD,
} from './utils'

export interface DrillDownTarget {
  from: string
  to: string
  dimension: 'provider' | 'pipeline_stage'
  dimensionValue: string
}

export interface CostOverTimeChartProps {
  data: TimeseriesResponse | null
  dimension: 'provider' | 'pipeline_stage'
  granularity: 'hour' | 'day' | 'week'
  loading?: boolean
  error?: Error | null
  onRetry?: () => void
  /** Wired by S1.13 — navigates to events filtered to (from, to, dimension, value). */
  onDrillDown?: (target: DrillDownTarget) => void
}

/** Flatten the buckets into a recharts-friendly row-per-bucket shape. */
export function flattenTimeseries(data: TimeseriesResponse): {
  chartRows: Array<Record<string, number | string>>
  seriesValues: string[]
} {
  const seen = new Set<string>()
  for (const b of data.buckets) {
    for (const k of Object.keys(b.series)) seen.add(k)
  }
  const seriesValues = [...seen].sort()
  const chartRows = data.buckets.map((b) => {
    const row: Record<string, number | string> = { time: b.time }
    let total = 0
    for (const k of seriesValues) {
      const v = b.series[k] ?? 0
      row[k] = v
      total += v
    }
    row.__total = total
    return row
  })
  return { chartRows, seriesValues }
}

/** Compute the (from, to) window for a clicked bucket given its index + granularity. */
export function bucketWindow(
  buckets: TimeseriesResponse['buckets'],
  bucketIndex: number,
  granularity: 'hour' | 'day' | 'week',
): { from: string; to: string } {
  const cur = buckets[bucketIndex]
  if (!cur) return { from: '', to: '' }
  const next = buckets[bucketIndex + 1]
  if (next) return { from: cur.time, to: next.time }
  const start = new Date(cur.time)
  const ms =
    granularity === 'hour'
      ? 3_600_000
      : granularity === 'day'
        ? 86_400_000
        : 7 * 86_400_000
  return { from: cur.time, to: new Date(start.getTime() + ms).toISOString() }
}

export function buildDrillDownTarget(
  buckets: TimeseriesResponse['buckets'],
  bucketIndex: number,
  granularity: 'hour' | 'day' | 'week',
  dimension: 'provider' | 'pipeline_stage',
  dimensionValue: string,
): DrillDownTarget {
  const { from, to } = bucketWindow(buckets, bucketIndex, granularity)
  return { from, to, dimension, dimensionValue }
}

interface CostTooltipPayloadEntry {
  name?: string
  value?: number
  color?: string
}

interface CostTooltipProps {
  active?: boolean
  payload?: CostTooltipPayloadEntry[]
  label?: string
  granularity: 'hour' | 'day' | 'week'
}

function CostTooltip({ active, payload, label, granularity }: CostTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  const total = payload.reduce((sum, p) => sum + (p.value ?? 0), 0)
  return (
    <div
      data-testid="cost-over-time-tooltip"
      className="rounded-lg border border-[rgba(212,175,55,0.12)] bg-[oklch(0.13_0.008_70)] p-2 text-xs shadow-lg"
    >
      <div className="mb-1 font-medium">
        {label ? formatBucketTime(label, granularity) : ''}
      </div>
      {payload.map((p) => (
        <div key={p.name ?? ''} className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="inline-block h-2 w-2 rounded-sm"
            style={{ backgroundColor: p.color }}
          />
          <span className="flex-1">{p.name}</span>
          <span className="tabular-nums">{formatCostUSD(p.value ?? 0)}</span>
        </div>
      ))}
      <div className="mt-1 border-t pt-1 text-right font-medium tabular-nums">
        Total: {formatCostUSD(total)}
      </div>
    </div>
  )
}

interface AreaChartClickState {
  activeTooltipIndex?: number
  activeLabel?: string
  activePayload?: Array<{ dataKey?: string; name?: string }>
}

export function CostOverTimeChart({
  data,
  dimension,
  granularity,
  loading = false,
  error = null,
  onRetry,
  onDrillDown,
}: CostOverTimeChartProps) {
  if (loading) {
    return (
      <div
        data-testid="cost-over-time-loading"
        role="status"
        aria-live="polite"
        className="h-72 w-full animate-pulse rounded bg-muted"
      />
    )
  }

  if (error) {
    return (
      <div
        data-testid="cost-over-time-error"
        role="alert"
        className="flex h-72 w-full flex-col items-center justify-center gap-2 rounded border border-destructive/30 p-4 text-sm"
      >
        <p>Failed to load cost timeseries.</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="rounded border px-3 py-1 text-xs hover:bg-muted"
          >
            Retry
          </button>
        )}
      </div>
    )
  }

  if (!data || data.buckets.length === 0) {
    return (
      <div
        data-testid="cost-over-time-empty"
        className="flex h-72 w-full items-center justify-center rounded border text-sm text-muted-foreground"
      >
        No data in this range
      </div>
    )
  }

  const { chartRows, seriesValues } = flattenTimeseries(data)

  const handleChartClick = (state: AreaChartClickState | null | undefined) => {
    if (!onDrillDown || !state) return
    const idx = state.activeTooltipIndex
    if (typeof idx !== 'number' || idx < 0) return
    // Best-effort series resolution: recharts surfaces the topmost-stacked
    // series first in `activePayload`. S1.13 may refine to per-Y-band lookup.
    const topSeries = state.activePayload?.[0]
    const dimensionValue = topSeries?.dataKey ?? topSeries?.name ?? seriesValues[0] ?? ''
    onDrillDown(
      buildDrillDownTarget(
        data.buckets,
        idx,
        granularity,
        dimension,
        dimensionValue,
      ),
    )
  }

  return (
    <div
      data-testid="cost-over-time-chart"
      data-dimension={dimension}
      data-series-count={seriesValues.length}
      className="h-72 w-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={chartRows}
          onClick={handleChartClick as never}
          style={{ background: 'transparent' }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(212,175,55,0.08)" />
          <XAxis
            dataKey="time"
            tickFormatter={(v: string) => formatBucketTime(v, granularity)}
            minTickGap={24}
            stroke="rgba(212,175,55,0.15)"
            tick={{ fill: 'rgba(212,175,55,0.40)', fontSize: 11 }}
          />
          <YAxis
            tickFormatter={(v: number) => formatCostUSD(v)}
            width={84}
            stroke="rgba(212,175,55,0.15)"
            tick={{ fill: 'rgba(212,175,55,0.40)', fontSize: 11 }}
          />
          <Tooltip
            content={(props) => {
              const tooltipProps = props as unknown as Omit<
                CostTooltipProps,
                'granularity'
              >
              return <CostTooltip {...tooltipProps} granularity={granularity} />
            }}
          />
          <Legend wrapperStyle={{ color: 'rgba(212,175,55,0.60)', fontSize: '11px' }} />
          {seriesValues.map((value) => (
            <Area
              key={value}
              type="monotone"
              dataKey={value}
              name={value}
              stackId="cost"
              stroke={colorForDimension(dimension, value)}
              fill={colorForDimension(dimension, value)}
              fillOpacity={0.55}
            />
          ))}
          {/* Total line — answers "is the absolute total trending?" while the
              stacks answer "who's spending?". */}
          <Line
            type="monotone"
            dataKey="__total"
            name="total"
            stroke="var(--brand-gold-cream)"
            strokeWidth={1.25}
            strokeOpacity={0.9}
            dot={{ r: 2, fill: 'var(--brand-gold-cream)', strokeWidth: 0 }}
            activeDot={{ r: 3, fill: 'var(--brand-gold-cream)' }}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
