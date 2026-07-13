/**
 * get_sensitive_degrees — L1 Gaṇita sensitive-degree serving surface
 * ===================================================================
 * W4-loop-1 (E-6 group4). Serves ga_sensitive_degree — the L1 sensitive-degree-check
 * asset stored in chart_facts under fact_category='sensitive_degree_check'
 * (275 rows/chart) but with NO deployed MCP tool serving it. Read-only.
 *
 * Sensitive degrees = classically flagged longitudes (gaṇḍānta, sandhi, mṛtyu-bhāga,
 * pushkara, etc.) checked against each graha's placement.
 *
 * Chart-scoped (principle #14): chart_id is the entitlement key; the capability route
 * enforces authorizeChartAccess before this handler runs. Bounded serving.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 200

export const getSensitiveDegreesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_sensitive_degrees',
  type:  'tool',
  layer: 'L1',
  name:  'get_sensitive_degrees',

  description: [
    'Retrieve sensitive-degree checks for a chart from chart_facts',
    "(fact_category='sensitive_degree_check', 275 rows/chart). Classically flagged",
    'longitudes (gaṇḍānta, sandhi, mṛtyu-bhāga, pushkara, etc.) checked against each',
    "graha's placement. Filter by ayanamsha_id, subject (fact_subject, e.g. graha code),",
    'or check_type (fact_key). Bounded with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all." },
    subject:      { type: 'string', description: 'Filter by fact_subject (e.g. a graha code like SUN, VEN). Omit for all.' },
    check_type:   { type: 'string', description: 'Filter by fact_key (the specific sensitive-degree check). Omit for all.' },
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
    bulk_context: { pre_fetch_priority: 35, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const subject      = args['subject'] ? String(args['subject']) : null
    const check_type   = args['check_type'] ? String(args['check_type']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ["chart_id = $1", "fact_category = 'sensitive_degree_check'"]
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (subject)      { filters.push(`UPPER(fact_subject) = UPPER($${p++})`); params.push(subject) }
    if (check_type)   { filters.push(`fact_key = $${p++}`); params.push(check_type) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT fact_id, fact_subject, fact_key, fact_value_num, fact_value_text,
             fact_value_jsonb, unit, ayanamsha_id, citation_ref
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
          filters: { ayanamsha_id, subject, check_type, limit },
          ...(total_matching === 0
            ? { empty_reason: `No sensitive-degree checks for chart ${chart_id}${subject ? ` subject '${subject}'` : ''}${check_type ? ` check '${check_type}'` : ''}.` }
            : {}),
          provenance: { tables: ['chart_facts'], fact_category: 'sensitive_degree_check' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
