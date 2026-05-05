'use client'

// One card per budget rule. Owns its own confirmation state but delegates the
// actual DELETE+refresh to the parent via onDeactivate so the page can keep
// the API-call surface in one place.

import { useState } from 'react'

import { cn } from '@/lib/utils'
import type {
  BudgetEvaluationResult,
  BudgetRuleRow,
} from '@/lib/observatory/budget/types'

import { BudgetStatusChip } from './BudgetStatusChip'

function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`
}

function alertThresholdsLabel(rule: BudgetRuleRow): string {
  const thresholds = Array.isArray(rule.alert_thresholds)
    ? (rule.alert_thresholds as Array<{ pct: number }>)
    : []
  if (thresholds.length === 0) return 'No alert thresholds configured'
  const pcts = thresholds.map((t) => `${t.pct}%`).join(', ')
  return `Alert at ${pcts}`
}

function progressGradient(status?: string): string {
  switch (status) {
    case 'ok':       return 'from-emerald-500 to-emerald-400'
    case 'warning':  return 'from-amber-500 to-amber-400'
    case 'alert':    return 'from-red-500 to-red-400'
    case 'exceeded': return 'from-red-600 to-red-500'
    default:         return 'from-[rgba(212,175,55,0.40)] to-[rgba(212,175,55,0.25)]'
  }
}

function statusTextColor(status?: string): string {
  switch (status) {
    case 'ok':       return 'text-emerald-400'
    case 'warning':  return 'text-amber-400'
    case 'alert':
    case 'exceeded': return 'text-red-400'
    default:         return 'text-[rgba(212,175,55,0.60)]'
  }
}

export interface BudgetRuleCardProps {
  rule: BudgetRuleRow
  /** undefined while evaluation is loading. */
  evaluation?: BudgetEvaluationResult
  /** Parent issues DELETE + refreshes the rules list. */
  onDeactivate: () => void
}

export function BudgetRuleCard({
  rule,
  evaluation,
  onDeactivate,
}: BudgetRuleCardProps) {
  const [confirming, setConfirming] = useState(false)

  const scopeLabel =
    rule.scope === 'total'
      ? 'global (total)'
      : `${rule.scope}: ${rule.scope_value ?? '—'}`

  return (
    <div
      data-testid={`budget-rule-card-${rule.budget_rule_id}`}
      data-rule-id={rule.budget_rule_id}
      className="rounded-xl border border-[rgba(212,175,55,0.12)] bg-[oklch(0.11_0.010_70)] p-5 transition-colors hover:border-[rgba(212,175,55,0.20)]"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-[#fce29a]">{rule.name}</div>
          <div className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">
            {scopeLabel} · {rule.period}
          </div>
        </div>
        {evaluation && (
          <BudgetStatusChip status={evaluation.status} pct_used={evaluation.pct_used} />
        )}
      </div>

      <div className="mt-4 flex items-center justify-between text-xs">
        <span className="text-[rgba(212,175,55,0.40)]">
          Budget:{' '}
          <span className="font-semibold text-[rgba(212,175,55,0.70)]">
            {formatUsd(rule.amount_usd)}
          </span>{' '}
          / {rule.period.replace(/ly$/, '')}
        </span>
        {evaluation && (
          <span className={cn('font-semibold tabular-nums', statusTextColor(evaluation.status))}>
            {evaluation.pct_used.toFixed(1)}% used
          </span>
        )}
      </div>

      {evaluation ? (
        <>
          <div
            data-testid={`budget-rule-progress-${rule.budget_rule_id}`}
            className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[rgba(212,175,55,0.08)]"
            role="progressbar"
            aria-valuenow={Math.min(100, Math.round(evaluation.pct_used))}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={cn(
                'h-full rounded-full bg-gradient-to-r transition-all duration-500',
                progressGradient(evaluation.status),
              )}
              style={{ width: `${Math.min(100, Math.max(0, evaluation.pct_used))}%` }}
            />
          </div>
          <div
            data-testid={`budget-rule-spend-${rule.budget_rule_id}`}
            className="mt-1.5 flex items-center justify-between text-xs tabular-nums"
          >
            <span className={cn('font-medium', statusTextColor(evaluation.status))}>
              {formatUsd(evaluation.current_spend_usd)} spent
            </span>
            <span className="text-[rgba(212,175,55,0.30)]">
              of {formatUsd(evaluation.amount_usd)}
            </span>
          </div>
        </>
      ) : (
        <div
          data-testid={`budget-rule-skeleton-${rule.budget_rule_id}`}
          role="status"
          aria-live="polite"
          className="mt-4 space-y-2"
        >
          <div className="h-2 w-full animate-pulse rounded-full bg-[rgba(212,175,55,0.06)]" />
          <div className="h-3 w-1/3 animate-pulse rounded bg-[rgba(212,175,55,0.06)]" />
        </div>
      )}

      <div className="mt-3 text-[10px] text-[rgba(212,175,55,0.35)]">
        {alertThresholdsLabel(rule)}
      </div>

      {confirming ? (
        <div className="mt-4 flex items-center gap-2">
          <span className="text-xs text-[rgba(212,175,55,0.60)]">Deactivate this rule?</span>
          <button
            type="button"
            data-testid={`budget-rule-confirm-${rule.budget_rule_id}`}
            onClick={() => {
              setConfirming(false)
              onDeactivate()
            }}
            className="rounded-lg border border-red-500/40 px-2.5 py-1 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/10"
          >
            Confirm
          </button>
          <button
            type="button"
            onClick={() => setConfirming(false)}
            className="rounded-lg border border-[rgba(212,175,55,0.15)] px-2.5 py-1 text-xs text-[rgba(212,175,55,0.50)] transition-colors hover:text-[#d4af37]"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          type="button"
          data-testid={`budget-rule-deactivate-${rule.budget_rule_id}`}
          onClick={() => setConfirming(true)}
          className="mt-4 rounded-lg border border-[rgba(212,175,55,0.12)] px-2.5 py-1 text-xs text-[rgba(212,175,55,0.40)] transition-colors hover:border-red-500/30 hover:text-red-400"
        >
          Deactivate
        </button>
      )}
    </div>
  )
}
