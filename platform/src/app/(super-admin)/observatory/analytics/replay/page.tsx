// Observatory Replay & Re-cost page (server component shell). AuthGate is
// enforced by the parent /observatory layout. The panel is a client component;
// this server file exists so the route is reachable.
//
// Phase O — O.4. Authored by USTAD_S4_5_REPLAY_RECOST.

import { ReplayPanel } from '@/lib/components/observatory/analytics/ReplayPanel'
import { ObsPageShell } from '@/lib/components/observatory/shared'

export const dynamic = 'force-dynamic'

export const metadata = {
  title: 'Replay & Re-cost — Observatory',
}

export default function ObservatoryReplayPage() {
  return (
    <ObsPageShell
      title="Replay & Re-cost"
      subtitle="Re-cost historical events against an alternative pricing version"
    >
      <ReplayPanel />
    </ObsPageShell>
  )
}
