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
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha. Omit for all." },
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

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const motif_class  = args['motif_class'] ? String(args['motif_class']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (motif_class)  { filters.push(`motif_class = $${p++}`);  params.push(motif_class) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT motif_id, ayanamsha_id, snapshot_type, motif_name, motif_class,
             involved_node_ids_array, involved_edge_ids_array, motif_strength,
             classical_citation_id, verification_pass_status, citation_ref, citation_human
      FROM bodha_cgm_motifs
      WHERE ${where}
      ORDER BY motif_strength DESC NULLS LAST, motif_name
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
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, motif_class, limit },
          provenance: { tables: ['bodha_cgm_motifs'], source: 'L2 Bodha CGM motifs; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
