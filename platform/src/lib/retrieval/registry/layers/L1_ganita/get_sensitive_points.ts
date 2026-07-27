/**
 * L1 retrieval: esoteric / sensitive points
 * Covers: all esoteric_point_* (13 sub-categories), bhrigu_nadi_point,
 *         lal_kitab_special_point, maharsi_specific_point, midpoint,
 *         saham_position, saturn_derived_point, nakshatra_pada_sensitive
 * Tool: marsys://tool/L1/get_sensitive_points
 *
 * MC-029 (Śodhana-Śeṣa W2) reconciliation note: this surface's `esoteric_point_yogi` /
 * `esoteric_point_avayogi` rows include a `bphs_93_20` formula_id variant that computes
 * the identical BPHS Ch.20 Yogi/Avayogi construction as the `sensitive_point_yogi`
 * category served by get_sensitive_degrees (ganita_sensitive_degrees_get) — confirmed
 * in agreement to ~4e-7 deg for both canonical charts across all 5 ayanamshas
 * (2026-07-27; locked by a regression test in
 * ga_writers/__tests__/test_ga_sensitive_degree.py). The `alt_96_40` formula_id rows
 * are a genuinely different classical convention (Krishnamurti variant), not a
 * divergence. For a single canonical Yogi/Avayogi answer, prefer
 * get_sensitive_degrees / sensitive_point_yogi; use this surface when the
 * multi-formula comparison itself (or the other 18 categories) is what's needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const SP_CATEGORIES = [
  'esoteric_point_avayogi', 'esoteric_point_bhrigu_bindu', 'esoteric_point_brahma',
  'esoteric_point_chatushphuta', 'esoteric_point_mrityu', 'esoteric_point_panchasphuta',
  'esoteric_point_pranapada_sphuta', 'esoteric_point_shiva', 'esoteric_point_sri_yantra_position',
  'esoteric_point_trikona_dasha_sphuta', 'esoteric_point_trisphuta', 'esoteric_point_vishnu',
  'esoteric_point_yogi', 'bhrigu_nadi_point', 'lal_kitab_special_point',
  'maharsi_specific_point', 'midpoint', 'saham_position', 'saturn_derived_point',
  'nakshatra_pada_sensitive',
]

export const getSensitivePointsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_sensitive_points',
  type: 'tool',
  layer: 'L1',
  name: 'get_sensitive_points',
  description:
    'Retrieve esoteric and sensitive mathematical points for a chart. ' +
    'Includes: 13 tradition-specific esoteric points (Yogi/Avayogi, Brahma/Vishnu/Shiva, ' +
    'Sri Yantra position, Mrityu Sphuta, Trikona Dasha Sphuta, Trisphuta, Panchasphuta, ' +
    'Pranapada, Chatushphuta, Bhrigu Bindu), ' +
    'Bhrigu Nadi point, 100 Lal Kitab special points, ' +
    'Maharṣi-specific points, midpoints (all graha pairs), ' +
    '2800 Arabic Parts (Sahams) across all ayanamshas, Saturn-derived points, ' +
    'and nakshatra-pada sensitive degrees. ' +
    'Covers 20 fact_categories (a large row set per chart).',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    tradition:    {
      type: 'string',
      description: 'Filter by tradition: esoteric | bhrigu | lal_kitab | maharsi | arabic_parts | saturn.',
      enum: ['esoteric', 'bhrigu', 'lal_kitab', 'maharsi', 'arabic_parts', 'saturn'],
    },
    categories:   { type: 'array', description: 'Explicit category list.', items: { type: 'string' } },
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
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 65, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? SP_CATEGORIES
      if (args.tradition) {
        const t = args.tradition as string
        const tMap: Record<string, string[]> = {
          esoteric:     SP_CATEGORIES.filter(c => c.startsWith('esoteric_point')),
          bhrigu:       ['bhrigu_nadi_point', 'esoteric_point_bhrigu_bindu'],
          lal_kitab:    ['lal_kitab_special_point'],
          maharsi:      ['maharsi_specific_point'],
          arabic_parts: ['saham_position'],
          saturn:       ['saturn_derived_point'],
        }
        categories = tMap[t] ?? categories
      }

      const params: unknown[] = [chartId, categories, limit, offset]
      // WP-1.8 (multi-formula collapse): project formula_id + formula_provenance_text so
      // multi-formula points (e.g. AVAYOGI computed both by BPHS Ch.20 → Virgo and by the
      // alternate 96°40' formula → Libra, differing by ~10° / a whole sign) are distinguishable.
      // These two rows share an IDENTICAL citation_ref, so any consumer pivoting on
      // (category, subject, fact_key) silently collapses them to ONE arbitrarily-chosen value.
      // We serve BOTH rows AND a `multi_formula` disclosure that names each formula_id — never collapse.
      let sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, formula_id, formula_provenance_text,
               verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY fact_category, ayanamsha_id, fact_key, formula_id LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // ── Multi-formula disclosure (WP-1.8) ────────────────────────────────────────
      // Group the served rows by (category, subject, ayanamsha, fact_key); any group with >1
      // DISTINCT formula_id is a multi-formula point whose values would collapse under a naive
      // key→value pivot. Surface each such group with every formula's value + provenance so the
      // consumer sees the genuine formula-level divergence instead of one silently-picked winner.
      const groups = new Map<string, { category: string; subject: unknown; ayanamsha: unknown; fact_key: unknown; variants: Map<string, { formula_id: string; formula_provenance_text: unknown; value: unknown; fact_id: unknown }> }>()
      for (const r of rows) {
        const fid = r['formula_id']
        if (fid == null) continue
        const gk = `${r['fact_category']}|${r['fact_subject']}|${r['ayanamsha_id']}|${r['fact_key']}`
        let g = groups.get(gk)
        if (!g) {
          g = { category: r['fact_category'] as string, subject: r['fact_subject'], ayanamsha: r['ayanamsha_id'], fact_key: r['fact_key'], variants: new Map() }
          groups.set(gk, g)
        }
        g.variants.set(String(fid), {
          formula_id: String(fid),
          formula_provenance_text: r['formula_provenance_text'],
          value: r['fact_value_text'] ?? r['fact_value_num'],
          fact_id: r['fact_id'],
        })
      }
      const multi_formula = [...groups.values()]
        .filter(g => g.variants.size > 1)
        .map(g => ({
          fact_category: g.category,
          fact_subject: g.subject,
          ayanamsha_id: g.ayanamsha,
          fact_key: g.fact_key,
          formula_count: g.variants.size,
          formulas: [...g.variants.values()],
        }))

      return {
        content: {
          chart_id: chartId,
          categories,
          rows,
          total: rows.length,
          // WP-1.8: never collapse multi-formula points — both rows are in `rows`; this block
          // names the divergence explicitly so a downstream key→value pivot cannot hide it.
          multi_formula,
          ...(multi_formula.length > 0 ? {
            multi_formula_note:
              `${multi_formula.length} point(s) here are computed by MORE THAN ONE classical formula ` +
              `(e.g. AVAYOGI: BPHS Ch.20 vs the alternate 96°40' convention). Both rows are served ` +
              `and disambiguated by formula_id — do NOT pivot on (category,subject,fact_key) alone, ` +
              `which would silently drop one formula's value.`,
          } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
