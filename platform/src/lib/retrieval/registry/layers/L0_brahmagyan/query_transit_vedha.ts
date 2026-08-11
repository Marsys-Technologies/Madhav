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
 * AUTHORITY RULING (ADJUDICATOR PK-R-9, 2026-08-11, IR-3): `bg_transit_vedha`
 * is RETIRED-IN-PLACE / non-authoritative for computation. `bg_transit_rules`
 * (rule_type='favourable', vedha_house IS NOT NULL — 41 rows) is the
 * authoritative vedha-pair corpus; it is what `gochara_grammar.primitives.
 * gochara_vedha_pair` and `ka_vedha_gochara/writer.py` both read (MR-41(a)).
 * Confirmed live, this table disagrees with `bg_transit_rules` on 4 rows and
 * is missing 8 rows entirely:
 *   - 4 Venus vedha_house disagreements: primary_transit_house 4 (this
 *     table says vedha_house=3, bg_transit_rules says 10), 5 (11 vs 9),
 *     8 (9 vs 1), 9 (5 vs 2).
 *   - 8 rows present in bg_transit_rules but ABSENT from this table
 *     entirely: Rahu houses 3/6/11, Ketu houses 3/6/11 (this table carries
 *     zero Rahu/Ketu rows at all), and Venus houses 11/12.
 * This is an OPEN L0 reconciliation item, not resolved by this ruling —
 * flagged here so a caller of THIS serving surface knows its rows are
 * reference-only and may diverge from the authoritative corpus, not a
 * silent, undisclosed discrepancy. This serving surface stays LIVE (it is
 * NOT being retired/unwired) — only its status as a scoring/computation
 * SOURCE is retired; it remains a legitimate, queryable classical reference
 * table in its own right (33 rows, real, live).
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
          governance_note: 'bg_transit_vedha has no CREATE TABLE migration anywhere in this repo (a documented governance anomaly) though the live table is real and queried here directly. AUTHORITY (PK-R-9): bg_transit_vedha is RETIRED-IN-PLACE / non-authoritative for computation -- bg_transit_rules (rule_type=favourable, vedha_house IS NOT NULL) is the authoritative vedha-pair corpus used by gochara_vedha_pair and ka_vedha_gochara/writer.py. This table disagrees with bg_transit_rules on 4 Venus rows (primary_transit_house 4: vedha_house 3 here vs 10; 5: 11 vs 9; 8: 9 vs 1; 9: 5 vs 2) and is missing 8 rows present in bg_transit_rules (Rahu houses 3/6/11, Ketu houses 3/6/11, Venus houses 11/12) -- an open L0 reconciliation item, not resolved here. This serving surface stays live as a reference-only table; only its authority as a computation source is retired.',
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
