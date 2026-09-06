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
import { grahaCodeOf } from '@/lib/retrieval/graha_labels'

// F-D25 (L1_W1_ANALYSIS_BATCH_D.md, NOW, §N.6; D-SERVICE ≤2 hops to L1): the writer
// (ga_transit_anchors.py) derives natal_sign/natal_degree_absolute/natal_nakshatra from
// chart_facts rows filtered on this EXACT (fact_category, fact_key) set, keyed by the
// graha's fact_subject code — but does not itself store the source fact_id on the
// written row. Re-deriving the same filter here at serve time (not fabricating it) lets
// each served row genuinely ground back to the chart_facts rows it was built from.
const SOURCE_FACT_CATEGORIES = ['graha_position', 'graha_sign_attributes']
const SOURCE_FACT_KEYS = ['sign', 'longitude_sidereal', 'nakshatra']

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
    'natal_house_from_moon: classical 1-based count from natal Moon sign (Moon own = 1). ' +
    'Each row carries constituent_fact_ids (§N.5) resolving back to the source chart_facts ' +
    'rows (graha_position/graha_sign_attributes) it was derived from.',
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
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Transit windows' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },
  density_contract: {
    paginated: true,
    facets: ['ayanamsha_id', 'graha'],
    empty_reason: true,
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
      const anchors = result.rows ?? []

      // F-D25: resolve each served row's real constituent chart_facts.fact_id(s) — the
      // exact same (fact_category, fact_key, fact_subject) filter the writer itself used,
      // re-run here at serve time. Batched per ayanamsha_id present on this page (never
      // per-row) to avoid an N+1 query pattern.
      const ayanamshasOnPage = [...new Set(anchors.map(a => String(a['ayanamsha_id'])))]
      const factIdsByAyanamshaAndSubject = new Map<string, string[]>()
      if (ayanamshasOnPage.length > 0) {
        const factRows = await query<{ ayanamsha_id: string; fact_subject: string; fact_id: string }>(
          `SELECT ayanamsha_id, fact_subject, fact_id
           FROM chart_facts
           WHERE chart_id = $1
             AND ayanamsha_id = ANY($2::text[])
             AND fact_category = ANY($3::text[])
             AND fact_key = ANY($4::text[])`,
          [chartId, ayanamshasOnPage, SOURCE_FACT_CATEGORIES, SOURCE_FACT_KEYS],
        )
        for (const r of factRows.rows) {
          const key = `${r.ayanamsha_id}|${r.fact_subject}`
          if (!factIdsByAyanamshaAndSubject.has(key)) factIdsByAyanamshaAndSubject.set(key, [])
          factIdsByAyanamshaAndSubject.get(key)!.push(r.fact_id)
        }
      }
      const groundedAnchors = anchors.map(row => {
        let subjectCode: string | null = null
        try { subjectCode = grahaCodeOf(String(row['graha'])) } catch { /* unrecognized graha string — leave ungrounded */ }
        const constituentFactIds = subjectCode
          ? factIdsByAyanamshaAndSubject.get(`${row['ayanamsha_id']}|${subjectCode}`) ?? []
          : []
        return { ...row, constituent_fact_ids: constituentFactIds }
      })

      return {
        content: {
          chart_id: chartId,
          ...(anchors.length === 0
            ? { empty_reason: `No transit anchors for chart ${chartId}${args.ayanamsha_id ? ` ayanamsha '${args.ayanamsha_id}'` : ''}${args.graha ? ` graha '${args.graha}'` : ''}.` }
            : {}),
          anchors: groundedAnchors,
          total: groundedAnchors.length,
          note: 'natal_house_from_moon: classical 1-based count from natal Moon sign; natal_degree_absolute: sidereal 0-360°. Each row\'s constituent_fact_ids resolve back to the chart_facts rows (graha_position/graha_sign_attributes) it was derived from (§N.5).',
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
