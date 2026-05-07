'use client'

// Cache savings — two-axis ribbon reimagining.
// Per-provider: top half rises to "saved by cache" (green), bottom half drops
// to "still paid even with cache" (red-orange). Together they equal the
// without-cache cost. The asymmetry is the story — wider top means cache is
// pulling its weight; wider bottom means there's room for more aggressive
// breakpoints.

import * as React from 'react'

import type { BreakdownsResponse } from '@/lib/observatory/types'

import { colorForProvider, formatCostUSD, formatTokenCount } from './utils'

// ---------------------------------------------------------------------------
// Display-only price stubs.
//
// The frontend does not have access to the authoritative pricing table. We
// surface an order-of-magnitude estimate of cache savings using a fixed
// per-provider input-token price proxy + a flat 10× cache-read discount.
// Labeled "estimated" in the UI either way.
// ---------------------------------------------------------------------------

const INPUT_PRICE_PER_MILLION_USD: Record<string, number> = {
  anthropic: 3.0,
  openai: 2.5,
  gemini: 1.25,
  deepseek: 0.27,
  nim: 0.5,
}
const CACHE_READ_DISCOUNT = 0.1
const FALLBACK_INPUT_PRICE = 1.0

const SAVED_COLOR = 'oklch(0.65 0.16 160)'
const STILL_PAID_COLOR = 'oklch(0.6 0.18 35)'

export interface CacheSavingsChartProps {
  data: BreakdownsResponse | null
  loading?: boolean
  error?: Error | null
  onRetry?: () => void
}

export interface CacheSavingsRow {
  provider: string
  cache_tokens: number
  cost_without_cache_usd: number
  cost_with_cache_usd: number
  estimated_savings_usd: number
}

export function computeCacheSavings(data: BreakdownsResponse): CacheSavingsRow[] {
  const rows: CacheSavingsRow[] = []
  for (const r of data.rows) {
    const cacheTokens = r.cache_tokens ?? 0
    if (cacheTokens <= 0) continue
    const inputPrice =
      INPUT_PRICE_PER_MILLION_USD[r.dim_value] ?? FALLBACK_INPUT_PRICE
    const without = (cacheTokens * inputPrice) / 1_000_000
    const withCache = without * CACHE_READ_DISCOUNT
    rows.push({
      provider: r.dim_value,
      cache_tokens: cacheTokens,
      cost_without_cache_usd: without,
      cost_with_cache_usd: withCache,
      estimated_savings_usd: without - withCache,
    })
  }
  return rows.sort((a, b) => b.estimated_savings_usd - a.estimated_savings_usd)
}

