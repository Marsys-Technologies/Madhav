import { redirect } from 'next/navigation'
import { query } from '@/lib/db/client'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { configService } from '@/lib/config/index'
import { PariprashnaApp } from '@/components/pariprashna/PariprashnaApp'

function formatBornLine(birthDate: string, birthTime: string, birthPlace: string): string {
  let dateLabel = birthDate
  try {
    const d = new Date(birthDate)
    if (!Number.isNaN(d.getTime())) {
      dateLabel = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    }
  } catch {
    // fall back to the raw string
  }
  const timeLabel = birthTime ? birthTime.slice(0, 5) : ''
  return [dateLabel, timeLabel, birthPlace].filter(Boolean).join(' · ')
}

/**
 * Paripraśna — the new adaptive conversation surface (lane C-1, PB-1
 * DHĀRĀ). Server component: resolves chart access + the chart pin (name +
 * birth line) exactly like the existing `consult` route, then hands off to
 * the client-rendered `<PariprashnaApp>`. Does NOT touch the existing
 * `consume`/`consult` chat trees — this is a wholly new route + component
 * tree per this lane's file scope.
 *
 * TRANSPORT: `PariprashnaApp` picks its transport at mount. With
 * `NEXT_PUBLIC_PARIPRASHNA_LIVE=1` (deploy-behind-a-flag), it opens a REAL SSE
 * stream against lane S-1's `/api/pariprashna` route via `useLiveStream`;
 * otherwise it replays canned fixtures via `useFixtureStream` (dev / component
 * work). Either way this page wires real chart identity + auth and passes the
 * chartId the live route requires.
 */
export default async function PariprashnaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params

  // PB-1 rollback gate — flag OFF means this surface does not exist yet for
  // this deploy; send the native back to the existing consult page for the
  // same chart rather than rendering a half-wired route.
  if (!configService.getFlag('PARIPRASHNA_ENABLED')) {
    redirect(`/clients/${id}/consult`)
  }

  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (access.permission === 'deny') redirect('/dashboard')

  const chartResult = await query<{ name: string; birth_date: string; birth_time: string; birth_place: string }>(
    'SELECT name, birth_date, birth_time, birth_place FROM charts WHERE id=$1',
    [id],
  )
  const chart = chartResult.rows[0] ?? null
  if (!chart) redirect('/dashboard')

  return (
    <PariprashnaApp
      chartId={id}
      chartPin={{
        name: chart.name,
        bornLine: formatBornLine(chart.birth_date, chart.birth_time, chart.birth_place),
      }}
    />
  )
}
