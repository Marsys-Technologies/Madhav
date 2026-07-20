/**
 * query_transit_engine — L0 Brahmagyan graha motion-parameter reference
 * =========================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_transit_engine`, 9 rows). Serves the classical per-graha average
 * daily motion / zodiac period / sign-residence reference (BPHS Ch.22 —
 * 266_bg_transit_tables.sql §1). Sibling of the already-served
 * bg_transit_rules table.
 *
 * SCOPE NOTE: read-only reference table, no relation to kala_*-prefixed
 * gochara serving code — this campaign's D-5 hard constraint is untouched.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryTransitEngineCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_transit_engine',
  type:  'tool',
  layer: 'L0',
  name:  'query_transit_engine',

  description: [
    'Query the classical graha average-motion reference (bg_transit_engine, 9 rows — one',
    'per graha — BPHS Ch.22). Each row: graha, avg_daily_motion_deg, zodiac_period_days,',
    'sign_residence_days, classical_citation. Filter by graha. Global classical reference —',
    "no chart_id needed; returns AVERAGE motion parameters only, not any chart's actual",
    'ephemeris-computed transit position.',
  ].join(' '),

  input_schema: {
    graha: { type: 'string', description: 'Filter by graha (case-insensitive, e.g. "Rahu"). Omit for all 9.' },
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
    const graha = args['graha'] ? String(args['graha']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (graha) { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation
      FROM bg_transit_engine
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
            ? { empty_reason: `No transit-engine rows matched (graha=${graha ?? 'any'}).` }
            : {}),
          disclaimer: 'Average classical motion parameters only — not a live ephemeris-computed position.',
          provenance: { tables: ['bg_transit_engine'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