export function CacheSavingsChart({
  data,
  loading = false,
  error = null,
  onRetry,
}: CacheSavingsChartProps) {
  const [hover, setHover] = React.useState<number | null>(null)

  if (loading) {
    return (
      <div
        data-testid="cache-savings-loading"
        role="status"
        aria-live="polite"
        className="h-72 w-full animate-pulse rounded bg-muted"
      />
    )
  }

  if (error) {
    return (
      <div
        data-testid="cache-savings-error"
        role="alert"
        className="flex h-72 w-full flex-col items-center justify-center gap-2 rounded border border-destructive/30 p-4 text-sm"
      >
        <p>Failed to load cache savings.</p>
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

  const rows = data ? computeCacheSavings(data) : []

  if (rows.length === 0) {
    return (
      <div
        data-testid="cache-savings-empty"
        className="flex h-72 w-full items-center justify-center rounded border text-sm text-muted-foreground"
      >
        No cached tokens in this range
      </div>
    )
  }

  const W = 880
  const H = 320
  const PAD_L = 60
  const PAD_R = 24
  const PAD_T = 28
  const PAD_B = 56
  const inner = { w: W - PAD_L - PAD_R, h: H - PAD_T - PAD_B }
  const mid = PAD_T + inner.h / 2

  const maxSide = Math.max(
    ...rows.map((r) => Math.max(r.estimated_savings_usd, r.cost_with_cache_usd)),
    0.0001,
  ) * 1.1

  const colWidth = inner.w / Math.max(1, rows.length)
  const xCenter = (i: number) => PAD_L + colWidth * (i + 0.5)
  const yUp = (v: number) => mid - (v / maxSide) * (inner.h / 2)
  const yDn = (v: number) => mid + (v / maxSide) * (inner.h / 2)

  const totalSaved = rows.reduce((s, r) => s + r.estimated_savings_usd, 0)
  const totalStillPaid = rows.reduce((s, r) => s + r.cost_with_cache_usd, 0)

  return (
    <div
      data-testid="cache-savings-chart"
      data-provider-count={rows.length}
      className="w-full"
    >
      <div className="relative w-full" style={{ aspectRatio: `${W} / ${H}` }}>
        <svg
          viewBox={`0 0 ${W} ${H}`}
          width="100%"
          height="100%"
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label="Cache savings ribbon: top = saved by cache, bottom = still paid"
        >
          {[0.25, 0.5, 0.75, 1].map((t) => (
            <React.Fragment key={t}>
              <line
                x1={PAD_L}
                x2={W - PAD_R}
                y1={mid - (inner.h / 2) * t}
                y2={mid - (inner.h / 2) * t}
                stroke="rgba(212,175,55,0.06)"
                strokeDasharray="2 4"
              />
              <line
                x1={PAD_L}
                x2={W - PAD_R}
                y1={mid + (inner.h / 2) * t}
                y2={mid + (inner.h / 2) * t}
                stroke="rgba(212,175,55,0.06)"
                strokeDasharray="2 4"
              />
            </React.Fragment>
          ))}
          <line
            x1={PAD_L}
            x2={W - PAD_R}
            y1={mid}
            y2={mid}
            stroke="rgba(212,175,55,0.22)"
          />

          {rows.map((r, i) => {
            const cx = xCenter(i)
            const half = Math.min(colWidth * 0.32, 28)
            const yTop = yUp(r.estimated_savings_usd)
            const yBot = yDn(r.cost_with_cache_usd)
            const opacity = hover === null || hover === i ? 1 : 0.5
            return (
              <g
                key={r.provider}
                onMouseEnter={() => setHover(i)}
                onMouseLeave={() => setHover((h) => (h === i ? null : h))}
              >
                <rect
                  x={cx - half}
                  y={yTop}
                  width={half * 2}
                  height={mid - yTop}
                  fill={SAVED_COLOR}
                  fillOpacity={0.42 * opacity}
                  stroke={SAVED_COLOR}
                  strokeOpacity={0.85 * opacity}
                  strokeWidth={1}
                  rx={2}
                />
                <rect
                  x={cx - half}
                  y={mid}
                  width={half * 2}
                  height={yBot - mid}
                  fill={STILL_PAID_COLOR}
                  fillOpacity={0.30 * opacity}
                  stroke={STILL_PAID_COLOR}
                  strokeOpacity={0.85 * opacity}
                  strokeWidth={1}
                  rx={2}
                />
                <circle cx={cx} cy={mid} r={3} fill={colorForProvider(r.provider)} />
                <text
                  x={cx}
                  y={H - PAD_B + 18}
                  textAnchor="middle"
                  fontSize={11}
                  fill="rgba(212,175,55,0.65)"
                >
                  {r.provider}
                </text>
                <text
                  x={cx}
                  y={H - PAD_B + 32}
                  textAnchor="middle"
                  fontSize={9}
                  fill="rgba(212,175,55,0.45)"
                >
                  {formatTokenCount(r.cache_tokens)} cached
                </text>
              </g>
            )
          })}

          <text x={PAD_L - 8} y={PAD_T + 12} textAnchor="end" fontSize={10} fill={SAVED_COLOR}>
            saved
          </text>
          <text
            x={PAD_L - 8}
            y={H - PAD_B - 4}
            textAnchor="end"
            fontSize={10}
            fill={STILL_PAID_COLOR}
          >
            still paid
          </text>
          <text x={PAD_L - 8} y={mid + 3} textAnchor="end" fontSize={10} fill="rgba(212,175,55,0.5)">
            $0
          </text>
          <text x={PAD_L - 8} y={yUp(maxSide / 1.1) + 3} textAnchor="end" fontSize={10} fill="rgba(212,175,55,0.5)">
            {formatCostUSD(maxSide / 1.1)}
          </text>
          <text x={PAD_L - 8} y={yDn(maxSide / 1.1) + 3} textAnchor="end" fontSize={10} fill="rgba(212,175,55,0.5)">
            {formatCostUSD(maxSide / 1.1)}
          </text>
        </svg>

        {hover !== null && rows[hover] && (
          <div
            data-testid="cache-savings-tooltip"
            className="pointer-events-none absolute rounded-lg border border-[rgba(212,175,55,0.12)] bg-[oklch(0.13_0.008_70)] p-2 text-xs shadow-lg"
            style={{
              left: `${(xCenter(hover) / W) * 100}%`,
              top: `${(mid / H) * 100}%`,
              transform: 'translate(-50%, -120%)',
            }}
          >
            <div className="mb-1 font-medium">{rows[hover].provider}</div>
            <div className="flex justify-between gap-4">
              <span>Cached tokens</span>
              <span className="tabular-nums">{formatTokenCount(rows[hover].cache_tokens)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Estimated without cache</span>
              <span className="tabular-nums">{formatCostUSD(rows[hover].cost_without_cache_usd)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Estimated with cache</span>
              <span className="tabular-nums">{formatCostUSD(rows[hover].cost_with_cache_usd)}</span>
            </div>
            <div className="mt-1 flex justify-between gap-4 border-t border-[rgba(212,175,55,0.12)] pt-1 font-medium">
              <span>Estimated savings</span>
              <span className="tabular-nums">{formatCostUSD(rows[hover].estimated_savings_usd)}</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[11px] tabular-nums">
        <span>
          <span className="text-[var(--brand-gold-cream)]">{formatCostUSD(totalSaved)}</span>{' '}
          <span className="text-[color-mix(in_oklch,var(--brand-gold)_55%,transparent)]">saved by cache</span>
        </span>
        <span>
          <span className="text-[var(--brand-gold-cream)]">{formatCostUSD(totalStillPaid)}</span>{' '}
          <span className="text-[color-mix(in_oklch,var(--brand-gold)_55%,transparent)]">still paid — review prompt-cache breakpoints</span>
        </span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Estimated using a display-only price proxy (Anthropic-style ≈10× cache discount).
      </p>
    </div>
  )
}
