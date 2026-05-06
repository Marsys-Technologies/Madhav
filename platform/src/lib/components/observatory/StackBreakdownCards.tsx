'use client'

import { cn } from '@/lib/utils'
import type { BreakdownsResponse, BreakdownRow } from '@/lib/observatory/types'
import { PROVIDER_COLORS } from './charts/utils'
import { formatUsd, formatTokens, formatRequests } from './kpi/format'

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
  nim: 'NIM',
}

const PROVIDER_ORDER = ['anthropic', 'openai', 'gemini', 'deepseek', 'nim']

function pct(part: number, total: number): string {
  if (total === 0) return '0%'
  return `${Math.round((part / total) * 100)}%`
}

function ProviderCrest({ color }: { color: string }) {
  return (
    <span
      aria-hidden="true"
      className="relative inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
      style={{
        background: `radial-gradient(circle at 30% 30%, ${color}55, ${color}10 70%, transparent 100%)`,
        boxShadow: `inset 0 0 0 1px ${color}55`,
      }}
    >
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
    </span>
  )
}

function SkeletonCard() {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] bg-[oklch(0.115_0.012_70)] p-4 animate-pulse">
      <div className="flex items-center gap-2">
        <div className="h-7 w-7 rounded-full bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
        <div className="h-3 w-20 rounded bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
      </div>
      <div className="h-7 w-28 rounded bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
      <div className="h-3 w-24 rounded bg-[color-mix(in_oklch,var(--brand-gold)_6%,transparent)]" />
    </div>
  )
}

interface StackCardProps {
  provider: string
  row: BreakdownRow
  totalCost: number
  isTop: boolean
}

function StackCard({ provider, row, totalCost, isTop }: StackCardProps) {
  const color = PROVIDER_COLORS[provider as keyof typeof PROVIDER_COLORS] ?? '#d4af37'
  const label = PROVIDER_LABELS[provider] ?? provider
  const share = pct(row.cost_usd, totalCost)
  const totalTokens = row.input_tokens + row.output_tokens + row.cache_tokens

  return (
    <div
      className={cn(
        'group relative flex flex-col gap-3 overflow-hidden rounded-xl border p-4 transition-all',
        isTop
          ? 'border-[color-mix(in_oklch,var(--brand-gold)_30%,transparent)] bg-[oklch(0.13_0.014_75)]'
          : 'border-[color-mix(in_oklch,var(--brand-gold)_12%,transparent)] bg-[oklch(0.115_0.012_70)] hover:border-[color-mix(in_oklch,var(--brand-gold)_22%,transparent)]',
      )}
    >
      {/* Tinted top accent bar */}
      <span
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-[2px]"
        style={{ background: `linear-gradient(90deg, ${color}, transparent)` }}
      />

      {/* Header: crest + label + share */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ProviderCrest color={color} />
          <span className="bt-label bt-label-upper" style={{ color }}>
            {label}
          </span>
        </div>
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-semibold tabular-nums"
          style={{ backgroundColor: `${color}1A`, color, boxShadow: `inset 0 0 0 1px ${color}33` }}
        >
          {share}
        </span>
      </div>

      {/* Primary: cost */}
      <p className="bt-num text-[var(--brand-gold-cream)] leading-none">
        {formatUsd(row.cost_usd)}
      </p>

      {/* Secondary metrics */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-[rgba(212,175,55,0.55)]">
        <span>
          <span className="text-[var(--brand-gold-cream)] tabular-nums">{formatRequests(row.request_count)}</span>{' '}
          calls
        </span>
        <span>
          <span className="text-[var(--brand-gold-cream)] tabular-nums">{formatTokens(totalTokens)}</span>{' '}
          tokens
        </span>
        <span>
          <span className="text-[var(--brand-gold-cream)] tabular-nums">{Math.round(row.avg_latency_ms)}ms</span>{' '}
          p50
        </span>
      </div>

      {/* Token split mini-bar */}
      {totalTokens > 0 && (
        <div className="flex h-1 w-full overflow-hidden rounded-full bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]">
          <div className="h-full" style={{ width: pct(row.input_tokens, totalTokens), backgroundColor: color, opacity: 0.95 }} />
          <div className="h-full" style={{ width: pct(row.output_tokens, totalTokens), backgroundColor: color, opacity: 0.55 }} />
          <div className="h-full" style={{ width: pct(row.cache_tokens, totalTokens), backgroundColor: color, opacity: 0.25 }} />
        </div>
      )}
    </div>
  )
}

export interface StackBreakdownCardsProps {
  data: BreakdownsResponse | null
  loading?: boolean
}

export function StackBreakdownCards({ data, loading = false }: StackBreakdownCardsProps) {
  if (loading || !data) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {PROVIDER_ORDER.map((p) => <SkeletonCard key={p} />)}
      </div>
    )
  }

  if (data.rows.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded-xl border border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] bg-[oklch(0.115_0.012_70)] text-sm text-[rgba(212,175,55,0.40)]">
        No provider data in this range
      </div>
    )
  }

  const totalCost = data.rows.reduce((s, r) => s + r.cost_usd, 0)
  const topProvider = data.rows.reduce((best, r) => (r.cost_usd > best.cost_usd ? r : best), data.rows[0]).dim_value

  const rowMap = new Map(data.rows.map((r) => [r.dim_value, r]))
  const ordered = PROVIDER_ORDER
    .filter((p) => rowMap.has(p))
    .map((p) => ({ provider: p, row: rowMap.get(p)! }))

  for (const r of data.rows) {
    if (!PROVIDER_ORDER.includes(r.dim_value)) {
      ordered.push({ provider: r.dim_value, row: r })
    }
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {ordered.map(({ provider, row }) => (
        <StackCard
          key={provider}
          provider={provider}
          row={row}
          totalCost={totalCost}
          isTop={provider === topProvider}
        />
      ))}
    </div>
  )
}
