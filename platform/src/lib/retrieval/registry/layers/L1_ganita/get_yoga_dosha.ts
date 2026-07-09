/**
 * L1 retrieval: yoga and dosha firings
 * Covers: yoga_fires, yoga_label, dosha_fires, dosha_label, bhadra_flag, panchaka_flag
 * Tool: marsys://tool/L1/get_yoga_dosha
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const YD_CATEGORIES = ['yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag']

// R5.3 B2 (Q9-N-1 ruling item B): `facet` was accepted on this URI's args (register_p1_ganita.ts's
// ganita_structural_get always passes it) but silently ignored — every facet routed through
// get_yoga_dosha (parivartana/yoga_fires/dosha_fires/graha_yuddha) returned the identical
// unfiltered ~530-row union of all 6 categories. This map scopes the two facets that DO have a
// clean 1:1 category grouping in this tool (yoga_fires→yoga rows, dosha_fires→dosha rows);
// parivartana/graha_yuddha are pre-existing routing mismatches (their real data lives in
// get_dispositors/get_graha_yuddha) and are out of scope for this bounded fix.
const FACET_TO_TYPE: Record<string, 'yoga' | 'dosha' | 'flag'> = {
  yoga_fires: 'yoga',
  dosha_fires: 'dosha',
}

export const getYogaDoshaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_yoga_dosha',
  type: 'tool',
  layer: 'L1',
  name: 'get_yoga_dosha',
  description:
    'Retrieve yoga and dosha data for a chart: yoga_fires (predicate firings with activating factors), ' +
    'yoga_label (canonical name and tradition), dosha_fires (affliction firings), dosha_label, ' +
    'bhadra_flag, and panchaka_flag. ' +
    'Every yoga/dosha firing carries its constituent grahas and fact_id for Bodha back-reference. ' +
    'Weak-tail signals (low-salience yogas) are included — strength is a column, not a gate. ' +
    'Covers 6 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    type:         { type: 'string', description: 'yoga | dosha | flag. Omit for all.', enum: ['yoga', 'dosha', 'flag'] },
    categories:   { type: 'array',  description: 'Subset of categories.', items: { type: 'string' } },
    facet:        { type: 'string', description: "Structural facet alias from ganita_structural_get " +
      "('yoga_fires' | 'dosha_fires' scope categories; other facet values are ignored here)." },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 500 },
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
    bulk_context: { pre_fetch_priority: 88, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const facet      = args.facet as string | undefined
      const type       = (args.type as string | undefined) ?? (facet ? FACET_TO_TYPE[facet] : undefined)

      let categories = (args.categories as string[]) ?? YD_CATEGORIES
      if (type === 'yoga')  categories = categories.filter(c => c.startsWith('yoga') || c === 'bhadra_flag')
      if (type === 'dosha') categories = categories.filter(c => c.startsWith('dosha'))
      if (type === 'flag')  categories = categories.filter(c => c.endsWith('_flag'))

      // Base filter params — shared by the COUNT query and the paged SELECT below, so
      // `total` (D5 coverage receipt — family size, envelope.ts buildCoverageStamp)
      // genuinely reflects the SAME filter conditions the page was drawn from, not a
      // re-guess or the page length mislabeled as the family size (the prior bug here).
      const baseParams: unknown[] = [chartId, categories]
      let whereClause = `chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        baseParams.push(args.ayanamsha_id as string)
        whereClause += ` AND ayanamsha_id = $${baseParams.length}`
      }

      const [countResult, result] = await Promise.all([
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM chart_facts WHERE ${whereClause}`,
          baseParams,
        ),
        query<Record<string, unknown>>(
          `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                  fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
           FROM chart_facts
           WHERE ${whereClause}
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT $${baseParams.length + 1} OFFSET $${baseParams.length + 2}`,
          [...baseParams, limit, offset],
        ),
      ])

      const total = Number(countResult.rows[0]?.total ?? 0)

      // R5.3 B2 (Q9-N-1 ruling item C): the dosha_label catalog row for "Kala Sarpa Dosha" is
      // NOT the genuine per-chart Rahu/Ketu computation — its constituent_facts_array cites an
      // unrelated placeholder fact shared by dozens of catalog rows. The real computed detection
      // lives in fact_category `kala_sarpa_per_varga` (an already-computed L1 fact, currently
      // fetched only via facet=dispositors on get_dispositors.ts — never reachable from this
      // dosha-facing facet). Bounded, zero-new-computation SELECT of that already-built category,
      // scoped to this same chart/ayanamsha filter, only when the caller actually asked for the
      // dosha facet — so this stays a targeted fix, not a blanket payload inflation.
      let kalaSarpaPerVarga: { natal: Record<string, unknown>[]; divisional_fired: Record<string, unknown>[] } | undefined
      if (facet === 'dosha_fires') {
        const ksParams: unknown[] = [chartId]
        let ksWhere = `chart_id = $1 AND fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'`
        if (args.ayanamsha_id) {
          ksParams.push(args.ayanamsha_id as string)
          ksWhere += ` AND ayanamsha_id = $${ksParams.length}`
        }
        const ksResult = await query<Record<string, unknown>>(
          `SELECT fact_id, ayanamsha_id, fact_value_jsonb, fact_value_text, verification_pass_status, citation_ref
           FROM chart_facts WHERE ${ksWhere}
           ORDER BY ayanamsha_id, (fact_value_jsonb->>'varga')`,
          ksParams,
        )
        const ksRows = ksResult.rows ?? []
        const natal = ksRows.filter(r => (r['fact_value_jsonb'] as { varga?: string } | null)?.varga === 'D1')
        const divisional_fired = ksRows.filter(r => {
          const v = r['fact_value_jsonb'] as { varga?: string; fires?: boolean } | null
          return v?.varga !== 'D1' && v?.fires === true
        })
        kalaSarpaPerVarga = { natal, divisional_fired }
      }

      return {
        content: {
          chart_id: chartId, categories, rows: result.rows ?? [], total,
          ...(kalaSarpaPerVarga ? { kala_sarpa_per_varga: kalaSarpaPerVarga } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
