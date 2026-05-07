'use client'

// Cost by model — bee-swarm reimagining.
// X axis: $/call. Bubble area: call count. Color: provider.
// Replaces the long horizontal bar with a layout that surfaces outliers
// (the one expensive-per-call model) instead of burying them in a sorted list.

import * as React from 'react'

import type { BreakdownsResponse } from '@/lib/observatory/types'

import { colorForDimension, colorForProvider, formatCostUSD, formatTokenCount } from './utils'

const TOP_N = 15
const OTHER_COLOR = '#94a3b8'

export interface CostByModelChartProps {
  data: BreakdownsResponse | null
  dimension?: 'provider' | 'pipeline_stage' | 'model'
  loading?: boolean
  error?: Error | null
  onRetry?: () => void
}

export interface CostByModelRow {
  label: string
  cost_usd: number
  request_count: number
  isOther: boolean
}

/** Sort by cost desc, take top N, roll the remainder up into "Other (k models)". */
export function rollUpModels(data: BreakdownsResponse): CostByModelRow[] {
  const sorted = [...data.rows].sort((a, b) => b.cost_usd - a.cost_usd)
  if (sorted.length <= TOP_N) {
    return sorted.map((r) => ({
      label: r.dim_value,
      cost_usd: r.cost_usd,
      request_count: r.request_count,
      isOther: false,
    }))
  }
  const top = sorted.slice(0, TOP_N).map((r) => ({
    label: r.dim_value,
    cost_usd: r.cost_usd,
    request_count: r.request_count,
    isOther: false,
  }))
  const rest = sorted.slice(TOP_N)
  const other: CostByModelRow = {
    label: `Other (${rest.length} models)`,
    cost_usd: rest.reduce((s, r) => s + r.cost_usd, 0),
    request_count: rest.reduce((s, r) => s + r.request_count, 0),
    isOther: true,
  }
  return [...top, other]
}

/** Lightweight model-name → provider inference for color coding when dimension='model'. */
function inferProvider(modelLabel: string): string {
  const lc = modelLabel.toLowerCase()
  if (lc.startsWith('claude')) return 'anthropic'
  if (lc.startsWith('gpt') || lc.startsWith('o1') || lc.startsWith('o3') || lc.startsWith('o4')) return 'openai'
  if (lc.startsWith('gemini')) return 'gemini'
  if (lc.startsWith('deepseek')) return 'deepseek'
  if (lc.includes('llama') || lc.includes('mistral') || lc.startsWith('nim')) return 'nim'
  return ''
}

function colorFor(row: CostByModelRow, dimension: CostByModelChartProps['dimension']): string {
  if (row.isOther) return OTHER_COLOR
  if (dimension === 'provider') return colorForProvider(row.label)
  if (dimension === 'pipeline_stage') return colorForDimension('pipeline_stage', row.label)
  const inferred = inferProvider(row.label)
  return inferred ? colorForProvider(inferred) : OTHER_COLOR
}

interface Bubble {
  row: CostByModelRow
  cx: number
  cy: number
  r: number
  fill: string
}

