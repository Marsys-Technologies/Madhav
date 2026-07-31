/**
 * query_mechanisms — L2 Bodha Mechanism (Yantra) serving surface
 * ===============================================================
 * SARVA-SIDDHI W-4 / CR-24 (BRIEF_SARVA_SIDDHI_v1_0.md §1 D-2; SARVA_SIDDHI_TRUTH_TABLE
 * Cluster 3). Serves `bodha_mechanisms` — the named, valenced CGM-subgraph objects the
 * `bo_yantra_mechanism` writer already builds (migration 445, D-2 Lane V-4) — as
 * FIRST-CLASS rows: mechanism_name, mechanism_class, valence, member chain/circuit
 * composition, edge-strength provenance (DR-7 `edge_strength_v1`) and a centrality
 * summary. Prior to this tool the table was reachable ONLY indirectly via
 * `traverse_chart_graph` subgraph traversal — never as first-class named mechanisms.
 * Read-only, bounded (LIMIT ≤50 + disclosed total + offset pagination).
 *
 * §N.6 Serving Density Principle: the CR-24 headline class is the chain/circuit family
 * (`convergent_dispositor_chain` / `dispositor_cycle` / `house_lordship_cycle`) — the
 * named multi-node mechanisms an acharya reads as a single structure. These are the
 * densest, most-actionable layer, so:
 *   - they are ordered FIRST (a class-priority sort key), ahead of the high-cardinality
 *     pairwise/triangle motifs (`mutual_aspect`, `mutual_aspect_triangle`) that would
 *     otherwise dominate a flat page and bury them;
 *   - a `chain_circuit_only` filter isolates them;
 *   - per-class + per-valence FACET counts over the FULL matching set are always
 *     returned (`facets`), plus `chain_circuit_count`, so a caller reading `count` can
 *     never mistake a page for the whole (density signaling is data, not narration).
 * No row is silently dropped (B.10) — everything is counted in `total_matching` and the
 * facet rollups even when it falls outside the current page.
 *
 * All `bodha_mechanisms` rows carry `verification_pass_status='single'` — there is no
 * catalog-only vs. confirmed split in this table, so a flat (facet-annotated) list is
 * honest; the field is still served per row for transparency.
 *
 * This docstring previously read `'pass'` and described it as "writer-confirmed". It was
 * neither: `bo_yantra_mechanism.py` stamped the literal unconditionally with no detector
 * behind it (SAMĀPTI A7-N8-AUDIT F-25, DVA Ruling 13 — 11/11 audited sites unearned), and
 * the serve layer's grounding check counted a bare `'pass'` as verified. Both are fixed;
 * the stored rows change at the next rebuild (C1-REBUILD).
 *
 * Chart-scoped (principle #14). Sparse-to-moderate by design (0 → a few hundred rows
 * across 5 ayanamshas); an empty list (total=0) is a valid result with an honest
 * `empty_reason`, not an error.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

/**
 * The CR-24 chain/circuit mechanism family — multi-node named structures (a convergent
 * dispositor chain, a closed dispositor cycle, a closed house-lordship circuit). These
 * are the "mechanism" specimens CR-24 asks to be served first-class, distinct from the
 * high-volume pairwise/triangle motifs also promoted into the table.
 */
const CHAIN_CIRCUIT_CLASSES = [
  'convergent_dispositor_chain',
  'dispositor_cycle',
  'house_lordship_cycle',
] as const

