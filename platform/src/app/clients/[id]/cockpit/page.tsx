import { redirect } from 'next/navigation'
import { query } from '@/lib/db/client'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CockpitShell } from '@/components/cockpit/CockpitShell'

export default async function CockpitPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')
  if (!access.canBuild) redirect(`/clients/${id}`)

  // Chart meta
  const { rows: chartRows } = await query<{
    id: string
    name: string
    birth_date: string
    birth_time: string
    birth_place: string
    created_at: string
  }>(
    'SELECT id, name, birth_date, birth_time::text AS birth_time, birth_place, created_at FROM charts WHERE id=$1',
    [id],
  )
  const chart = chartRows[0]
  if (!chart) redirect(`/clients`)

  // Latest build
  const { rows: buildRows } = await query<{
    build_id: string
    status: string
    created_at: string
    ayanamshas: string[]
  }>(
    `SELECT id AS build_id, status, created_at, ayanamshas
     FROM builds WHERE chart_id=$1 ORDER BY created_at DESC LIMIT 1`,
    [id],
  )
  const latestBuild = buildRows[0] ?? null

  return (
    <CockpitShell
      chartId={id}
      chartName={chart.name}
      birthDate={chart.birth_date}
      birthTime={chart.birth_time}
      birthPlace={chart.birth_place}
      latestBuild={latestBuild}
    />
  )
}
