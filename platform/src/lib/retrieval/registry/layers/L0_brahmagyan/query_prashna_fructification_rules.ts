/**
 * query_prashna_fructification_rules — L0 Brahmagyan prashna timing reference
 * ===============================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_prashna_fructification_rules`, 5 rows). Serves the classical Prashna
 * fructification-timing (degree→time-unit conversion) reference
 * (261_bg_prashna_rules_schema.sql). Global classical reference — no
 * chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPrashnaFructificationRulesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_prashna_fructification_rules',
  type:  'tool',
  layer: 'L0',
  name:  'query_prashna_fructification_rules',

  description: [
    'Query the Prashna fructification-timing reference (bg_prashna_fructification_rules,',
    '5 rows). Each row: rule_id, time_unit (hours|days|weeks|months|years),',
    'degree_conversion_rule, applicable_when, classical_citation. Filter by rule_id or',
    'time_unit. Global classical reference — no chart_id needed.',
  ].join(' '),

  input_schema: {
    rule_id:   { type: 'string', description: 'Filter by rule_id. Omit for all 5.' },
    time_unit: { type: 'string', description: 'Filter by time_unit (hours|days|weeks|months|years). Omit for all.' },
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
    const ruleId   = args['rule_id'] ? String(args['rule_id']) : null
    const timeUnit = args['time_unit'] ? String(args['time_unit']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (ruleId)   { filters.push(`rule_id = $${p++}`); params.push(ruleId) }
    if (timeUnit) { filters.push(`LOWER(time_unit) = LOWER($${p++})`); params.push(timeUnit) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT rule_id, time_unit, degree_conversion_rule, applicable_when, classical_citation
      FROM bg_prashna_fructification_rules
      WHERE ${where}
      ORDER BY rule_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { rule_id: ruleId, time_unit: timeUnit },
          ...(result.rows.length === 0
            ? { empty_reason: `No fructification-rule rows matched (rule_id=${ruleId ?? 'any'}, time_unit=${timeUnit ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical Prashna fructification-timing rules — chart-agnostic reference.',
          provenance: { tables: ['bg_prashna_fructification_rules'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
