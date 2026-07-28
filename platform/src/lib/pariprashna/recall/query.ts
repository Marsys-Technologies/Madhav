import 'server-only'
/**
 * recall/query.ts — PB-2 (SMṚTI) lane M-4. DAL half of per-chart recall.
 *
 * Fetches nearest-neighbor prior messages via pgvector, scoped to a chart's
 * OTHER conversations (threads). Uses the pgvector infrastructure that
 * ALREADY EXISTS in this codebase — `conversation_message_embeddings`
 * (`embedding VECTOR(768)`, ivfflat/cosine index `idx_cme_embedding`,
 * `migrations/001_baseline.sql`) — no new table or extension is created by
 * this lane.
 *
 * Content extraction reads BOTH shapes an embedded message may have, so a
 * candidate produced by the ORIGINAL backfill script (legacy `parts_json`
 * blob) and one produced by the M-4-extended backfill (canonical
 * `message_parts` text/reasoning rows, M-1's schema) are both eligible:
 *   - canonical rows (M-1, migration 467): `message_parts` where
 *     `kind IN ('text','reasoning')`, seq-ordered.
 *   - legacy rows: the first `parts_json` element with `type = 'text'`
 *     (mirrors `scripts/backfill_conversation_embeddings.ts`'s own extraction).
 * The canonical shape is preferred (COALESCE) when both are present.
 */
import { query } from '@/lib/db/client'
import type { RecallCandidate, RecallQueryInput } from './types'

const DEFAULT_CANDIDATE_LIMIT = 25

interface CandidateRow {
  message_id: string
  conversation_id: string
  conversation_title: string | null
  created_at: string
  content: string | null
  distance: number
}

/**
 * Fetch cross-thread candidate messages for `input.chartId`, nearest-neighbor
 * ordered by cosine distance to `input.queryEmbedding`. Excludes
 * `input.excludeConversationId` (the calling turn's OWN thread) so recall
 * never "recalls" the very conversation asking the question. Returns
 * candidates with non-empty content only — a message with no extractable
 * text/reasoning content cannot be a "prior conclusion".
 */
export async function fetchCrossThreadCandidates(
  input: RecallQueryInput,
): Promise<RecallCandidate[]> {
  const vecLiteral = `[${input.queryEmbedding.join(',')}]`
  const candidateLimit = input.candidateLimit ?? DEFAULT_CANDIDATE_LIMIT

  const { rows } = await query<CandidateRow>(
    `SELECT cm.id                AS message_id,
            cm.conversation_id   AS conversation_id,
            co.title             AS conversation_title,
            cm.created_at        AS created_at,
            COALESCE(
              (SELECT string_agg(mp.body->>'text', E'\\n\\n' ORDER BY mp.seq)
                 FROM message_parts mp
                WHERE mp.message_id = cm.id
                  AND mp.kind IN ('text', 'reasoning')
                  AND (mp.body->>'text') IS NOT NULL
                  AND (mp.body->>'text') <> ''),
              (SELECT (elem->>'text')
                 FROM jsonb_array_elements(cm.parts_json) AS elem
                WHERE elem->>'type' = 'text'
                  AND (elem->>'text') IS NOT NULL
                  AND (elem->>'text') <> ''
                LIMIT 1)
            )                    AS content,
            (e.embedding <=> $1::vector) AS distance
       FROM conversation_message_embeddings e
       JOIN conversation_messages cm ON cm.id = e.message_id
       JOIN conversations co        ON co.id = cm.conversation_id
      WHERE co.chart_id = $2
        AND ($3::uuid IS NULL OR cm.conversation_id <> $3::uuid)
      ORDER BY distance ASC
      LIMIT $4`,
    [vecLiteral, input.chartId, input.excludeConversationId ?? null, candidateLimit],
  )

  return rows
    .filter((r) => r.content != null && r.content.trim().length > 0)
    .map((r) => ({
      message_id: r.message_id,
      conversation_id: r.conversation_id,
      conversation_title: r.conversation_title,
      created_at: r.created_at,
      content: r.content as string,
      similarity: 1 - r.distance,
    }))
}
