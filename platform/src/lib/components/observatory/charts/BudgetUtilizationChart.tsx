'use client'

// O.3 budgets — burndown reimagining.
// One row per evaluation: shows the period as a horizontal track, with
// solid actual-burn from period_start → today, dashed projection from
// today → period_end based on the current daily run-rate, a budget
// ceiling line, and a red dot at the projected exhaustion day if the
// run-rate exhausts the cap before the period ends.

import * as React from 'react'

import type {
  BudgetEvaluationResult,
  BudgetStatus,
} from '@/lib/observatory/budget/types'

const STATUS_TINT: Record<BudgetStatus, string> = {
  ok: 'oklch(0.65 0.16 160)',
  warning: 'oklch(0.78 0.13 80)',
  alert: 'oklch(0.6 0.18 35)',
  exceeded: 'oklch(0.45 0.20 28)',
}

const MS_DAY = 86_400_000

interface Burndown {
  result: BudgetEvaluationResult
  totalDays: number
  daysElapsed: number
  dailyBurn: number
  projectedExhaustDay: number | null
  remainingDays: number
}

function buildBurndown(result: BudgetEvaluationResult): Burndown {
  const start = new Date(result.period_start).getTime()
  const end = new Date(result.period_end).getTime()
  const today = Date.now()
  const totalDays = Math.max(1, Math.round((end - start) / MS_DAY))
  const daysElapsed = Math.max(0.5, Math.min(totalDays, (today - start) / MS_DAY))
  const dailyBurn = result.current_spend_usd / daysElapsed
  let projectedExhaustDay: number | null = null
  if (dailyBurn > 0) {
    const remaining = result.amount_usd - result.current_spend_usd
    const daysLeft = remaining / dailyBurn
    if (daysLeft >= 0 && daysElapsed + daysLeft <= totalDays) {
      projectedExhaustDay = daysElapsed + daysLeft
    }
  }
  const remainingDays = Math.max(0, totalDays - daysElapsed)
  return { result, totalDays, daysElapsed, dailyBurn, projectedExhaustDay, remainingDays }
}

function scopeLabel(r: BudgetEvaluationResult): string {
  const scope = r.scope === 'total' ? 'global' : `${r.scope}:${r.scope_value ?? '—'}`
  return `${r.name} — ${scope} (${r.period})`
}

interface BurndownRowProps {
  burn: Burndown
  width: number
}

