/**
 * query_transit_vedha — L0 Brahmagyan gochara vedha (obstruction) reference
 * =============================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_transit_vedha`, 33 rows). Serves the classical Gochara vedha
 * (obstruction-nullification) rule reference — BPHS Ch.29 / Phaladeepika
 * Ch.26.
 *
 * GOVERNANCE ANOMALY (flagged, not fixed — TABLE_CONCEPT_DISPOSITIONS_v2_0.md
 * row for this table): no CREATE TABLE for bg_transit_vedha exists anywhere
 * in this repo's migration history (platform/supabase/migrations/,
 * platform/migrations/, _archive/, or the pre-squash schema snapshot),
 * though the table is real and live (confirmed via read-only DB
 * introspection this session: columns id, primary_graha,
 * primary_transit_house, vedha_graha, vedha_house, vedha_type,
 * classical_note, classical_citation, created_at). This wiring pass does
 * NOT attempt to author a replacement migration for the missing DDL — per
 * the task brief, the anomaly is reported, not "fixed."
 *
 * SCOPE NOTE: read-only reference table, distinct from and does not touch
 * any kala_*-prefixed gochara serving code (frozen-as-found this campaign).
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryTransitVedhaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_transit_vedha',
  type:  'tool',
  layer: 'L0',
  name:  'query_transit_vedha',

  description: [
    'Query the classical Gochara vedha (transit-obstruction) reference (bg_transit_vedha,',
    '33 rows — BPHS Ch.29; Phaladeepika Ch.26). Each row: primary_graha,',
    'primary_transit_house, vedha_graha (nullable), vedha_house, vedha_type (e.g.',
    'house_pair), classical_note, classical_citation. Filter by primary_graha or',
    'primary_transit_house. Global classical reference — no chart_id needed; returns the',
    "obstruction RULE only, not any chart's currently-active vedha state.",
  ].join(' '),

  input_schema: {
    primary_graha:         { type: 'string', description: 'Filter by primary_graha (case-insensitive). Omit for all.' },
    primary_transit_house: { type: 'number', description: 'Filter by primary_transit_house (1-12). Omit for all.' },
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
    const primaryGraha = args['primary_graha'] ? String(args['primary_graha']) : null
    const primaryHouse = args['primary_transit_house'] != null ? Number(args['primary_transit_house']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (primaryGraha) { filters.push(`LOWER(primary_graha) = LOWER($${p++})`); params.push(primaryGraha) }
    if (primaryHouse != null && Number.isInteger(primaryHouse)) { filters.push(`primary_transit_house = $${p++}`); params.push(primaryHouse) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT primary_graha, primary_transit_house, vedha_graha, vedha_house, vedha_type,
             classical_note, classical_citation
      FROM bg_transit_vedha
      WHERE ${where}
      ORDER BY primary_graha, primary_transit_house`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { primary_graha: primaryGraha, primary_transit_house: primaryHouse },
          ...(result.rows.length === 0
            ? { empty_reason: `No vedha rows matched (primary_graha=${primaryGraha ?? 'any'}, primary_transit_house=${primaryHouse ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical vedha obstruction rules only — not a computed current-transit vedha verdict.',
          provenance: { tables: ['bg_transit_vedha'] },
          governance_note: 'bg_transit_vedha has no CREATE TABLE migration anywhere in this repo (a documented governance anomaly) though the live table is real and queried here directly.',
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
