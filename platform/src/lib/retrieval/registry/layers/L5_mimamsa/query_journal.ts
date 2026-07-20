/**
 * query_journal — L5 Mīmāṃsā native Q&A journal (mimamsa_journal)
 * =====================================================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `mimamsa_journal`, migration 354_mimamsa_seva_abhilekha.sql). Native question/answer
 * journal tied to specific predictions — prompt_shown, native_answer, resulting_event_id.
 * Zero references anywhere prior to this pass (only cockpit cache-clear tooling touched
 * the table name).
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryJournalCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_journal',
  type:  'tool',
  layer: 'L5',
  name:  'query_journal',

  description: [
    'Retrieve the native Q&A journal from mimamsa_journal (mi_seva_abhilekha). Each row:',
    'prediction_id, prompt_shown, native_answer, answered_at, resulting_event_id,',
    'provenance_tag. Filters: prediction_id, answered_only (only rows with a recorded',
    `native_answer). Bounded to ${MAX_LIMIT} rows with a disclosed total, ordered newest first.`,
  ].join(' '),

  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID. Required.', required: true },
    prediction_id:  { type: 'string', description: 'Filter by prediction_id. Omit for all.' },
    answered_only:  { type: 'boolean', description: 'If true, only return rows with a non-null native_answer. Default false.' },
    limit:          { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: false },
    bulk_context: { pre_fetch_priority: 10, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const predictionId  = args['prediction_id'] ? String(args['prediction_id']) : null
    const answeredOnly  = args['answered_only'] === true
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (predictionId) { filters.push(`prediction_id = $${p++}`); params.push(predictionId) }
    if (answeredOnly) { filters.push('native_answer IS NOT NULL') }
    const where = filters.join(' AND ')

    const sql = `
      SELECT journal_id, prediction_id, prompt_shown, native_answer,
             to_char(answered_at, 'YYYY-MM-DD"T"HH24:MI:SSZ') AS answered_at,
             resulting_event_id, provenance_tag,
             to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SSZ') AS created_at
      FROM mimamsa_journal
      WHERE ${where}
      ORDER BY created_at DESC
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_journal WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { prediction_id: predictionId, answered_only: answeredOnly, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No journal rows matched (prediction_id=${predictionId ?? 'any'}, answered_only=${answeredOnly}).` }
            : {}),
          provenance: { tables: ['mimamsa_journal'], source: 'L5 Mīmāṃsā native Q&A journal (mi_seva_abhilekha); served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
