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

  // Latest build — `builds` was retired; graceful null if table absent
  let latestBuild: { build_id: string; status: string; created_at: string; ayanamshas: string[] } | null = null
  try {
    const { rows: buildRows } = await query<{
      build_id: string
      status: string
      created_at: string
      ayanamshas: string[]
    }>(
      `SELECT id AS build_id, state AS status, created_at, '{}'::text[] AS ayanamshas
       FROM build_runs WHERE chart_id=$1 ORDER BY created_at DESC LIMIT 1`,
      [id],
    )
    latestBuild = buildRows[0] ?? null
  } catch {
    // build_runs unavailable — CockpitShell degrades gracefully with latestBuild=null
  }

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
