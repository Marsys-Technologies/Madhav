import { getServerUser } from '@/lib/firebase/server'
import { resolveChartPageAccess } from '@/lib/auth/chart-page-guard'
import { query } from '@/lib/db/client'
import { redirect, notFound } from 'next/navigation'
import { ConsumeChat } from '@/components/consume/ConsumeChat'
import {
  getConversation,
  listConversations,
} from '@/lib/conversations'
import { loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
import { configService } from '@/lib/config/index'
import type { AudienceTier } from '@/lib/prompts/types'
import { isCorrectionArchived } from '@/lib/conversations/readOnly'
import { loadHistoricalConversationMessages } from '@/lib/conversations/historicalReading'
import { HistoricalConversationView } from '@/components/consume/HistoricalConversationView'
import '@/components/profile/jataka-workspace.css'

export default async function ConsultConversationPage({
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

  const conversation = await getConversation({
    id: conversationId,
    userId: user.uid,
    isSuperAdmin,
  })
  // History links use current chart access plus the conversation ownership checked
  // above. Render correction archives without a composer.
  if (conversation?.chart_id === id && isCorrectionArchived(conversation)) {
    if (!isSuperAdmin) {
      const access = await resolveChartPageAccess(id)
      if (access?.user.uid !== user.uid || access.permission === 'deny') redirect('/dashboard')
    }
    const historicalMessages = await loadHistoricalConversationMessages(conversationId)
    return <HistoricalConversationView conversation={conversation} messages={historicalMessages} />
  }

  if (!isSuperAdmin && chart.client_id !== user.uid) redirect('/dashboard')
  if (!conversation || conversation.chart_id !== id) notFound()

  // LCA-2 / WP-1.1: the legacy `reports` relation was RETIRED (DDL only in
  // platform/migrations/_archive; ABSENT from deployed Cloud SQL). The prior
  // `SELECT * FROM reports` here raised a permanent 42P01 (undefined_table) that
  // crashed this server-component render for EVERY chart. We do NOT resurrect the
  // table: resolve an empty result so the page always renders and ConsumeChat
  // receives no legacy domain reports (content comes from the live retrieval path).
  const [reportsResult, conversations, messages] = await Promise.all([
    Promise.resolve({ rows: [] as unknown[] }),
    listConversations({ chartId: id, userId: user.uid, module: 'consume' }),
    loadConversationMessagesV2(conversationId),
  ])
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const reports = reportsResult.rows as any[]

  const chartMeta = [chart.birth_date, chart.birth_place].filter(Boolean).join(' · ')

  const panelModeEnabled = configService.getFlag('PANEL_MODE_ENABLED')
  const costVisibilityEnabled = configService.getFlag('COST_VISIBILITY_FOR_USERS')
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
      costVisibilityEnabled={costVisibilityEnabled}
      audienceTier={audienceTier}
    />
  )
}
