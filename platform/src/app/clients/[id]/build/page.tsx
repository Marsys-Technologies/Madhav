import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { CockpitShell } from '@/components/cockpit/CockpitShell'

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

  return (
    <div data-testid="build-page-root" data-permission={access.permission}>
      <CockpitShell chartId={id} />
    </div>
  )
}
