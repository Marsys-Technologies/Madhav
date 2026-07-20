/**
 * query_formula_constants — L0 Brahmagyan formula-constants registry
 * =======================================================================
 * W2b dark-set wiring, Batch 2 (TABLE_CONCEPT_DISPOSITIONS_v2_0.md borderline
 * SERVE-gap set, `brahma_formula_constants`, 18 rows). Serves the mixed
 * CLASSICAL/NATIVE_JUDGMENT/ENGINEERING/CONFLATION_BUG constants registry
 * (389_brahma_formula_constants.sql). Only one confirmed live internal
 * reader exists (recalibrationEnqueue.ts, an unrelated scheduling-timing
 * lookup) — the CLASSICAL-tagged rows themselves have no serving route.
 * Judgment-call table per the disposition doc; wired per the ruling's
 * default-bias.
 *
 * Global reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryFormulaConstantsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_formula_constants',
  type:  'tool',
  layer: 'L0',
  name:  'query_formula_constants',

  description: [
    'Query the formula-constants registry (brahma_formula_constants, 18 rows). Each row:',
    'constant_id, value_jsonb, class (classical|native_judgment|engineering|',
    'conflation_bug), consumer_assets[] (which layer assets read this constant),',
    'citation_or_ratification, calibratable flag, bounds, version. Filter by constant_id',
    'or class. Global reference — no chart_id needed. CLASSICAL rows are cite-and-encode',
    '(never tuned); NATIVE_JUDGMENT rows are ratified and L5-calibratable within bounds;',
    'CONFLATION_BUG rows are documented defects, not live formulas.',
  ].join(' '),

  input_schema: {
    constant_id: { type: 'string', description: 'Filter by exact constant_id. Omit for all.' },
    class:       { type: 'string', description: 'Filter by class (classical|native_judgment|engineering|conflation_bug). Omit for all.' },
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
    const constantId = args['constant_id'] ? String(args['constant_id']) : null
    const cls        = args['class'] ? String(args['class']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (constantId) { filters.push(`constant_id = $${p++}`); params.push(constantId) }
    if (cls)        { filters.push(`class = $${p++}`); params.push(cls) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT constant_id, value_jsonb, class, consumer_assets, citation_or_ratification,
             calibratable, bounds, version
      FROM brahma_formula_constants
      WHERE ${where}
      ORDER BY constant_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { constant_id: constantId, class: cls },
          ...(result.rows.length === 0
            ? { empty_reason: `No formula-constant rows matched (constant_id=${constantId ?? 'any'}, class=${cls ?? 'any'}).` }
            : {}),
          disclaimer: 'Formula-constants registry — CLASSICAL rows cite-and-encode only, never tuned; CONFLATION_BUG rows are documented defects, not live formulas.',
          provenance: { tables: ['brahma_formula_constants'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