export const queryMechanismsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_mechanisms',
  type:  'tool',
  layer: 'L2',
  name:  'query_mechanisms',

  description: [
    'Retrieve named, valenced Mechanism (Yantra) objects from bodha_mechanisms — the',
    'first-class CGM-subgraph mechanisms the bo_yantra_mechanism writer builds. Each row:',
    'mechanism_name, mechanism_class (convergent_dispositor_chain | dispositor_cycle |',
    'house_lordship_cycle | yoga_cluster | mutual_reception | parivartana_chain | stellium |',
    'mutual_aspect | mutual_aspect_triangle | graha_bhava_affliction), valence',
    '(benefic|malefic|mixed|neutral), member_node_ids / member_edge_ids composition,',
    'edge_strength_avg/min/max (DR-7 edge_strength_v1 provenance), centrality_summary, and a',
    'grounding citation. The chain/circuit family (multi-node named mechanisms) is served',
    'FIRST and can be isolated via chain_circuit_only. Filters: ayanamsha_id, mechanism_class,',
    'valence, chain_circuit_only. Per-class and per-valence facet counts over the full match',
    'set are always returned. Bounded (LIMIT ≤50) with a disclosed total, offset pagination,',
    'and an honest empty_reason when a chart carries no mechanisms.',
  ].join(' '),

  input_schema: {
    chart_id:          { type: 'string',  description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:      { type: 'string',  description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all 5." },
    mechanism_class:   { type: 'string',  description: 'Filter by a single mechanism_class. Omit for all.' },
    valence:           { type: 'string',  description: 'Filter by valence (benefic|malefic|mixed|neutral). Omit for all.' },
    chain_circuit_only:{ type: 'boolean', description: 'When true, return only the CR-24 chain/circuit family (convergent_dispositor_chain, dispositor_cycle, house_lordship_cycle). Default false.' },
    limit:             { type: 'number',  description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:            { type: 'number',  description: 'Pagination offset (default 0).' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'graph_traversal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'graph',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  density_contract: {
    paginated: true,
    facets: ['mechanism_class', 'valence', 'chain_circuit'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const mechanism_class = args['mechanism_class'] ? String(args['mechanism_class']) : null
    const valence = args['valence'] ? String(args['valence']) : null
    const chain_circuit_only = args['chain_circuit_only'] === true || args['chain_circuit_only'] === 'true'
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)    { filters.push(`ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (mechanism_class) { filters.push(`mechanism_class = $${p++}`); params.push(mechanism_class) }
    if (valence)         { filters.push(`valence = $${p++}`);         params.push(valence) }
    if (chain_circuit_only) {
      filters.push(`mechanism_class = ANY($${p++})`)
      params.push([...CHAIN_CIRCUIT_CLASSES])
    }
    const where = filters.join(' AND ')
    // Snapshot BEFORE the class-priority param is appended: countSql's WHERE clause only ever
    // references the filter placeholders above, so it must be bound with exactly those values —
    // binding it against the full `params` (post class-priority push) sends more parameter
    // values than the count query's placeholders, which postgres rejects with
    // "bind message supplies N parameters, but prepared statement requires M" (EL-37 root cause).
    const filterParams = [...params]

    // §N.6: chain/circuit family sorts FIRST (priority 0), everything else after (priority 1),
    // then by edge-strength and structural size. The class-priority list is passed as a param
    // so no mechanism-class string is hard-coded into the SQL text.
    const classPriorityParam = `$${p++}`
    params.push([...CHAIN_CIRCUIT_CLASSES])

    const rowsSql = `
      SELECT mechanism_id, ayanamsha_id, snapshot_type, mechanism_name, mechanism_class, valence,
             member_node_ids_array, member_edge_ids_array, domains_affected_array,
             edge_strength_avg, edge_strength_min, edge_strength_max, edge_strength_formula_version,
             constituent_ga_vichara_ids_array, centrality_summary_jsonb, source_motif_id,
             verification_pass_status, citation_ref, citation_human,
             (mechanism_class = ANY(${classPriorityParam})) AS is_chain_circuit
      FROM bodha_mechanisms
      WHERE ${where}
      ORDER BY (mechanism_class = ANY(${classPriorityParam})) DESC,
               edge_strength_avg DESC NULLS LAST,
               COALESCE(array_length(member_node_ids_array, 1), 0) DESC,
               mechanism_name ASC
      LIMIT $${p} OFFSET $${p + 1}`

    // Facet rollups computed over the FULL matching set (not the page) — §N.6 density signal.
    const facetSql = `
      SELECT mechanism_class, valence,
             (mechanism_class = ANY(${classPriorityParam})) AS is_chain_circuit,
             COUNT(*)::text AS n
      FROM bodha_mechanisms
      WHERE ${where}
      GROUP BY mechanism_class, valence, is_chain_circuit`

    try {
      const [rowsRes, facetRes, countRes] = await Promise.all([
        query(rowsSql, [...params, limit, offset]),
        query<{ mechanism_class: string; valence: string; is_chain_circuit: boolean; n: string }>(facetSql, params),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_mechanisms WHERE ${where}`, filterParams),
      ])

      const total_matching = Number(countRes.rows[0]?.total ?? 0)

      const by_mechanism_class: Record<string, number> = {}
      const by_valence: Record<string, number> = {}
      let chain_circuit_count = 0
      for (const f of facetRes.rows) {
        const n = Number(f.n)
        by_mechanism_class[f.mechanism_class] = (by_mechanism_class[f.mechanism_class] ?? 0) + n
        by_valence[f.valence] = (by_valence[f.valence] ?? 0) + n
        if (f.is_chain_circuit) chain_circuit_count += n
      }

      const empty_reason = total_matching === 0
        ? 'No mechanisms (bodha_mechanisms) exist for this chart under the given filters. ' +
          'Either bo_yantra_mechanism has not been built for this chart, or the chart legitimately ' +
          'carries no motif/chain/circuit structure matching the filters (a correct negative, not an error).'
        : null

      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          chain_circuit_count,
          facets: {
            by_mechanism_class,
            by_valence,
            chain_circuit_classes: [...CHAIN_CIRCUIT_CLASSES],
          },
          empty_reason,
          filters: { ayanamsha_id, mechanism_class, valence, chain_circuit_only, limit, offset },
          provenance: {
            tables: ['bodha_mechanisms'],
            source: 'L2 Bodha mechanisms (bo_yantra_mechanism / migration 445); served chart-scoped, ' +
              'chain/circuit family first, budgeted. Edge-strength provenance: DR-7 edge_strength_v1.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
