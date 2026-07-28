/**
 * L1 retrieval: ga_transit_anchors (Natal Transit Anchors)
 * Reads the ga_transit_anchors table built by the ga_transit_anchors L1 writer.
 * Provides natal position anchors for Gochara (transit) calculation:
 *   - natal_sign: which sign each graha occupies natally
 *   - natal_house_from_moon: classical 1-based house count from natal Moon sign
 *   - natal_degree_absolute: sidereal longitude (0-360°)
 * One row per (chart_id, ayanamsha_id, graha) — 9 grahas × 5 ayanamshas = 45 rows.
 * Tool: marsys://tool/L1/get_transit_anchors
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getTransitAnchorsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_transit_anchors',
  type: 'tool',
  layer: 'L1',
  name: 'get_transit_anchors',
  description:
    'Retrieve natal transit anchor data for a chart: the natal sign, classical house from Moon, ' +
    'and absolute sidereal degree for each of the 9 grahas, by ayanamsha. ' +
    'Used as the reference substrate for all Gochara (planetary transit) computations — ' +
    'sign-ingress triggers, degree-exact conjunctions, and classical vedha rules. ' +
    '45 rows per chart (9 grahas × 5 ayanamshas). ' +
    'natal_house_from_moon: classical 1-based count from natal Moon sign (Moon own = 1).',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha (e.g. lahiri_chitrapaksha). Omit for all 5.' },
    graha:        { type: 'string', description: 'Filter to one graha (sun/moon/mars/mercury/jupiter/venus/saturn/rahu/ketu). Omit for all 9.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 50 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Transit windows' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 50, 100)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId]
      let sql = `
        SELECT id, chart_id, ayanamsha_id, graha,
               natal_sign, natal_house_from_moon, natal_degree_absolute, computed_at
        FROM ga_transit_anchors
        WHERE chart_id = $1
      `
      if (args.ayanamsha_id) {
        params.push(args.ayanamsha_id as string)
        sql += ` AND ayanamsha_id = $${params.length}`
      }
      if (args.graha) {
        params.push((args.graha as string).toLowerCase())
        sql += ` AND graha = $${params.length}`
      }
      params.push(limit)
      params.push(offset)
      sql += ` ORDER BY ayanamsha_id, graha LIMIT $${params.length - 1} OFFSET $${params.length}`

      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          chart_id: chartId,
          anchors: result.rows ?? [],
          total: result.rows?.length ?? 0,
          note: 'natal_house_from_moon: classical 1-based count from natal Moon sign; natal_degree_absolute: sidereal 0-360°',
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
