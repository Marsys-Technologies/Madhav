import 'server-only'
import { query } from '@/lib/db/client'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import { readingMessages } from '@/lib/conversations/reading'
import { filterMessages } from './filterMessages'
import type { UIMessage } from 'ai'

export async function publicReading(slug: string) {
  // Do not select private conversation/message metadata on the public door.
  const { rows } = await query<{ conversation_id: string; message_id: string | null; hide_reasoning: boolean; hide_methodology: boolean;
    chart_id: string; user_id: string; role: string; status: string; title: string | null; revoked_at: string | null; expires_at: string | null }>(`SELECT s.conversation_id, s.message_id, s.hide_reasoning, s.hide_methodology,
      s.revoked_at, s.expires_at, c.chart_id, c.user_id, c.title, p.role, p.status
    FROM conversation_shares s JOIN conversations c ON c.id=s.conversation_id
      JOIN profiles p ON p.id=c.user_id WHERE s.slug=$1 AND s.created_by=c.user_id`, [slug])
  const share = rows[0]
  if (!share) return { state: 'missing' as const }
  if (share.revoked_at || (share.expires_at && new Date(share.expires_at).getTime() <= Date.now())) return { state: 'unavailable' as const }
  if (share.status !== 'active') return { state: 'unavailable' as const }
  const permission = await authorizeChartAccess({ principal: { uid: share.user_id, role: share.role === 'super_admin' ? 'super_admin' : 'guest' }, chartId: share.chart_id, db: { query } })
  if (permission === 'deny') return { state: 'unavailable' as const }
  const messages = await readingMessages(share.conversation_id, share.message_id, !share.hide_reasoning)
  if (messages.length === 0) return { state: 'unavailable' as const }
  // A thread title may describe an excluded earlier question.
  return { state: 'ready' as const, title: share.message_id ? 'Consultation answer' : share.title ?? 'Shared reading',
    messages: filterMessages(messages, share.hide_reasoning, share.hide_methodology) as UIMessage[] }
}
