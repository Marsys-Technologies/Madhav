/**
 * L1 retrieval: graha strength (shadbala, vimsopaka, composite, ishta/kashta)
 * Covers: graha_shadbala_*, graha_vimsopaka_*, vimsopaka_bala_per_graha,
 *         graha_saptavargaja_bala_component, graha_ishta_phala, graha_kashta_phala,
 *         pranic_strength_per_graha, graha_in_house_composite_strength,
 *         graha_composite_state_classification, graha_special_state_rollup,
 *         graha_yoga_karaka_flag, graha_tri_deva_role_strength
 * Tool: marsys://tool/L1/get_strength
 *
 * FRAME FACET (R5 W2, design §27.3): the 21 strength categories are formula OUTPUTS
 * computed at build time from the lagna-relative chart — those numbers are FROZEN
 * (design brief must_not_touch: salience/priors/formula constants) and are never
 * recomputed here for a different frame. What DOES change with frame is which
 * `graha_in_house_composite_strength` row (SUBJECT_IN_HOUSE_N, N=1..12) is the graha's
 * OWN active house under that frame — e.g. "how strong is Jupiter judged from Moon"
 * needs to know Jupiter sits in the 11th-from-Moon, then read the *_IN_HOUSE_11 row.
 * `frame` resolves that active-house index per graha in the SAME call (no second
 * get_positions round-trip) via `resolveFrameReferenceSign` + `houseCountedFrom`
 * (address_resolver.ts, W1's resolver — reused, not re-derived per design §19).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import {
  resolveFrameReferenceSign, houseCountedFrom, GRAHA_CODE_TO_NAME,
  type ReferenceFrame, type ZodiacSign,
} from '../../../address_resolver'
import { DEFAULT_AYANAMSHA } from '../../constants'

const FRAME_VALUES: ReferenceFrame[] = ['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']

const STRENGTH_CATEGORIES = [
  'graha_shadbala_cheshta', 'graha_shadbala_dig', 'graha_shadbala_drik',
  'graha_shadbala_kala', 'graha_shadbala_naisargika', 'graha_shadbala_sthana',
  'graha_shadbala_total', 'graha_vimsopaka_dasavarga', 'graha_vimsopaka_saptavarga',
  'graha_vimsopaka_shadvarga', 'graha_vimsopaka_shodasavarga', 'vimsopaka_bala_per_graha',
  'graha_saptavargaja_bala_component', 'graha_ishta_phala', 'graha_kashta_phala',
  'pranic_strength_per_graha', 'graha_in_house_composite_strength',
  'graha_composite_state_classification', 'graha_special_state_rollup',
  'graha_yoga_karaka_flag', 'graha_tri_deva_role_strength',
]

export const getStrengthCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_strength',
  type: 'tool',
  layer: 'L1',
  name: 'get_strength',
  description:
    'Retrieve all graha strength metrics for a chart: Shadbala (6 components + total), ' +
    'Vimsopaka Bala (4 varga groupings), Saptavargaja Bala, Ishta/Kashta Phala, Pranic strength, ' +
    'composite in-house strength, composite state classification, special state rollup (exalted/debilitated/combust etc.), ' +
    'yoga-karaka flag, and Tri-deva role strength. ' +
    'Every row carries fact_id for Bodha salience computation via salience_formula_v1. ' +
    'Covers 21 strength-related fact_categories.',
  input_schema: {
    chart_id: {
      type: 'string', description: 'Chart UUID', required: true,
    },
    ayanamsha_id: {
      type: 'string', description: 'Filter by ayanamsha_id. Omit for all.',
    },
    categories: {
      type: 'array',
      description: 'Subset of strength categories (default: all 21).',
      items: { type: 'string' },
    },
    graha_key: {
      type: 'string',
      description: 'Filter to one graha (e.g. "SU" for Sun). Omit for all.',
    },
    frame: {
      type: 'string',
      description: 'Reference frame (default: lagna). When non-lagna, the response includes ' +
        'a `frame_context` map of each graha\'s ACTIVE house under that frame (e.g. from Moon) — ' +
        'so a graha_in_house_composite_strength row for the graha\'s real from-frame house can be ' +
        'picked out of the returned table in this same call, without a second get_positions lookup. ' +
        'The strength VALUES themselves are frozen build-time formula output and are never recomputed.',
      enum: FRAME_VALUES,
      default: 'lagna',
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
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 85, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? STRENGTH_CATEGORIES
      const frame = ((args.frame as string) ?? 'lagna') as ReferenceFrame
      if (!FRAME_VALUES.includes(frame)) {
        return {
          content: `Unsupported frame "${frame}". Supported: ${FRAME_VALUES.join(', ')} (design §27.3).`,
          is_error: true,
        }
      }
      const frameAyanamsha = (args.ayanamsha_id as string) ?? DEFAULT_AYANAMSHA

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
      if (args.graha_key) {
        sql += ` AND fact_key ILIKE $${params.length + 1}`
        params.push(`${args.graha_key as string}%`)
      }
      sql += ` ORDER BY fact_category, ayanamsha_id, fact_key LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      let frameContext: Record<string, unknown> | undefined
      if (frame !== 'lagna') {
        try {
          const { sign: referenceSign } = await resolveFrameReferenceSign(chartId, frame, { ayanamsha_id: frameAyanamsha })
          const grahaCodes = Object.keys(GRAHA_CODE_TO_NAME)
          const signRes = await query<{ fact_subject: string; fact_value_text: string | null }>(
            `SELECT fact_subject, fact_value_text FROM chart_facts
             WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_position'
               AND fact_subject = ANY($3::text[]) AND fact_key = 'sign'`,
            [chartId, frameAyanamsha, grahaCodes],
          )
          const activeHouseByGraha: Record<string, number> = {}
          for (const r of signRes.rows) {
            if (!r.fact_value_text) continue
            activeHouseByGraha[GRAHA_CODE_TO_NAME[r.fact_subject] ?? r.fact_subject] =
              houseCountedFrom(referenceSign as ZodiacSign, r.fact_value_text as ZodiacSign)
          }
          frameContext = {
            frame, reference_sign: referenceSign, ayanamsha_id: frameAyanamsha,
            active_house_by_graha: activeHouseByGraha,
            note: `Each graha's ACTUAL house counted from ${frame} (${referenceSign}). To read that ` +
              `graha's strength "from ${frame}", select its graha_in_house_composite_strength row for ` +
              `fact_subject = "<GRAHA>_IN_HOUSE_<active_house_by_graha[GRAHA]>" from the rows above. ` +
              `Strength VALUES are frozen build-time output — only which row is "active" changes with frame.`,
          }
        } catch (e) {
          frameContext = { frame, error: `could not resolve frame "${frame}": ${String(e)}` }
        }
      }

      return {
        content: {
          chart_id: chartId, categories, frame, rows, total: rows.length,
          ...(frameContext ? { frame_context: frameContext } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
