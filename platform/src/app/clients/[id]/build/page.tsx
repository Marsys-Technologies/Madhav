import { redirect } from 'next/navigation'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import ConstellationCanvas from '@/components/build_orchestrator/ConstellationCanvas'
import { BuildButton } from '@/components/cockpit/BuildButton'

// This page replaces the old BuildChat shell with the Constellation visualization.
// BuildButton is wired in as the primary build trigger (C-S8.5).
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
      <div data-testid="build-button-container">
        <BuildButton chartId={id} />
      </div>
      <ConstellationCanvas chartId={id} />
    </div>
  )
}
