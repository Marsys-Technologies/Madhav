/**
 * get_kp_cusps — L1 Gaṇita dedicated KP (Krishnamurti Paddhati) cusp serving surface
 * ===================================================================================
 * SARVA-SIDDHI W-4 lane D-4 (CR-30). Closes the long-standing "no dedicated MCP face
 * for KP sub-lords" gap tracked as CR-30 in the vidhi primitive `kp_cusp_sublord_read`.
 *
 * This is a SERVING route only — NO new computation (B.10). Every value returned here
 * is already computed and stored in chart_facts by the L1 `ga_*` writers. This tool
 * assembles the KP-cusp picture that was previously reachable only bundled inside the
 * Jaimini+KP omnibus (get_karakas) or via the raw category route (chart_facts_query):
 *
 *   - cusp_kp_lords            → the full KP chain per cusp: star_lord / sub_lord /
 *                                sub_sub_lord / prana_lord (CUSP_01..CUSP_12)
 *   - kp_cuspal_significators  → sign_lord, star_lord, sub_lord, significators_json,
 *                                cusp_longitude_sidereal (CUSP_1..CUSP_12)
 *   - bhava_cusps              → cusp degrees (placidus/sripati start/madhya/end)
 *                                (BHAVA_01..BHAVA_12)
 *   - kp_ruling_planets_natal  → RP_* ruling-planet set for the natal moment
 *   - graha_kp_lords           → per-graha KP chain (opt-in via include_graha_kp_lords)
 *
 * The star_lord/sub_lord values in cusp_kp_lords and kp_cuspal_significators agree
 * row-for-row (verified live against the native chart); cusp_kp_lords is used as the
 * authoritative chain source (it carries the deeper sub_sub/prana levels) and its
 * agreement with kp_cuspal_significators is asserted at assembly time — a divergence is
 * surfaced as a `chain_divergence` flag on the affected cusp rather than silently picked.
 *
 * KP-canonical ayanamsha is Krishnamurti; that is the default here (school_conventions.ts
 * §3 — "KP uses Krishnamurti ayanamsha"). All 5 stored ayanamshas are queryable via
 * `ayanamsha_id`. Chart-scoped (principle #14): chart_id is the entitlement key.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const KP_CATEGORIES = [
  'cusp_kp_lords',
  'kp_cuspal_significators',
  'bhava_cusps',
  'kp_ruling_planets_natal',
] as const

const GRAHA_KP_CATEGORY = 'graha_kp_lords'

// KP-canonical ayanamsha (K.S. Krishnamurti). Not the system-wide Lahiri default —
// a KP tool must default to the KP ayanamsha to be doctrinally correct.
const DEFAULT_AYANAMSHA = 'krishnamurti'

// Deterministic sidereal-longitude → rashi label. This is a pure formatting lookup
// (floor(lon/30)) over an ALREADY-STORED longitude, not an astronomical computation —
// the same class of in-response transform get_positions performs for frame re-basing.
// It never invents a numeric value; it labels a stored one.
const RASHIS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]
function signFromLongitude(lon: number | null): string | null {
  if (lon == null || Number.isNaN(lon)) return null
  const norm = ((lon % 360) + 360) % 360
  return RASHIS[Math.floor(norm / 30)] ?? null
}

// Cusp subjects are keyed inconsistently across categories:
//   cusp_kp_lords → CUSP_01..CUSP_12 ; kp_cuspal_significators → CUSP_1..CUSP_12
//   bhava_cusps   → BHAVA_01..BHAVA_12
// Parse the trailing integer to a 1..12 house number regardless of prefix/padding.
function houseFromSubject(subject: string): number | null {
  const m = /(\d{1,2})$/.exec(subject)
  if (!m) return null
  const n = Number(m[1])
  return n >= 1 && n <= 12 ? n : null
}

interface FactRow {
  fact_id: string
  fact_category: string
  ayanamsha_id: string
  fact_subject: string
  fact_key: string
  fact_value_text: string | null
  fact_value_num: number | null
  fact_value_jsonb: unknown
}

export const getKpCuspsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_kp_cusps',
  type:  'tool',
  layer: 'L1',
  name:  'get_kp_cusps',

  description: [
    'Retrieve the dedicated KP (Krishnamurti Paddhati) cuspal picture for a chart, first-class.',
    'For each of the 12 bhava cusps: cusp sidereal longitude, sign (rashi), and the full KP',
    'lord chain — sign_lord (rashi lord) / star_lord (nakshatra lord) / sub_lord / sub_sub_lord /',
    'prana_lord — plus the cuspal significators list and the cusp degrees (Placidus and Sripati',
    'start/madhya/end). Also returns the KP ruling planets for the natal moment (Ascendant lord,',
    'Ascendant sub-lord, Moon sign/star lord, Day lord). SERVING ONLY — no new computation; every',
    'value is an already-stored L1 fact (categories cusp_kp_lords, kp_cuspal_significators,',
    'bhava_cusps, kp_ruling_planets_natal). Defaults to the KP-canonical Krishnamurti ayanamsha;',
    'pass ayanamsha_id to select any of the 5 stored ayanamshas. Pass include_graha_kp_lords=true',
    'to also get each graha\'s own KP star/sub/sub_sub/prana chain (graha_kp_lords). Each cusp',
    'carries the source fact_ids for Bodha constituent_facts_array back-reference.',
  ].join(' '),

  input_schema: {
    chart_id:               { type: 'string',  description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:           { type: 'string',  description: `Ayanamsha (default '${DEFAULT_AYANAMSHA}', the KP-canonical one). Others: lahiri_chitrapaksha, raman, true_chitra, surya_siddhanta_classical.` },
    include_graha_kp_lords: { type: 'boolean', description: 'If true, also return the per-graha KP lord chain (graha_kp_lords). Default false.' },
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

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : DEFAULT_AYANAMSHA
    const includeGraha = args['include_graha_kp_lords'] === true || args['include_graha_kp_lords'] === 'true'

    const categories: string[] = [...KP_CATEGORIES]
    if (includeGraha) categories.push(GRAHA_KP_CATEGORY)

    const sql = `
      SELECT fact_id, fact_category, ayanamsha_id, fact_subject, fact_key,
             fact_value_text, fact_value_num, fact_value_jsonb
      FROM chart_facts
      WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = ANY($3::text[])
      ORDER BY fact_category, fact_subject, fact_key`

    try {
      const res = await query<FactRow>(sql, [chart_id, ayanamsha_id, categories])
      const rows = res.rows ?? []

      if (rows.length === 0) {
        return {
          content: {
            chart_id,
            ayanamsha_id,
            cusps: [],
            ruling_planets: [],
            count: 0,
            empty_reason:
              `No KP cusp facts for chart_id=${chart_id} at ayanamsha_id=${ayanamsha_id}. ` +
              `The KP categories (cusp_kp_lords, kp_cuspal_significators, bhava_cusps, ` +
              `kp_ruling_planets_natal) are written by the L1 ga_* build; a 0-row result means ` +
              `either the ayanamsha_id is not one of the 5 built, or the chart has not been built.`,
            provenance: {
              tables: ['chart_facts'],
              categories,
              source: 'L1 Gaṇita KP cuspal facts; served chart-scoped, no new computation (B.10).',
            },
          },
          is_error: false,
        }
      }

      // Index by house for the four cusp-keyed categories.
      type CuspAccum = {
        house: number
        cusp_longitude_sidereal: number | null
        sign: string | null
        sign_lord: string | null
        star_lord: string | null
        sub_lord: string | null
        sub_sub_lord: string | null
        prana_lord: string | null
        significators: unknown
        cusp_degrees: Record<string, number | null>
        chain_divergence: string[] | null
        fact_ids: string[]
      }
      const byHouse = new Map<number, CuspAccum>()
      const ensure = (h: number): CuspAccum => {
        let c = byHouse.get(h)
        if (!c) {
          c = {
            house: h, cusp_longitude_sidereal: null, sign: null, sign_lord: null,
            star_lord: null, sub_lord: null, sub_sub_lord: null, prana_lord: null,
            significators: null, cusp_degrees: {}, chain_divergence: null, fact_ids: [],
          }
          byHouse.set(h, c)
        }
        return c
      }

      const rulingPlanets: Array<Record<string, unknown>> = []
      const rpByRole = new Map<string, Record<string, unknown>>()
      const grahaKpLords = new Map<string, Record<string, unknown>>()

      for (const r of rows) {
        const cat = r.fact_category
        if (cat === 'cusp_kp_lords') {
          const h = houseFromSubject(r.fact_subject)
          if (h == null) continue
          const c = ensure(h)
          c.fact_ids.push(r.fact_id)
          if (r.fact_key === 'star_lord')    c.star_lord    = r.fact_value_text
          if (r.fact_key === 'sub_lord')     c.sub_lord     = r.fact_value_text
          if (r.fact_key === 'sub_sub_lord') c.sub_sub_lord = r.fact_value_text
          if (r.fact_key === 'prana_lord')   c.prana_lord   = r.fact_value_text
        } else if (cat === 'kp_cuspal_significators') {
          const h = houseFromSubject(r.fact_subject)
          if (h == null) continue
          const c = ensure(h)
          c.fact_ids.push(r.fact_id)
          if (r.fact_key === 'cusp_longitude_sidereal') {
            c.cusp_longitude_sidereal = r.fact_value_num
            c.sign = signFromLongitude(r.fact_value_num)
          }
          if (r.fact_key === 'sign_lord') c.sign_lord = r.fact_value_text
          if (r.fact_key === 'significators_json') c.significators = r.fact_value_jsonb
          // Cross-source integrity: star_lord/sub_lord also live here; they must match
          // the cusp_kp_lords chain. Record any divergence rather than silently choosing.
          if (r.fact_key === 'star_lord' && c.star_lord != null && r.fact_value_text !== c.star_lord) {
            (c.chain_divergence ??= []).push(`star_lord: cusp_kp_lords=${c.star_lord} vs kp_cuspal_significators=${r.fact_value_text}`)
          }
          if (r.fact_key === 'sub_lord' && c.sub_lord != null && r.fact_value_text !== c.sub_lord) {
            (c.chain_divergence ??= []).push(`sub_lord: cusp_kp_lords=${c.sub_lord} vs kp_cuspal_significators=${r.fact_value_text}`)
          }
        } else if (cat === 'bhava_cusps') {
          const h = houseFromSubject(r.fact_subject)
          if (h == null) continue
          const c = ensure(h)
          c.fact_ids.push(r.fact_id)
          c.cusp_degrees[r.fact_key] = r.fact_value_num
        } else if (cat === 'kp_ruling_planets_natal') {
          const role = r.fact_subject
          const rp = rpByRole.get(role) ?? { role, ruling_planet: null, longitude_sidereal: null, fact_ids: [] as string[] }
          if (r.fact_key === 'ruling_planet')      rp['ruling_planet']     = r.fact_value_text
          if (r.fact_key === 'longitude_sidereal') rp['longitude_sidereal'] = r.fact_value_num
          ;(rp['fact_ids'] as string[]).push(r.fact_id)
          rpByRole.set(role, rp)
        } else if (cat === GRAHA_KP_CATEGORY) {
          const g = r.fact_subject
          const gk = grahaKpLords.get(g) ?? { graha: g, star_lord: null, sub_lord: null, sub_sub_lord: null, prana_lord: null, fact_ids: [] as string[] }
          if (r.fact_key === 'star_lord')    gk['star_lord']    = r.fact_value_text
          if (r.fact_key === 'sub_lord')     gk['sub_lord']     = r.fact_value_text
          if (r.fact_key === 'sub_sub_lord') gk['sub_sub_lord'] = r.fact_value_text
          if (r.fact_key === 'prana_lord')   gk['prana_lord']   = r.fact_value_text
          ;(gk['fact_ids'] as string[]).push(r.fact_id)
          grahaKpLords.set(g, gk)
        }
      }

      for (const rp of rpByRole.values()) rulingPlanets.push(rp)
      rulingPlanets.sort((a, b) => String(a['role']).localeCompare(String(b['role'])))

      const cusps = Array.from(byHouse.values()).sort((a, b) => a.house - b.house)

      const content: Record<string, unknown> = {
        chart_id,
        ayanamsha_id,
        cusps,
        ruling_planets: rulingPlanets,
        count: cusps.length,
        provenance: {
          tables: ['chart_facts'],
          categories,
          source: 'L1 Gaṇita KP cuspal facts; served chart-scoped, no new computation (B.10). ' +
            'sign labels are a deterministic longitude→rashi lookup over the stored ' +
            'cusp_longitude_sidereal, not a recomputed value.',
        },
      }
      if (includeGraha) {
        content['graha_kp_lords'] = Array.from(grahaKpLords.values())
          .sort((a, b) => String(a['graha']).localeCompare(String(b['graha'])))
      }
      return { content, is_error: false }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
