/**
 * get_medical_indications — L1 Gaṇita Vaidya-phala serving surface
 * ==================================================================
 * WP-1.3(a) / F-L10-001 (LCA-19). Serves ga_medical — the L1 medical-indication
 * (Vaidya-phala) asset that was computed and stored (45 rows/chart on both charts)
 * but had NO deployed MCP tool serving it. This tool exposes it read-only.
 *
 * NOT a diagnosis: every row carries not_diagnosis=true and an indication_tier.
 * These are classical graha→dosha/organ watch-indications, not medical advice.
 *
 * Chart-scoped (principle #14): chart_id is the entitlement key; the primitives
 * route enforces authorizeChartAccess before this handler runs. Bounded serving.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const getMedicalIndicationsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_medical_indications',
  type:  'tool',
  layer: 'L1',
  name:  'get_medical_indications',

  description: [
    'Retrieve classical medical (Vaidya-phala) indications for a chart from ga_medical.',
    'Per-graha rows: natal_sign, natal_nakshatra, indication_strength, dosha_aggravated',
    '(vata/pitta/kapha), organ_watch, body_part_watch, nakshatra_body_part, indication_tier,',
    'and classical_citation. NOT a diagnosis (not_diagnosis=true on every row) — these are',
    'classical watch-indications, not medical advice. Filters: graha, ayanamsha_id,',
    'indication_tier. Bounded to 50 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:        { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha:           { type: 'string', description: 'Filter by graha (e.g. Sun, Moon, Mars). Omit for all.' },
    ayanamsha_id:    { type: 'string', description: "Filter by ayanamsha (e.g. 'LAHIRI'). Omit for all." },
    indication_tier: { type: 'string', description: 'Filter by indication tier. Omit for all.' },
    limit:           { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const graha           = args['graha'] ? String(args['graha']) : null
    const ayanamsha_id    = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const indication_tier = args['indication_tier'] ? String(args['indication_tier']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha)           { filters.push(`graha = $${p++}`);           params.push(graha) }
    if (ayanamsha_id)    { filters.push(`ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (indication_tier) { filters.push(`indication_tier = $${p++}`); params.push(indication_tier) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT id, graha, ayanamsha_id, natal_sign, natal_nakshatra, indication_strength,
             dosha_aggravated, organ_watch, body_part_watch, nakshatra_body_part,
             indication_tier, not_diagnosis, classical_citation
      FROM ga_medical
      WHERE ${where}
      ORDER BY graha, ayanamsha_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_medical WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { graha, ayanamsha_id, indication_tier, limit },
          disclaimer: 'NOT a medical diagnosis — classical Vaidya-phala watch-indications only.',
          provenance: { tables: ['ga_medical'], source: 'L1 Gaṇita Vaidya-phala; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
