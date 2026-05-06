// Observatory Events page (server component shell). AuthGate is enforced by
// the parent layout. The ExportPanel is now rendered inside EventsClient so
// it lives within the obs-shell context (see OBS-UX-S5).

import { EventsClient } from '@/lib/components/observatory/pages/EventsClient'

export const dynamic = 'force-dynamic'

export default function ObservatoryEventsPage() {
  return <EventsClient />
}
