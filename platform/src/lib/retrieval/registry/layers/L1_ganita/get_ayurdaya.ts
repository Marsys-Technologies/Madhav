/**
 * get_ayurdaya — L1 Gaṇita longevity (Āyurdāya) serving surface
 * ==============================================================
 * W4-loop-1 (E-6 group4). Serves ga_ayurdaya — the L1 longevity asset stored in
 * chart_facts under fact_category='ayurdaya' (130 rows/chart across the 3 classical
 * methods × 5 ayanamshas) but with NO deployed MCP tool serving it. Read-only.
 *
 * Answers longevity-band questions: the Piṇḍāyu / Aṃśāyu / Naisargikāyu methods each
 * yield total_years and a band (alpāyu / madhyāyu / pūrṇāyu). NOT a death prediction —
 * classical longevity computation only; rows carry the method + band verbatim from L1.
 *
 * Chart-scoped (principle #14): chart_id is the entitlement key; the capability route
 * enforces authorizeChartAccess before this handler runs. Bounded serving.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 200

export const getAyurdayaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_ayurdaya',
  type:  'tool',
  layer: 'L1',
  name:  'get_ayurdaya',

  description: [
    'Retrieve classical longevity (Āyurdāya) computations for a chart from chart_facts',
    "(fact_category='ayurdaya'). Covers the classical methods (Piṇḍāyu / Aṃśāyu /",
    'Naisargikāyu, subject codes like AMSAYU/PINDAYU/NISARGAYU) — each with total_years',
    '(fact_value_num) and a longevity band (fact_value_text: alpayu/madhyayu/purnayu).',
    'Filter by ayanamsha_id (omit for all 5) or method (fact_subject). NOT a death',
    'prediction — classical longevity-band computation only. Bounded with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all 5." },
    method:       { type: 'string', description: 'Filter by longevity method fact_subject (e.g. AMSAYU, PINDAYU, NISARGAYU). Omit for all.' },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
    bulk_context: { pre_fetch_priority: 45, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const method       = args['method'] ? String(args['method']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ["chart_id = $1", "fact_category = 'ayurdaya'"]
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (method)       { filters.push(`UPPER(fact_subject) = UPPER($${p++})`); params.push(method) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT fact_id, fact_subject, fact_key, fact_value_num, fact_value_text,
             unit, ayanamsha_id, citation_ref
      FROM chart_facts
      WHERE ${where}
      ORDER BY ayanamsha_id, fact_subject, fact_key
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query<Record<string, unknown>>(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM chart_facts WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, method, limit },
          ...(total_matching === 0
            ? { empty_reason: `No ayurdaya (longevity) facts for chart ${chart_id}${ayanamsha_id ? ` at ayanamsha '${ayanamsha_id}'` : ''}${method ? ` for method '${method}'` : ''}.` }
            : {}),
          disclaimer: 'NOT a death prediction — classical Āyurdāya longevity-band computation only.',
          note: 'fact_value_num = total_years for the method; fact_value_text = longevity band (alpayu/madhyayu/purnayu).',
          provenance: { tables: ['chart_facts'], fact_category: 'ayurdaya' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
