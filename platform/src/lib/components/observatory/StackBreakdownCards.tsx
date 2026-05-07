'use client'

// Provider/stage breakdown cards — Direction 2 "Sparkline card".
// Each card carries a 7-day cost trace in the provider/stage color, replacing
// the share-fill bar. Width-resilient single-line secondary metrics.

import { cn } from '@/lib/utils'
import type {
  BreakdownsResponse,
  BreakdownRow,
  TimeseriesResponse,
} from '@/lib/observatory/types'
import { PROVIDER_COLORS, STAGE_COLORS } from './charts/utils'
import { formatUsd, formatTokens, formatLatencyMs } from './kpi/format'

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
  nim: 'NIM',
}

const PROVIDER_ORDER = ['anthropic', 'openai', 'gemini', 'deepseek', 'nim']

const STAGE_LABELS: Record<string, string> = {
  classify: 'Classify',
  retrieve: 'Retrieve',
  compose: 'Compose',
  synthesize: 'Synthesize',
  audit: 'Audit',
  planner: 'Planner',
  title: 'Title',
  history_summary: 'History',
  other: 'Other',
}

const STAGE_ORDER = [
  'classify',
  'retrieve',
  'planner',
  'compose',
  'synthesize',
  'audit',
  'history_summary',
  'title',
  'other',
]

function pct(part: number, total: number): string {
  if (total === 0) return '0%'
  const v = (part / total) * 100
  if (v < 1 && v > 0) return '<1%'
  return `${Math.round(v)}%`
}

function pluralize(n: number, singular: string, plural?: string): string {
  return n === 1 ? singular : (plural ?? `${singular}s`)
}

export function extractSeries(ts: TimeseriesResponse | null | undefined, key: string): number[] {
  if (!ts || ts.buckets.length === 0) return []
  return ts.buckets.map((b) => b.series[key] ?? 0)
}

function SkeletonCard() {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)] bg-[oklch(0.115_0.012_70)] p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-3 w-20 rounded bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
        <div className="h-3 w-10 rounded bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
      </div>
      <div className="h-8 w-32 rounded bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
      <div className="h-8 w-full rounded bg-[color-mix(in_oklch,var(--brand-gold)_6%,transparent)]" />
    </div>
  )
}

interface StackCardProps {
  label: string
  color: string
  row: BreakdownRow
  totalCost: number
  isTop: boolean
  series?: number[]
}

