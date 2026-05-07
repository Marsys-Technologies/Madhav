'use client'

import { cn } from '@/lib/utils'
import type { BreakdownsResponse, BreakdownRow } from '@/lib/observatory/types'
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

function pctNum(part: number, total: number): number {
  if (total === 0) return 0
  return (part / total) * 100
}

function pluralize(n: number, singular: string, plural?: string): string {
  return n === 1 ? singular : (plural ?? `${singular}s`)
}

function SkeletonCard() {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-[rgba(var(--brand-gold-rgb),0.08)] bg-[oklch(0.115_0.012_70)] p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-3 w-20 rounded bg-[rgba(var(--brand-gold-rgb),0.08)]" />
        <div className="h-3 w-10 rounded bg-[rgba(var(--brand-gold-rgb),0.08)]" />
      </div>
      <div className="h-8 w-32 rounded bg-[rgba(var(--brand-gold-rgb),0.08)]" />
      <div className="h-1 w-full rounded bg-[rgba(var(--brand-gold-rgb),0.08)]" />
      <div className="grid grid-cols-3 gap-2">
        <div className="h-8 rounded bg-[rgba(var(--brand-gold-rgb),0.06)]" />
        <div className="h-8 rounded bg-[rgba(var(--brand-gold-rgb),0.06)]" />
        <div className="h-8 rounded bg-[rgba(var(--brand-gold-rgb),0.06)]" />
      </div>
    </div>
  )
}

interface StackCardProps {
  label: string
  color: string
  row: BreakdownRow
  totalCost: number
  isTop: boolean
}

function StackCard({ label, color, row, totalCost, isTop }: StackCardProps) {
  const sharePct = pctNum(row.cost_usd, totalCost)
  const shareLabel = pct(row.cost_usd, totalCost)
  const totalTokens = row.input_tokens + row.output_tokens + row.cache_tokens

  return (
    <div
      className={cn(
        'group relative flex flex-col gap-3 overflow-hidden rounded-2xl border p-4 transition-all',
        'bg-gradient-to-br from-[oklch(0.13_0.014_75)] to-[oklch(0.105_0.01_70)]',
        isTop
          ? 'border-[rgba(var(--brand-gold-rgb),0.24)] shadow-[0_0_0_1px_rgba(var(--brand-gold-rgb),0.08)]'
          : 'border-[rgba(var(--brand-gold-rgb),0.1)] hover:border-[rgba(var(--brand-gold-rgb),0.18)]',
      )}
    >
      {/* Tinted top accent bar — opacity scales with cost share */}
      <span
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-[3px]"
        style={{
          background: `linear-gradient(90deg, ${color} 0%, ${color}80 ${Math.max(8, Math.min(100, sharePct))}%, transparent 100%)`,
        }}
      />

      {/* Subtle radial halo behind the metric — only on top card */}
      {isTop && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full opacity-30"
          style={{ background: `radial-gradient(circle, ${color}40, transparent 70%)` }}
        />
      )}

      {/* Header: dot + label + share */}
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
          className="rounded-full px-2 py-0.5 text-[10px] font-semibold tabular-nums"
          style={{
            backgroundColor: `${color}1A`,
            color: `color-mix(in oklch, ${color} 80%, white 20%)`,
            boxShadow: `inset 0 0 0 1px ${color}33`,
          }}
        >
          {shareLabel}
        </span>
      </div>

      {/* Primary: cost */}
      <p className="bt-num text-3xl font-light tabular-nums text-[var(--brand-gold-cream)] leading-none">
        {formatUsd(row.cost_usd)}
      </p>

      {/* Share bar — subtle, full-width */}
      <div className="relative h-[3px] w-full overflow-hidden rounded-full bg-[rgba(var(--brand-gold-rgb),0.06)]">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.max(2, sharePct)}%`, backgroundColor: color, opacity: 0.7 }}
        />
      </div>

      {/* Secondary metrics — three-column grid for visual rhythm */}
      <div className="grid grid-cols-3 gap-2 pt-1 text-[10px] text-[rgba(212,175,55,0.45)]">
        <Metric value={row.request_count.toLocaleString()} label={pluralize(row.request_count, 'call', 'calls')} />
        <Metric value={formatTokens(totalTokens)} label="tokens" />
        <Metric value={formatLatencyMs(row.avg_latency_ms)} label="p50" />
      </div>
    </div>
  )
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="bt-num text-sm font-medium tabular-nums text-[var(--brand-gold-cream)]">
        {value}
      </span>
      <span className="bt-label-upper tracking-wider">{label}</span>
    </div>
  )
}

// ── Public surfaces ──────────────────────────────────────────────────────────

export interface StackBreakdownCardsProps {
  data: BreakdownsResponse | null
  loading?: boolean
  /** Which dimension the rows belong to; controls labels + colors. */
  dimension?: 'provider' | 'pipeline_stage'
}

export function StackBreakdownCards({
  data,
  loading = false,
  dimension = 'provider',
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
      <div className="flex h-24 items-center justify-center rounded-2xl border border-[rgba(var(--brand-gold-rgb),0.1)] bg-[oklch(0.115_0.012_70)] text-sm text-[rgba(212,175,55,0.40)]">
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
        />
      ))}
    </div>
  )
}
