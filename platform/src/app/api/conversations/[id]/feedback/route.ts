/**
 * GET/POST /api/conversations/[id]/feedback — message rating + dispute capture.
 *
 * `message_feedback` (the dedicated table) was dropped in WS-0. This route was left as
 * an unconditional stub: GET always returned `{ feedback: [] }` and POST always
 * returned `{ ok: true, rating: ... }` without ever touching a database — a reader's
 * thumbs-down (or a future dispute comment) was accepted, acknowledged with a 200, and
 * silently discarded. Restored here per `BRAHMA_DEFERRED_FEATURES.md` §4's own named
 * option: an additive `feedback` sub-object on `conversation_messages.metadata_json`
 * (the existing free-form jsonb column), the SAME convention already used for
 * `provenance_stamp` and `acharya_reading_receipt` (see
 * `platform/src/lib/pariprashna/receipt/store.ts`) — no migration, no new table.
 *
 * Ownership check brought to parity with every sibling `[id]` route
 * (`route.ts`, `messages/route.ts`, `branches/route.ts`, `export/route.ts`,
 * `share/route.ts`): this was the only route in the directory that skipped
 * `getConversation`'s ownership check entirely.
 *
 * Residual silent-failure guard: an UPDATE that matches zero rows (message does not
 * belong to this conversation, or does not exist) now returns 404, never the old
 * unconditional `{ ok: true }` — a write that did not land must never be reported as a
 * success.
 */
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { res } from '@/lib/errors'

const FEEDBACK_METADATA_KEY = 'feedback' as const

async function resolveAccess(userId: string): Promise<boolean> {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId],
  )
  return result.rows[0]?.role === 'super_admin'
}

interface FeedbackRow {
  id: string
  rating: 1 | -1 | null
  comment: string | null
}

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const { rows } = await query<FeedbackRow>(
      `SELECT id,
              (metadata_json #>> '{${FEEDBACK_METADATA_KEY},rating}')::smallint AS rating,
              metadata_json #>> '{${FEEDBACK_METADATA_KEY},comment}' AS comment
         FROM conversation_messages
        WHERE conversation_id = $1
          AND metadata_json -> '${FEEDBACK_METADATA_KEY}' ->> 'rating' IS NOT NULL`,
      [id],
    )

    return Response.json({
      feedback: rows.map((r) => ({ message_id: r.id, rating: r.rating, comment: r.comment })),
    })
  } catch {
    return res.dbError()
  }
}

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { messageId?: unknown; rating?: unknown; comment?: unknown }
  try {
    body = await req.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const messageId = body.messageId
  if (typeof messageId !== 'string' || !messageId) {
    return res.badRequest('messageId required')
  }
  const rating = body.rating
  if (rating !== 1 && rating !== -1 && rating !== null) {
    return res.badRequest('rating must be 1, -1, or null')
  }
  // Free-text dispute/explanation, additive to the existing thumbs rating (the
  // pre-WS-0 `message_feedback.comment` column's shape). Not yet surfaced by the
  // client UI (`useFeedback` only sends `rating`), but the capture path honestly
  // supports it now rather than needing a second migration-of-behavior later.
  const comment =
    typeof body.comment === 'string' && body.comment.trim().length > 0
      ? body.comment.trim().slice(0, 4000)
      : null

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const feedbackPayload = JSON.stringify({
      rating,
      comment,
      user_id: user.uid,
      updated_at: new Date().toISOString(),
    })

    const { rowCount } = await query(
      `UPDATE conversation_messages
          SET metadata_json = jsonb_set(
                coalesce(metadata_json, '{}'::jsonb),
                '{${FEEDBACK_METADATA_KEY}}',
                $3::jsonb,
                true
              )
        WHERE id = $1 AND conversation_id = $2`,
      [messageId, id, feedbackPayload],
    )

    // §N.8 / no-silent-discard: the pre-fix stub returned `{ ok: true }`
    // unconditionally, with no query ever run. A zero-row UPDATE (message does not
    // exist, or belongs to a different conversation) must not be reported as a
    // captured submission either — 404, not a hollow 200.
    if (!rowCount) return res.notFound('message')

    return Response.json({ ok: true, rating, comment })
  } catch {
    return res.dbError()
  }
}
