import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { archivedReadOnlyResponse, isCorrectionArchived } from '@/lib/conversations/readOnly'
import { checkReadingReadiness } from '@/lib/charts/readingGate'
import { errorResponse, res } from '@/lib/errors'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/**
 * POST /api/chat/consult/regenerate
 *
 * Called when the client commits an edit to a past user message and re-runs
 * synthesis from that branch point. Responsibility: truncate conversation_messages
 * after the branch point so persistence reflects the new branch.
 *
 * The actual synthesis is performed by the normal consult route — the client
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

  let body: { conversation_id?: unknown; parent_message_id?: unknown } | null
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  if (!body || typeof body !== 'object') return res.badRequest('invalid body')
  const { conversation_id, parent_message_id } = body
  if (!conversation_id) return res.badRequest('conversation_id required')
  if (!parent_message_id) return res.badRequest('parent_message_id required')
  if (typeof conversation_id !== 'string' || !UUID_RE.test(conversation_id)) {
    return res.badRequest('Invalid conversation_id')
  }
  if (typeof parent_message_id !== 'string' || !UUID_RE.test(parent_message_id)) {
    return res.badRequest('Invalid parent_message_id')
  }

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
  // Jātaka chart workspace: history archived by a chart-details correction is read-only.
  if (isCorrectionArchived(conv)) return archivedReadOnlyResponse()

  // Same shared readiness gate as the legacy consult door, checked
  // before the truncation so a refused re-post never strands a shortened
  // conversation.
  const readingGate = await checkReadingReadiness(conv.chart_id)
  if (!readingGate.ok) {
    return errorResponse(readingGate.code, readingGate.message, 409, { retry: readingGate.retryable })
  }

  // Lock and inspect the stored parent in the same statement as the delete.
  // A stale client can omit attachments from its follow-up Consult request.
  let parent: { has_attachment: boolean } | undefined
  try {
    const { rows } = await query<{ has_attachment: boolean }>(
      `WITH parent AS MATERIALIZED (
        SELECT created_at, EXISTS (
          SELECT 1
          FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(parts_json) = 'array' THEN parts_json ELSE '[]'::jsonb END
          ) AS part
          WHERE part->>'type' IN ('file', 'image', 'audio')
        ) AS has_attachment
        FROM conversation_messages
        WHERE id=$1 AND conversation_id=$2
        FOR UPDATE
      ), truncated AS (
        DELETE FROM conversation_messages
        USING parent
        WHERE conversation_messages.conversation_id=$2
          AND conversation_messages.created_at > parent.created_at
          AND NOT parent.has_attachment
      )
      SELECT has_attachment FROM parent`,
      [parent_message_id, conversation_id],
    )
    parent = rows[0]
  } catch {
    return res.dbError()
  }

  if (!parent) return res.notFound('parent_message')
  if (parent.has_attachment) {
    const response = errorResponse('ATTACHMENT_UNAVAILABLE',
      'This turn contains an attachment. You can send a new text message.', 503, { retry: false })
    response.headers.set('Cache-Control', 'private, no-store')
    return response
  }

  return Response.json({ ok: true, truncated_after: parent_message_id })
}