export function CostByModelChart({
  data,
  dimension = 'model',
  loading = false,
  error = null,
  onRetry,
}: CostByModelChartProps) {
  const [hover, setHover] = React.useState<number | null>(null)

  if (loading) {
    return (
      <div
        data-testid="cost-by-model-loading"
        role="status"
        aria-live="polite"
        className="h-96 w-full animate-pulse rounded bg-muted"
      />
    )
  }

  if (error) {
    return (
      <div
        data-testid="cost-by-model-error"
        role="alert"
        className="flex h-96 w-full flex-col items-center justify-center gap-2 rounded border border-destructive/30 p-4 text-sm"
      >
        <p>Failed to load model breakdown.</p>
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

  if (!data || data.rows.length === 0) {
    return (
      <div
        data-testid="cost-by-model-empty"
        className="flex h-72 w-full items-center justify-center rounded border text-sm text-muted-foreground"
      >
        No data in this range
      </div>
    )
  }

  const rows = rollUpModels(data).filter((r) => r.request_count > 0)
  const W = 880
  const H = 320
  const PAD_L = 56
  const PAD_R = 24
  const PAD_T = 32
  const PAD_B = 40
  const inner = { w: W - PAD_L - PAD_R, h: H - PAD_T - PAD_B }

  const cps = rows.map((r) => r.cost_usd / Math.max(1, r.request_count))
  const maxCps = Math.max(...cps, 0.0001) * 1.1
  const maxCalls = Math.max(...rows.map((r) => r.request_count), 1)

  const xOf = (v: number) => PAD_L + (v / maxCps) * inner.w
  const radius = (calls: number) => 5 + Math.sqrt((calls / maxCalls) * 100) * 1.6
  // Deterministic vertical jitter — sin(seed) keyed on row index.
  const yOf = (i: number) =>
    PAD_T + inner.h / 2 + Math.sin(i * 17.31) * (inner.h / 2 - 22)

  const bubbles: Bubble[] = rows.map((r, i) => ({
    row: r,
    cx: xOf(cps[i]),
    cy: yOf(i),
    r: radius(r.request_count),
    fill: colorFor(r, dimension),
  }))

  const ticks = [0, 0.25, 0.5, 0.75, 1]

  return (
    <div
      data-testid="cost-by-model-chart"
      data-row-count={rows.length}
      className="w-full"
    >
      <div className="relative w-full" style={{ aspectRatio: `${W} / ${H}` }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          height="100%"
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label="Models plotted by cost-per-call (x) and call volume (size)"
        >
          {ticks.map((t) => (
            <line
              key={t}
              x1={xOf(maxCps * t)}
              x2={xOf(maxCps * t)}
              y1={PAD_T}
              y2={H - PAD_B}
              stroke="rgba(212,175,55,0.08)"
              strokeDasharray="2 4"
            />
          ))}
          <line
            x1={PAD_L}
            x2={W - PAD_R}
            y1={PAD_T + inner.h / 2}
            y2={PAD_T + inner.h / 2}
            stroke="rgba(212,175,55,0.12)"
          />

          {bubbles.map((b, i) => (
            <g
              key={`${b.row.label}-${i}`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover((h) => (h === i ? null : h))}
            >
              <circle
                cx={b.cx}
                cy={b.cy}
                r={b.r}
                fill={b.fill}
                fillOpacity={hover === i ? 0.6 : 0.35}
                stroke={b.fill}
                strokeWidth={1.25}
              />
              <text
                x={b.cx + b.r + 5}
                y={b.cy + 3}
                fontSize={10}
                fill="var(--brand-gold-cream)"
                fillOpacity={hover === i ? 1 : 0.75}
              >
                {b.row.label}
              </text>
            </g>
          ))}

          {ticks.map((t) => (
            <text
              key={`tick-${t}`}
              x={xOf(maxCps * t)}
              y={H - PAD_B + 16}
              textAnchor="middle"
              fontSize={10}
              fill="rgba(212,175,55,0.5)"
            >
              {formatCostUSD(maxCps * t)}
            </text>
          ))}
          <text x={PAD_L} y={H - 6} fontSize={10} fill="rgba(212,175,55,0.4)">
            ← cheap per call
          </text>
          <text
            x={W - PAD_R}
            y={H - 6}
            textAnchor="end"
            fontSize={10}
            fill="rgba(212,175,55,0.4)"
          >
            expensive per call →
          </text>
        </svg>

        {hover !== null && bubbles[hover] && (
          <div
            data-testid="cost-by-model-tooltip"
            className="pointer-events-none absolute rounded-lg border border-[rgba(212,175,55,0.12)] bg-[oklch(0.13_0.008_70)] p-2 text-xs shadow-lg"
            style={{
              left: `${(bubbles[hover].cx / W) * 100}%`,
              top: `${(bubbles[hover].cy / H) * 100}%`,
              transform: 'translate(-50%, -120%)',
            }}
          >
            <div className="mb-1 font-medium">{bubbles[hover].row.label}</div>
            <div className="flex justify-between gap-4">
              <span>Cost</span>
              <span className="tabular-nums">{formatCostUSD(bubbles[hover].row.cost_usd)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Requests</span>
              <span className="tabular-nums">{formatTokenCount(bubbles[hover].row.request_count)}</span>
            </div>
            <div className="flex justify-between gap-4 border-t border-[rgba(212,175,55,0.12)] pt-1 text-[var(--brand-gold-cream)]">
              <span>$/call</span>
              <span className="tabular-nums">
                {formatCostUSD(bubbles[hover].row.cost_usd / Math.max(1, bubbles[hover].row.request_count))}
              </span>
            </div>
          </div>
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        <span
          aria-hidden="true"
          className="mr-1 inline-block h-2 w-2 rounded-full align-middle"
          style={{ backgroundColor: OTHER_COLOR }}
        />
        x = $/call · bubble size = call count · color = provider · top {TOP_N} models, remainder grouped
      </p>
    </div>
  )
}
