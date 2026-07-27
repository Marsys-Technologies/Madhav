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
 * MC-029 (Śodhana Builder T6 "YOGI-BINDU"): also serves fact_category=
 * 'sensitive_point_yogi' — the Yogi/Avayogi/Duplicate-Yogi/Sahayogi rows the same
 * ga_sensitive_degree writer now computes (a standard classical Tajika/Jyotish
 * construct that had NO served category anywhere before this pass). Both categories
 * share this one surface rather than splitting into a second tool, since callers
 * already treat this as "the sensitive-degree tool" and a caller filtering by
 * check_type/subject gets both transparently; `fact_category` is now returned on
 * every row so a caller can tell the two families apart.
 *
 * Chart-scoped (principle #14): chart_id is the entitlement key; the capability route
 * enforces authorizeChartAccess before this handler runs. Bounded serving.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 200

// MC-029: the set of fact_category values this surface serves. Extending this array
// (rather than a single hardcoded string) is how a future sensitive-point category gets
// added to this tool without a second serving surface or a breaking schema change.
const SERVED_FACT_CATEGORIES = ['sensitive_degree_check', 'sensitive_point_yogi'] as const

export const getSensitiveDegreesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_sensitive_degrees',
  type:  'tool',
  layer: 'L1',
  name:  'get_sensitive_degrees',

  description: [
    'Retrieve sensitive-degree checks for a chart from chart_facts',
    "(fact_category='sensitive_degree_check'). Classically flagged",
    'longitudes (gaṇḍānta, sandhi, mṛtyu-bhāga, pushkara, etc.) checked against each',
    "graha's placement. Also serves fact_category='sensitive_point_yogi' — the Yogi/",
    'Avayogi/Duplicate-Yogi/Sahayogi Tajika construct (Yogi Sphuta = Sun+Moon+93°20\', ',
    'Yogi Graha = its nakshatra lord; Avayogi = Yogi+186°40\', its nakshatra lord; ',
    'Duplicate-Yogi/Sahayogi = the rasi lord of the Yogi Sphuta\'s own sign). Filter by ',
    "ayanamsha_id, subject (fact_subject, e.g. graha code or YOGI/AVAYOGI/DUPLICATE_YOGI/",
    "SAHAYOGI), or check_type (fact_key). Every row carries fact_category so the two ",
    'families are distinguishable. Bounded with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all." },
    subject:      { type: 'string', description: "Filter by fact_subject (e.g. a graha code like SUN, VEN, or a Yogi-system subject YOGI/AVAYOGI/DUPLICATE_YOGI/SAHAYOGI). Omit for all." },
    check_type:   { type: 'string', description: 'Filter by fact_key (the specific sensitive-degree or Yogi-system check). Omit for all.' },
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

    // MC-029: fact_category = ANY(...) rather than a single '=' so this surface serves
    // BOTH sensitive_degree_check and sensitive_point_yogi without a schema/route change.
    const filters: string[] = ["chart_id = $1", "fact_category = ANY($2)"]
    const params: unknown[] = [chart_id, [...SERVED_FACT_CATEGORIES]]
    let p = 3
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (subject)      { filters.push(`UPPER(fact_subject) = UPPER($${p++})`); params.push(subject) }
    if (check_type)   { filters.push(`fact_key = $${p++}`); params.push(check_type) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_num, fact_value_text,
             fact_value_jsonb, unit, ayanamsha_id, citation_ref
      FROM chart_facts
      WHERE ${where}
      ORDER BY ayanamsha_id, fact_category, fact_subject, fact_key
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
          provenance: { tables: ['chart_facts'], fact_category: [...SERVED_FACT_CATEGORIES] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
