import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { redirect } from 'next/navigation'
import { ConsumeChat } from '@/components/consume/ConsumeChat'
import { listConversations } from '@/lib/conversations'
import { configService } from '@/lib/config/index'
import type { AudienceTier } from '@/lib/prompts/types'

export default async function ConsumePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  const user = await getServerUser()
  if (!user) redirect('/login')

  const [profileResult, chartResult] = await Promise.all([
    query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid]),
    query<{ name: string; birth_date: string; birth_place: string; client_id: string }>(
      'SELECT name, birth_date, birth_place, client_id FROM charts WHERE id=$1',
      [id]
    ),
  ])

  const profile = profileResult.rows[0] ?? null
  const chart = chartResult.rows[0] ?? null

  if (!chart) redirect('/dashboard')
  if (profile?.role !== 'super_admin' && chart.client_id !== user.uid) redirect('/dashboard')

  const [reportsResult, conversations] = await Promise.all([
    query('SELECT * FROM reports WHERE chart_id=$1 ORDER BY domain ASC', [id]),
    listConversations({ chartId: id, userId: user.uid, module: 'consume' }),
  ])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const reports = reportsResult.rows as any[]

  const chartMeta = [chart.birth_date, chart.birth_place].filter(Boolean).join(' · ')

  const panelModeEnabled = configService.getFlag('PANEL_MODE_ENABLED')
  const audienceTier: AudienceTier = profile?.role === 'super_admin' ? 'super_admin' : 'client'

  return (
    <ConsumeChat
      chartId={id}
      chartName={chart.name}
      chartMeta={chartMeta}
      reports={reports}
      conversations={conversations.map(c => ({
        id: c.id,
        title: c.title,
        created_at: c.created_at,
        chart_id: c.chart_id,
        user_id: c.user_id,
        module: c.module,
      }))}
      panelModeEnabled={panelModeEnabled}
      audienceTier={audienceTier}
    />
  )
}