function StackCard({ label, color, row, totalCost, isTop, series }: StackCardProps) {
  const shareLabel = pct(row.cost_usd, totalCost)
  const totalTokens = row.input_tokens + row.output_tokens + row.cache_tokens

  return (
    <div
      className={cn(
        'group relative flex flex-col gap-3 overflow-hidden rounded-2xl border p-4 transition-all',
        'bg-gradient-to-br from-[oklch(0.13_0.014_75)] to-[oklch(0.105_0.01_70)]',
        isTop
          ? 'border-[color-mix(in_oklch,var(--brand-gold)_24%,transparent)] shadow-[0_0_0_1px_color-mix(in_oklch,var(--brand-gold)_8%,transparent)]'
          : 'border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] hover:border-[color-mix(in_oklch,var(--brand-gold)_18%,transparent)]',
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}80` }}
          />
          <span
            className="bt-label bt-label-upper tracking-wider"
            style={{ color: `color-mix(in oklch, ${color} 75%, white 25%)` }}
          >
            {label}
          </span>
        </div>
        <span
          className="text-[10px] font-semibold uppercase tabular-nums tracking-wider"
          style={{ color: `color-mix(in oklch, ${color} 70%, white 30%)` }}
        >
          {shareLabel}
        </span>
      </div>

      <div className="flex items-end justify-between gap-3">
        <p className="bt-num text-3xl font-light tabular-nums text-[var(--brand-gold-cream)] leading-none">
          {formatUsd(row.cost_usd)}
        </p>
        {series && series.length >= 2 ? <Sparkline data={series} color={color} /> : null}
      </div>

      <p className="text-[10px] tabular-nums text-[color-mix(in_oklch,var(--brand-gold)_50%,transparent)]">
        <span className="text-[color-mix(in_oklch,var(--brand-gold)_75%,white_25%)]">
          {row.request_count.toLocaleString()}
        </span>{' '}
        {pluralize(row.request_count, 'call', 'calls')}
        <span className="mx-1.5 text-[color-mix(in_oklch,var(--brand-gold)_25%,transparent)]">·</span>
        <span className="text-[color-mix(in_oklch,var(--brand-gold)_75%,white_25%)]">
          {formatTokens(totalTokens)}
        </span>{' '}
        tok
        <span className="mx-1.5 text-[color-mix(in_oklch,var(--brand-gold)_25%,transparent)]">·</span>
        <span className="text-[color-mix(in_oklch,var(--brand-gold)_75%,white_25%)]">
          {formatLatencyMs(row.avg_latency_ms)}
        </span>{' '}
        p50
      </p>
    </div>
  )
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const W = 88
  const H = 32
  const P = 2
  const max = Math.max(...data, 0.0001)
  const min = Math.min(...data)
  const range = max - min || 1
  const points = data.map((v, i) => {
    const x = P + (i / (data.length - 1)) * (W - 2 * P)
    const y = H - P - ((v - min) / range) * (H - 2 * P)
    return [x, y] as const
  })
  const path = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(' ')
  const area =
    `${path} L${points[points.length - 1][0].toFixed(1)},${H - P} ` +
    `L${points[0][0].toFixed(1)},${H - P} Z`
  const last = points[points.length - 1]

  return (
    <svg
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      className="shrink-0"
      aria-hidden="true"
    >
      <path d={area} fill={color} fillOpacity={0.15} />
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={1.25}
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.85}
      />
      <circle cx={last[0]} cy={last[1]} r={1.75} fill={color} />
    </svg>
  )
}

export interface StackBreakdownCardsProps {
  data: BreakdownsResponse | null
  loading?: boolean
  dimension?: 'provider' | 'pipeline_stage'
  series?: TimeseriesResponse | null
}

export function StackBreakdownCards({
  data,
  loading = false,
  dimension = 'provider',
  series,
}: StackBreakdownCardsProps) {
  const isStage = dimension === 'pipeline_stage'
  const orderList = isStage ? STAGE_ORDER : PROVIDER_ORDER
  const labelMap = isStage ? STAGE_LABELS : PROVIDER_LABELS
  const colorMap = isStage ? STAGE_COLORS : PROVIDER_COLORS

  if (loading || !data) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {orderList.slice(0, 5).map((p) => (
          <SkeletonCard key={p} />
        ))}
      </div>
    )
  }

  if (data.rows.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded-2xl border border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] bg-[oklch(0.115_0.012_70)] text-sm text-[rgba(212,175,55,0.40)]">
        No {isStage ? 'stage' : 'provider'} data in this range
      </div>
    )
  }

  const totalCost = data.rows.reduce((s, r) => s + r.cost_usd, 0)
  const topKey = data.rows.reduce((best, r) => (r.cost_usd > best.cost_usd ? r : best), data.rows[0])
    .dim_value

  const rowMap = new Map(data.rows.map((r) => [r.dim_value, r]))
  const ordered = orderList
    .filter((k) => rowMap.has(k))
    .map((k) => ({ key: k, row: rowMap.get(k)! }))

  for (const r of data.rows) {
    if (!orderList.includes(r.dim_value)) {
      ordered.push({ key: r.dim_value, row: r })
    }
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {ordered.map(({ key, row }) => (
        <StackCard
          key={key}
          label={labelMap[key] ?? key}
          color={(colorMap as Record<string, string>)[key] ?? '#94a3b8'}
          row={row}
          totalCost={totalCost}
          isTop={key === topKey}
          series={series ? extractSeries(series, key) : undefined}
        />
      ))}
    </div>
  )
}
