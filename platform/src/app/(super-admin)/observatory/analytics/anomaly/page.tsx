// Observatory — Anomaly Detection (O.4 — S4.6). Server component.
// AuthGate is enforced by the parent observatory layout. The initial result
// is computed in-process via detectAnomalies() so the panel hydrates with
// real data and no API round-trip.

import { AnomalyPanel } from '@/lib/components/observatory/analytics/AnomalyPanel'
import { detectAnomalies } from '@/lib/observatory/analytics/anomaly'
import { ObsPageShell } from '@/lib/components/observatory/shared'

export const dynamic = 'force-dynamic'
export const metadata = { title: 'Anomaly Detection — Observatory' }

export default async function AnomalyDetectionPage() {
  const initialResult = await detectAnomalies()
  return (
    <ObsPageShell
      title="Anomaly Detection"
      subtitle="Z-score outliers across providers, stages, and users · 14-day lookback"
      testId="observatory-anomaly-page"
      tone="warn"
    >
      <AnomalyPanel initialResult={initialResult} />
    </ObsPageShell>
  )
}
