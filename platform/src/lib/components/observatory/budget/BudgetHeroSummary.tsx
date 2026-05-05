// At-a-glance summary of budget health — committed spend, actual spend, and
// overall health status across all active rules.

import type {
  BudgetEvaluationResult,
  BudgetRuleRow,
} from '@/lib/observatory/budget/types'

function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`
}

function formatUsdPrecise(amount: number): string {
  return `$${amount.toFixed(6)}`
}

function healthValue(evaluations: BudgetEvaluationResult[]): {
  text: string
  colorClass: string
  sub: string
} {
  const statuses = evaluations.map((e) => e.status)
  if (statuses.includes('exceeded')) {
    return {
      text: '⚠ Over budget',
      colorClass: 'text-red-400',
      sub: `${statuses.filter((s) => s === 'exceeded').length} rule(s) exceeded`,
    }
  }
  if (statuses.includes('alert')) {
    return {
      text: 'Alert',
      colorClass: 'text-red-400',
      sub: `${statuses.filter((s) => s === 'alert').length} rule(s) in alert`,
    }
  }
  if (statuses.includes('warning')) {
    return {
      text: 'Warning',
      colorClass: 'text-amber-400',
      sub: `${statuses.filter((s) => s === 'warning').length} rule(s) near limit`,
    }
  }
  return {
    text: 'All clear',
    colorClass: 'text-emerald-400',
    sub: `${evaluations.length} rule(s) within budget`,
  }
}

export interface BudgetHeroSummaryProps {
  rules: BudgetRuleRow[]
  evaluations: BudgetEvaluationResult[]
}

export function BudgetHeroSummary({ rules, evaluations }: BudgetHeroSummaryProps) {
  const monthlyCommitted = rules
    .filter((r) => r.period === 'monthly')
    .reduce((sum, r) => sum + r.amount_usd, 0)

  const totalSpend = evaluations.reduce(
    (sum, e) => sum + e.current_spend_usd,
    0,
  )

  const health = healthValue(evaluations)

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-4">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
          Committed (monthly)
        </p>
        <p className="mt-2 text-2xl font-bold tabular-nums text-[#fce29a]">
          {formatUsd(monthlyCommitted)} / mo
        </p>
        <p className="mt-1 text-xs text-[rgba(212,175,55,0.40)]">
          {rules.filter((r) => r.period === 'monthly').length} monthly rule(s)
        </p>
      </div>

      <div className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-4">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
          Total current spend
        </p>
        <p className="mt-2 text-2xl font-bold tabular-nums text-[#fce29a]">
          {formatUsdPrecise(totalSpend)}
        </p>
        <p className="mt-1 text-xs text-[rgba(212,175,55,0.40)]">
          across {evaluations.length} evaluated rule(s)
        </p>
      </div>

      <div className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-4">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-[rgba(212,175,55,0.35)]">
          Health status
        </p>
        <p className={`mt-2 text-2xl font-bold ${health.colorClass}`}>
          {health.text}
        </p>
        <p className="mt-1 text-xs text-[rgba(212,175,55,0.40)]">{health.sub}</p>
      </div>
    </div>
  )
}
