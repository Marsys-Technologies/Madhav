import 'server-only'
import { query } from '@/lib/db/client'
import { loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
import { buildShareViewMessages, type ShareViewMessage } from '@/lib/share/shareView'

export interface SharedConversationView {
  title: string | null
  optionalChartName: string | undefined
  visibleMessages: ShareViewMessage[]
}

/**
 * Call only after the page's verified ACTIVE-user guard. Any such viewer with the
 * slug is eligible; no owner/admin restriction or second profile read is added.
 * A nonempty UID is only a presence precondition, not proof of authentication.
 * Reduce stored messages here before any client-component props are constructed.
 */
export async function readSharedConversationView(params: {
  slug: string
  verifiedViewerUid: string
}): Promise<SharedConversationView | null> {
  if (!params.verifiedViewerUid) return null
  const { slug } = params
  const shareResult = await query<{
    conversation_id: string
    revoked_at: string | null
    expires_at: string | null
    hide_reasoning: boolean
    hide_methodology: boolean
  }>(
    'SELECT conversation_id, revoked_at, expires_at, hide_reasoning, hide_methodology FROM conversation_shares WHERE slug=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())',
    [slug]
  )
  const share = shareResult.rows[0] ?? null

  if (!share) return null

  // SS N-379: read only what the page renders (no SELECT *).
  const conversationResult = await query<{
    title: string | null
    chart_id: string
  }>('SELECT title, chart_id FROM conversations WHERE id=$1', [share.conversation_id])
  const conversation = conversationResult.rows[0] ?? null
  if (!conversation) return null

  const chartResult = await query<{ name: string }>(
    'SELECT name FROM charts WHERE id=$1',
    [conversation.chart_id]
  )
  const chart = chartResult.rows[0] ?? null

  const messages = await loadConversationMessagesV2(share.conversation_id, { includeCanonicalText: true })

  // X-S8 / SS N-379: the STORED hide options of the share row are ALWAYS applied,
  // whatever R10_SELECTIVE_SHARE says. The flag only controls whether the options
  // are OFFERED on NEW shares (the dialog control and the POST body parsing): a
  // switch must never un-hide content someone chose to hide.
  //
  // The reduction happens HERE, on the server: SharedConversation is a client
  // component, so anything passed to it is in the RSC payload the viewer's browser
  // receives. buildShareViewMessages applies the hide options and then builds a NEW
  // minimal message per turn (text only, opaque display role); tool-call parts,
  // data-* parts and message metadata never leave the server.
  const visibleMessages = buildShareViewMessages(
    messages,
    share.hide_reasoning === true,
    share.hide_methodology === true,
  )

  return { title: conversation.title, optionalChartName: chart?.name, visibleMessages }
}
