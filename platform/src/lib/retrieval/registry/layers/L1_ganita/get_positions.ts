/**
 * L1 retrieval: graha positions
 * Covers: graha_position, upagraha_position, aprakasha_position, sun_derived_upagraha,
 *         sandhi_flag, nakshatra_cross_ayanamsha
 * Tool: marsys://tool/L1/get_positions
 *
 * FRAME FACET (R5 W2, design §27.3): all rows are written lagna-relative (`house_d1` is
 * counted from Lagna). An optional `frame` param re-bases each row's house onto a
 * non-lagna reference frame (chandra/surya/arudha/karakamsha) IN THE SAME CALL — the
 * Sudarshana-style "what house is Jupiter in, from Moon" judgment becomes one facet
 * instead of an unaddressable classical discipline. Reuses `resolveFrameReferenceSign` +
 * `houseCountedFrom` from address_resolver.ts (design §27.2's resolver) rather than
 * re-deriving frame math here — single-source mandate (design §19).
 *
 * W2 structural-close SC-2/SC-5 (RETRIEVAL_STRATEGY_v1_0.md §5.2 register rows, serving-side
 * only — no writer change):
 *   - SC-2 (graha speed/retro/combustion): retrograde_flag and combustion_state were ALREADY
 *     served here (part of the default `graha_position` category, see description) — the
 *     register's three named categories (graha_speed_state/graha_retrogression_state/
 *     graha_combustion_state) are dead names a writer overlap-guard reserves but never
 *     actually emits (verified live: zero rows for any of the three, any chart). The one
 *     genuinely missing piece is a NUMERIC speed (degrees/day) for the natal moment —
 *     chart_facts has no such value to serve (a real writer gap, out of this lane's scope).
 *     It IS reachable today via a different, already-served capability: `query_planet_position`
 *     (L0, ephemeris_daily-backed, date range 1900-01-01..2150-12-31) returns `speed_dps` and
 *     `is_retrograde` for any date, including the chart's own birth date — a SERVED-VIA cross
 *     reference, not a gap, per the coverage doctrine (§5.2).
 *   - SC-5 (nakshatra_cross_ayanamsha unserved): real, computed, chart_facts-resident category
 *     (per-graha 5-ayanamsha nakshatra-stability check) with zero prior serving route. Added to
 *     the `categories` enum below (NOT the unconditional default, to preserve CR-50's default-
 *     page discipline) — reachable via categories:["nakshatra_cross_ayanamsha"].
 *
 * F-B32 (L1_W6_CLOSE_REPORT_v1_0.md §5, cycle 184): `sun_derived_upagraha` (KALA_SUN,
 * MRITYU_SUN, YAMAGHANTAKA, ARTHA_PRAHARA — 4 Sun-derived shadow points, `ga_sensitive_
 * writer.py`-owned, 20 rows/ayanamsha) and `sandhi_flag` (bhava-junction flag per graha,
 * `ga_positions_writer.py`-owned via `_build_chalit_rows`, already correctly declared in this
 * asset's own `natural_key_partition` since migration 876) had zero serving path anywhere —
 * this closed the same class of gap SC-5 closed for nakshatra_cross_ayanamsha. Deliberately
 * deferred across cycles 181-183 pending a careful pass on THIS specific file (frame-rebasing
 * math, CR-50 discipline, heavily exercised — a materially higher blast radius than the other
 * F-B32 slices) rather than a rushed addition. `sun_derived_upagraha` genuinely HAS `house_d1`
 * rows (confirmed live) so the `frame` facet applies to it exactly like `upagraha_position` —
 * joined the `include_upagrahas` bundle rather than left opt-in-only, since it IS an upagraha
 * conceptually and a caller asking for "all the upagrahas" should get it without a second
 * category name to remember. `sandhi_flag` has no `house_d1` rows (flag/reasons text only, not
 * a position) — added to the `categories` enum only, alongside nakshatra_cross_ayanamsha,
 * never bundled into `include_upagrahas` (it is not an upagraha).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { planKpAwareRead, ayanamshaServeOrderBy, KP_AWARE_AYANAMSHA_ID_TEXT } from '../../handler_ayanamsha'
import { CITATION_HUMAN_SELECT, normalizeNarrationRows } from './citation_narration'
import {
  resolveFrameReferenceSign, houseCountedFrom, ZODIAC_SIGNS, grahaCodeOf,
  type ReferenceFrame, type ZodiacSign,
} from '../../../address_resolver'
import { DEFAULT_AYANAMSHA, AYANAMSHA_SERVE_ORDER } from '../../constants'
import { CROSS_CHECK_KEY } from '../../../ayanamsha_cross_check'
import { fetchPositionsCrossCheck } from '../../../ayanamsha_cross_check_reads'

const FRAME_VALUES: ReferenceFrame[] = ['lagna', 'chandra', 'surya', 'arudha', 'karakamsha']

function isZodiacSign(v: string | null): v is ZodiacSign {
  return v !== null && (ZODIAC_SIGNS as readonly string[]).includes(v)
}

import { BUILD_FENCE_INPUT, classifyBuildFence, explicitEmptyBuildFenceRefusal } from '../../generation/served_generation'

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
    'NAVAMSA_LAGNA) — upagrahas (Gulika, Mandi, Sun-derived shadow points, etc.) and aprakasha ' +
    '(dark/shadow) bodies are NOT interleaved into the default page. Pass ' +
    '`include_upagrahas: true` (or an explicit `categories` list containing ' +
    '"upagraha_position"/"sun_derived_upagraha"/"aprakasha_position") to fetch those behind this ' +
    'facet — when present, upagraha/aprakasha rows are still served AFTER the grahas, never ' +
    'interleaved. ' +
    'Each row carries fact_id for Bodha constituent_facts_array back-reference. ' +
    'Covers fact_categories: graha_position, upagraha_position, sun_derived_upagraha, ' +
    'aprakasha_position. ' +
    'Optional `frame` facet (lagna default | chandra | surya | arudha | karakamsha) re-bases each ' +
    'row\'s house count onto that reference frame in-response (design §27.3) — e.g. frame:"chandra" ' +
    'answers "what house is X in, from Moon" in one call, without a second lookup; applies to ' +
    'sun_derived_upagraha rows too (they carry house_d1), not just graha/upagraha_position. ' +
    'graha_position.retrograde_flag / graha_position.combustion_state ARE the served retrograde ' +
    'and combustion state (already on the default page) — numeric speed (degrees/day) for the ' +
    'chart\'s birth date is NOT stored here; fetch it via query_planet_position(date=<birth date>). ' +
    'Two further real categories are available on request, not on the default page or the ' +
    'include_upagrahas bundle: nakshatra_cross_ayanamsha (per-graha 5-ayanamsha nakshatra-' +
    'stability check) via categories:["nakshatra_cross_ayanamsha"], and sandhi_flag ' +
    '(bhava-junction flag per graha — not an upagraha, no house_d1) via ' +
    'categories:["sandhi_flag"].',
  input_schema: {
    build_id: BUILD_FENCE_INPUT,
    chart_id: {
      type: 'string',
      description: 'UUID of the chart (<chart_uuid> from asset_registry)',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: KP_AWARE_AYANAMSHA_ID_TEXT,
    },
    categories: {
      type: 'array',
      description: 'Optional EXPLICIT list of fact_categories to include — overrides the CR-50 default ' +
        '(graha_position only) and `include_upagrahas` entirely when supplied. Includes the SC-5 ' +
        'opt-in category nakshatra_cross_ayanamsha (per-graha 5-ayanamsha nakshatra-stability check) ' +
        'and the F-B32 opt-in category sandhi_flag (bhava-junction flag per graha) — neither is on ' +
        'the default page or the include_upagrahas bundle.',
      items: {
        type: 'string',
        enum: ['graha_position', 'upagraha_position', 'sun_derived_upagraha', 'aprakasha_position',
          'nakshatra_cross_ayanamsha', 'sandhi_flag'],
      },
    },
    include_upagrahas: {
      type: 'boolean',
      description: 'CR-50: when true (and `categories` is omitted), also includes upagraha_position, ' +
        'sun_derived_upagraha, and aprakasha_position rows behind this explicit facet — served AFTER ' +
        'the 9 grahas + Lagna, never interleaved into the default page. Default false.',
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
        'stored lagna-relative `house_d1` (fact_key) value. F-159: frame="chandra" additionally ' +
        'carries `ayanamsha_frame_sensitivity` — a disclosure (never a correctness ruling) of ' +
        'whether the Moon\'s own sign, the frame-determining fact, agrees across the 5 real ' +
        'ayanamshas.',
      enum: FRAME_VALUES,
      default: 'lagna',
    },
    include_cross_check: {
      type: 'boolean',
      description: 'Lahiri-primary PR-3: when true, adds `ayanamsha_cross_check` — the sign and nakshatra of every ' +
        'graha on this page under the other four ayanamshas, as a LABELLED cross-check ("Cross-check, not the ' +
        'reading"; categorical equality only, degrees shown never compared). Default false. Independently of ' +
        'this flag, a page that serves the Lagna or the Moon always carries the compact identity cross-check ' +
        '(Lagna sign, Moon sign, Moon nakshatra). Not applied under ayanamsha_id:"all" (that is the raw multi-row option).',
      default: false,
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
      // sun_derived_upagraha/aprakasha_position are opt-in via `include_upagrahas`, never
      // interleaved by default. sun_derived_upagraha joins this bundle (F-B32, cycle 184) since
      // it IS an upagraha conceptually, unlike sandhi_flag (categories-only, see below).
      const includeUpagrahas = (args.include_upagrahas as boolean) === true
      const categories = (args.categories as string[] | undefined)
        ?? (includeUpagrahas
          ? ['graha_position', 'upagraha_position', 'sun_derived_upagraha', 'aprakasha_position']
          : ['graha_position'])
      const frame = ((args.frame as string) ?? 'lagna') as ReferenceFrame
      if (!FRAME_VALUES.includes(frame)) {
        return {
          content: `Unsupported frame "${frame}". Supported: ${FRAME_VALUES.join(', ')} (design §27.3).`,
          is_error: true,
        }
      }
      // SS N-358: a KP category in an explicit list is read at krishnamurti (the default page has none).
      const kp = planKpAwareRead(args, categories)
      const aya = kp.aya
      // The frame's reference sign is read under ONE ayanamsha: the requested one, else Lahiri (also under "all").
      const frameAyanamsha = aya.id ?? DEFAULT_AYANAMSHA
      const planet = (args.planet as string | undefined)?.trim() || undefined
      const buildFence = classifyBuildFence(args.build_id)
      if (buildFence.kind === 'explicit_empty') return explicitEmptyBuildFenceRefusal('get_positions', chartId)
      const buildIds = buildFence.kind === 'resolved' ? buildFence.build_ids : null

      const params: unknown[] = [chartId, categories]
      let sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref, ${CITATION_HUMAN_SELECT}
        FROM chart_facts
        WHERE chart_id = $1
          AND fact_category = ANY($2::text[])
      `
      // includeInvariant: the opt-in category nakshatra_cross_ayanamsha is stored under the
      // ayanamsha_id='INVARIANT' sentinel (ga_nakshatra); a bare equality filter would drop it.
      sql += kp.filter(params, { includeInvariant: true })
      if (buildIds) {
        sql += ` AND build_id = ANY($${params.length + 1}::uuid[])`
        params.push(buildIds)
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
      sql += ` ORDER BY ${ayanamshaServeOrderBy()},
                 CASE fact_category
                   WHEN 'graha_position' THEN 0
                   WHEN 'upagraha_position' THEN 1
                   WHEN 'aprakasha_position' THEN 2
                   ELSE 3
                 END,
                 fact_category, fact_key
               LIMIT $${params.length - 1} OFFSET $${params.length}`

      const result = await query<Record<string, unknown>>(sql, params)
      let rows = kp.label(normalizeNarrationRows(result.rows))

      let frameNote: string | undefined
      // F-159: populated only for frame:'chandra' — see resolveFrameReferenceSign's own doc.
      let ayanamshaFrameSensitivity: unknown
      if (frame !== 'lagna' && rows.length > 0) {
        try {
          const { sign: referenceSign, ayanamsha_frame_sensitivity } =
            await resolveFrameReferenceSign(chartId, frame, { ayanamsha_id: frameAyanamsha, ...(buildIds ? { build_id: buildIds } : {}) })
          ayanamshaFrameSensitivity = ayanamsha_frame_sensitivity

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
                 AND ayanamsha_id = ANY($2::text[]) AND fact_subject = ANY($3::text[])
                 ${buildIds ? 'AND build_id = ANY($4::uuid[])' : ''}`,
              buildIds ? [chartId, ayanamshaIds, subjects, buildIds] : [chartId, ayanamshaIds, subjects],
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

      // Lahiri-primary PR-3 (SS N-342): the labelled cross-check. The primary answer above is final and
      // is never reordered or merged with it. Always-on, compact, for the identity facts this page serves
      // (Lagna sign, Moon sign, Moon nakshatra); the full per-graha form is opt-in via include_cross_check.
      // Not applied under the raw "all" option (the caller already has every ayanamsha's rows).
      let crossCheck: Awaited<ReturnType<typeof fetchPositionsCrossCheck>> | undefined
      if (aya.id !== null && (AYANAMSHA_SERVE_ORDER as readonly string[]).includes(aya.id)) {
        const subjects = [...new Set(rows
          .filter(r => r.fact_category === 'graha_position' && typeof r.fact_subject === 'string')
          .map(r => r.fact_subject as string))]
        const identitySubjects = subjects.filter(s => s === 'LAGNA' || s === 'MOON')
        if (args.include_cross_check === true && subjects.length > 0) {
          crossCheck = await fetchPositionsCrossCheck(chartId, aya.id, { subjects, identityOnly: false, mode: 'full', buildIds })
        } else if (identitySubjects.length > 0) {
          crossCheck = await fetchPositionsCrossCheck(chartId, aya.id, { subjects: identitySubjects, identityOnly: true, mode: 'compact', buildIds })
        }
      }

      return {
        content: {
          chart_id: chartId, ...kp.echo(rows), categories, frame, planet: planet ?? null, rows, total: rows.length,
          ...(crossCheck ? { [CROSS_CHECK_KEY]: crossCheck } : {}),
          include_upagrahas: includeUpagrahas,
          // DENS-F: an explicit `categories` list may name categories this asset does not own (another asset's rows of chart_facts).
          // They are served unchanged (never dropped, B.10) but disclosed here so a caller cannot read the page as only this asset's rows.
          ...(foreign(categories).length > 0
            ? { categories_outside_asset: foreign(categories), categories_outside_asset_note: 'These requested categories belong to another asset; their rows are served but are not this surface\'s own layer.' }
            : {}),
          ...(rows.length === 0
            ? { empty_reason: `No position fact for chart ${chartId} in categories [${categories.join(', ')}]${aya.id ? ` at ayanamsha '${aya.id}'` : ''}${planet ? ` for planet '${planet}'` : ''}${offset > 0 ? ` (offset ${offset})` : ''}.` }
            : {}),
          ...(frameNote ? { frame_note: frameNote } : {}),
          // F-159: disclosure-only — the chandra frame's OWN Moon-sign agreement across the 5
          // real ayanamshas, never a ruling on which ayanamsha is correct.
          ...(ayanamshaFrameSensitivity ? { ayanamsha_frame_sensitivity: ayanamshaFrameSensitivity } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
  // DENS-F (CLAUDE.md §N.6): the facets are real inputs; `categories` is the facet that selects the rows
  // (asset_declarations.json ga_positions.density_facet). Pagination is a limit/offset pair; the handler returns
  // `empty_reason` on a zero-row page.
  density_contract: {
    paginated: true,
    facets: ['ayanamsha_id', 'categories', 'include_upagrahas', 'planet', 'frame'],
    empty_reason: true,
  },
}

// DENS-F: the categories this surface serves AS ga_positions' own rows (asset_declarations.json ga_positions.density_facet).
const OWN_CATEGORIES = ['graha_position', 'sandhi_flag']
const foreign = (cs: string[]): string[] => cs.filter(c => !OWN_CATEGORIES.includes(c))
