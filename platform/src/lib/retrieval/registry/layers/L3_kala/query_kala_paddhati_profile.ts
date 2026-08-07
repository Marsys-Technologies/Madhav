/**
 * query_kala_paddhati_profile — L3 Kāla paddhati (convention) profile serving surface
 * ==========================================================================
 * ṢAḌ-DARŚANA W3 lane-w3rit, registry item 37.
 *
 * WHY THIS FILE EXISTS — THE DOCUMENTED GAP IT CLOSES:
 * `kala_sky_pattern.ts`'s `fetchPaddhatiProfile` calls
 * `callPlatformPrimitive('query_kala_paddhati_profile', ...)` but the capability
 * was never registered in the L3 registry. SHAD_DARSHANA_STATE.md Night-3 close
 * documents the gap verbatim: "Item 37 partial: storage/reader/divergence-block
 * closed; `query_kala_paddhati_profile` capability itself doesn't exist yet —
 * needs a shared `index.ts` boundary negotiation the lane correctly declined to
 * resolve unilaterally. Degrades honestly (honest_empty, corpus-default fallback
 * disclosed) in the meantime." This file closes that gap.
 *
 * TABLE: `kala_paddhati_profile` (seeded by migrations 533/534/537 — versioned
 * config data, no writer, per ADJUDICATION-8's stated precedent of the weights-v0
 * seed pattern, brief §2.5.4). Schema: chart_id × factor_family × convention_id ×
 * school_tag × constraint_role × convention_status × provenance × corpus_gap_ref ×
 * native_confirmed × awaiting_native_confirmation × version (zero-padded) ×
 * confirmation_provenance (nullable, migration 534).
 *
 * ── ADJUDICATION-8 RAILS (binding, both enforced here) ──────────────────────
 *
 * RAIL 2: This capability NEVER filters on `convention_status`. The consumer
 * (`kala_sky_pattern.ts`'s fetchPaddhatiProfile) is the ONLY place that splits
 * operative (`computed`) vs divergence-slot (`declared_not_computed`) rows. A
 * WHERE clause on convention_status here would silently break the divergence
 * surface that ADJUDICATION-8's own design requires to be "real rather than
 * decorative". Both convention_status values are served; the consumer filters.
 *
 * RAIL 3: native_confirmed, awaiting_native_confirmation, and
 * confirmation_provenance are served verbatim from the stored row. This
 * capability NEVER synthesizes, inverts, or defaults these columns — what is on
 * record is what the native has attested, and the capability cannot speak for
 * the native beyond that.
 *
 * ── VERSION ORDERING NOTE ────────────────────────────────────────────────────
 * Version selection is CLIENT-SIDE in `fetchPaddhatiProfile` via string-sort
 * (the zero-padded `paddhati_v01`/`paddhati_v02` pattern from migration 533's
 * own header). This capability returns ALL rows for the chart, ordered by
 * version ASC then factor_family/convention_id, so a client doing string-sort
 * on the version column gets the same result regardless of which version filter
 * the client applies. `paddhati_v10` would sort below `paddhati_v2` without
 * zero-padding — the seeded data uses zero-padded versions; this capability
 * does not try to normalize them, because doing so would mutate the stored value.
 *
 * ── LAYER SEATING ────────────────────────────────────────────────────────────
 * kala_paddhati_profile is a per-chart config table in the Kāla (L3) layer,
 * seeded by migration (no writer, no asset_registry row). URI prefix L3 follows
 * the campaign's layer-seating convention for all kala_* tables, even though
 * this particular table carries no `depends_on` DAG edges (it is config, not a
 * built asset). The capability is registered alongside the other L3 capabilities
 * in `layers/L3_kala/index.ts`.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryKalaPaddhatiProfileCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_kala_paddhati_profile',
  type:  'tool',
  layer: 'L3',
  name:  'query_kala_paddhati_profile',

  description: [
    'Retrieve the per-chart paddhati (convention) profile from kala_paddhati_profile',
    '(ṢAḌ-DARŚANA item 37 / ADJUDICATION-8). Each row: factor_family (e.g. "agnivasa"),',
    'convention_id, school_tag, constraint_role (hard/soft/informational),',
    'convention_status (computed | declared_not_computed — BOTH values are returned;',
    'the consumer filters on computed for grading per ADJUDICATION-8 rail 2),',
    'provenance, corpus_gap_ref, native_confirmed, awaiting_native_confirmation,',
    'version (zero-padded, e.g. paddhati_v01/paddhati_v02 — version selection is',
    'string-sort client-side; paddhati_v10 would sort below paddhati_v2 without padding),',
    'confirmation_provenance (set iff native_confirmed=TRUE, migration 534).',
    'Returns all versions for the chart; client applies ORDER BY version DESC to get latest.',
    'native_confirmed and confirmation_provenance are served verbatim — ADJUDICATION-8 rail 3.',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    factor_family: {
      type: 'string',
      description: "Filter by factor_family (e.g. 'agnivasa'). Omit for all families.",
    },
    version: {
      type: 'string',
      description: "Filter by exact version string (e.g. 'paddhati_v01'). Omit for all versions.",
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  register: { reader_label: 'Consulting the chart — paddhati convention profile' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const factor_family = args['factor_family'] ? String(args['factor_family']) : null
    const version       = args['version']       ? String(args['version'])       : null

    // Build WHERE clause — never filter on convention_status (ADJUDICATION-8 rail 2).
    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (factor_family) { filters.push(`factor_family = $${p++}`); params.push(factor_family) }
    if (version)       { filters.push(`version = $${p++}`);       params.push(version) }
    const where = filters.join(' AND ')

    // All columns the consumer (kala_sky_pattern.ts's PaddhatiConventionRow) needs,
    // including confirmation_provenance (nullable, added in migration 534).
    // ORDER BY version ASC, factor_family, convention_id — deterministic, so
    // the client's string-sort version selection is stable across calls.
    const sql = `
      SELECT factor_family, convention_id, school_tag, constraint_role,
             convention_status, provenance, corpus_gap_ref,
             native_confirmed, awaiting_native_confirmation, version,
             confirmation_provenance
      FROM kala_paddhati_profile
      WHERE ${where}
      ORDER BY version ASC, factor_family, convention_id`

    try {
      const rowsRes = await query(sql, params)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          filters: {
            factor_family: factor_family ?? 'all',
            version: version ?? 'all',
          },
          provenance: {
            tables: ['kala_paddhati_profile'],
            source: 'ṢAḌ-DARŚANA W3 item 37 (ADJUDICATION-8) — per-chart paddhati convention profile; versioned config seeded by migrations 533/534/537, no writer.',
            adjudication_8_rail_2: 'convention_status NOT filtered here — consumer (kala_sky_pattern.ts fetchPaddhatiProfile) is the only place that splits operative vs declared rows.',
            adjudication_8_rail_3: 'native_confirmed and confirmation_provenance served verbatim from the stored row — this capability does not synthesize them.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
