// Observatory Budgets page (O.3 — S3.3). Server component. Reads from the
// frozen S3.1 backend loaders (listBudgetRules, evaluateAllRules) — semantic
// equivalent of the API client's fetchBudgetRules + evaluateBudgets, but
// usable from RSC without absolute-URL gymnastics. AuthGate is enforced by
// the parent layout. OBS-UX-S5: ObsPageShell + SectionLabel.

import {
  BudgetHeroSummary,
  BudgetsRulesList,
  CreateBudgetRuleSection,
  RunEvaluationButton,
} from '@/lib/components/observatory/budget'
import { BudgetUtilizationChart } from '@/lib/components/observatory/charts/BudgetUtilizationChart'
import { evaluateAllRules } from '@/lib/observatory/budget/evaluate'
import { listBudgetRules } from '@/lib/observatory/budget/persist'
import { ObsPageShell, ObsCard, SectionLabel } from '@/lib/components/observatory/shared'

export const dynamic = 'force-dynamic'

export default async function ObservatoryBudgetsPage() {
  const [rules, evaluations] = await Promise.all([
    listBudgetRules('active'),
    evaluateAllRules(),
  ])

  return (
    <ObsPageShell
      title="Budget Rules"
      subtitle="Spending limits and utilisation alerts by provider, model, or stage"
      testId="observatory-budgets-page"
      headerRight={<RunEvaluationButton />}
    >
      <section aria-label="Budget overview">
        <SectionLabel accent>Overview</SectionLabel>
        <BudgetHeroSummary rules={rules} evaluations={evaluations} />
      </section>

      <section aria-label="Utilisation summary">
        <SectionLabel>Utilisation</SectionLabel>
        <ObsCard padding="normal">
          <BudgetUtilizationChart results={evaluations} />
        </ObsCard>
      </section>

      <section aria-label="Active rules" className="space-y-3">
        <SectionLabel>Active rules</SectionLabel>
        <BudgetsRulesList rules={rules} evaluations={evaluations} />
      </section>

      <section aria-label="Add budget rule" className="space-y-3">
        <SectionLabel>Add budget rule</SectionLabel>
        <CreateBudgetRuleSection />
      </section>
    </ObsPageShell>
  )
}
