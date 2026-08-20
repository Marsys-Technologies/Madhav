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
    all: {
      type: 'boolean',
      description: 'ŚODHANA T3 (MC-014): default false — `graha_in_house_composite_strength` ' +
        '(the one category with a row per graha PER HOUSE, 12x a graha\'s real placement) is ' +
        'filtered to each graha\'s single ACTUAL house under `frame` by default, dropping the ' +
        'other 11 counterfactual "what if this graha sat in house N" rows per graha. Every ' +
        'other strength category (Shadbala, Vimsopaka, Ishta/Kashta, etc.) is one row per ' +
        'graha already and is unaffected either way. Pass true to get every counterfactual ' +
        'placement row for every graha (the pre-fix behavior).',
      default: false,
    },
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
  register: { reader_label: 'Consulting the chart — Strengths & dignities' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 85, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId       = args.chart_id as string
      // F-60 fix: the requested limit is recorded BEFORE the 2000-row hard cap is applied,
      // so a silent truncation can be disclosed explicitly instead of hidden inside a
      // same-shaped response (see `limit_capped` below).
      const requestedLimit = (args.limit as number) ?? 500
      const limit          = Math.min(requestedLimit, 2000)
      const limitCapped    = requestedLimit > 2000
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
      const all = (args.all as boolean) === true

      // F-60 fix: build the WHERE clause + its params ONCE, shared by a dedicated COUNT
      // query (the true pre-LIMIT/OFFSET row count matching this filter) and the SELECT
      // query (the capped, paginated page) — so `total_available` below is never derived
      // from the served page's own length (the defect: `total: servedRows.length` silently
      // reported a post-cap, post-filter page length as if it were the true row count).
      const whereParams: unknown[] = [chartId, categories]
      let whereClause = `WHERE chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        whereClause += ` AND ayanamsha_id = $${whereParams.length + 1}`
        whereParams.push(args.ayanamsha_id as string)
      }
      if (args.graha_key) {
        // R5 W3 (graha_portrait lane) fix: the graha's identity lives in `fact_subject`
        // (e.g. "SAT", "SAT_IN_HOUSE_5"), NEVER in `fact_key` (fact_key is a generic
        // component name shared across every graha — "rupa", "score", "bphs_weighted" —
        // confirmed empty-set live against both canonical charts before this fix). The
        // prior `fact_key ILIKE` filter matched zero rows for every category except by
        // accident; filtering fact_subject with an exact-or-prefixed-or-suffixed match
        // covers both the bare-code categories (fact_subject = "SAT") and the
        // graha_in_house_composite_strength category (fact_subject = "SAT_IN_HOUSE_5").
        whereClause += ` AND (fact_subject = $${whereParams.length + 1}
                  OR fact_subject ILIKE $${whereParams.length + 2}
                  OR fact_subject ILIKE $${whereParams.length + 3})`
        const grahaKey = args.graha_key as string
        whereParams.push(grahaKey, `${grahaKey}\\_%`, `%\\_${grahaKey}`)
      }

      // F-60 fix: the TRUE pre-cap, pre-offset row count matching this filter — a distinct
      // field from the served page length, computed by its own COUNT(*) query sharing the
      // exact same WHERE predicate (never guessed from, or conflated with, the page below).
      const countSql = `SELECT COUNT(*)::int AS total_count FROM chart_facts ${whereClause}`
      const countResult = await query<{ total_count: number }>(countSql, whereParams)
      const totalAvailable = Number(countResult.rows?.[0]?.total_count ?? 0)

      const params: unknown[] = [...whereParams, limit, offset]
      const limitParamIdx = whereParams.length + 1
      const offsetParamIdx = whereParams.length + 2
      const sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        ${whereClause}
        ORDER BY fact_category, ayanamsha_id, fact_key LIMIT $${limitParamIdx} OFFSET $${offsetParamIdx}
      `

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // ŚODHANA T3 (MC-014): active-house-by-graha is now computed for EVERY frame
      // (previously only for frame !== 'lagna', since only the frame_context DISPLAY
      // depended on it) — the `all:false` default below needs it for `frame:'lagna'` too,
      // since that is the tool's own default frame and exactly where the counterfactual-row
      // complaint was measured (~520 rows for one chart's full strength pull).
      let activeHouseByGraha: Record<string, number> | undefined
      let frameContext: Record<string, unknown> | undefined
      try {
        const { sign: referenceSign } = await resolveFrameReferenceSign(chartId, frame, { ayanamsha_id: frameAyanamsha })
        const grahaCodes = Object.keys(GRAHA_CODE_TO_NAME)
        const signRes = await query<{ fact_subject: string; fact_value_text: string | null }>(
          `SELECT fact_subject, fact_value_text FROM chart_facts
           WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_position'
             AND fact_subject = ANY($3::text[]) AND fact_key = 'sign'`,
          [chartId, frameAyanamsha, grahaCodes],
        )
        activeHouseByGraha = {}
        for (const r of signRes.rows) {
          if (!r.fact_value_text) continue
          activeHouseByGraha[GRAHA_CODE_TO_NAME[r.fact_subject] ?? r.fact_subject] =
            houseCountedFrom(referenceSign as ZodiacSign, r.fact_value_text as ZodiacSign)
        }
        // frame_context is only SURFACED for a non-lagna frame (unchanged external shape —
        // a lagna-frame active house is just the natal house, nothing new to disclose here).
        if (frame !== 'lagna') {
          frameContext = {
            frame, reference_sign: referenceSign, ayanamsha_id: frameAyanamsha,
            active_house_by_graha: activeHouseByGraha,
            note: `Each graha's ACTUAL house counted from ${frame} (${referenceSign}). To read that ` +
              `graha's strength "from ${frame}", select its graha_in_house_composite_strength row for ` +
              `fact_subject = "<GRAHA>_IN_HOUSE_<active_house_by_graha[GRAHA]>" from the rows above. ` +
              `Strength VALUES are frozen build-time output — only which row is "active" changes with frame.`,
          }
        }
      } catch (e) {
        activeHouseByGraha = undefined
        if (frame !== 'lagna') frameContext = { frame, error: `could not resolve frame "${frame}": ${String(e)}` }
      }

      let servedRows = rows
      let counterfactualRowsDropped = 0
      if (!all && activeHouseByGraha) {
        const kept: Record<string, unknown>[] = []
        for (const row of rows) {
          if (row['fact_category'] !== 'graha_in_house_composite_strength') { kept.push(row); continue }
          const subject = String(row['fact_subject'] ?? '')
          const m = /^(.+)_IN_HOUSE_(\d+)$/.exec(subject)
          if (!m) { kept.push(row); continue } // unrecognized shape — never silently drop (B.10).
          const [, grahaCode, houseStr] = m
          const grahaName = GRAHA_CODE_TO_NAME[grahaCode] ?? grahaCode
          const activeHouse = activeHouseByGraha[grahaName]
          if (activeHouse === undefined || Number(houseStr) === activeHouse) kept.push(row)
          else counterfactualRowsDropped += 1
        }
        servedRows = kept
      }

      return {
        content: {
          chart_id: chartId, categories, frame, rows: servedRows,
          // `total` is the ROWS SERVED IN THIS PAGE (unchanged shape/name — callers that
          // already treat this as a page-length receipt keep working). F-60 fix: it is no
          // longer the only count reported — `total_available` (below) is the TRUE row
          // count matching this chart_id/categories/ayanamsha_id/graha_key filter, computed
          // by its own COUNT(*) query, independent of `limit`/`offset`/the 2000-row cap/the
          // `all:false` counterfactual-row drop. A caller that previously read `total` as
          // "how many rows exist" was reading a page-length; `total_available` is the field
          // that actually answers that question.
          total: servedRows.length,
          total_available: totalAvailable,
          limit, offset,
          ...(limitCapped ? {
            limit_capped: true,
            requested_limit: requestedLimit,
            note_limit_cap: `The requested limit (${requestedLimit}) exceeds this tool's hard cap of ` +
              '2000 and was reduced to 2000 for this call — disclosed explicitly rather than silently ' +
              'truncated. `total_available` above reports the true row count matching the filter; use ' +
              '`offset` to page through the remainder.',
          } : {}),
          ...(frameContext ? { frame_context: frameContext } : {}),
          ...(!all ? {
            all: false,
            counterfactual_rows_dropped: counterfactualRowsDropped,
            note: counterfactualRowsDropped > 0
              ? `${counterfactualRowsDropped} counterfactual graha_in_house_composite_strength row(s) ` +
                `("what if this graha sat in a different house") were dropped — only each graha's ` +
                `ACTUAL house (under frame:'${frame}') is served by default. Pass all:true for every ` +
                'counterfactual placement.'
              : 'No counterfactual graha_in_house_composite_strength rows were present to drop.',
          } : { all: true }),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
