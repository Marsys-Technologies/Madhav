// At-a-glance summary of budget health — committed spend, actual spend, and
// overall health status across all active rules. OBS-UX-S5: ring gauge,
// status-toned ObsCard, gold/charcoal palette.

import type {
  BudgetEvaluationResult,
  BudgetRuleRow,
} from '@/lib/observatory/budget/types'
import { ObsCard } from '../shared/ObsCard'
import { RingGauge } from '../shared/RingGauge'

function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`
}

function formatUsdPrecise(amount: number): string {
  return `$${amount.toFixed(6)}`
}

type HealthTone = 'good' | 'warn' | 'bad'

function healthValue(evaluations: BudgetEvaluationResult[]): {
  text: string
  tone: HealthTone
  sub: string
} {
  const statuses = evaluations.map((e) => e.status)
  if (statuses.includes('exceeded')) {
    return {
      text: 'Over budget',
      tone: 'bad',
      sub: `${statuses.filter((s) => s === 'exceeded').length} rule(s) exceeded`,
    }
  }
  if (statuses.includes('alert')) {
    return {
      text: 'Alert',
      tone: 'bad',
      sub: `${statuses.filter((s) => s === 'alert').length} rule(s) in alert`,
    }
  }
  if (statuses.includes('warning')) {
    return {
      text: 'Warning',
      tone: 'warn',
      sub: `${statuses.filter((s) => s === 'warning').length} rule(s) near limit`,
    }
  }
  return {
    text: 'All clear',
    tone: 'good',
    sub: `${evaluations.length} rule(s) within budget`,
  }
}

const TONE_COLOR: Record<HealthTone, string> = {
  good: 'text-[var(--status-success)]',
  warn: 'text-[var(--status-warn)]',
  bad: 'text-[var(--status-halt)]',
}

const TONE_GAUGE: Record<HealthTone, 'success' | 'warn' | 'halt'> = {
  good: 'success',
  warn: 'warn',
  bad: 'halt',
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

  // Aggregate utilization: sum of spend / sum of committed amount across all
  // evaluations (cap at 1.5 for the ring's visual ceiling).
  const totalCommitted = evaluations.reduce((s, e) => s + e.amount_usd, 0)
  const utilization = totalCommitted > 0 ? Math.min(totalSpend / totalCommitted, 1.5) : 0
  const utilizationPct = Math.round(utilization * 100)

  const health = healthValue(evaluations)

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <ObsCard padding="normal" tone="hot" className="flex items-center gap-5">
        <RingGauge
          value={Math.min(utilization, 1)}
          tone={TONE_GAUGE[health.tone]}
          size={132}
          thickness={10}
          label={<span className="bt-num">{utilizationPct}<span className="text-base ml-0.5 opacity-70">%</span></span>}
          sublabel="utilization"
          ariaLabel={`Budget utilization ${utilizationPct}%`}
        />
        <div className="flex-1 min-w-0">
          <p className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">Committed (monthly)</p>
          <p className="mt-1 bt-num text-[var(--brand-gold)]">{formatUsd(monthlyCommitted)}<span className="text-sm font-normal opacity-70 ml-1">/ mo</span></p>
          <p className="mt-1 text-xs text-[rgba(212,175,55,0.50)]">
            {rules.filter((r) => r.period === 'monthly').length} monthly rule(s)
          </p>
        </div>
      </ObsCard>

      <ObsCard padding="normal">
        <p className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">Total current spend</p>
        <p className="mt-2 bt-num text-[var(--brand-gold-cream)]">
          {formatUsdPrecise(totalSpend)}
        </p>
        <p className="mt-1 text-xs text-[rgba(212,175,55,0.50)]">
          across {evaluations.length} evaluated rule(s)
        </p>
      </ObsCard>

      <ObsCard padding="normal" tone={health.tone}>
        <p className="bt-label bt-label-upper text-[rgba(212,175,55,0.55)]">Health status</p>
        <p className={`mt-2 bt-num ${TONE_COLOR[health.tone]}`}>{health.text}</p>
        <p className="mt-1 text-xs text-[rgba(212,175,55,0.50)]">{health.sub}</p>
      </ObsCard>
    </div>
  )
}
