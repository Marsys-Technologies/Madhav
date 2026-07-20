/**
 * query_transit_av_gates — L0 Brahmagyan Ashtakavarga transit-gate reference
 * ==============================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_transit_av_gates`, 8 rows). Serves the classical Ashtakavarga (AV)
 * kakshya/SAV-threshold/vedha-AV gate reference (BPHS Ch.66-68;
 * Phaladeepika Ch.26 — 397_bg_transit_av_gates.sql).
 *
 * SCOPE NOTE: this table's own migration comment states the internal
 * gochara-transit scoring service reads it on demand as a scoring input.
 * This capability is a NEW, independent read-only path serving the
 * REFERENCE rows directly — it does not touch, wrap, or modify
 * `kala_gochara_windows` or any kala_*-prefixed serving code
 * (register_gochara_windows.ts / query_temporal_activation.ts), which
 * remain frozen-as-found per this campaign's D-5 hard constraint.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryTransitAvGatesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_transit_av_gates',
  type:  'tool',
  layer: 'L0',
  name:  'query_transit_av_gates',

  description: [
    'Query the Ashtakavarga (AV) transit-gate reference (bg_transit_av_gates, 8 rows —',
    'BPHS Ch.66-68; Phaladeepika Ch.26). gate_kind one of kakshya (per-graha benefic-lord',
    'kakshya sector), sav_threshold (min SAV bindhu to qualify), vedha_av (AV-enhanced',
    'vedha nullification). Each row: graha, house_from_moon, kakshya_lord, min_av_score,',
    'min_sav_score, effect, classical_citation. Filter by gate_kind or graha. Global',
    'classical reference — no chart_id needed; returns the GATE RULES only, not any',
    "chart's computed transit-window scoring output.",
  ].join(' '),

  input_schema: {
    gate_kind: { type: 'string', description: 'Filter by gate_kind (kakshya|sav_threshold|vedha_av). Omit for all.' },
    graha:     { type: 'string', description: 'Filter by graha (case-insensitive). Omit for all.' },
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
    const gateKind = args['gate_kind'] ? String(args['gate_kind']) : null
    const graha    = args['graha'] ? String(args['graha']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (gateKind) { filters.push(`gate_kind = $${p++}`); params.push(gateKind) }
    if (graha)    { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT gate_kind, graha, house_from_moon, kakshya_lord, min_av_score, min_sav_score,
             effect, classical_citation, rule_notes
      FROM bg_transit_av_gates
      WHERE ${where}
      ORDER BY gate_kind, graha, house_from_moon`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { gate_kind: gateKind, graha },
          ...(result.rows.length === 0
            ? { empty_reason: `No AV transit-gate rows matched (gate_kind=${gateKind ?? 'any'}, graha=${graha ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical AV gate rules only — not a computed per-chart transit-window score.',
          provenance: { tables: ['bg_transit_av_gates'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
