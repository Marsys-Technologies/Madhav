/**
 * query_prashna_significators — L0 Brahmagyan prashna significator reference
 * ==============================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_prashna_significators`, 12 rows). Serves the classical Prashna
 * significator-derivation rules per question class (261_bg_prashna_rules_schema.sql).
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryPrashnaSignificatorsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_prashna_significators',
  type:  'tool',
  layer: 'L0',
  name:  'query_prashna_significators',

  description: [
    'Query the Prashna significator-derivation reference (bg_prashna_significators, 12 rows).',
    'Each row: question_class, querent_house/querent_planet, quesited_house/quesited_planet,',
    'significator_rule, classical_citation. Filter by question_class. Global classical',
    'reference — no chart_id needed.',
  ].join(' '),

  input_schema: {
    question_class: { type: 'string', description: 'Filter by question_class (case-insensitive). Omit for all 12.' },
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
    const questionClass = args['question_class'] ? String(args['question_class']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (questionClass) { filters.push(`LOWER(question_class) = LOWER($${p++})`); params.push(questionClass) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT question_class, querent_house, querent_planet, quesited_house, quesited_planet,
             significator_rule, classical_citation
      FROM bg_prashna_significators
      WHERE ${where}
      ORDER BY question_class`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { question_class: questionClass },
          ...(result.rows.length === 0
            ? { empty_reason: `No prashna-significator rows matched (question_class=${questionClass ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical Prashna significator-derivation rules — chart-agnostic reference.',
          provenance: { tables: ['bg_prashna_significators'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
