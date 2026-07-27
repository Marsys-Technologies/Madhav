/**
 * query_discoveries — L2 Bodha non-obvious discoveries serving surface
 * ====================================================================
 * WP-1.3j / F-0129..0137 (W1-FOLLOWUP). Serves bodha_discoveries — the ranked
 * "what an acharya would miss" discovery ledger (thousands of rows/chart across
 * 5 ayanamshas) that was computed and stored but had NO MCP serving path.
 * Read-only, bounded (LIMIT ≤50 + disclosed total + offset pagination).
 *
 * Chart-scoped (principle #14). Ordered by composite_discovery_rank (1 = most salient).
 *
 * MC-015/026 (ŚODHANA T8): the raw `bodha_discoveries` table stores the SAME
 * underlying finding once per ayanāṃśa variant (5 ayanāṃśas built per chart) AND
 * once per matching MSR signal instance — e.g. one hypothesis_text can repeat
 * ~40 times within a single ayanāṃśa alone, on top of the ×5 ayanāṃśa repeat.
 * Served flat, ~1,269 rows collapse to a handful of real motifs served as if they
 * were hundreds of distinct discoveries. `discovery_families` collapses rows that
 * share (discovery_class, discovery_subsystem, hypothesis_text) into one entry
 * carrying a cross-ayanāṃśa agreement score (e.g. "5/5 ayanāṃśas agree"), a bounded
 * member list, and the best-ranked member's narrative fields — copying the
 * structural pattern of `query_temporal_activation`'s `window_families` verbatim.
 * The raw `rows` array is KEPT for back-compat; new callers should prefer
 * `discovery_families`.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

interface DiscoveryFamilyRow {
  discovery_class: string | null
  discovery_subsystem: string | null
  hypothesis_text: string | null
  member_count: string | number
  ayanamsha_count: string | number
  ayanamsha_ids: string[] | null
  member_discovery_ids: string[] | null
  best_composite_discovery_rank: string | number | null
  max_non_obviousness_score: string | number | null
  max_consequence_score: string | number | null
  affected_domains_array: string[] | null
  affected_domains_variant_count: string | number | null
  surface_reading: string | null
  depth_reading: string | null
  why_an_acharya_misses_it: string | null
  novelty_class: string | null
}

export const queryDiscoveriesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_discoveries',
  type:  'tool',
  layer: 'L2',
  name:  'query_discoveries',

  description: [
    'Retrieve ranked non-obvious chart discoveries from bodha_discoveries (ph: bo_* discovery engine).',
    'Each row is a cross-subsystem finding an individual acharya would likely miss, with a',
    'non_obviousness_score, consequence_score, composite_discovery_rank (1 = most salient),',
    'surface_reading vs depth_reading (+ surface_depth_delta), hypothesis_text, novelty_class,',
    'and why_an_acharya_misses_it. Filters: ayanamsha_id, discovery_class, domain. Ordered by',
    'composite_discovery_rank ASC. Bounded (LIMIT ≤50) with a disclosed total and offset pagination.',
    'MC-015/026: the raw `rows` array repeats the SAME underlying finding once per ayanāṃśa',
    'variant and once per matching signal instance (a single motif can appear ~40+ times).',
    'Prefer `discovery_families` — one entry per distinct (discovery_class, discovery_subsystem,',
    'hypothesis_text) motif, with a cross-ayanāṃśa agreement score (e.g. "5/5 ayanāṃśas agree"),',
    'a bounded member_discovery_ids list, and the best-ranked member\'s narrative fields.',
  ].join(' '),

  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:   { type: 'string', description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all." },
    discovery_class:{ type: 'string', description: 'Filter by discovery_class. Omit for all.' },
    domain:         { type: 'string', description: 'Filter to discoveries whose affected_domains_array contains this domain (e.g. "wealth", "career", "relationship", "health", "character"). Omit for all.' },
    limit:          { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}). Applies independently to both rows and discovery_families.` },
    offset:         { type: 'number', description: 'Pagination offset (default 0). Applies to rows; discovery_families is offset identically.' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const discovery_class = args['discovery_class'] ? String(args['discovery_class']) : null
    const domain = args['domain'] ? String(args['domain']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)    { filters.push(`ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (discovery_class) { filters.push(`discovery_class = $${p++}`); params.push(discovery_class) }
    if (domain)          { filters.push(`$${p++} = ANY(affected_domains_array)`); params.push(domain) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT discovery_id, ayanamsha_id, discovery_class, discovery_subsystem,
             non_obviousness_score, consequence_score, composite_discovery_rank,
             novelty_class, corroboration_count, corroborating_methods_array,
             affected_domains_array, surface_reading, depth_reading, surface_depth_delta,
             hypothesis_text, why_an_acharya_misses_it, meaningfulness_basis,
             constituent_refs_jsonb, cross_subsystem_refs_jsonb,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_discoveries
      WHERE ${where}
      ORDER BY composite_discovery_rank ASC NULLS LAST, non_obviousness_score DESC NULLS LAST
      LIMIT $${p} OFFSET $${p + 1}`

    // MC-015/026: family-collapse aggregate, computed server-side over the FULL matching
    // set (not just the bounded `rows` page above) — with ~40x intra-ayanāṃśa duplication
    // on top of the ×5 ayanāṃśa duplication, the top-K raw rows by rank are frequently ALL
    // one motif, so a family view built only from the bounded page would undercount both
    // the true member_count and the cross-ayanāṃśa agreement denominator. This mirrors
    // query_temporal_activation's window_families collapse structurally, but aggregates in
    // SQL (GROUP BY) rather than in JS over a fetched page, since the duplication ratio here
    // is far higher (1,269 rows -> a handful of motifs) than a bounded page could reflect.
    const familySql = `
      SELECT discovery_class, discovery_subsystem, hypothesis_text,
             COUNT(*)                                  AS member_count,
             COUNT(DISTINCT ayanamsha_id)               AS ayanamsha_count,
             array_agg(DISTINCT ayanamsha_id)           AS ayanamsha_ids,
             (array_agg(discovery_id ORDER BY composite_discovery_rank ASC NULLS LAST))[1:10] AS member_discovery_ids,
             MIN(composite_discovery_rank)              AS best_composite_discovery_rank,
             MAX(non_obviousness_score)                 AS max_non_obviousness_score,
             MAX(consequence_score)                     AS max_consequence_score,
             (array_agg(to_jsonb(affected_domains_array) ORDER BY composite_discovery_rank ASC NULLS LAST))[1] AS affected_domains_array,
             COUNT(DISTINCT affected_domains_array)      AS affected_domains_variant_count,
             (array_agg(surface_reading ORDER BY composite_discovery_rank ASC NULLS LAST))[1]         AS surface_reading,
             (array_agg(depth_reading ORDER BY composite_discovery_rank ASC NULLS LAST))[1]           AS depth_reading,
             (array_agg(why_an_acharya_misses_it ORDER BY composite_discovery_rank ASC NULLS LAST))[1] AS why_an_acharya_misses_it,
             (array_agg(novelty_class ORDER BY composite_discovery_rank ASC NULLS LAST))[1]            AS novelty_class
      FROM bodha_discoveries
      WHERE ${where}
      GROUP BY discovery_class, discovery_subsystem, hypothesis_text
      ORDER BY MIN(composite_discovery_rank) ASC NULLS LAST
      LIMIT $${p} OFFSET $${p + 1}`

    try {
      const [rowsRes, countRes, ayanamshaUniverseRes, familyRowsRes, familyCountRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_discoveries WHERE ${where}`, params),
        query<{ n: string }>(`SELECT COUNT(DISTINCT ayanamsha_id)::text AS n FROM bodha_discoveries WHERE ${where}`, params),
        query<DiscoveryFamilyRow>(familySql, [...params, limit, offset]),
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM (
             SELECT 1 FROM bodha_discoveries WHERE ${where}
             GROUP BY discovery_class, discovery_subsystem, hypothesis_text
           ) fam`,
          params,
        ),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      const ayanamsha_universe_count = Number(ayanamshaUniverseRes.rows[0]?.n ?? 0)
      const total_family_count = Number(familyCountRes.rows[0]?.total ?? 0)

      const discovery_families = familyRowsRes.rows.map(f => {
        const ayanamsha_count = Number(f.ayanamsha_count ?? 0)
        return {
          discovery_class: f.discovery_class,
          discovery_subsystem: f.discovery_subsystem,
          hypothesis_text: f.hypothesis_text,
          member_count: Number(f.member_count ?? 0),
          ayanamsha_count,
          ayanamsha_ids: f.ayanamsha_ids ?? [],
          // e.g. "5/5 ayanamshas agree" — denominator is the ayanamsha universe actually
          // represented under the SAME filters as this family query (so an explicit
          // ayanamsha_id filter correctly collapses the denominator to 1, not the chart's
          // full 5-ayanamsha build).
          ayanamsha_agreement: `${ayanamsha_count}/${ayanamsha_universe_count} ayanamshas agree`,
          member_discovery_ids: f.member_discovery_ids ?? [],
          best_composite_discovery_rank: f.best_composite_discovery_rank,
          max_non_obviousness_score: f.max_non_obviousness_score,
          max_consequence_score: f.max_consequence_score,
          affected_domains_array: f.affected_domains_array ?? [],
          affected_domains_variant_count: Number(f.affected_domains_variant_count ?? 1),
          surface_reading: f.surface_reading,
          depth_reading: f.depth_reading,
          why_an_acharya_misses_it: f.why_an_acharya_misses_it,
          novelty_class: f.novelty_class,
        }
      })

      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          // MC-015/026: family-collapsed view — prefer this over `rows` for a non-duplicated
          // read. See docstring + tool description for why `rows` alone over-represents.
          discovery_families,
          discovery_family_count: discovery_families.length,
          total_family_count,
          more_families_available: offset + discovery_families.length < total_family_count,
          ayanamsha_universe_count,
          filters: { ayanamsha_id, discovery_class, domain, limit, offset },
          provenance: {
            tables: ['bodha_discoveries'],
            source: 'L2 Bodha discovery ledger; served chart-scoped, budgeted.',
            note: 'discovery_families collapses (discovery_class, discovery_subsystem, hypothesis_text) ' +
              'duplicates across ayanāṃśa variants and repeated signal instances into one motif per family ' +
              '(MC-015/026). `rows` is the raw, undeduplicated set — kept for back-compat.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
