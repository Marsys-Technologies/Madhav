'use client'

// Direction 3 — single 100%-stacked horizontal bar that summarizes the
// provider/stage cost distribution at a glance. Sits above the per-card grid
// so the user sees the *shape* before the *details*.

import type { BreakdownsResponse } from '@/lib/observatory/types'
import { PROVIDER_COLORS, STAGE_COLORS } from './charts/utils'
import { formatUsd } from './kpi/format'

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
  nim: 'NIM',
}

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

export interface StackedDistributionBarProps {
  data: BreakdownsResponse | null
  loading?: boolean
  dimension?: 'provider' | 'pipeline_stage'
}

export function StackedDistributionBar({
  data,
  loading = false,
  dimension = 'provider',
}: StackedDistributionBarProps) {
  const isStage = dimension === 'pipeline_stage'
  const labelMap = isStage ? STAGE_LABELS : PROVIDER_LABELS
  const colorMap = isStage ? STAGE_COLORS : PROVIDER_COLORS
  const colorOf = (k: string) =>
    (colorMap as Record<string, string>)[k] ?? '#94a3b8'
  const labelOf = (k: string) => labelMap[k] ?? k

  if (loading || !data) {
    return (
      <div className="rounded-2xl border border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] bg-[oklch(0.115_0.012_70)] p-4 animate-pulse">
        <div className="h-4 w-32 rounded bg-[color-mix(in_oklch,var(--brand-gold)_8%,transparent)]" />
        <div className="mt-3 h-9 w-full rounded-lg bg-[color-mix(in_oklch,var(--brand-gold)_6%,transparent)]" />
      </div>
    )
  }

  const total = data.rows.reduce((s, r) => s + r.cost_usd, 0)
  if (total === 0 || data.rows.length === 0) return null

  const segments = [...data.rows]
    .sort((a, b) => b.cost_usd - a.cost_usd)
    .map((r) => ({
      key: r.dim_value,
      cost_usd: r.cost_usd,
      pct: (r.cost_usd / total) * 100,
    }))

  return (
    <div className="rounded-2xl border border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] bg-gradient-to-br from-[oklch(0.13_0.014_75)] to-[oklch(0.105_0.01_70)] p-4">
      <div className="flex items-center justify-between pb-3">
        <span className="bt-label bt-label-upper tracking-[0.16em] text-[color-mix(in_oklch,var(--brand-gold)_70%,white_30%)]">
          Cost distribution
        </span>
        <span className="bt-num text-sm font-light tabular-nums">
          {formatUsd(total)} total
        </span>
      </div>

      <div
        className="flex h-9 w-full overflow-hidden rounded-lg"
        role="img"
        aria-label={`${dimension} cost distribution: ${segments.map((s) => `${labelOf(s.key)} ${s.pct.toFixed(0)}%`).join(', ')}`}
      >
        {segments.map((s) => (
          <div
            key={s.key}
            className="relative h-full transition-all hover:brightness-110"
            style={{ width: `${s.pct}%`, backgroundColor: colorOf(s.key) }}
            title={`${labelOf(s.key)} — ${formatUsd(s.cost_usd)} (${s.pct.toFixed(1)}%)`}
          >
            <span className="absolute inset-0 flex items-center justify-center text-[10px] font-semibold text-black/70 mix-blend-screen">
              {s.pct >= 6 ? `${Math.round(s.pct)}%` : ''}
            </span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-1.5 pt-3 text-[11px]">
        {segments.map((s) => (
          <span key={s.key} className="flex items-center gap-1.5 tabular-nums">
            <span
              aria-hidden="true"
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: colorOf(s.key) }}
            />
            <span
              className="font-semibold uppercase tracking-wider"
              style={{
                color: `color-mix(in oklch, ${colorOf(s.key)} 70%, white 30%)`,
              }}
            >
              {labelOf(s.key)}
            </span>
            <span className="text-[color-mix(in_oklch,var(--brand-gold)_55%,transparent)]">
              {formatUsd(s.cost_usd)}
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
