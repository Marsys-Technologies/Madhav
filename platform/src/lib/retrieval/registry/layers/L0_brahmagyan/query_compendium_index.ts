/**
 * query_compendium_index — L0 Brahmagyan classical-text compendium index
 * ==========================================================================
 * W2b dark-set wiring, Batch 2 (TABLE_CONCEPT_DISPOSITIONS_v2_0.md
 * SERVE-gap set, `brahma_compendium_index`, 9538 rows). Serves the
 * classical-text index/table-of-contents structure (text_id/chapter/topic
 * linking to chunk_ids — 176_l0_phase_alpha_new_content_tables.sql §3.12).
 *
 * DRIFT-BUG NOTE (disposition doc): `coverage_matrix.ts` previously claimed
 * this table was covered by `query_classical_texts` — false; that tool
 * queries `classical_text_chunks`, a different table. That one-line drift
 * is corrected in this same wiring pass (coverage_matrix.ts now points at
 * this new capability) since it is the direct, trivial byproduct of
 * closing this exact gap — not a separate defect fix.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 100

export const queryCompendiumIndexCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_compendium_index',
  type:  'tool',
  layer: 'L0',
  name:  'query_compendium_index',

  description: [
    'Query the classical-text compendium index/table-of-contents (brahma_compendium_index,',
    '9538 rows). Each row: text_id, chapter_num, chapter_title_en/sa, topic_id, verse_start/',
    'end, chunk_ids[] (link into classical_text_chunks), summary_text (mechanical',
    'first-N-chunks synopsis, not LLM-generated), significance,',
    'classical_significance_score. Filter by text_id, chapter_num, or topic_id. Global',
    `classical reference — no chart_id needed. Bounded to ${MAX_LIMIT} rows with a`,
    'disclosed total; use text_id + chapter_num to narrow for a specific chapter\'s index.',
  ].join(' '),

  input_schema: {
    text_id:     { type: 'string', description: 'Filter by text_id. Omit for all (paginated).' },
    chapter_num: { type: 'number', description: 'Filter by chapter_num. Omit for all.' },
    topic_id:    { type: 'string', description: 'Filter by topic_id. Omit for all.' },
    limit:       { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 10, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const textId     = args['text_id'] ? String(args['text_id']) : null
    const chapterNum = args['chapter_num'] != null ? Number(args['chapter_num']) : null
    const topicId    = args['topic_id'] ? String(args['topic_id']) : null
    const rawLimit   = args['limit'] != null ? Number(args['limit']) : MAX_LIMIT
    const limit      = Math.min(Math.max(1, Number.isFinite(rawLimit) ? rawLimit : MAX_LIMIT), MAX_LIMIT)

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (textId)     { filters.push(`text_id = $${p++}`); params.push(textId) }
    if (chapterNum != null && Number.isInteger(chapterNum)) { filters.push(`chapter_num = $${p++}`); params.push(chapterNum) }
    if (topicId)    { filters.push(`topic_id = $${p++}`); params.push(topicId) }
    const where = filters.join(' AND ')

    const countSql = `SELECT COUNT(*)::int AS total FROM brahma_compendium_index WHERE ${where}`
    const sql = `
      SELECT index_id, text_id, chapter_num, chapter_title_en, chapter_title_sa, topic_id,
             verse_start, verse_end, chunk_ids, summary_text, significance,
             classical_significance_score
      FROM brahma_compendium_index
      WHERE ${where}
      ORDER BY text_id, chapter_num, verse_start
      LIMIT $${p}`
    params.push(limit)

    try {
      const [countResult, result] = await Promise.all([
        query<{ total: number }>(countSql, params.slice(0, -1)),
        query<Record<string, unknown>>(sql, params),
      ])
      const total = countResult.rows[0]?.total ?? result.rows.length
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          total,
          filters: { text_id: textId, chapter_num: chapterNum, topic_id: topicId },
          ...(result.rows.length === 0
            ? { empty_reason: `No compendium-index rows matched (text_id=${textId ?? 'any'}, chapter_num=${chapterNum ?? 'any'}, topic_id=${topicId ?? 'any'}).` }
            : {}),
          disclaimer: 'Mechanical text index/TOC only — summary_text is a deterministic first-N-chunks synopsis, not LLM-generated interpretation.',
          provenance: { tables: ['brahma_compendium_index'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
