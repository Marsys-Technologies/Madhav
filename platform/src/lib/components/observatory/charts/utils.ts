// Shared chart utilities — color palettes + value formatters used by every
// Observatory chart so that a given provider/stage paints the same color
// across CostOverTime, CostByModel, CacheSavings, and any future chart.
//
// Authored by USTAD_S1_11_OBSERVATORY_CHARTS for sub-phase O.1.

import type {
  LlmPipelineStage,
  LlmProvider,
} from '@/lib/db/schema/observatory'

export const PROVIDER_COLORS: Record<LlmProvider, string> = {
  anthropic: '#d97757',
  openai: '#10a37f',
  gemini: '#4285f4',
  deepseek: '#7e57c2',
  nim: '#76b900',
}

export const STAGE_COLORS: Record<LlmPipelineStage, string> = {
  classify: '#6366f1',
  compose: '#06b6d4',
  retrieve: '#f59e0b',
  synthesize: '#10b981',
  audit: '#ef4444',
  other: '#94a3b8',
  // Added by migration 041
  planner: '#a78bfa',
  title: '#f472b6',
  history_summary: '#34d399',
}

const FALLBACK_COLOR = '#64748b'

export function colorForProvider(provider: string): string {
  return PROVIDER_COLORS[provider as LlmProvider] ?? FALLBACK_COLOR
}

export function colorForStage(stage: string): string {
  return STAGE_COLORS[stage as LlmPipelineStage] ?? FALLBACK_COLOR
}

export function colorForDimension(
  dimension: 'provider' | 'pipeline_stage',
  value: string,
): string {
  return dimension === 'provider' ? colorForProvider(value) : colorForStage(value)
}

const COST_FORMATTER_6DP = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 6,
  maximumFractionDigits: 6,
})

const COST_FORMATTER_2DP = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** Six-decimal USD formatting; sub-cent values keep their precision. */
export function formatCostUSD(n: number): string {
  if (!Number.isFinite(n)) return '$0.000000'
  if (Math.abs(n) >= 1) return `$${COST_FORMATTER_2DP.format(n)}`
  return `$${COST_FORMATTER_6DP.format(n)}`
}

export function formatTokenCount(n: number): string {
  if (!Number.isFinite(n) || n <= 0) return '0'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`
  return String(Math.round(n))
}

/** Format a bucket-start ISO timestamp per the timeseries granularity. */
export function formatBucketTime(
  iso: string,
  granularity: 'hour' | 'day' | 'week',
): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  if (granularity === 'hour') {
    const hh = String(d.getHours()).padStart(2, '0')
    return `${hh}:00`
  }
  // Both day and week buckets render as "Mon D" — week buckets are simply
  // the Monday-anchor day label for the bucket.
  const month = d.toLocaleString('en-US', { month: 'short' })
  return `${month} ${d.getDate()}`
}
