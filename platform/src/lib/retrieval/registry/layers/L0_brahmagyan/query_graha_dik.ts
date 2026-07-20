/**
 * query_graha_dik — L0 Brahmagyan Dig Bala (directional strength) reference
 * ============================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_graha_dik`, 9 rows). Serves the classical per-graha peak-house /
 * peak-direction / debility-house Dig Bala reference (BPHS Ch.27; Saravali
 * Ch.3; Brihat Jataka Ch.2). Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryGrahaDikCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_graha_dik',
  type:  'tool',
  layer: 'L0',
  name:  'query_graha_dik',

  description: [
    'Query the Dig Bala (directional strength) reference (bg_graha_dik, 9 rows — BPHS Ch.27;',
    'Saravali Ch.3; Brihat Jataka Ch.2). Each graha has a peak_house (bhava of maximum Dig',
    'Bala) + peak_direction, a debility_house (180° opposite, Dig Bala = 0), an optional',
    'paired_graha sharing the same peak house, and a school_note (parashari|tajika|debated).',
    'Filter by graha. Global classical reference — no chart_id needed; returns the peak-house',
    'RULE only, not any chart\'s computed Dig Bala score.',
  ].join(' '),

  input_schema: {
    graha: { type: 'string', description: 'Filter by graha (case-insensitive, e.g. "Saturn"). Omit for all 9.' },
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
    bulk_context: { pre_fetch_priority: 25, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const graha = args['graha'] ? String(args['graha']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (graha) { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, peak_house, peak_direction, debility_house, paired_graha, school_note, classical_citation
      FROM bg_graha_dik
      WHERE ${where}
      ORDER BY graha`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { graha },
          ...(result.rows.length === 0
            ? { empty_reason: `No Dig Bala rows matched (graha=${graha ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical peak-house reference only — not a computed per-chart Dig Bala score.',
          provenance: { tables: ['bg_graha_dik'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
