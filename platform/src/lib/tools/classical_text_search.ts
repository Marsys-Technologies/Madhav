/**
 * Tool 25: classical_text_search
 * Semantic search over classical_chunks using Vertex AI text-embedding-004 + pgvector cosine similarity.
 * Full implementation M8-E-S1 (2026-05-14).
 */

import 'server-only'
import { GoogleAuth } from 'google-auth-library'
import { query } from '@/lib/db/client'

export interface ClassicalTextSearchInput {
  query: string
  schools?: string[]
  tier_max?: number
  limit?: number
}

export interface ClassicalTextSearchResult {
  chunk_id: string
  text_key: string
  title: string
  author: string | null
  tradition: string
  chapter: string | null
  verse_range: string | null
  content: string
  confidence_baseline: number
  similarity: number
}

export interface ClassicalTextSearchOutput {
  results: ClassicalTextSearchResult[]
  total_searched: number
  query_embedding_dim: number
}

// Must match ingestion pipeline embed model (ingest_utils.py EMBED_MODEL)
const VERTEX_EMBED_MODEL = 'text-embedding-004'
const VERTEX_EMBED_DIM = 768

interface ChunkRow {
  chunk_id: string
  text_key: string
  title: string
  author: string | null
  tradition: string
  chapter: string | null
  verse_range: string | null
  content: string
  attribution_baseline_confidence: number
  distance: number
}

async function embedQuery(queryText: string): Promise<number[]> {
  const project = process.env.GCP_PROJECT ?? ''
  const location = process.env.VERTEX_AI_LOCATION ?? 'us-central1'

  if (!project) {
    throw new Error('GCP_PROJECT env var not set — required for Vertex AI embeddings')
  }

  const endpoint =
    `https://${location}-aiplatform.googleapis.com/v1/projects/${project}` +
    `/locations/${location}/publishers/google/models/${VERTEX_EMBED_MODEL}:predict`

  const auth = new GoogleAuth({ scopes: ['https://www.googleapis.com/auth/cloud-platform'] })
  const client = await auth.getClient()
  const tokenResponse = await client.getAccessToken()
  const token = tokenResponse.token ?? ''

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      instances: [{ task_type: 'RETRIEVAL_QUERY', content: queryText }],
    }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Vertex AI embeddings returned ${response.status}: ${body.slice(0, 200)}`)
  }

  const data = await response.json()
  const values = data.predictions?.[0]?.embeddings?.values as number[] | undefined
  if (!values || values.length !== VERTEX_EMBED_DIM) {
    throw new Error(
      `Vertex AI returned unexpected embedding shape: got ${values?.length ?? 0}, expected ${VERTEX_EMBED_DIM}`
    )
  }
  return values
}

export async function classical_text_search(
  input: ClassicalTextSearchInput
): Promise<ClassicalTextSearchOutput> {
  const { query: queryText, schools, tier_max, limit = 5 } = input

  const embedding = await embedQuery(queryText)
  const embeddingParam = '[' + embedding.join(',') + ']'

  const conditions: string[] = []
  const params: unknown[] = [embeddingParam, Math.min(limit, 20)]
  let idx = 3

  if (schools && schools.length > 0) {
    conditions.push(`ct.school = ANY($${idx++}::text[])`)
    params.push(schools)
  }
  if (tier_max !== undefined) {
    conditions.push(`ct.tier <= $${idx++}`)
    params.push(tier_max)
  }

  // Only search chunks that have embeddings
  conditions.push('cc.embedding IS NOT NULL')

  const where = conditions.length > 0 ? `AND ${conditions.join(' AND ')}` : ''

  const sql = `
    SELECT
      cc.id::text        AS chunk_id,
      ct.text_key,
      ct.title,
      ct.author,
      ct.tradition,
      cc.chapter,
      cc.verse_range,
      cc.content,
      ct.attribution_baseline_confidence,
      cc.embedding <=> $1::vector AS distance
    FROM classical_chunks cc
    JOIN classical_texts ct ON ct.id = cc.text_id
    WHERE TRUE ${where}
    ORDER BY cc.embedding <=> $1::vector
    LIMIT $2
  `

  const { rows, rowCount } = await query<ChunkRow>(sql, params)

  const results: ClassicalTextSearchResult[] = rows.map(row => ({
    chunk_id: row.chunk_id,
    text_key: row.text_key,
    title: row.title,
    author: row.author,
    tradition: row.tradition,
    chapter: row.chapter,
    verse_range: row.verse_range,
    content: row.content,
    confidence_baseline: Number(row.attribution_baseline_confidence),
    similarity: 1 - Number(row.distance),
  }))

  return {
    results,
    total_searched: rowCount ?? results.length,
    query_embedding_dim: VERTEX_EMBED_DIM,
  }
}
