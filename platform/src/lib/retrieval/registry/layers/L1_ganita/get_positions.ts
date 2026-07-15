/**
 * L1 retrieval: graha positions
 * Covers: graha_position, upagraha_position, aprakasha_position
 * Tool: marsys://tool/L1/get_positions
 *
 * FRAME FACET (R5 W2, design §27.3): all rows are written lagna-relative (`house_d1` is
 * counted from Lagna). An optional `frame` param re-bases each row's house onto a
 * non-lagna reference frame (chandra/surya/arudha/karakamsha) IN THE SAME CALL — the
 * Sudarshana-style "what house is Jupiter in, from Moon" judgment becomes one facet
 * instead of an unaddressable classical discipline. Reuses `resolveFrameReferenceSign` +
 * `houseCountedFrom` from address_resolver.ts (design §27.2's resolver) rather than
 * re-deriving frame math here — single-source mandate (design §19).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import {
  resolveFrameReferenceSign, houseCountedFrom, ZODIAC_SIGNS, grahaCodeOf,
  type ReferenceFrame, type ZodiacSign,
} from '../../../address_resolver'
import { DEFAULT_AYANAMSHA } from '../../constants'

const FRAME_VALUES: ReferenceFrame[] = ['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']

function isZodiacSign(v: string | null): v is ZodiacSign {
  return v !== null && (ZODIAC_SIGNS as readonly string[]).includes(v)
}

export const getPositionsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_positions',
  type: 'tool',
  layer: 'L1',
  name: 'get_positions',
  description:
    'Retrieve Gaṇita graha positions for a chart. Returns sidereal longitudes, rashi, nakshatra, pada, ' +
    'retrograde status, and combust status. ' +
    'CR-50: the DEFAULT page serves ONLY the 9 classical grahas (Sun/Moon/Mars/Mercury/Jupiter/' +
    'Venus/Saturn/Rahu/Ketu) plus Lagna (fact_category graha_position, fact_subject LAGNA/' +
    'NAVAMSA_LAGNA) — upagrahas (Gulika, Mandi, etc.) and aprakasha (dark/shadow) bodies are NOT ' +
    'interleaved into the default page. Pass `include_upagrahas: true` (or an explicit `categories` ' +
    'list containing "upagraha_position"/"aprakasha_position") to fetch those behind this facet — ' +
    'when present, upagraha/aprakasha rows are still served AFTER the grahas, never interleaved. ' +
    'Each row carries fact_id for Bodha constituent_facts_array back-reference. ' +
    'Covers fact_categories: graha_position, upagraha_position, aprakasha_position. ' +
    'Optional `frame` facet (lagna default | chandra | surya | arudha | karakamsha) re-bases each ' +
    'row\'s house count onto that reference frame in-response (design §27.3) — e.g. frame:"chandra" ' +
    'answers "what house is X in, from Moon" in one call, without a second lookup.',
  input_schema: {
    chart_id: {
      type: 'string',
      description: 'UUID of the chart (<chart_uuid> from asset_registry)',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: 'Filter by ayanamsha_id (e.g. LAHIRI). Omit for all ayanamshas.',
    },
    categories: {
      type: 'array',
      description: 'Optional EXPLICIT list of fact_categories to include — overrides the CR-50 default ' +
        '(graha_position only) and `include_upagrahas` entirely when supplied.',
      items: { type: 'string', enum: ['graha_position', 'upagraha_position', 'aprakasha_position'] },
    },
    include_upagrahas: {
      type: 'boolean',
      description: 'CR-50: when true (and `categories` is omitted), also includes upagraha_position ' +
        'and aprakasha_position rows behind this explicit facet — served AFTER the 9 grahas + Lagna, ' +
        'never interleaved into the default page. Default false.',
      default: false,
    },
    planet: {
      type: 'string',
      description: 'Optional: filter to a single graha/planet by name (e.g. "Sun", "Moon", "Mars"), ' +
        'matched case-insensitively against fact_subject. Omit to return all planets. ' +
        '(SC-20 fix: every caller of this tool already declared `planet` in its own schema, but this ' +
        'handler never read it — the filter was silently ignored. Now honored.)',
    },
    frame: {
      type: 'string',
      description: 'Reference frame to re-base house counts onto (default: lagna). ' +
        'chandra=from Moon, surya=from Sun, arudha=from Arudha Lagna, karakamsha=from Karakamsha. ' +
        'When set to a non-lagna frame, each row gains a `house_from_frame` field alongside the ' +
        'stored lagna-relative `house_d1` (fact_key) value.',
      enum: FRAME_VALUES,
      default: 'lagna',
    },
    offset: { type: 'number', description: 'Pagination offset (default 0)', default: 0 },
    limit:  { type: 'number', description: 'Rows per page (default 200, max 1000)', default: 200 },
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
    bulk_context: { pre_fetch_priority: 90, always_include: true },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0
      // CR-50: an EXPLICIT `categories` list always wins (back-compat + power-user override).
      // Otherwise, the default page is graha_position ONLY (9 grahas + Lagna) — upagraha_position/
      // aprakasha_position are opt-in via `include_upagrahas`, never interleaved by default.
      const includeUpagrahas = (args.include_upagrahas as boolean) === true
      const categories = (args.categories as string[] | undefined)
        ?? (includeUpagrahas
          ? ['graha_position', 'upagraha_position', 'aprakasha_position']
          : ['graha_position'])
      const frame = ((args.frame as string) ?? 'lagna') as ReferenceFrame
      if (!FRAME_VALUES.includes(frame)) {
        return {
          content: `Unsupported frame "${frame}". Supported: ${FRAME_VALUES.join(', ')} (design §27.3).`,
          is_error: true,
        }
      }
      const frameAyanamsha = (args.ayanamsha_id as string) ?? DEFAULT_AYANAMSHA
      const planet = (args.planet as string | undefined)?.trim() || undefined

      const params: unknown[] = [chartId, categories]
      let sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1
          AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      if (planet) {
        // W4-loop-1 (E-5 group2): chart_facts.fact_subject stores 3-letter graha CODES
        // (SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN), NOT full names — so
        // `fact_subject ILIKE 'Venus'` matched nothing while unfiltered returned rows.
        // Canonicalize the requested planet name to its fact_subject code; fall back to a
        // case-insensitive ILIKE on the raw value for non-graha subjects (upagrahas, etc.).
        let planetMatched = false
        try {
          const code = grahaCodeOf(planet)
          sql += ` AND fact_subject = $${params.length + 1}`
          params.push(code)
          planetMatched = true
        } catch {
          // not a known graha name/code — fall through to the raw ILIKE below
        }
        if (!planetMatched) {
          sql += ` AND fact_subject ILIKE $${params.length + 1}`
          params.push(planet)
        }
      }
      params.push(limit, offset)
      // CR-50: when a call spans multiple categories (include_upagrahas=true or an explicit
      // multi-category list), grahas + Lagna still LEAD the ordering — upagraha_position/
      // aprakasha_position sort after graha_position rather than interleaving alphabetically
      // (plain `fact_category` ASC would put aprakasha_position BEFORE graha_position).
      sql += ` ORDER BY ayanamsha_id,
                 CASE fact_category
                   WHEN 'graha_position' THEN 0
                   WHEN 'upagraha_position' THEN 1
                   WHEN 'aprakasha_position' THEN 2
                   ELSE 3
                 END,
                 fact_category, fact_key
               LIMIT $${params.length - 1} OFFSET $${params.length}`

      const result = await query<Record<string, unknown>>(sql, params)
      let rows = result.rows ?? []

      let frameNote: string | undefined
      if (frame !== 'lagna' && rows.length > 0) {
        try {
          const { sign: referenceSign } = await resolveFrameReferenceSign(chartId, frame, { ayanamsha_id: frameAyanamsha })

          const houseRows = rows.filter(r => r.fact_key === 'house_d1')
          if (houseRows.length === 0) {
            frameNote = `frame "${frame}" requested but this page contains no \`house_d1\` rows to ` +
              `re-base — \`house_from_frame\` NOT added. Rows served lagna-relative (house_d1) only.`
          } else {
            // R-28 fix: the 'sign' fact_key row for a given (ayanamsha_id, fact_subject) pair
            // sorts AFTER 'house_d1' alphabetically within the same ORDER BY — on a paginated
            // page (default limit 200, no ayanamsha_id filter → up to 5x rows), the 'sign' rows
            // could be truncated out of THIS page entirely, silently leaving signByKey empty
            // and house_from_frame never added even though frame_note claimed delivery
            // (previously: build the lookup from the SAME already-paginated `rows`, no
            // guarantee the matching 'sign' rows survived truncation). Fetch the 'sign' rows
            // for exactly the (ayanamsha_id, fact_subject) pairs present in THIS page via a
            // dedicated, un-paginated query so house_from_frame is delivered regardless of
            // where pagination falls.
            const ayanamshaIds = Array.from(new Set(houseRows.map(r => r.ayanamsha_id as string)))
            const subjects = Array.from(new Set(houseRows.map(r => r.fact_subject as string)))
            const signResult = await query<{ ayanamsha_id: string; fact_subject: string; fact_value_text: string | null }>(
              `SELECT ayanamsha_id, fact_subject, fact_value_text FROM chart_facts
               WHERE chart_id = $1 AND fact_key = 'sign'
                 AND ayanamsha_id = ANY($2::text[]) AND fact_subject = ANY($3::text[])`,
              [chartId, ayanamshaIds, subjects],
            )
            const signByKey = new Map<string, ZodiacSign>()
            for (const r of signResult.rows ?? []) {
              if (isZodiacSign(r.fact_value_text)) {
                signByKey.set(`${r.ayanamsha_id}::${r.fact_subject}`, r.fact_value_text)
              }
            }

            let rebased = 0
            rows = rows.map(r => {
              if (r.fact_key !== 'house_d1') return r
              const sign = signByKey.get(`${r.ayanamsha_id}::${r.fact_subject}`)
              if (!sign) return r
              rebased++
              return { ...r, house_from_frame: houseCountedFrom(referenceSign, sign) }
            })

            frameNote = rebased > 0
              ? `houses re-based from ${frame} (reference sign: ${referenceSign}, ` +
                `ayanamsha ${frameAyanamsha}) as \`house_from_frame\` alongside the stored lagna-relative ` +
                `\`house_d1\`: ${rebased}/${houseRows.length} house_d1 rows in this page carry it. ` +
                `Rows whose ayanamsha differs from "${frameAyanamsha}" are NOT re-based ` +
                `(pass matching ayanamsha_id to re-base a specific ayanamsha's rows).`
              : `frame "${frame}" requested but no matching \`sign\` rows were resolvable for the ` +
                `${houseRows.length} house_d1 row(s) in this page (0/${houseRows.length} rebased) — ` +
                `\`house_from_frame\` NOT added. Rows served lagna-relative (house_d1) only.`
          }
        } catch (e) {
          frameNote = `frame "${frame}" requested but could not be resolved: ${String(e)}. ` +
            `Rows served lagna-relative (house_d1) only.`
        }
      }

      return {
        content: {
          chart_id: chartId, categories, frame, planet: planet ?? null, rows, total: rows.length,
          include_upagrahas: includeUpagrahas,
          ...(frameNote ? { frame_note: frameNote } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