function BurndownRow({ burn, width }: BurndownRowProps) {
  const H = 96
  const PAD_L = 16
  const PAD_R = 80
  const PAD_T = 28
  const PAD_B = 22
  const inner = { w: width - PAD_L - PAD_R, h: H - PAD_T - PAD_B }

  const yMax = Math.max(burn.result.amount_usd, burn.result.current_spend_usd) * 1.05

  const xOf = (d: number) => PAD_L + (d / burn.totalDays) * inner.w
  const yOf = (v: number) => PAD_T + inner.h - (v / yMax) * inner.h

  const tint = STATUS_TINT[burn.result.status]

  // Actual line: linear from (0, 0) → (today, current_spend)
  const actualPath = `M${xOf(0).toFixed(1)},${yOf(0).toFixed(1)} L${xOf(burn.daysElapsed).toFixed(1)},${yOf(burn.result.current_spend_usd).toFixed(1)}`

  // Projection: from today onward to either exhaustion or period end
  const projEnd = burn.projectedExhaustDay ?? burn.totalDays
  const projY = burn.projectedExhaustDay !== null ? yOf(burn.result.amount_usd) : yOf(burn.result.current_spend_usd + burn.dailyBurn * burn.remainingDays)
  const projPath = `M${xOf(burn.daysElapsed).toFixed(1)},${yOf(burn.result.current_spend_usd).toFixed(1)} L${xOf(projEnd).toFixed(1)},${projY.toFixed(1)}`

  const cliffStart = burn.projectedExhaustDay !== null ? Math.max(0, burn.projectedExhaustDay - 3) : null

  return (
    <svg viewBox={`0 0 ${width} ${H}`} width="100%" height={H} preserveAspectRatio="none">
      {cliffStart !== null && (
        <rect
          x={xOf(cliffStart)}
          y={PAD_T}
          width={xOf(burn.projectedExhaustDay!) - xOf(cliffStart)}
          height={inner.h}
          fill="oklch(0.6 0.18 35)"
          fillOpacity={0.10}
        />
      )}
      {/* Budget ceiling */}
      <line
        x1={PAD_L}
        x2={width - PAD_R}
        y1={yOf(burn.result.amount_usd)}
        y2={yOf(burn.result.amount_usd)}
        stroke="rgba(212,175,55,0.4)"
        strokeDasharray="4 4"
      />
      <text
        x={width - PAD_R + 4}
        y={yOf(burn.result.amount_usd) + 3}
        fontSize={10}
        fill="rgba(212,175,55,0.65)"
      >
        ${burn.result.amount_usd.toFixed(0)} cap
      </text>

      {/* Actual */}
      <path d={actualPath} fill="none" stroke="var(--brand-gold-cream)" strokeWidth={2} />
      {/* Projection */}
      <path d={projPath} fill="none" stroke="var(--brand-gold)" strokeWidth={1.25} strokeDasharray="3 3" strokeOpacity={0.7} />

      {/* Today marker */}
      <line
        x1={xOf(burn.daysElapsed)}
        x2={xOf(burn.daysElapsed)}
        y1={PAD_T}
        y2={H - PAD_B}
        stroke="rgba(212,175,55,0.4)"
      />
      <text
        x={xOf(burn.daysElapsed)}
        y={PAD_T - 6}
        textAnchor="middle"
        fontSize={10}
        fill="rgba(212,175,55,0.7)"
      >
        today
      </text>

      {/* Exhaustion */}
      {burn.projectedExhaustDay !== null && (
        <>
          <circle
            cx={xOf(burn.projectedExhaustDay)}
            cy={yOf(burn.result.amount_usd)}
            r={4}
            fill={tint}
          />
          <text
            x={xOf(burn.projectedExhaustDay) + 8}
            y={yOf(burn.result.amount_usd) - 6}
            fontSize={10}
            fill={tint}
          >
            runs out d{Math.round(burn.projectedExhaustDay)}
          </text>
        </>
      )}

      {/* X tick labels at start, today, end */}
      <text x={PAD_L} y={H - 6} fontSize={10} fill="rgba(212,175,55,0.5)">
        d0
      </text>
      <text x={width - PAD_R} y={H - 6} textAnchor="end" fontSize={10} fill="rgba(212,175,55,0.5)">
        d{burn.totalDays}
      </text>
    </svg>
  )
}

export interface BudgetUtilizationChartProps {
  results: BudgetEvaluationResult[]
}

export function BudgetUtilizationChart({ results }: BudgetUtilizationChartProps) {
  const ref = React.useRef<HTMLDivElement | null>(null)
  const [width, setWidth] = React.useState(800)

  React.useEffect(() => {
    if (!ref.current) return
    const el = ref.current
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        if (e.contentRect.width > 0) setWidth(e.contentRect.width)
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  if (!results || results.length === 0) {
    return (
      <div
        data-testid="budget-utilization-empty"
        className="flex h-40 w-full items-center justify-center rounded border border-dashed text-sm text-muted-foreground"
      >
        No active budget rules
      </div>
    )
  }

  const rows = results.map(buildBurndown)

  return (
    <div
      ref={ref}
      data-testid="budget-utilization-chart"
      data-row-count={rows.length}
      className="w-full rounded border border-[color-mix(in_oklch,var(--brand-gold)_10%,transparent)] bg-[oklch(0.115_0.012_70)] p-4"
    >
      <div className="flex flex-col gap-4">
        {rows.map((burn) => (
          <div key={burn.result.rule_id} className="flex flex-col gap-1">
            <div className="flex items-baseline justify-between text-[11px]">
              <span className="font-semibold uppercase tracking-wider text-[color-mix(in_oklch,var(--brand-gold)_70%,white_30%)]">
                {scopeLabel(burn.result)}
              </span>
              <span className="tabular-nums text-[color-mix(in_oklch,var(--brand-gold)_55%,transparent)]">
                ${burn.result.current_spend_usd.toFixed(2)} of ${burn.result.amount_usd.toFixed(2)} ·{' '}
                <span style={{ color: STATUS_TINT[burn.result.status] }}>
                  {Math.round(burn.result.pct_used)}%
                </span>{' '}
                · ${burn.dailyBurn.toFixed(2)}/d
                {burn.projectedExhaustDay !== null && (
                  <>
                    {' · '}
                    <span style={{ color: STATUS_TINT[burn.result.status] }}>
                      {Math.max(0, Math.round(burn.projectedExhaustDay - burn.daysElapsed))}d runway
                    </span>
                  </>
                )}
              </span>
            </div>
            <BurndownRow burn={burn} width={width} />
          </div>
        ))}
      </div>
    </div>
  )
}
