import { readCockpitChartIdentity } from '@/lib/charts/pageIdentity'
import { redirect } from 'next/navigation'
import { readCockpitLatestBuild } from '@/lib/build/cockpitLatestBuild'
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
  const { rows: chartRows } = await readCockpitChartIdentity(id)
  const chart = chartRows[0]
  if (!chart) redirect('/dashboard')

  // Latest build — `builds` was retired; graceful null if table absent
  // Current run metadata has no governed ayanamsha selection/count. Keep this
  // projection to observed run fields; the Shell discloses the count as unavailable.
  const { latestBuild, latestBuildUnavailable } = await readCockpitLatestBuild(id)

  return (
    <CockpitShell
      chartId={id}
      chartName={chart.name}
      birthDate={chart.birth_date}
      birthTime={chart.birth_time}
      birthPlace={chart.birth_place}
      latestBuild={latestBuild}
      latestBuildUnavailable={latestBuildUnavailable}
    />
  )
}
