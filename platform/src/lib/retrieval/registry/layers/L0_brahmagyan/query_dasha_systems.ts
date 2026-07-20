/**
 * query_dasha_systems — L0 Brahmagyan classical dasha-system reference
 * =========================================================================
 * W2b dark-set wiring, Batch 2 (TABLE_CONCEPT_DISPOSITIONS_v2_0.md
 * SERVE-gap set, `brahma_dasha_systems`, 18 rows). Serves the classical
 * dasha-system definitions (computation_pseudocode, classical_citations,
 * school — 176_l0_phase_alpha_new_content_tables.sql §3.10). Only prior
 * reference was a design-comment in parity_check.ts (proposed, not live) —
 * this is a genuine, previously-unserved concept.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryDashaSystemsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_dasha_systems',
  type:  'tool',
  layer: 'L0',
  name:  'query_dasha_systems',

  description: [
    'Query the classical dasha-system definitions reference (brahma_dasha_systems, 18',
    'rows). Each row: canonical_id, name_en/name_sa, total_cycle_years, base_unit',
    '(nakshatra_lord|sign_lord|special), sequence_jsonb, computation_method,',
    'computation_pseudocode, conditions_for_use, school, classical_citations. Filter by',
    'canonical_id or school. Global classical reference — no chart_id needed; returns the',
    "system DEFINITION only, not any chart's computed dasha periods (see get_dashas).",
  ].join(' '),

  input_schema: {
    canonical_id: { type: 'string', description: 'Filter by exact canonical_id. Omit for all.' },
    school:       { type: 'string', description: 'Filter by school (case-insensitive). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const canonicalId = args['canonical_id'] ? String(args['canonical_id']) : null
    const school      = args['school'] ? String(args['school']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (canonicalId) { filters.push(`canonical_id = $${p++}`); params.push(canonicalId) }
    if (school)      { filters.push(`LOWER(school) = LOWER($${p++})`); params.push(school) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT canonical_id, name_sa, name_en, total_cycle_years, base_unit, sequence_jsonb,
             computation_method, computation_pseudocode, conditions_for_use, school,
             classical_citations
      FROM brahma_dasha_systems
      WHERE ${where}
      ORDER BY canonical_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { canonical_id: canonicalId, school },
          ...(result.rows.length === 0
            ? { empty_reason: `No dasha-system rows matched (canonical_id=${canonicalId ?? 'any'}, school=${school ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical dasha-system definitions only — not any chart\'s computed dasha periods.',
          provenance: { tables: ['brahma_dasha_systems'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
