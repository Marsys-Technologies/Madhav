import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { redirect, notFound } from 'next/navigation'
import { ConsumeChat } from '@/components/consume/ConsumeChat'
import {
  getConversation,
  listConversations,
  loadConversationMessages,
} from '@/lib/conversations'
import { configService } from '@/lib/config/index'
import type { AudienceTier } from '@/lib/prompts/types'

export default async function ConsumeConversationPage({
  params,
}: {
  params: Promise<{ id: string; conversationId: string }>
}) {
  const { id, conversationId } = await params

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
  const isSuperAdmin = profile?.role === 'super_admin'
  if (!isSuperAdmin && chart.client_id !== user.uid) redirect('/dashboard')

  const conversation = await getConversation({
    id: conversationId,
    userId: user.uid,
    isSuperAdmin,
  })
  if (!conversation || conversation.chart_id !== id) notFound()

  const [reportsResult, conversations, messages] = await Promise.all([
    query('SELECT * FROM reports WHERE chart_id=$1 ORDER BY domain ASC', [id]),
    listConversations({ chartId: id, userId: user.uid, module: 'consume' }),
    loadConversationMessages(conversationId),
  ])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const reports = reportsResult.rows as any[]

  const chartMeta = [chart.birth_date, chart.birth_place].filter(Boolean).join(' · ')

  const panelModeEnabled = configService.getFlag('PANEL_MODE_ENABLED')
  const consumeUiV2Enabled = configService.getFlag('CONSUME_UI_V2_ENABLED')
  const chatV2Enabled = configService.getFlag('CHAT_V2_ENABLED')
  const audienceTier: AudienceTier = isSuperAdmin ? 'super_admin' : 'client'

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
      currentConversationId={conversationId}
      initialMessages={messages}
      panelModeEnabled={panelModeEnabled}
      consumeUiV2Enabled={consumeUiV2Enabled}
      chatV2Enabled={chatV2Enabled}
      audienceTier={audienceTier}
    />
  )
}
