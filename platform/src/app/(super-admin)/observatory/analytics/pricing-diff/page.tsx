// Observatory — Pricing Diff Monitor (O.4 — S4.4). Server component.
// AuthGate is enforced by the parent observatory layout. The initial result
// is computed in-process via checkPricingHealth() so the panel hydrates with
// real data and no API round-trip.

import { PricingDiffPanel } from '@/lib/components/observatory/analytics/PricingDiffPanel'
import { checkPricingHealth } from '@/lib/observatory/analytics/pricing_diff'
import { ObsPageShell } from '@/lib/components/observatory/shared'

export const dynamic = 'force-dynamic'
export const metadata = { title: 'Pricing Diff Monitor' }

export default async function PricingDiffPage() {
  const initialResult = await checkPricingHealth()
  return (
    <ObsPageShell
      title="Pricing Diff Monitor"
      subtitle="Active pricing version health · drift across providers and models"
      testId="observatory-pricing-diff-page"
    >
      <PricingDiffPanel initialResult={initialResult} />
    </ObsPageShell>
  )
}
