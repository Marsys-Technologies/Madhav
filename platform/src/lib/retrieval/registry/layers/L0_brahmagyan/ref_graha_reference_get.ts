/**
 * ref_graha_reference_get — L0 Brahmagyan graha reference reader
 * ============================================================================
 * W-L0-4 served-surface contract (MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md
 * §3.1 delivery fidelity / §4.2 W-L0-4): `bg_reference` (table `reference_planets`,
 * 11 rows — the nine grahas plus ascendant and midheaven) had NO served path at
 * all; every other L0 reference asset is reachable through a query_* capability.
 * This is that path. It computes NOTHING — it serves the stored per-graha
 * reference row: canonical names (en/sa), exaltation/debilitation/mooltrikona,
 * own signs, natural beneficence, kāraka domains, daśā years, and the row's
 * source_citation.
 *
 * PRESENTATION OBLIGATION (strategy §2.2): names in both scripts and the source
 * witness are served AS DATA on every row. NULL dignity fields (ascendant,
 * midheaven — angles, not grahas) are returned as null, never hidden or
 * backfilled; unresolved alternatives stay visible in the citation text itself
 * (e.g. Rahu: "exaltation debated, Taurus per Parasara").
 *
 * Global classical reference — no chart_id, by construction.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const refGrahaReferenceGetCapability: CapabilityDescriptor = {
  // W-L0-4 served-surface contract: explicit declaration (detector:
  // __tests__/l0_density_contract.test.ts — do not remove; values follow the
  // deriveDensityContract evidence rules in ../../descriptor_defaults.ts).
  density_contract: {
    max_verdict_bytes: 1024,
    max_digest_bytes: 4096,
    paginated: false,
    facets: ['planet_id'],
    empty_reason: true,
  },
  uri:   'marsys://tool/L0/ref_graha_reference_get',
  type:  'tool',
  layer: 'L0',
  name:  'ref_graha_reference_get',

  description: [
    'Get the graha reference row(s) from reference_planets (11 rows — the nine grahas plus',
    'ascendant and midheaven; BPHS Ch.3 citations per row). Each row carries canonical_name_en',
    '/ canonical_name_sa, exaltation sign+degree, debilitation sign, mooltrikona sign, own',
    'signs, natural_benefic, karak_domains, dasha_years, and the source_citation. Filter by',
    'planet_id (e.g. "venus", "ascendant"). NULL dignity fields are returned as null — angles',
    'carry no dignity; debated values (Rahu/Ketu exaltation) stay visible in the citation.',
    'Global classical reference — no chart_id needed; returns the stored RULE row only, not',
    'any chart\'s computed dignity.',
  ].join(' '),

  input_schema: {
    planet_id: { type: 'string', description: 'Filter by planet_id (case-insensitive, e.g. "venus"). Omit for all 11.' },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 25, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const planetId = args['planet_id'] ? String(args['planet_id']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (planetId) { filters.push(`LOWER(planet_id) = LOWER($${p++})`); params.push(planetId) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT planet_id, canonical_name_en, canonical_name_sa,
             exaltation_sign, exaltation_degree, debilitation_sign, mooltrikona_sign,
             own_signs, natural_benefic, karak_domains, dasha_years, source_citation
      FROM reference_planets
      WHERE ${where}
      ORDER BY planet_id`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { planet_id: planetId },
          ...(result.rows.length === 0
            ? { empty_reason: `No graha reference row matched (planet_id=${planetId ?? 'any'}).` }
            : {}),
          disclaimer:
            'Stored classical reference row only — not a computed per-chart dignity or strength. ' +
            'NULL dignity fields are honest nulls (angles carry no dignity), not missing data.',
          provenance: { tables: ['reference_planets'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
