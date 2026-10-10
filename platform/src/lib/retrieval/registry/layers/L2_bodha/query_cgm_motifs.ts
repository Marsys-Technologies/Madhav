/**
 * query_cgm_motifs — L2 Bodha CGM motif serving surface
 * =======================================================
 * WP-1.3(a) / F-L10-005 (LCA-19). Serves bodha_cgm_motifs — mutual-reception /
 * stellium / parivartana pattern motifs (Chart Graph Model) that were computed but
 * had NO MCP serving path (only reachable to internal engines). Read-only, bounded.
 *
 * Chart-scoped (principle #14). Row counts are sparse (0–6/chart) — some charts
 * legitimately have no motifs; the tool returns an empty list with total=0, not an error.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { resolveHandlerAyanamsha, pushAyanamshaFilter, ayanamshaServeOrderBy, ayanamshaScopeEcho, type HandlerAyanamsha, PRIMARY_AYANAMSHA_ID_INPUT_TEXT } from '../../handler_ayanamsha'

const MAX_LIMIT = 50

export const queryCgmMotifsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_cgm_motifs',
  type:  'tool',
  layer: 'L2',
  name:  'query_cgm_motifs',

  description: [
    'Retrieve Chart Graph Model (CGM) motifs from bodha_cgm_motifs — recurring',
    'structural patterns such as mutual reception, stellium, and parivartana yoga.',
    'Fields: motif_name, motif_class, involved_node_ids, involved_edge_ids,',
    'motif_strength, classical_citation_id, verification_pass_status. Filters:',
    'ayanamsha_id, motif_class. Bounded with a disclosed total. Sparse by design —',
    'an empty list (total=0) means no motifs fired for the chart, not an error.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: PRIMARY_AYANAMSHA_ID_INPUT_TEXT },
    motif_class:  { type: 'string', description: 'Filter by motif class (e.g. mutual_reception, stellium). Omit for all.' },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'graph_traversal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'graph',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  // Band phase 4 ("Reading the whole chart") — B.11 whole-chart-read (CGM motifs).
  register: { reader_label: 'Reading the whole chart' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },

  // §N.6 serving-density contract (DENS-SERVED): bounded by `limit` with a disclosed `total_matching` / `more_available` (paginated in this contract's sense: a bounded read whose total / truncation the response discloses, not an offset / cursor pager), filterable by the
  // facets below; an empty result carries `empty_reason` naming the applied filters (see the handler).
  density_contract: {
    paginated: true,
    facets: ['ayanamsha_id', 'motif_class'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    // SS N-339/N-342 (PR-2): Lahiri-primary at handler level; ayanamsha_id:'all' / ayanamsha_scope:'all' opts out.
    let aya: HandlerAyanamsha
    try {
      aya = resolveHandlerAyanamsha(args)
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
    const ayanamsha_id = aya.id
    const motif_class  = args['motif_class'] ? String(args['motif_class']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    const ayaSql = pushAyanamshaFilter(aya, params)
    let p = params.length + 1
    if (motif_class)  { filters.push(`motif_class = $${p++}`);  params.push(motif_class) }
    const where = filters.join(' AND ') + ayaSql

    const sql = `
      SELECT motif_id, ayanamsha_id, snapshot_type, motif_name, motif_class,
             involved_node_ids_array, involved_edge_ids_array, motif_strength,
             classical_citation_id, verification_pass_status, citation_ref, citation_human
      FROM bodha_cgm_motifs
      WHERE ${where}
      ORDER BY motif_strength DESC NULLS LAST, motif_name, ${ayanamshaServeOrderBy()}
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_cgm_motifs WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          ...ayanamshaScopeEcho(aya),
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, motif_class, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No CGM motif rows matched for this chart (ayanamsha_id=${ayanamsha_id ?? 'any'}, motif_class=${motif_class ?? 'any'}).` }
            : {}),
          provenance: { tables: ['bodha_cgm_motifs'], source: 'L2 Bodha CGM motifs; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
