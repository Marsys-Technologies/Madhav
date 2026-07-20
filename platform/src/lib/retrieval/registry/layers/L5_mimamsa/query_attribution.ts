/**
 * query_attribution — L5 Mīmāṃsā per-signal credit/blame attribution (mimamsa_attribution)
 * ================================================================================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `mimamsa_attribution`, migration 351_mimamsa_pariksha.sql). A genuine explainability
 * concept, schema-distinct from the GATED mi_adhilepa overlay family (no leakage_status /
 * applies_to_reading columns here) — for each matched prediction, which signal(s) get
 * credit or blame, along which dimension (timing/magnitude/domain/falsifier/manifestation).
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 100

export const queryAttributionCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_attribution',
  type:  'tool',
  layer: 'L5',
  name:  'query_attribution',

  description: [
    'Retrieve per-signal credit/blame attribution rows from mimamsa_attribution (mi_pariksha).',
    'Each row: match_id, signal_id, family_id, dimension (timing|magnitude|domain|falsifier|',
    'manifestation), credit_blame (signed contribution score), channel_fired.',
    'Answers "which signal(s) explain why this prediction matched (or missed)?" — the',
    'explainability layer over L5 outcome matching. Filters: match_id, signal_id, dimension.',
    `emits_references: signal_id references back to bodha_msr_signals. Bounded to`,
    `${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:  { type: 'string', description: 'Chart UUID. Required.', required: true },
    match_id:  { type: 'string', description: 'Filter by outcome-match id. Omit for all.' },
    signal_id: { type: 'string', description: 'Filter by signal id. Omit for all.' },
    dimension: { type: 'string', description: 'Filter by dimension (timing|magnitude|domain|falsifier|manifestation). Omit for all.', enum: ['timing', 'magnitude', 'domain', 'falsifier', 'manifestation'] },
    limit:     { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 15, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const matchId   = args['match_id'] ? String(args['match_id']) : null
    const signalId  = args['signal_id'] ? String(args['signal_id']) : null
    const dimension = args['dimension'] ? String(args['dimension']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (matchId)   { filters.push(`match_id = $${p++}`); params.push(matchId) }
    if (signalId)  { filters.push(`signal_id = $${p++}`); params.push(signalId) }
    if (dimension) { filters.push(`dimension = $${p++}`); params.push(dimension) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT match_id, signal_id, family_id, dimension, credit_blame, channel_fired,
             attribution_formula_ver
      FROM mimamsa_attribution
      WHERE ${where}
      ORDER BY ABS(credit_blame) DESC NULLS LAST
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_attribution WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { match_id: matchId, signal_id: signalId, dimension, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No attribution rows matched (match_id=${matchId ?? 'any'}, signal_id=${signalId ?? 'any'}, dimension=${dimension ?? 'any'}).` }
            : {}),
          provenance: { tables: ['mimamsa_attribution'], source: 'L5 Mīmāṃsā per-signal credit/blame attribution (mi_pariksha); served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
