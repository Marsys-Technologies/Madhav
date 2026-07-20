/**
 * query_prashna_lagna_methods — L0 Brahmagyan prashna-lagna derivation reference
 * ==================================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_prashna_lagna_methods`, 5 rows). Serves the classical Prashna
 * (horary) lagna-derivation method reference (261_bg_prashna_rules_schema.sql).
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPrashnaLagnaMethodsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_prashna_lagna_methods',
  type:  'tool',
  layer: 'L0',
  name:  'query_prashna_lagna_methods',

  description: [
    'Query the Prashna (horary) lagna-derivation method reference',
    '(bg_prashna_lagna_methods, 5 rows). Each row: method_id, method_name (+ Sanskrit),',
    'derivation_rule (text + optional JSON), tradition (tajika|kp|parashari|prashna_marga|',
    'swara), is_primary flag, classical_citation. Filter by method_id or tradition. Global',
    'classical reference — no chart_id needed.',
  ].join(' '),

  input_schema: {
    method_id: { type: 'string', description: 'Filter by method_id. Omit for all 5.' },
    tradition: { type: 'string', description: 'Filter by tradition (tajika|kp|parashari|prashna_marga|swara). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 15, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const methodId  = args['method_id'] ? String(args['method_id']) : null
    const tradition = args['tradition'] ? String(args['tradition']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (methodId)  { filters.push(`method_id = $${p++}`); params.push(methodId) }
    if (tradition) { filters.push(`LOWER(tradition) = LOWER($${p++})`); params.push(tradition) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT method_id, method_name, method_name_sa, derivation_rule, derivation_rule_jsonb,
             classical_citation, is_primary, tradition
      FROM bg_prashna_lagna_methods
      WHERE ${where}
      ORDER BY method_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { method_id: methodId, tradition },
          ...(result.rows.length === 0
            ? { empty_reason: `No prashna-lagna-method rows matched (method_id=${methodId ?? 'any'}, tradition=${tradition ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical horary lagna-derivation methods only — chart-agnostic reference.',
          provenance: { tables: ['bg_prashna_lagna_methods'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
