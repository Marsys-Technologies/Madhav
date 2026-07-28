/**
 * L1 retrieval: karakas, KP, Jaimini placements
 * Covers: karaka_chara_position, karakamsa_position, swamsa_position, arudha_pada,
 *         bhava_arudha, karaka_house_lord_overlap_flag, karakatva_strength_per_significance,
 *         kp_cuspal_significators, kp_ruling_planets_natal,
 *         jaimini_tri_deva_role_per_graha
 * Tool: marsys://tool/L1/get_karakas
 *
 * W2 structural-close S-3/SC-5 (RETRIEVAL_STRATEGY_v1_0.md §5.2 register rows, serving-side
 * only — no writer change): `bhava_arudha` (A1-A12 + AL/UPA, full Parashari 2-exception rule,
 * written by ga_sensitive_writer.py) was computed and stored in chart_facts but had zero
 * serving route — this tool served only the related `arudha_pada` category. Added to the
 * default page (small row count, same shape as arudha_pada). `karaka_web_per_varga` and
 * `karaka_bhava_concordance` are also real, computed, chart_facts-resident categories with
 * zero prior serving route (SC-5) — NOT added to the unconditional default (they are large,
 * per-varga/per-house-pair row sets that would dominate/paginate out the smaller karaka
 * categories on the default page, per the §N.6 density discipline already established for
 * get_positions' CR-50 upagraha facet) — request them explicitly via `categories`.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const KARAKA_CATEGORIES = [
  'karaka_chara_position', 'karakamsa_position', 'swamsa_position', 'arudha_pada',
  'bhava_arudha',
  'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
  'kp_cuspal_significators', 'kp_ruling_planets_natal', 'jaimini_tri_deva_role_per_graha',
]

/**
 * Real, computed, chart_facts-resident categories with no default-page inclusion (too large
 * per §N.6 density discipline) but fully queryable via an explicit `categories` request —
 * documented here (not just in prose) so a maintainer can find every category this tool can
 * reach, not only the ones on the default page.
 */
const KARAKA_OPT_IN_CATEGORIES = ['karaka_web_per_varga', 'karaka_bhava_concordance']

export const getKarakasCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_karakas',
  type: 'tool',
  layer: 'L1',
  name: 'get_karakas',
  description:
    'Retrieve Jaimini karaka and KP (Krishnamurti Paddhati) data for a chart. ' +
    'Includes: Chara Karaka positions (AK/AmK/BK/MK/PK/GK/DK — the 7 temporal significators), ' +
    'Karakamsa position (rashi/house where AK sits in Navamsha), Swamsa position, ' +
    'Arudha Padas (A1–A12 across ayanamshas and divisionals), ' +
    'Bhava Arudha (A1-A12 + Arudha Lagna + Upapada, full Parashari 2-exception rule — on the ' +
    'default page alongside arudha_pada; a sibling arudha reckoning, not a duplicate), ' +
    'Karaka-house-lord overlap flags (e.g. AK also lords the 10th house), ' +
    'Karakatva strength per significator (how strongly each graha signifies its karakatvas), ' +
    'KP cuspal significators (Star lord + Sub lord + Sub-sub for each of 12 cusps), ' +
    'KP ruling planets for the natal moment, ' +
    'and Jaimini Tri-Deva role (Brahma/Vishnu/Maheshvara graha identification). ' +
    'Covers 10 fact_categories on the default page. Two further real, computed categories are ' +
    'available on request (not on the default page — large per-varga/per-house-pair row sets): ' +
    '`karaka_web_per_varga` (karaka relationships recomputed per divisional chart) and ' +
    '`karaka_bhava_concordance` (per-house karaka concordance) — pass ' +
    'categories:["karaka_web_per_varga"] / ["karaka_bhava_concordance"] explicitly to fetch them.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    system:       { type: 'string', description: 'Filter by system: jaimini | kp. Omit for all.', enum: ['jaimini', 'kp'] },
    categories:   {
      type: 'array',
      description: 'Explicit category list — overrides the default page entirely. Also the only ' +
        'way to reach the two opt-in categories not on the default page: karaka_web_per_varga, ' +
        'karaka_bhava_concordance.',
      items: { type: 'string' },
    },
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
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — House & lordships' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 82, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? KARAKA_CATEGORIES
      if (args.system === 'jaimini') {
        categories = categories.filter(c => c.startsWith('karaka') || c.startsWith('jaimini') || ['swamsa_position', 'karakamsa_position', 'arudha_pada', 'karakatva_strength_per_significance'].includes(c))
      }
      if (args.system === 'kp') {
        categories = categories.filter(c => c.startsWith('kp'))
      }

      const params: unknown[] = [chartId, categories, limit, offset]
      let sql = `
        SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY fact_category, ayanamsha_id, fact_key LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0,
          // §N.6: density signaling is data, not narration — machine-readable pointer to the
          // real categories this tool can reach but does not include on the default page.
          opt_in_categories_available: KARAKA_OPT_IN_CATEGORIES,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
