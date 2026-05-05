// Observatory Budgets page (O.3 — S3.3). Server component. Reads from the
// frozen S3.1 backend loaders (listBudgetRules, evaluateAllRules) — semantic
// equivalent of the API client's fetchBudgetRules + evaluateBudgets, but
// usable from RSC without absolute-URL gymnastics. AuthGate is enforced by
// the parent layout.

import {
  BudgetHeroSummary,
  BudgetsRulesList,
  CreateBudgetRuleSection,
  RunEvaluationButton,
} from '@/lib/components/observatory/budget'
import { BudgetUtilizationChart } from '@/lib/components/observatory/charts/BudgetUtilizationChart'
import { evaluateAllRules } from '@/lib/observatory/budget/evaluate'
import { listBudgetRules } from '@/lib/observatory/budget/persist'

export const dynamic = 'force-dynamic'

export default async function ObservatoryBudgetsPage() {
  const [rules, evaluations] = await Promise.all([
    listBudgetRules('active'),
    evaluateAllRules(),
  ])

  return (
    <div
      data-testid="observatory-budgets-page"
      className="min-h-full bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]"
    >
      <div className="border-b border-[rgba(212,175,55,0.10)] px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-heading text-xl font-semibold text-[#fce29a] tracking-wide">
              Budget Rules
            </h1>
            <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">
              Spending limits and utilisation alerts by provider, model, or stage
            </p>
          </div>
          <RunEvaluationButton />
        </div>
      </div>

      <div className="flex flex-col gap-8 p-6">
        <section aria-label="Budget overview">
          <BudgetHeroSummary rules={rules} evaluations={evaluations} />
        </section>

        <section aria-label="Utilisation summary">
          <BudgetUtilizationChart results={evaluations} />
        </section>

        <section aria-label="Active rules" className="space-y-2">
          <h2 className="text-sm font-medium text-[rgba(212,175,55,0.45)]">Active rules</h2>
          <BudgetsRulesList rules={rules} evaluations={evaluations} />
        </section>

        <section aria-label="Add budget rule" className="space-y-2">
          <h2 className="text-sm font-medium text-[rgba(212,175,55,0.45)]">Add budget rule</h2>
          <CreateBudgetRuleSection />
        </section>
      </div>
    </div>
  )
}
