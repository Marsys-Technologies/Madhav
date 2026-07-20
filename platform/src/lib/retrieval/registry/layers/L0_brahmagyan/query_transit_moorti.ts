/**
 * query_transit_moorti — L0 Brahmagyan Moorti Nirnaya (transit-nakshatra quality) reference
 * ==============================================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_transit_moorti`, 27 rows). Serves the classical nakshatra-offset →
 * moorti-quality reference (Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28
 * — 401_bg_transit_moorti.sql).
 *
 * SCOPE NOTE: this table's own migration comment states the internal
 * ka_gochara transit-scoring service reads it to add a moorti_tier to
 * convergence-window scoring. This capability is a NEW, independent
 * read-only path serving the REFERENCE rows directly — it does not touch,
 * wrap, or modify any kala_*-prefixed serving code (register_gochara_windows.ts
 * / query_temporal_activation.ts), which remain frozen-as-found per this
 * campaign's D-5 hard constraint.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryTransitMoortiCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_transit_moorti',
  type:  'tool',
  layer: 'L0',
  name:  'query_transit_moorti',

  description: [
    'Query the Moorti Nirnaya transit-nakshatra quality reference (bg_transit_moorti,',
    '27 rows — Phaladeepika Ch.26; BPHS Ch.28). Keyed by nakshatra_offset (1-27, counted',
    'from natal janma nakshatra). Each row: moorti_name (swarna|rajata|tamra|loha),',
    'quality_tier (1=best..4), phala_brief, classical_citation. Filter by nakshatra_offset',
    'or moorti_name. Global classical reference — no chart_id needed; returns the RULE only,',
    "not any chart's computed current-transit moorti.",
  ].join(' '),

  input_schema: {
    nakshatra_offset: { type: 'number', description: 'Filter by nakshatra_offset (1-27). Omit for all.' },
    moorti_name:      { type: 'string', description: 'Filter by moorti_name (swarna|rajata|tamra|loha). Omit for all.' },
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
    const nakshatraOffset = args['nakshatra_offset'] != null ? Number(args['nakshatra_offset']) : null
    const moortiName      = args['moorti_name'] ? String(args['moorti_name']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (nakshatraOffset != null && Number.isInteger(nakshatraOffset)) { filters.push(`nakshatra_offset = $${p++}`); params.push(nakshatraOffset) }
    if (moortiName) { filters.push(`LOWER(moorti_name) = LOWER($${p++})`); params.push(moortiName) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation, rule_notes
      FROM bg_transit_moorti
      WHERE ${where}
      ORDER BY nakshatra_offset`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { nakshatra_offset: nakshatraOffset, moorti_name: moortiName },
          ...(result.rows.length === 0
            ? { empty_reason: `No moorti rows matched (nakshatra_offset=${nakshatraOffset ?? 'any'}, moorti_name=${moortiName ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical Moorti Nirnaya reference only — not a computed current-transit moorti verdict.',
          provenance: { tables: ['bg_transit_moorti'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
