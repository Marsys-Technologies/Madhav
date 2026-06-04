import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors/errors'
import { embedText } from '@/lib/embeddings/embedText'
import { getFlag } from '@/lib/config'

interface SearchResult {
  id: string
  title: string
  snippet: string
  score?: number
}

const TRGM_SQL = `
  SELECT DISTINCT ON (c.id)
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
         ) AS snippet,
         GREATEST(
           similarity(COALESCE(c.title, ''), $3),
           similarity(cm.parts_json::text, $3)
         ) AS trgm_score
  FROM conversations c
  LEFT JOIN conversation_messages cm ON cm.conversation_id = c.id
  WHERE c.user_id = $1
    AND c.archived_at IS NULL
    AND (
      c.title ILIKE $2
      OR (cm.parts_json IS NOT NULL AND similarity(cm.parts_json::text, $3) > 0.2)
    )
  ORDER BY c.id, COALESCE(c.updated_at, c.created_at) DESC
  LIMIT $4
`

const COSINE_SQL = `
  SELECT cme.message_id,
         cm.conversation_id,
         1 - (cme.embedding <=> $1::vector) AS cosine_score
  FROM conversation_message_embeddings cme
  JOIN conversation_messages cm ON cm.id = cme.message_id
  JOIN conversations c ON c.id = cm.conversation_id
  WHERE c.user_id = $2
    AND c.archived_at IS NULL
  ORDER BY cme.embedding <=> $1::vector
  LIMIT 50
`

export async function GET(req: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { searchParams } = new URL(req.url)
  const q = (searchParams.get('q') ?? '').trim()
  const limit = Math.min(parseInt(searchParams.get('limit') ?? '20', 10), 20)
  const semanticRequested =
    searchParams.get('semantic') === 'true' &&
    true

  if (!q) {
    return Response.json({ conversations: [] })
  }

  // ── Trgm path (always runs) ────────────────────────────────────────────────

  let trgmRows: Array<{ id: string; title: string | null; snippet: string | null; trgm_score: number }> = []
  try {
    const { rows } = await query<{
      id: string
      title: string | null
      snippet: string | null
      trgm_score: number
    }>(TRGM_SQL, [user.uid, `%${q}%`, q, limit])
    trgmRows = rows
  } catch {
    return res.dbError()
  }

  // ── Semantic path (only when flag ON and ?semantic=true) ───────────────────

  if (!semanticRequested) {
    const conversations: SearchResult[] = trgmRows.map(row => ({
      id: row.id,
      title: row.title ?? 'Untitled',
      snippet: row.snippet ?? '',
    }))
    return Response.json({ conversations })
  }

  // Embed query — fall back to trgm-only on failure.
  let queryEmbedding: number[]
  try {
    queryEmbedding = await embedText(q)
  } catch (err) {
    console.error('[semantic-search] embed failed, falling back to trgm', err)
    const conversations: SearchResult[] = trgmRows.map(row => ({
      id: row.id,
      title: row.title ?? 'Untitled',
      snippet: row.snippet ?? '',
    }))
    return new Response(JSON.stringify({ conversations }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'X-Search-Mode': 'trgm-fallback',
      },
    })
  }

  const vecParam = '[' + queryEmbedding.join(',') + ']'
  let cosineRows: Array<{ message_id: string; conversation_id: string; cosine_score: number }> = []
  try {
    const { rows } = await query<{
      message_id: string
      conversation_id: string
      cosine_score: number
    }>(COSINE_SQL, [vecParam, user.uid])
    cosineRows = rows
  } catch {
    // Cosine query failed (e.g. pgvector not available) — degrade to trgm-only.
    const conversations: SearchResult[] = trgmRows.map(row => ({
      id: row.id,
      title: row.title ?? 'Untitled',
      snippet: row.snippet ?? '',
    }))
    return new Response(JSON.stringify({ conversations }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'X-Search-Mode': 'trgm-fallback',
      },
    })
  }

  // ── Hybrid merge + scoring ─────────────────────────────────────────────────

  // Map trgm results: conversationId → { title, snippet, trgm_score }
  const trgmMap = new Map(
    trgmRows.map(r => [r.id, { title: r.title ?? 'Untitled', snippet: r.snippet ?? '', trgm_score: r.trgm_score }]),
  )

  // Map cosine results: conversationId → best cosine_score
  const cosineMap = new Map<string, number>()
  for (const row of cosineRows) {
    const existing = cosineMap.get(row.conversation_id) ?? 0
    if (row.cosine_score > existing) cosineMap.set(row.conversation_id, row.cosine_score)
  }

  // Union of all conversation IDs
  const allIds = new Set([...trgmMap.keys(), ...cosineMap.keys()])

  // For cosine-only hits, fetch title+snippet
  const missingIds = [...allIds].filter(id => !trgmMap.has(id))
  if (missingIds.length > 0) {
    try {
      const { rows } = await query<{ id: string; title: string | null; snippet: string | null }>(
        `SELECT c.id,
                c.title,
                LEFT(
                  COALESCE(
                    (SELECT elem->>'text' FROM jsonb_array_elements(cm.parts_json) AS elem
                     WHERE elem->>'type' = 'text' LIMIT 1),
                    ''
                  ),
                  120
                ) AS snippet
         FROM conversations c
         LEFT JOIN LATERAL (
           SELECT parts_json FROM conversation_messages
           WHERE conversation_id = c.id
           ORDER BY created_at DESC LIMIT 1
         ) cm ON true
         WHERE c.id = ANY($1::text[]) AND c.user_id = $2`,
        [missingIds, user.uid],
      )
      for (const r of rows) {
        trgmMap.set(r.id, { title: r.title ?? 'Untitled', snippet: r.snippet ?? '', trgm_score: 0 })
      }
    } catch {
      // Best-effort — continue with what we have
    }
  }

  type ScoredResult = { id: string; title: string; snippet: string; score: number }
  const scored: ScoredResult[] = []

  for (const id of allIds) {
    const trgm = trgmMap.get(id)
    const cosine = cosineMap.get(id) ?? 0
    const trgmScore = trgm?.trgm_score ?? 0
    let boost = 0
    if (cosine >= 0.78) boost += 2
    if (trgmScore >= 0.3) boost += 1
    scored.push({
      id,
      title: trgm?.title ?? 'Untitled',
      snippet: trgm?.snippet ?? '',
      score: cosine + boost,
    })
  }

  scored.sort((a, b) => b.score - a.score)

  const conversations: SearchResult[] = scored.slice(0, limit).map(r => ({
    id: r.id,
    title: r.title,
    snippet: r.snippet,
    score: r.score,
  }))

  return Response.json({ conversations })
}
