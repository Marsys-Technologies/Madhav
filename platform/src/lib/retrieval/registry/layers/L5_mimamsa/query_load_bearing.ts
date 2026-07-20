/**
 * query_load_bearing — L5 Mīmāṃsā conclusion interpretability (mimamsa_load_bearing)
 * ==========================================================================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `mimamsa_load_bearing`, migration 350_mimamsa_adhilepa.sql). Written by the same
 * mi_adhilepa.py writer as the GATED calibration-overlay tables (mimamsa_fact_adjustment /
 * mimamsa_signal_adjustment / mimamsa_convergence_adjustment / mimamsa_anchor_adjustment),
 * but DELIBERATELY distinct: its schema carries no `leakage_status` / `applies_to_reading`
 * columns (confirmed against migration 350's DDL) — it is explanatory/interpretability
 * metadata ("which signal_id is load_bearing/supporting/redundant for conclusion_id"), not
 * raw calibration-multiplier internals. Per TABLE_CONCEPT_DISPOSITIONS_v2_0.md §6, this
 * table is explicitly NOT extended to GATED — it is a genuine, valuable "why does this
 * conclusion hold" concept, served here distinct from its GATED siblings.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 100

export const queryLoadBearingCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/query_load_bearing',
  type:  'tool',
  layer: 'L5',
  name:  'query_load_bearing',

  description: [
    'Retrieve conclusion interpretability rows from mimamsa_load_bearing (mi_adhilepa —',
    'NOT the GATED calibration-overlay siblings; this table has no leakage_status column).',
    'Each row: conclusion_id, signal_id, sensitivity (score), role (load_bearing|',
    'supporting|redundant). Answers "which signals actually carry the weight of this',
    'conclusion, and which are redundant?" Filters: conclusion_id, role.',
    `Ordered by sensitivity DESC. Bounded to ${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID. Required.', required: true },
    conclusion_id: { type: 'string', description: 'Filter by conclusion_id. Omit for all.' },
    role:          { type: 'string', description: 'Filter by role (load_bearing|supporting|redundant). Omit for all.', enum: ['load_bearing', 'supporting', 'redundant'] },
    limit:         { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const conclusionId = args['conclusion_id'] ? String(args['conclusion_id']) : null
    const role         = args['role'] ? String(args['role']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (conclusionId) { filters.push(`conclusion_id = $${p++}`); params.push(conclusionId) }
    if (role)         { filters.push(`role = $${p++}`); params.push(role) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT conclusion_id, signal_id, sensitivity, role, formula_version
      FROM mimamsa_load_bearing
      WHERE ${where}
      ORDER BY sensitivity DESC NULLS LAST
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM mimamsa_load_bearing WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { conclusion_id: conclusionId, role, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No load-bearing rows matched (conclusion_id=${conclusionId ?? 'any'}, role=${role ?? 'any'}).` }
            : {}),
          provenance: { tables: ['mimamsa_load_bearing'], source: 'L5 Mīmāṃsā conclusion interpretability (mi_adhilepa, non-GATED sibling); served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
