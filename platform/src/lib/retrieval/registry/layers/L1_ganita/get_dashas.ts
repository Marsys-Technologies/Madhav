/**
 * L1 retrieval: Vimshottari (+ multi-system) dasha periods
 * Source: chart_dashas table (not chart_facts)
 * Tool: marsys://tool/L1/get_dashas
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getDashasCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_dashas',
  type: 'tool',
  layer: 'L1',
  name: 'get_dashas',
  description:
    'Retrieve dasha period data for a chart from the chart_dashas table. ' +
    'Includes all 7 dasha systems built by L1: Vimshottari, Yogini, Ashtottari, ' +
    'Chara (Jaimini), Narayana, Shoola, and Kalachakra. ' +
    'Returns period boundaries (start/end dates), lord graha, level (Maha/Antar/Pratyantar/etc.), ' +
    'and the dasha system identifier. ' +
    'Use date filters to retrieve the dasha running on a specific date (e.g. today). ' +
    'Contains 536,471 rows for the native across all systems and ayanamshas.',
  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:  { type: 'string', description: 'Filter by ayanamsha_id (e.g. LAHIRI). Omit for all.' },
    dasha_system:  {
      type: 'string',
      description: 'Dasha system name: VIMSHOTTARI | YOGINI | ASHTOTTARI | CHARA | NARAYANA | SHOOLA | KALACHAKRA.',
    },
    level:         { type: 'number', description: 'Dasha level (1=Maha, 2=Antar, 3=Pratyantar). Omit for all.' },
    date_contains: { type: 'string', description: 'ISO date (YYYY-MM-DD). Returns dashas active on this date.' },
    lord_graha:    { type: 'string', description: 'Filter by lord graha abbreviation (e.g. SU, MO, MA).' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 200 },
  },
  required_inputs: ['chart_id'],
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 85, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId, limit, offset]
      let sql = `SELECT * FROM chart_dashas WHERE chart_id = $1`

      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      if (args.dasha_system) {
        sql += ` AND dasha_system = $${params.length + 1}`
        params.push(args.dasha_system as string)
      }
      if (args.level !== undefined) {
        sql += ` AND level = $${params.length + 1}`
        params.push(args.level as number)
      }
      if (args.lord_graha) {
        sql += ` AND lord_graha = $${params.length + 1}`
        params.push(args.lord_graha as string)
      }
      if (args.date_contains) {
        sql += ` AND start_date <= $${params.length + 1}::date AND end_date >= $${params.length + 2}::date`
        params.push(args.date_contains as string)
        params.push(args.date_contains as string)
      }
      sql += ` ORDER BY dasha_system, ayanamsha_id, start_date LIMIT $2 OFFSET $3`

      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: { chart_id: chartId, source_table: 'chart_dashas', rows: result.rows ?? [], total: result.rows?.length ?? 0 },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
