/**
 * query_cdlm_summary — L2 Bodha CDLM chart-summary serving surface
 * ==================================================================
 * WP-1.3(a) / F-L10-004 (LCA-19). Serves bodha_cdlm_chart_summary — the cross-domain
 * linkage strength summary (5 rows/chart, one per ayanamsha) that was computed and
 * stored but had NO MCP serving path. Read-only, bounded.
 *
 * Chart-scoped (principle #14). This is a whole-chart CDLM digest: total linkage,
 * contradiction density, dominant/weakest domains, bridge/asymmetric link counts.
 *
 * ── W2 dark-set wiring: `tier` facet (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0,
 * DARK_SET_WIRING_PLAN_v1_0 "CDLM rollup tiers" — S-effort item, "extend the existing
 * CDLM-serving capability with a tier/rollup_level facet rather than adding 3 new
 * standalone tools") ─────────────────────────────────────────────────────────────
 *
 * Three sibling CDLM tables were real (`226_bodha_spec_tables.sql`) but had zero
 * serving route (TABLE_CONCEPT_DISPOSITIONS_v2_0 §8, `RETRIEVAL_STRATEGY_v1_0.md`
 * §5.3's own named priority items): `bodha_cdlm_domain_rollups` (60 rows, per-domain
 * linkage rollups), `bodha_cdlm_pattern_clusters` (10 rows, detected cross-domain
 * patterns), `bodha_cdlm_evolution_gradients` (0 rows on the live chart — dynamic-dasha
 * evolution trends, genuinely empty is a real possibility for a static-natal-only
 * build, not a bug). These are depth-tiers of ONE CDLM concept, not 3 new concepts —
 * the `tier` facet reaches all three from this same capability. Default tier
 * (`chart_summary`) is unchanged from before this wave — fully backward compatible,
 * no existing caller's shape changes.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

type CdlmTier = 'chart_summary' | 'domain_rollups' | 'pattern_clusters' | 'evolution_gradients'

const TIER_TABLE: Record<CdlmTier, string> = {
  chart_summary:       'bodha_cdlm_chart_summary',
  domain_rollups:       'bodha_cdlm_domain_rollups',
  pattern_clusters:     'bodha_cdlm_pattern_clusters',
  evolution_gradients:  'bodha_cdlm_evolution_gradients',
}

// Per-tier column lists (each table's real schema, 226_bodha_spec_tables.sql) — every
// tier still surfaces verification_pass_status + citation_ref/citation_human so a
// caller can always ground a row, regardless of which tier it came from.
const TIER_COLUMNS: Record<CdlmTier, string> = {
  chart_summary: `summary_id, ayanamsha_id, snapshot_type, chart_typology_class,
             total_chart_linkage, contradiction_density,
             dominant_3_domains_array, weakest_3_domains_array,
             bridge_link_count, asymmetric_link_count,
             house_to_domain_strength_jsonb, karaka_to_domain_strength_jsonb,
             pattern_cluster_markers_jsonb, verification_pass_status,
             citation_ref, citation_human`,
  domain_rollups: `rollup_id, ayanamsha_id, snapshot_type, domain,
             total_inbound_linkage, total_outbound_linkage, diagonal_density,
             signal_count_for_domain, top_3_linked_domains_jsonb,
             contradiction_density, pattern_markers_for_domain_array,
             verification_pass_status, citation_ref, citation_human`,
  pattern_clusters: `pattern_id, ayanamsha_id, snapshot_type, pattern_marker_type,
             involved_domains_array, cluster_strength_total, involved_cells_array,
             involved_signals_array, contradicts_other_patterns_array, remedy_theme_jsonb,
             classical_archetype_match, predicted_outcome_class, active_dasha_windows_jsonb,
             verification_pass_status, citation_ref, citation_human`,
  evolution_gradients: `gradient_id, ayanamsha_id, dynamic_system_id, domain_row, domain_col,
             evolution_class, gradient_score, trend_iso_window_array, peak_period_lord,
             peak_period_iso, trough_period_iso, predicted_next_peak_iso,
             verification_pass_status, citation_ref, citation_human`,
}

const TIER_ORDER_BY: Record<CdlmTier, string> = {
  chart_summary:        'ayanamsha_id',
  domain_rollups:        'ayanamsha_id, domain',
  pattern_clusters:      'cluster_strength_total DESC NULLS LAST',
  evolution_gradients:   'ayanamsha_id, domain_row, domain_col',
}

export const queryCdlmSummaryCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_cdlm_summary',
  type:  'tool',
  layer: 'L2',
  name:  'query_cdlm_summary',

  description: [
    'Retrieve the Cross-Domain Linkage Matrix (CDLM) for a chart, across four depth tiers',
    '(the `tier` facet — default chart_summary, fully backward compatible):',
    "'chart_summary' (default) — bodha_cdlm_chart_summary, one row per ayanamsha:",
    'chart_typology_class, total_chart_linkage, contradiction_density, dominant_3_domains,',
    'weakest_3_domains, bridge_link_count, asymmetric_link_count, house_to_domain_strength,',
    'karaka_to_domain_strength.',
    "'domain_rollups' — bodha_cdlm_domain_rollups, per-domain linkage rollup (optionally",
    'filter by `domain`): total_inbound_linkage, total_outbound_linkage, diagonal_density,',
    'signal_count_for_domain, top_3_linked_domains, contradiction_density.',
    "'pattern_clusters' — bodha_cdlm_pattern_clusters, detected cross-domain patterns:",
    'pattern_marker_type, involved_domains, cluster_strength_total, classical_archetype_match,',
    'predicted_outcome_class.',
    "'evolution_gradients' — bodha_cdlm_evolution_gradients, dynamic-dasha CDLM trend over time:",
    'evolution_class (steepening/weakening/stable/oscillating), gradient_score, peak/trough periods.',
    'All tiers share verification_pass_status + citation. Filters: ayanamsha_id (all tiers),',
    'domain (domain_rollups only). Bounded with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha (e.g. 'LAHIRI'). Omit for all." },
    tier: {
      type: 'string',
      description: [
        'CDLM depth tier. "chart_summary" (default, whole-chart digest) | "domain_rollups"',
        '(per-domain linkage) | "pattern_clusters" (detected cross-domain patterns) |',
        '"evolution_gradients" (dynamic-dasha trend over time).',
      ].join(' '),
      enum: ['chart_summary', 'domain_rollups', 'pattern_clusters', 'evolution_gradients'],
      default: 'chart_summary',
    },
    domain: {
      type: 'string',
      description: "domain_rollups tier ONLY — filter to one domain (e.g. 'career', 'marriage'). Omit for all domains.",
    },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  // Band phase 4 ("Reading the whole chart") — B.11 whole-chart-read (CDLM cross-domain).
  register: { reader_label: 'Reading the whole chart' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const rawTier = args['tier'] ? String(args['tier']) : 'chart_summary'
    if (!(rawTier in TIER_TABLE)) {
      return { content: { error: `Unknown tier: ${rawTier}. Valid: ${Object.keys(TIER_TABLE).join(', ')}`, chart_id }, is_error: true }
    }
    const tier = rawTier as CdlmTier
    const table = TIER_TABLE[tier]

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const domain = args['domain'] ? String(args['domain']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    // domain filter only applies to domain_rollups (that table has a `domain` column;
    // the other three tiers don't — silently ignored for any other tier, not an error,
    // since a caller might reasonably leave it set while switching tiers).
    if (domain && tier === 'domain_rollups') { filters.push(`domain = $${p++}`); params.push(domain) }
    const where = filters.join(' AND ')

    const columns = TIER_COLUMNS[tier]
    const orderBy = TIER_ORDER_BY[tier]

    const sql = `
      SELECT ${columns}
      FROM ${table}
      WHERE ${where}
      ORDER BY ${orderBy}
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ${table} WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          tier,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, domain: tier === 'domain_rollups' ? domain : undefined, limit },
          provenance: { tables: [table], source: `L2 Bodha CDLM ${tier} tier; served chart-scoped.` },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id, tier }, is_error: true }
    }
  },
}
