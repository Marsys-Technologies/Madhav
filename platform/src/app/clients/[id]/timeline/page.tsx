import { redirect } from 'next/navigation'
import { query } from '@/lib/db/client'
import type { LELEvent } from '@/lib/lel/parser'
import { TimelineView } from '@/components/timeline/TimelineView'
import { ChartNav } from '@/components/journey1/ChartNav'
import { ZoneRoot } from '@/components/shared/ZoneRoot'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'

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

  const chartResult = await query<{ name: string }>('SELECT name FROM charts WHERE id=$1', [id])
  if (!chartResult.rows[0]) redirect('/dashboard')

  if ((await searchParams)?.tab === 'predictions') redirect(`/clients/${id}/samiksha`)

  const { rows: events } = await query<LELEvent>(
    `SELECT event_id AS id,
            CASE date_confidence
              WHEN 'year_only' THEN to_char(event_date, 'YYYY')
              WHEN 'month_known' THEN to_char(event_date, 'YYYY-MM')
              ELSE to_char(event_date, 'YYYY-MM-DD')
            END AS date,
            category, description AS body,
            jsonb_strip_nulls(jsonb_build_object(
              'maha_lord', chart_state->>'dasha_md',
              'antar_lord', chart_state->>'dasha_ad'
            )) AS chart_state
       FROM life_events
      WHERE chart_id = $1
      ORDER BY event_date DESC, event_id ASC`,
    [id],
  )

  return (
    <ZoneRoot zone="vellum" className="flex h-full flex-col">
      <ChartNav chartId={id} canBuild={access.canBuild} active="events" />
      <TimelineView events={events} chartId={id} />
    </ZoneRoot>
  )
}
