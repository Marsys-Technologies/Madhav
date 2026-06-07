/**
 * read_classical_text.ts — L0FR Stream C MCP Tool (2026-06-07)
 *
 * MCP tool: read_classical_text
 * Semantic + full-text search over the classical_text_chunks table.
 * Delegates to the platform /api/retrieval/classical-text endpoint.
 *
 * Also includes stub registrations for:
 *   - read_chapter
 *   - list_classical_texts
 *   - find_verses_about
 *   - search_classical_texts
 *
 * All five tools satisfy the L0FR Stream C requirement of ≥4 retrieval capabilities
 * in BOTH MCP and Consume Chat channels.
 *
 * L0FR Stream C — brahmagyan.texts capability registration
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'
import type { Principal } from '../types.js'

const { Pool } = pg

// ── DB pool (lazy singleton) ──────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      throw new Error('[read_classical_text] DATABASE_URL not set')
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Embedding helper (calls sidecar /embed) ───────────────────────────────────

async function getEmbedding(text: string): Promise<number[] | null> {
  const sidecarUrl = process.env['PYTHON_SIDECAR_URL']
  if (!sidecarUrl) return null
  try {
    const res = await fetch(`${sidecarUrl}/embed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal: AbortSignal.timeout(8000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { embedding?: number[] }
    return data.embedding ?? null
  } catch {
    return null
  }
}

// ── Tool: read_classical_text ─────────────────────────────────────────────────

const ReadClassicalTextInput = z.object({
  query: z.string().min(3).describe('Search query — semantic or verse ref (e.g. "BPHS CH7:V14")'),
  schools: z.array(z.string()).optional().describe('Filter by tradition_school'),
  limit: z.number().int().min(1).max(20).optional().default(5).describe('Max results (1-20)'),
})

interface ChunkRow {
  chunk_id: string
  text_id: string
  chapter: number | null
  verse_ref: string | null
  content_en: string
  tradition_school: string | null
  rank: number
}

async function doReadClassicalText(input: z.infer<typeof ReadClassicalTextInput>) {
  const { query, schools, limit = 5 } = input
  const pool = getPool()

  // Try vector search first
  const embedding = await getEmbedding(query)
  let rows: ChunkRow[] = []

  if (embedding) {
    const embStr = '[' + embedding.join(',') + ']'
    let sql = `
      SELECT chunk_id, text_id, chapter, verse_ref, content_en, tradition_school,
             (1 - (embedding <=> $1::vector))::float AS rank
      FROM classical_text_chunks
      WHERE embedding IS NOT NULL`
    const params: unknown[] = [embStr]
    if (schools && schools.length > 0) {
      sql += ` AND tradition_school = ANY($${params.length + 1}::text[])`
      params.push(schools)
    }
    sql += ` ORDER BY embedding <=> $1::vector LIMIT $${params.length + 1}`
    params.push(limit)
    const res = await pool.query(sql, params)
    rows = res.rows as ChunkRow[]
  }

  // FTS fallback
  if (rows.length === 0) {
    const tsq = query.trim().split(/\s+/).filter(w => w.length > 2).map(w => `${w}:*`).join(' & ')
    if (!tsq) {
      // ILIKE fallback
      let sql = `
        SELECT chunk_id, text_id, chapter, verse_ref, content_en, tradition_school, 0.5::float AS rank
        FROM classical_text_chunks WHERE content_en ILIKE $1`
      const params: unknown[] = [`%${query.substring(0, 50)}%`]
      if (schools && schools.length > 0) {
        sql += ` AND tradition_school = ANY($${params.length + 1}::text[])`
        params.push(schools)
      }
      sql += ` LIMIT $${params.length + 1}`
      params.push(limit)
      const res = await pool.query(sql, params)
      rows = res.rows as ChunkRow[]
    } else {
      try {
        let sql = `
          SELECT chunk_id, text_id, chapter, verse_ref, content_en, tradition_school,
                 ts_rank(to_tsvector('english', content_en), to_tsquery('english', $1))::float AS rank
          FROM classical_text_chunks
          WHERE to_tsvector('english', content_en) @@ to_tsquery('english', $1)`
        const params: unknown[] = [tsq]
        if (schools && schools.length > 0) {
          sql += ` AND tradition_school = ANY($${params.length + 1}::text[])`
          params.push(schools)
        }
        sql += ` ORDER BY rank DESC LIMIT $${params.length + 1}`
        params.push(limit)
        const res = await pool.query(sql, params)
        rows = res.rows as ChunkRow[]
      } catch {
        // ILIKE fallback on FTS parse error
        let sql = `SELECT chunk_id, text_id, chapter, verse_ref, content_en, tradition_school, 0.5::float AS rank
                   FROM classical_text_chunks WHERE content_en ILIKE $1 LIMIT $2`
        const res = await pool.query(sql, [`%${query.substring(0, 50)}%`, limit])
        rows = res.rows as ChunkRow[]
      }
    }
  }

  return {
    results: rows.map(r => ({
      chunk_id: r.chunk_id,
      text_key: r.text_id,
      chapter: r.chapter !== null ? String(r.chapter) : null,
      verse_range: r.verse_ref ?? null,
      text: r.content_en ?? '',
      confidence_baseline: Math.max(0, Math.min(1, Number(r.rank) || 0.5)),
      school: r.tradition_school ?? null,
    })),
    total: rows.length,
    query_used: query,
  }
}

// ── Tool: read_chapter ────────────────────────────────────────────────────────

const ReadChapterInput = z.object({
  text_id: z.string().min(2).describe('Classical text identifier (e.g. bphs, saravali)'),
  chapter: z.number().int().min(1).describe('Chapter number'),
  limit: z.number().int().min(1).max(100).optional().default(50),
})

async function doReadChapter(input: z.infer<typeof ReadChapterInput>) {
  const { text_id, chapter, limit = 50 } = input
  const pool = getPool()
  const res = await pool.query(
    `SELECT chunk_id, verse_ref, content_en, content_sa
     FROM classical_text_chunks
     WHERE text_id = $1 AND chapter = $2
     ORDER BY verse_start, chunk_id LIMIT $3`,
    [text_id, chapter, Math.min(limit, 100)],
  )
  return { text_id, chapter, chunks: res.rows, total: res.rowCount ?? 0 }
}

// ── Tool: list_classical_texts ────────────────────────────────────────────────

async function doListClassicalTexts() {
  const pool = getPool()
  const res = await pool.query(`
    SELECT t.text_id, t.title_en, t.author, t.school, t.tradition,
           COUNT(c.chunk_id) AS chunk_count, s.source_url, t.license
    FROM classical_texts t
    LEFT JOIN classical_text_chunks c ON c.text_id = t.text_id
    LEFT JOIN classical_texts_source s ON s.text_id = t.text_id
    GROUP BY t.text_id, t.title_en, t.author, t.school, t.tradition, s.source_url, t.license
    ORDER BY t.text_id
  `)
  return {
    texts: res.rows.map((r: Record<string, unknown>) => ({
      text_id: r['text_id'],
      title: r['title_en'],
      author: r['author'],
      school: r['school'],
      tradition: r['tradition'],
      chunk_count: parseInt(String(r['chunk_count'] ?? '0'), 10),
      source_url: r['source_url'],
      license: r['license'],
    })),
    total: res.rowCount ?? 0,
  }
}

// ── Tool: find_verses_about ───────────────────────────────────────────────────

const FindVersesAboutInput = z.object({
  topic: z.string().min(3).describe('Topic to search for (e.g. "exalted Mars in 10th house")'),
  text_ids: z.array(z.string()).optional().describe('Restrict to these text_ids'),
  top_k: z.number().int().min(1).max(20).optional().default(10),
})

async function doFindVersesAbout(input: z.infer<typeof FindVersesAboutInput>) {
  const { topic, text_ids, top_k = 10 } = input
  const results = await doReadClassicalText({ query: topic, limit: top_k })
  let filtered = results.results
  if (text_ids && text_ids.length > 0) {
    const idSet = new Set(text_ids)
    filtered = filtered.filter(r => idSet.has(r.text_key))
  }
  return { results: filtered, total: filtered.length, topic }
}

// ── Tool: search_classical_texts ─────────────────────────────────────────────

const SearchClassicalTextsInput = z.object({
  query: z.string().min(3).describe('Search query text'),
  top_k: z.number().int().min(1).max(20).optional().default(5),
  schools: z.array(z.string()).optional(),
})

// ── Register functions ────────────────────────────────────────────────────────

export function registerReadClassicalText(
  server: McpServer,
  _getPrincipal: () => Principal,
): void {
  server.tool(
    'read_classical_text',
    'Semantic + full-text search over the classical Jyotish corpus ' +
    '(BPHS, Saravali, Brihat Jataka, Hora Sara, Uttara Kalamrita, Jaimini Sutras, etc.). ' +
    'Use for verse-addressable citation lookup or free-text semantic queries. ' +
    'Returns chunk content, verse reference, chapter, tradition, and similarity score. ' +
    'Not chart-bound. L0FR Stream C — brahmagyan.texts',
    ReadClassicalTextInput.shape,
    async (params) => {
      try {
        const result = await doReadClassicalText(ReadClassicalTextInput.parse(params))
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'read_classical_text', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerReadChapter(
  server: McpServer,
  _getPrincipal: () => Principal,
): void {
  server.tool(
    'read_chapter',
    'Fetch all verse chunks for a specific chapter of a classical text. ' +
    'Returns the full sequence of chunks (verse_ref, content_en, content_sa) for that chapter. ' +
    'Not chart-bound. L0FR Stream C — brahmagyan.texts',
    ReadChapterInput.shape,
    async (params) => {
      try {
        const result = await doReadChapter(ReadChapterInput.parse(params))
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'read_chapter', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerListClassicalTexts(
  server: McpServer,
  _getPrincipal: () => Principal,
): void {
  server.tool(
    'list_classical_texts',
    'List all classical Jyotish texts ingested in the corpus with metadata. ' +
    'Returns text_id, title, author, school/tradition, chunk count, and licensing info. ' +
    'Use to discover available texts before querying. Not chart-bound. L0FR Stream C',
    {},
    async () => {
      try {
        const result = await doListClassicalTexts()
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'list_classical_texts', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerFindVersesAbout(
  server: McpServer,
  _getPrincipal: () => Principal,
): void {
  server.tool(
    'find_verses_about',
    'Discover classical text verses about a specific astrological topic using embedding similarity. ' +
    'Optionally restrict to specific text_ids. Not chart-bound. L0FR Stream C — brahmagyan.texts',
    FindVersesAboutInput.shape,
    async (params) => {
      try {
        const result = await doFindVersesAbout(FindVersesAboutInput.parse(params))
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'find_verses_about', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}

export function registerSearchClassicalTexts(
  server: McpServer,
  _getPrincipal: () => Principal,
): void {
  server.tool(
    'search_classical_texts',
    'Combined embedding + full-text search over the classical Jyotish corpus. ' +
    'Alias for read_classical_text with renamed parameters for clarity. ' +
    'Not chart-bound. L0FR Stream C — brahmagyan.texts',
    SearchClassicalTextsInput.shape,
    async (params) => {
      try {
        const p = SearchClassicalTextsInput.parse(params)
        const result = await doReadClassicalText({ query: p.query, schools: p.schools, limit: p.top_k ?? 5 })
        return { content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }] }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, tool: 'search_classical_texts', message: msg }, null, 2) }],
          isError: true,
        }
      }
    },
  )
}
