import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { res } from '@/lib/errors'

/**
 * POST /api/chat/consume/regenerate
 *
 * Called when the client commits an edit to a past user message and re-runs
 * synthesis from that branch point. Responsibility: truncate conversation_messages
 * after the branch point so persistence reflects the new branch.
 *
 * The actual synthesis is performed by the normal consume route — the client
 * re-submits with the truncated message history after calling this endpoint.
 *
 * Body:
 *   { conversation_id: string, parent_message_id: string }
 *
 * parent_message_id is the ID of the last message to KEEP (the edited user
 * message). All conversation_messages created AFTER parent_message_id are deleted.
 */
export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { conversation_id?: string; parent_message_id?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const { conversation_id, parent_message_id } = body
  if (!conversation_id) return res.badRequest('conversation_id required')
  if (!parent_message_id) return res.badRequest('parent_message_id required')

  // Resolve access: owner or super_admin.
  let isSuperAdmin = false
  try {
    const result = await query<{ role: string }>(
      'SELECT role FROM profiles WHERE id=$1',
      [user.uid],
    )
    isSuperAdmin = result.rows[0]?.role === 'super_admin'
  } catch {
    return res.dbError()
  }

  const conv = await getConversation({
    id: conversation_id,
    userId: user.uid,
    isSuperAdmin,
  }).catch(() => null)

  if (!conv) return res.notFound('conversation')

  // Get the created_at timestamp of the parent message so we can delete everything after it.
  let parentCreatedAt: string | null = null
  try {
    const { rows } = await query<{ created_at: string }>(
      'SELECT created_at FROM conversation_messages WHERE id=$1 AND conversation_id=$2',
      [parent_message_id, conversation_id],
    )
    parentCreatedAt = rows[0]?.created_at ?? null
  } catch {
    return res.dbError()
  }

  if (!parentCreatedAt) {
    return res.notFound('parent_message')
  }

  // Delete all conversation_messages created strictly after the parent message.
  try {
    await query(
      'DELETE FROM conversation_messages WHERE conversation_id=$1 AND created_at > $2',
      [conversation_id, parentCreatedAt],
    )
  } catch {
    return res.dbError()
  }

  return Response.json({ ok: true, truncated_after: parent_message_id })
}
