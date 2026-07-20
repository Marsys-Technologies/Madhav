/**
 * query_triangulation — L2 Bodha multi-tradition concordance (bodha_triangulation)
 * =====================================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bodha_triangulation`, 200 real rows — migration 392, "the most consequential DARK
 * class: real data with no discovered TS-registry route" per the original harvest).
 *
 * Per-question-class Parashari/Jaimini/KP/Tajika tradition-stack concordance
 * (extends bo_sangati, consumed by P4 verdict assembly's tradition_concordance field).
 *
 * Standalone-vs-facet decision (DARK_SET_WIRING_PLAN_v1_0.md's own note): checked the
 * FK shape before deciding. `signal_ids` is a bare `UUID[]` with NO foreign-key
 * constraint to `bodha_discoveries` or `bodha_msr_signals` (confirmed via migration
 * 392's DDL — no REFERENCES clause anywhere) — so this is NOT a strict facet-shaped
 * relation onto either sibling capability. Wired as a standalone leaf tool, per the
 * plan's own fallback guidance.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryTriangulationCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_triangulation',
  type:  'tool',
  layer: 'L2',
  name:  'query_triangulation',

  description: [
    'Retrieve multi-tradition concordance rows from bodha_triangulation. Each row: one',
    '(question_class, tradition) pair — tradition in {parashari, jaimini, kp, tajika} —',
    'with verdict_inputs_jsonb, concordance_score (mean salience of the top-5 signals from',
    "that tradition's signal pool), and signal_ids (loose array reference, not an FK).",
    'Use to see whether the four classical traditions agree or diverge on a question class.',
    'Filters: ayanamsha_id, question_class, tradition.',
    `Bounded to ${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:   { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    question_class: { type: 'string', description: 'Filter by question_class. Omit for all.' },
    tradition:      { type: 'string', description: 'Filter by tradition (parashari|jaimini|kp|tajika). Omit for all.', enum: ['parashari', 'jaimini', 'kp', 'tajika'] },
    limit:          { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 25, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id  = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const questionClass = args['question_class'] ? String(args['question_class']) : null
    const tradition     = args['tradition'] ? String(args['tradition']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)  { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (questionClass) { filters.push(`question_class = $${p++}`); params.push(questionClass) }
    if (tradition)      { filters.push(`tradition = $${p++}`); params.push(tradition) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT triangulation_id, ayanamsha_id, question_class, tradition, verdict_inputs,
             concordance_score, signal_ids, formula_version, engine_version,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_triangulation
      WHERE ${where}
      ORDER BY question_class, tradition
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_triangulation WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, question_class: questionClass, tradition, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No triangulation rows matched (ayanamsha_id=${ayanamsha_id ?? 'any'}, question_class=${questionClass ?? 'any'}, tradition=${tradition ?? 'any'}).` }
            : {}),
          provenance: { tables: ['bodha_triangulation'], source: 'L2 Bodha multi-tradition (Parashari/Jaimini/KP/Tajika) concordance; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
