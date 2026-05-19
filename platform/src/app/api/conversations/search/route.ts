import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors/errors'

interface SearchResult {
  id: string
  title: string
  snippet: string
}

export async function GET(req: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { searchParams } = new URL(req.url)
  const q = (searchParams.get('q') ?? '').trim()
  const limit = Math.min(parseInt(searchParams.get('limit') ?? '20', 10), 20)

  if (!q) {
    return Response.json({ conversations: [] })
  }

  try {
    // Combined title ILIKE and body trigram similarity search.
    // Parts_json is a JSONB array of UIMessage parts; we extract the first
    // text part's content as the snippet via jsonb_array_elements.
    const { rows } = await query<{
      id: string
      title: string | null
      snippet: string | null
    }>(
      `SELECT DISTINCT ON (c.id)
         c.id,
         c.title,
         LEFT(
           COALESCE(
             (
               SELECT elem->>'text'
               FROM jsonb_array_elements(cm.parts_json) AS elem
               WHERE elem->>'type' = 'text'
               LIMIT 1
             ),
             ''
           ),
           120
         ) AS snippet
       FROM conversations c
       LEFT JOIN conversation_messages cm ON cm.conversation_id = c.id
       WHERE c.user_id = $1
         AND c.archived_at IS NULL
         AND (
           c.title ILIKE $2
           OR (cm.parts_json IS NOT NULL AND similarity(cm.parts_json::text, $3) > 0.2)
         )
       ORDER BY c.id, COALESCE(c.updated_at, c.created_at) DESC
       LIMIT $4`,
      [user.uid, `%${q}%`, q, limit]
    )

    const conversations: SearchResult[] = rows.map(row => ({
      id: row.id,
      title: row.title ?? 'Untitled',
      snippet: row.snippet ?? '',
    }))

    return Response.json({ conversations })
  } catch {
    return res.dbError()
  }
}
