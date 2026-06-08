import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CockpitShell } from '@/lib/components/cockpit/v2/CockpitShell'
import { query } from '@/lib/db/client'

// v2 cockpit — replaces legacy ConstellationCanvas per VISUAL_CONTRACT v2 §C-S8.5.
// CockpitShell assembles LiveDependencyGraph, OverallProgress, TelemetryStrip,
// AssetTable, and BuildControlsBar with built-in polling + SSE subscriptions.
export default async function BuildPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const access = await resolveChartPageAccess(id)
  if (!access) redirect('/login')

  // Build is owner/super_admin only. View-only grantees are explicitly NOT
  // allowed in (per Unit 3.consult_nav AC.1 — granted chart shows no Build).
  if (!access.canBuild) redirect(`/clients/${id}`)

  // Prefetch chart metadata server-side so CockpitShell doesn't show "Loading chart…"
  const { rows: chartRows } = await query<{ subject_name: string | null; birth_date: string | null; birth_time: string | null; birth_place: string | null }>(
    'SELECT subject_name, birth_date, birth_time::text, birth_place FROM charts WHERE id=$1',
    [id]
  ).catch(() => ({ rows: [] }))
  const initialChartMeta = chartRows[0] ?? null

  return (
    <div data-testid="build-page-root" data-permission={access.permission}>
      <CockpitShell chartId={id} initialChartMeta={initialChartMeta} />
    </div>
  )
}
