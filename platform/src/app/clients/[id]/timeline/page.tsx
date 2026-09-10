import { redirect } from 'next/navigation'
import { query } from '@/lib/db/client'
import { parseLEL } from '@/lib/lel/parser'
import { TimelineView } from '@/components/timeline/TimelineView'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'

// V3-E-019: converged off the retired inline `chart.client_id !== user.uid`
// model onto resolveChartPageAccess — see the sibling layout for the full
// rationale. `canWrite` follows the canonical build bar (owner or super_admin),
// which is what the previous `role === 'super_admin'` test was approximating.
export default async function TimelinePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string }>('SELECT name FROM charts WHERE id=$1', [id])
  if (!chartResult.rows[0]) redirect('/dashboard')

  const { events, predictions, parseErrors } = await parseLEL(id)

  return (
    <ZoneRoot zone="vellum" className="flex h-full flex-col">
      <TimelineView
        events={events}
        predictions={predictions}
        parseErrors={parseErrors}
        chartId={id}
        canWrite={access.canBuild}
      />
    </ZoneRoot>
  )
}
