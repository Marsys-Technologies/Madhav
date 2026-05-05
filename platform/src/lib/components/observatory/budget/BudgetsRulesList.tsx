'use client'

// Client wrapper around the rule cards list. Owns the DELETE+refresh side
// effect so each BudgetRuleCard can stay a pure UI component.

import { useRouter } from 'next/navigation'
import { useState } from 'react'

import type {
  BudgetEvaluationResult,
  BudgetRuleRow,
} from '@/lib/observatory/budget/types'

import { BudgetRuleCard } from './BudgetRuleCard'

export interface BudgetsRulesListProps {
  rules: BudgetRuleRow[]
  evaluations: BudgetEvaluationResult[]
}

export function BudgetsRulesList({ rules, evaluations }: BudgetsRulesListProps) {
  const router = useRouter()
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const evalById = new Map(evaluations.map((e) => [e.rule_id, e]))
  const sorted = [...rules].sort((a, b) => {
    const aPct = evalById.get(a.budget_rule_id)?.pct_used ?? -1
    const bPct = evalById.get(b.budget_rule_id)?.pct_used ?? -1
    return bPct - aPct
  })

  if (sorted.length === 0) {
    return (
      <div
        data-testid="budgets-empty"
        className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-[rgba(212,175,55,0.15)] py-12 text-center"
      >
        <span className="text-3xl opacity-20">◎</span>
        <p className="text-sm font-medium text-[rgba(212,175,55,0.45)]">No active budget rules</p>
        <p className="text-xs text-[rgba(212,175,55,0.30)]">Create a rule below to start tracking spend</p>
      </div>
    )
  }

  async function handleDeactivate(id: string) {
    setPendingId(id)
    setError(null)
    try {
      const response = await fetch(
        `/api/admin/observatory/budget-rules/${encodeURIComponent(id)}`,
        { method: 'DELETE', credentials: 'same-origin' },
      )
      if (!response.ok && response.status !== 204) {
        throw new Error(`Deactivate failed (${response.status})`)
      }
      router.refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deactivate failed')
    } finally {
      setPendingId(null)
    }
  }

  return (
    <div data-testid="budgets-rules-list" className="space-y-3">
      {error ? (
        <div role="alert" className="text-xs text-red-600">
          {error}
        </div>
      ) : null}
      {sorted.map((rule) => (
        <BudgetRuleCard
          key={rule.budget_rule_id}
          rule={rule}
          evaluation={evalById.get(rule.budget_rule_id)}
          onDeactivate={() => handleDeactivate(rule.budget_rule_id)}
        />
      ))}
      {pendingId ? (
        <div
          role="status"
          className="text-xs text-muted-foreground"
          data-testid="budgets-deactivating"
        >
          Deactivating…
        </div>
      ) : null}
    </div>
  )
}
