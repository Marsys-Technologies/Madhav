import 'server-only'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const runtime = 'nodejs'

/**
 * γ7: Stream-resume endpoint.
 *
 * GET /api/chat/consult/resume?query_id=<UUID>[&since_chars=<N>]
 *
 * Returns the partial synthesis output stored in pending_streams as JSON so
 * the client can restore mid-stream text after a disconnect (tab close, network
 * partition). If the row has been deleted (stream completed + β2 persisted),
 * returns 404 and the client falls back to conversation-list restore.
 *
 * `since_chars` — number of characters the client already rendered; the
 * endpoint returns only the suffix. Defaults to 0 (return everything).
 */
export async function GET(request: Request) {
  const user = await getServerUser()
  if (!user) return new Response('Unauthorized', { status: 401 })

  const url = new URL(request.url)
  const queryId = url.searchParams.get('query_id')
  const sinceChars = Math.max(0, parseInt(url.searchParams.get('since_chars') ?? '0', 10))

  if (!queryId) return new Response('Missing query_id', { status: 400 })

  const result = await query(
    `SELECT accumulated_text, last_event_seq
     FROM pending_streams
     WHERE query_id = $1 AND user_id = $2 AND expires_at > now()`,
    [queryId, user.uid],
  )

  if (!result.rows.length) {
    return new Response(null, { status: 404 })
  }

  const accumulatedText = (result.rows[0].accumulated_text as string) ?? ''
  const suffix = sinceChars > 0 ? accumulatedText.slice(sinceChars) : accumulatedText

  if (!suffix) {
    return new Response(null, { status: 204 })
  }

  return Response.json({
    query_id: queryId,
    text: suffix,
    since_chars: sinceChars,
    last_event_seq: result.rows[0].last_event_seq as number,
  })
}
