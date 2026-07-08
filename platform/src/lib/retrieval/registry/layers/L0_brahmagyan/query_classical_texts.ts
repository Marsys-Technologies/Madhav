/**
 * L0 retrieval: classical_text_chunks (classical text chunks)
 * Tool: marsys://tool/L0/query_classical_texts
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryClassicalTextsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L0/query_classical_texts',
  type: 'tool',
  layer: 'L0',
  name: 'query_classical_texts',
  description:
    'Query the classical text corpus (classical_text_chunks) — classical text chunks ' +
    'from Brihat Parashara Hora Shastra, Saravali, Brihat Jataka, Uttara Kalamrita, ' +
    'Phala Deepika, Jataka Parijata, and other canonical texts. ' +
    'Each chunk is a verse or shloka with: text_id, chapter, verse_ref, topics, ' +
    'tradition_school, and the original Sanskrit + English translation. ' +
    'Use to cite classical sources for astrological observations. ' +
    'Supports keyword search in English translation and filter by source text or topic.',
  input_schema: {
    keyword:     { type: 'string', description: 'Keyword/phrase to search in English translation (ILIKE).' },
    text_source: { type: 'string', description: 'Filter by source text id (e.g. BPHS, Saravali, Brihat_Jataka).' },
    topic:       { type: 'string', description: 'Filter by topic tag (matches topics array).' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 20 },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'prose_citation',
  traversal_level: 'L-SOURCE',
  tool_role: 'hybrid_retrieval',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: false },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const limit  = Math.min((args.limit as number) ?? 20, 200)
      const offset = (args.offset as number) ?? 0
      const params: unknown[] = [limit, offset]
      let sql = `SELECT * FROM classical_text_chunks WHERE 1=1`
      if (args.keyword)     { sql += ` AND content_en ILIKE $${params.length + 1}`; params.push(`%${args.keyword as string}%`) }
      if (args.text_source) { sql += ` AND text_id = $${params.length + 1}`; params.push(args.text_source as string) }
      if (args.topic)       { sql += ` AND $${params.length + 1} = ANY(topics)`; params.push(args.topic as string) }
      sql += ` ORDER BY text_id, chapter, verse_start LIMIT $1 OFFSET $2`
      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // E-3 empty-with-reason (R5 W0a punch-list, P8): a bare {rows: [], total: 0}
      // is indistinguishable from "the corpus has nothing on this term" (false) vs.
      // "this exact spelling/keyword is not indexed" (usually true). When a keyword
      // search comes back empty, say WHY and — where pg_trgm is available — surface
      // the nearest indexed topic tags as an honest, computed (not fabricated)
      // alternate-spelling suggestion.
      if (rows.length === 0 && args.keyword) {
        const keyword = args.keyword as string
        let nearestTopics: string[] = []
        try {
          const suggest = await query<{ topic: string }>(
            `
              SELECT topic FROM (
                SELECT DISTINCT unnest(topics) AS topic FROM classical_text_chunks
              ) t
              WHERE similarity(topic, $1) > 0.15
              ORDER BY similarity(topic, $1) DESC
              LIMIT 5
            `,
            [keyword]
          )
          nearestTopics = suggest.rows.map(r => r.topic)
        } catch {
          // pg_trgm similarity() unavailable or query failed — degrade to a
          // reason-only empty response rather than erroring the whole call.
          nearestTopics = []
        }
        return {
          content: {
            rows: [],
            total: 0,
            empty_reason: `No classical_text_chunks rows matched keyword "${keyword}" — this exact ` +
              `spelling/phrase is not indexed in the corpus (this does NOT mean the corpus is silent ` +
              `on the underlying concept — try a topic filter or an alternate spelling).`,
            nearest_indexed_topics: nearestTopics,
          },
          is_error: false,
        }
      }

      return { content: { rows, total: rows.length }, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
