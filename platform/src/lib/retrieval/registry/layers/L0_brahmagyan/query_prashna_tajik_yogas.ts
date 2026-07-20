/**
 * query_prashna_tajik_yogas — L0 Brahmagyan Tajik horary yoga reference
 * =========================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_prashna_tajik_yogas`, 16 rows). Serves the classical Tajik horary
 * yoga set used in Prashna judgment (261_bg_prashna_rules_schema.sql).
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPrashnaTajikYogasCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_prashna_tajik_yogas',
  type:  'tool',
  layer: 'L0',
  name:  'query_prashna_tajik_yogas',

  description: [
    'Query the Tajik horary yoga reference (bg_prashna_tajik_yogas, 16 rows). Each row:',
    'yoga_id, yoga_name (+ Sanskrit), judgment_meaning, formation_rule (text + optional',
    'JSON), classical_citation, is_fructification_indicator flag. Filter by yoga_id or',
    'is_fructification_indicator. Global classical reference — no chart_id needed.',
  ].join(' '),

  input_schema: {
    yoga_id: { type: 'string', description: 'Filter by yoga_id. Omit for all 16.' },
    is_fructification_indicator: { type: 'boolean', description: 'Filter to fructification-indicator yogas only.' },
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
    const yogaId = args['yoga_id'] ? String(args['yoga_id']) : null
    const isFructIndicator = typeof args['is_fructification_indicator'] === 'boolean'
      ? args['is_fructification_indicator'] as boolean
      : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (yogaId) { filters.push(`yoga_id = $${p++}`); params.push(yogaId) }
    if (isFructIndicator != null) { filters.push(`is_fructification_indicator = $${p++}`); params.push(isFructIndicator) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT yoga_id, yoga_name, yoga_name_sa, judgment_meaning, formation_rule,
             formation_rule_jsonb, classical_citation, is_fructification_indicator
      FROM bg_prashna_tajik_yogas
      WHERE ${where}
      ORDER BY yoga_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { yoga_id: yogaId, is_fructification_indicator: isFructIndicator },
          ...(result.rows.length === 0
            ? { empty_reason: `No Tajik-yoga rows matched (yoga_id=${yogaId ?? 'any'}, is_fructification_indicator=${isFructIndicator ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical Tajik horary yoga reference — chart-agnostic.',
          provenance: { tables: ['bg_prashna_tajik_yogas'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
