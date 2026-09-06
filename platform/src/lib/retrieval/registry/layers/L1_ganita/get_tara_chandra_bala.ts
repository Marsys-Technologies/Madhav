/**
 * L1 retrieval: Tara Bala and Chandra Bala
 * Covers: tara_bala_natal_baseline, chandra_bala_natal_baseline
 * Tool: marsys://tool/L1/get_tara_chandra_bala
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getTaraChanndraBalaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_tara_chandra_bala',
  type: 'tool',
  layer: 'L1',
  name: 'get_tara_chandra_bala',
  description:
    'Retrieve Tara Bala and Chandra Bala natal baselines for a chart. ' +
    'Tara Bala: nakshatra-based strength computed as the count-position of each ' +
    'nakshatra from the natal Moon nakshatra (Purva Bhadrapada for the native); ' +
    'odd-counted nakshatras (1,3,5,7,9) are favorable, even unfavorable. ' +
    'Chandra Bala: Moon\'s positional strength relative to each graha by rashi distance; ' +
    'the Moon in a friend/own/exalted rashi gains full Chandra Bala. ' +
    'Both are inputs to overall Panchanga-based timing considerations. ' +
    'Covers 2 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 200 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  // F-B28 (L1_W1_ANALYSIS_BATCH_B.md, MUST, §N.6 items 3 & 4): total previously reported
  // the PAGE size (result.rows.length), not the true matching count -- a truncated answer
  // was indistinguishable from a complete one. Now backed by a real COUNT(*) query.
  density_contract: {
    paginated: true,
    facets: ['ayanamsha_id'],
    empty_reason: true,
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0

      const whereParams: unknown[] = [chartId, ['tara_bala_natal_baseline', 'chandra_bala_natal_baseline']]
      let where = `chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        whereParams.push(args.ayanamsha_id as string)
        where += ` AND ayanamsha_id = $${whereParams.length}`
      }

      const sql = `
        SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE ${where}
        ORDER BY fact_category, ayanamsha_id, fact_key
        LIMIT $${whereParams.length + 1} OFFSET $${whereParams.length + 2}`

      const [rowsRes, countRes] = await Promise.all([
        query<Record<string, unknown>>(sql, [...whereParams, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM chart_facts WHERE ${where}`, whereParams),
      ])
      const rows = rowsRes.rows ?? []
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id: chartId,
          rows,
          total_matching,
          more_available: total_matching > rows.length,
          ...(total_matching === 0
            ? { empty_reason: `No Tara Bala/Chandra Bala facts for chart ${chartId}${args.ayanamsha_id ? ` ayanamsha '${args.ayanamsha_id}'` : ''}.` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
