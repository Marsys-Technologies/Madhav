import { redirect } from 'next/navigation'
import { readChartTitleName } from '@/lib/charts/pageIdentity'
import { readTimelineEvents } from '@/lib/mimamsa/timelinePageData'
import { TimelineView } from '@/components/timeline/TimelineView'
import { ChartNav } from '@/components/journey1/ChartNav'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { NextResponse } from 'next/server'

// V3-E-019: converged off the retired inline `chart.client_id !== user.uid`
// model onto resolveChartPageAccess — see the sibling layout for the full
// rationale. The chart guard runs before any event data is loaded.
export default async function TimelinePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams?: Promise<{ tab?: string | string[] }>
}) {
  const { id } = await params

  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await readChartTitleName(id)
  if (!chartResult.rows[0]) redirect('/dashboard')

  if ((await searchParams)?.tab === 'predictions') redirect(`/clients/${id}/samiksha`)

  const { rows: events } = await readTimelineEvents(id)

  const canLogEvent = access.role === 'super_admin' && !((await requireSuperAdmin()) instanceof NextResponse)

  return (
    <ZoneRoot zone="vellum" className="flex min-h-full flex-col">
      <ChartNav chartId={id} canBuild={access.canBuild} active="events" />
      <TimelineView key={id} events={events} chartId={id} canLogEvent={canLogEvent} />
    </ZoneRoot>
  )
}
