/**
 * query_cgm_paths — L2 Bodha CGM dispositor-path serving surface
 * ================================================================
 * WP-1.3(a) / F-L10-006 (LCA-19). Serves bodha_cgm_paths — dispositor chain paths
 * (45 rows/chart) that were computed but only readable by an internal L4 ph_nimitta
 * engine — UNREACHABLE over the deployed channel. Read-only, bounded.
 *
 * Chart-scoped (principle #14). Includes final-dispositor flags and path centrality.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryCgmPathsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_cgm_paths',
  type:  'tool',
  layer: 'L2',
  name:  'query_cgm_paths',

  description: [
    'Retrieve Chart Graph Model (CGM) dispositor-chain paths from bodha_cgm_paths.',
    'Fields: path_type, from_node_id, to_node_id, path_node_ids, path_edge_ids,',
    'path_length, path_strength, is_final_dispositor, convergence_count, path_label_human.',
    'Filters: ayanamsha_id, path_type, final_only (only final-dispositor paths).',
    'Bounded with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string',  description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string',  description: "Filter by ayanamsha. Omit for all." },
    path_type:    { type: 'string',  description: 'Filter by path_type. Omit for all.' },
    final_only:   { type: 'boolean', description: 'If true, only paths ending at a final dispositor.' },
    limit:        { type: 'number',  description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
  // Band phase 4 ("Reading the whole chart") — B.11 whole-chart-read (CGM graph paths).
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
    const path_type    = args['path_type'] ? String(args['path_type']) : null
    const final_only   = args['final_only'] === true
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (path_type)    { filters.push(`path_type = $${p++}`);    params.push(path_type) }
    if (final_only)   { filters.push(`is_final_dispositor = true`) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT path_id, ayanamsha_id, snapshot_type, path_type, from_node_id, to_node_id,
             path_node_ids_array, path_edge_ids_array, path_length, path_strength,
             is_final_dispositor, convergence_count, path_label_human,
             verification_pass_status, citation_ref, citation_human
      FROM bodha_cgm_paths
      WHERE ${where}
      ORDER BY path_strength DESC NULLS LAST, path_length
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_cgm_paths WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, path_type, final_only, limit },
          provenance: { tables: ['bodha_cgm_paths'], source: 'L2 Bodha CGM dispositor paths; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
