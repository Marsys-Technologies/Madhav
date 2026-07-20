/**
 * query_prashna_special_techniques — L0 Brahmagyan prashna technique reference
 * ================================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_prashna_special_techniques`, 3 rows). Serves the classical Prashna
 * special-technique reference (261_bg_prashna_rules_schema.sql). Global
 * classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPrashnaSpecialTechniquesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_prashna_special_techniques',
  type:  'tool',
  layer: 'L0',
  name:  'query_prashna_special_techniques',

  description: [
    'Query the Prashna special-technique reference (bg_prashna_special_techniques, 3 rows).',
    'Each row: technique_id, technique_name (+ Sanskrit), application_rule,',
    'classical_citation. Filter by technique_id. Global classical reference — no chart_id',
    'needed.',
  ].join(' '),

  input_schema: {
    technique_id: { type: 'string', description: 'Filter by technique_id. Omit for all 3.' },
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
    const techniqueId = args['technique_id'] ? String(args['technique_id']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (techniqueId) { filters.push(`technique_id = $${p++}`); params.push(techniqueId) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT technique_id, technique_name, technique_name_sa, application_rule, classical_citation
      FROM bg_prashna_special_techniques
      WHERE ${where}
      ORDER BY technique_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { technique_id: techniqueId },
          ...(result.rows.length === 0
            ? { empty_reason: `No special-technique rows matched (technique_id=${techniqueId ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical Prashna special-technique reference — chart-agnostic.',
          provenance: { tables: ['bg_prashna_special_techniques'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
