import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { fetchBuildState } from '@/lib/build/dataSource'
import { listConversations } from '@/lib/conversations'
import { BuildChat } from '@/components/build/BuildChat'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'

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

  const [layersResult, chartResult, conversations, state] = await Promise.all([
    query<{ layer: string; sublayer: string; status: 'not_started' | 'in_progress' | 'complete' }>(
      'SELECT layer, sublayer, status FROM pyramid_layers WHERE chart_id=$1 ORDER BY layer, sublayer',
      [id]
    ),
    query<{ id: string; name: string }>(
      'SELECT id, name FROM charts WHERE id=$1',
      [id]
    ),
    listConversations({ chartId: id, userId: access.user.uid, module: 'build' }),
    fetchBuildState(),
  ])

  if (!chartResult.rows[0]) redirect('/dashboard')
  const chart = chartResult.rows[0]

  const insights = layersResult.rows
    .filter(l => l.status === 'complete')
    .slice(-5)
    .map(l => ({
      id: `${l.layer}-${l.sublayer}`,
      severity: 'positive' as const,
      text: `${l.layer}${l.sublayer ? ` / ${l.sublayer}` : ''} built`,
    }))

  return (
    <div data-testid="build-page-root" data-permission={access.permission}>
    <BuildChat
      chartId={id}
      chartName={chart.name}
      conversations={conversations}
      arc={state.macro_phase.macro_arc}
      activePhaseId={state.macro_phase.id}
      brief={state.current_brief}
      insights={insights}
      mirrorPairs={state.mirror_pairs}
      layers={layersResult.rows}
    />
    </div>
  )
}
