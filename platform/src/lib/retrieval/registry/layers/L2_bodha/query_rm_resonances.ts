/**
 * query_rm_resonances — L2 Bodha graha-resonance serving surface
 * ==============================================================
 * WP-1.3j / F-0161,0165,0174 (W1-FOLLOWUP). Serves bodha_rm_resonances — the
 * per-graha remedial-resonance scores (45 rows/chart across 5 ayanamshas: 9 grahas ×
 * 5 ayanamshas) computed and stored but with NO MCP serving path. Read-only, bounded.
 *
 * This is the per-chart weakness/priority map that drives query_rm_prescriptions.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryRmResonancesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_rm_resonances',
  type:  'tool',
  layer: 'L2',
  name:  'query_rm_resonances',

  description: [
    'Retrieve per-graha remedial resonance scores from bodha_rm_resonances (Remedial Matrix).',
    'Each row scores one graha: resonance_score, weakness_score, contradiction_factor, domain_burden,',
    'motif_burden, is_yoga_karaka_flag, is_chara_karaka_role, weakest_rank_in_chart,',
    'remedy_priority_class, and the associated doshas / motifs / cdlm cells. Filters: ayanamsha_id, graha.',
    'Ordered by resonance_score DESC. Bounded (LIMIT ≤50) with a disclosed total + offset pagination.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    graha:        { type: 'string', description: 'Filter by graha. Omit for all.' },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:       { type: 'number', description: 'Pagination offset (default 0).' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 45, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const graha = args['graha'] ? String(args['graha']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (graha)        { filters.push(`graha = $${p++}`);        params.push(graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT resonance_id, ayanamsha_id, graha, resonance_score, weakness_score,
             contradiction_factor, domain_burden, motif_burden,
             is_yoga_karaka_flag, is_chara_karaka_role, weakest_rank_in_chart,
             remedy_priority_class, associated_doshas_array, associated_motifs_array,
             associated_cdlm_cells_array, verification_pass_status, citation_ref, citation_human,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_rm_resonances
      WHERE ${where}
      ORDER BY resonance_score DESC NULLS LAST, weakness_score DESC NULLS LAST
      LIMIT $${p} OFFSET $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_rm_resonances WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          filters: { ayanamsha_id, graha, limit, offset },
          provenance: { tables: ['bodha_rm_resonances'], source: 'L2 Bodha Remedial Matrix resonances; served chart-scoped, budgeted.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
