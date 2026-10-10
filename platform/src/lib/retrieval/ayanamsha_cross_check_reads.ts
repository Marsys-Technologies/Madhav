/**
 * ayanamsha_cross_check_reads.ts — the DB side of the labelled cross-check (Lahiri-primary PR-3).
 * ==============================================================================================
 * `ayanamsha_cross_check.ts` is pure; this file reads the per-ayanamsha IDENTITY FACTS it compares
 * from the stored rows, for the surfaces that serve those facts as THE answer:
 *
 *   lagna_sign      chart_facts graha_position / LAGNA / sign
 *   moon_sign       chart_facts graha_position / MOON  / sign
 *   moon_nakshatra  chart_facts graha_position / MOON  / nakshatra
 *   maha_lord       chart_dashas vimshottari level 1 row(s) containing the as-of date
 *
 * Each read covers all five stored ayanamshas in ONE query per source (no per-ayanamsha loop), never
 * LIMIT-reduces (every matching row is returned and aggregated deterministically in JS), and is
 * non-blocking: a failure becomes `{ not_available: true, reason: 'cross_check_read_failed' }`, never a
 * thrown error and never an invented agreement. Longitudes are read only so they can be SHOWN beside a
 * sign / nakshatra; they are never compared.
 */
import { query } from '@/lib/db/client'
import { resolveChartServedGeneration, resolvedRowsBuildId } from './registry/generation/served_generation'
import { AYANAMSHA_SERVE_ORDER } from './registry/constants'
import { GRAHA_CODE_TO_NAME } from './graha_labels'
import {
  buildAyanamshaCrossCheck,
  identityFactSpecs,
  CROSS_CHECK_HEADING,
  ALL_IDENTITY_FACT_KEYS,
  type AyanamshaCrossCheck,
  type CrossCheckFactSpec,
  type CrossCheckInputRow,
  type CrossCheckScope,
  type IdentityFactKey,
} from './ayanamsha_cross_check'

export interface IdentityCrossCheckOptions {
  /** Which identity facts this surface serves (and so cross-checks). */
  readonly facts: readonly IdentityFactKey[]
  /** The as-of date for `maha_lord` (YYYY-MM-DD). Default: today (UTC date, as get_dashas does). */
  readonly asOfDate?: string
  /** Served-generation fence for the chart_facts reads (null/undefined = unfenced, as the surface itself reads). */
  readonly positionBuildIds?: readonly string[] | null
  /** The ga_dashas build that produced the served dasha rows. */
  readonly dashaBuildId?: string | null
  readonly scope?: CrossCheckScope
  /** Extra fact specs appended after the identity ones (e.g. Antardasha lord). */
  readonly extraRows?: readonly CrossCheckInputRow[]
  readonly extraFacts?: readonly CrossCheckFactSpec[]
}

interface PositionReadRow {
  ayanamsha_id: string
  fact_subject: string
  fact_key: string
  fact_value_text: string | null
  fact_value_num: string | number | null
}

interface DashaReadRow {
  ayanamsha_id: string
  lord_graha: string | null
}

const num = (v: string | number | null): number | undefined => {
  if (v === null || v === undefined) return undefined
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n : undefined
}

/** Pure: turn the raw position rows into cross-check input rows (degrees shown, never compared). */
export function positionRowsToCrossCheckRows(rows: readonly PositionReadRow[], facts: readonly IdentityFactKey[]): CrossCheckInputRow[] {
  const want = new Set<IdentityFactKey>(facts)
  const lon = new Map<string, number>()
  for (const r of rows) {
    if (r.fact_key === 'longitude_sidereal') {
      const n = num(r.fact_value_num)
      if (n !== undefined) lon.set(`${r.ayanamsha_id}|${r.fact_subject}`, n)
    }
  }
  const out: CrossCheckInputRow[] = []
  for (const r of rows) {
    const deg = lon.get(`${r.ayanamsha_id}|${r.fact_subject}`)
    const withDeg = deg !== undefined ? { degrees: deg } : {}
    if (r.fact_subject === 'LAGNA' && r.fact_key === 'sign' && want.has('lagna_sign')) {
      out.push({ ayanamsha_id: r.ayanamsha_id, fact_key: 'lagna_sign', value: r.fact_value_text, ...withDeg })
    } else if (r.fact_subject === 'MOON' && r.fact_key === 'sign' && want.has('moon_sign')) {
      out.push({ ayanamsha_id: r.ayanamsha_id, fact_key: 'moon_sign', value: r.fact_value_text, ...withDeg })
    } else if (r.fact_subject === 'MOON' && r.fact_key === 'nakshatra' && want.has('moon_nakshatra')) {
      out.push({ ayanamsha_id: r.ayanamsha_id, fact_key: 'moon_nakshatra', value: r.fact_value_text, ...withDeg })
    }
  }
  return out
}

/** Pure: the Mahadasha lord(s) per ayanamsha, joined deterministically (a boundary day can hold two). */
export function dashaRowsToCrossCheckRows(rows: readonly DashaReadRow[]): CrossCheckInputRow[] {
  const byAya = new Map<string, Set<string>>()
  for (const r of rows) {
    if (!r.lord_graha) continue
    const set = byAya.get(r.ayanamsha_id) ?? new Set<string>()
    set.add(r.lord_graha)
    byAya.set(r.ayanamsha_id, set)
  }
  return [...byAya.entries()].map(([ayanamsha_id, set]) => ({
    ayanamsha_id, fact_key: 'maha_lord', value: [...set].sort().join(' / '),
  }))
}

/**
 * Read + build the compact IDENTITY cross-check for `chartId`, anchored on `primaryId` (the ayanamsha the
 * surface served: Lahiri unless the caller asked for another). Never throws.
 */
export async function fetchIdentityCrossCheck(
  chartId: string,
  primaryId: string,
  opts: IdentityCrossCheckOptions,
): Promise<AyanamshaCrossCheck> {
  const facts = opts.facts
  try {
    const wantsPositions = facts.some((f) => f === 'lagna_sign' || f === 'moon_sign' || f === 'moon_nakshatra')
    const wantsDasha = facts.includes('maha_lord')
    const ayas = [...AYANAMSHA_SERVE_ORDER] as string[]

    const positionP: Promise<PositionReadRow[]> = wantsPositions
      ? (() => {
          const params: unknown[] = [chartId, ayas]
          let fence = ''
          if (opts.positionBuildIds && opts.positionBuildIds.length > 0) {
            params.push([...opts.positionBuildIds])
            fence = ` AND build_id = ANY($${params.length}::uuid[])`
          }
          return query<PositionReadRow>(
            `SELECT ayanamsha_id, fact_subject, fact_key, fact_value_text, fact_value_num
               FROM chart_facts
              WHERE chart_id = $1 AND ayanamsha_id = ANY($2::text[]) AND fact_category = 'graha_position'
                AND ((fact_subject = 'LAGNA' AND fact_key IN ('sign', 'longitude_sidereal'))
                  OR (fact_subject = 'MOON'  AND fact_key IN ('sign', 'nakshatra', 'longitude_sidereal')))${fence}
              ORDER BY ayanamsha_id, fact_subject, fact_key, fact_id`,
            params,
          ).then((r) => r.rows)
        })()
      : Promise.resolve([])

    const dashaP: Promise<DashaReadRow[]> = wantsDasha
      ? (() => {
          const asOf = opts.asOfDate ?? new Date().toISOString().slice(0, 10)
          const params: unknown[] = [chartId, ayas, asOf]
          let fence = ''
          if (opts.dashaBuildId) {
            params.push(opts.dashaBuildId)
            fence = ` AND build_id = $${params.length}::uuid`
          }
          return query<DashaReadRow>(
            `SELECT ayanamsha_id, lord_graha
               FROM chart_dashas
              WHERE chart_id = $1 AND ayanamsha_id = ANY($2::text[]) AND system_id = 'vimshottari'
                AND level_n = 1 AND start_date <= $3::date AND end_date >= $3::date${fence}
              ORDER BY ayanamsha_id, start_date, lord_graha`,
            params,
          ).then((r) => r.rows)
        })()
      : Promise.resolve([])

    const [positionRows, dashaRows] = await Promise.all([positionP, dashaP])
    const rows: CrossCheckInputRow[] = [
      ...positionRowsToCrossCheckRows(positionRows, facts),
      ...dashaRowsToCrossCheckRows(dashaRows),
      ...(opts.extraRows ?? []),
    ]
    return buildAyanamshaCrossCheck(rows, primaryId, {
      facts: [...identityFactSpecs(facts), ...(opts.extraFacts ?? [])],
      scope: opts.scope ?? 'identity_facts',
    })
  } catch (err) {
    console.error('[ayanamsha_cross_check] identity cross-check read failed (non-fatal; the primary answer is unaffected):', err)
    return { not_available: true, reason: 'cross_check_read_failed', heading: CROSS_CHECK_HEADING, primary_id: primaryId }
  }
}

/**
 * The ONE shared identity block (SS N-360) for the surfaces that do not themselves serve a positions or dashas
 * page (chart_snapshot, and dossier through it): all four identity facts, through the same
 * `fetchIdentityCrossCheck` -> `buildAyanamshaCrossCheck` path as get_positions / get_dashas. The chart_facts
 * reads are fenced to the chart's served generation and the Mahadasha read to the served ga_dashas build when
 * the generation resolves; when it does not, the reads are unfenced exactly as get_positions' default page is.
 * Never throws.
 */
export async function fetchChartIdentityCrossCheck(chartId: string, primaryId: string): Promise<AyanamshaCrossCheck> {
  let positionBuildIds: readonly string[] | null = null
  let dashaBuildId: string | null = null
  try {
    const generation = await resolveChartServedGeneration(chartId, null)
    if (generation.served_build_ids.length > 0) positionBuildIds = generation.served_build_ids
    dashaBuildId = resolvedRowsBuildId(generation, 'ga_dashas')
  } catch (err) {
    console.error('[ayanamsha_cross_check] served-generation resolution failed for the identity block (reads unfenced):', err)
  }
  return fetchIdentityCrossCheck(chartId, primaryId, {
    facts: ALL_IDENTITY_FACT_KEYS, positionBuildIds, dashaBuildId, scope: 'identity_facts',
  })
}

// ── Opt-in cross-check for a get_positions page (`include_cross_check:true`) ──────────────────────────


/** The fact key a graha subject's sign / nakshatra are compared under (identity ones keep their names). */
export function positionFactKey(subject: string, field: 'sign' | 'nakshatra'): string {
  if (subject === 'LAGNA' && field === 'sign') return 'lagna_sign'
  if (subject === 'MOON' && field === 'sign') return 'moon_sign'
  if (subject === 'MOON' && field === 'nakshatra') return 'moon_nakshatra'
  return `${subject.toLowerCase()}_${field}`
}

function positionFactLabel(subject: string, field: 'sign' | 'nakshatra'): string {
  const name = subject === 'LAGNA' ? 'Lagna' : (GRAHA_CODE_TO_NAME[subject] ?? subject)
  return `${name} ${field}`
}

/** Pure: raw rows -> input rows for the subjects asked for (sign everywhere, nakshatra except Lagna). */
export function positionPageRowsToCrossCheckRows(rows: readonly PositionReadRow[]): CrossCheckInputRow[] {
  const lon = new Map<string, number>()
  for (const r of rows) {
    if (r.fact_key === 'longitude_sidereal') {
      const n = num(r.fact_value_num)
      if (n !== undefined) lon.set(`${r.ayanamsha_id}|${r.fact_subject}`, n)
    }
  }
  const out: CrossCheckInputRow[] = []
  for (const r of rows) {
    if (r.fact_key !== 'sign' && r.fact_key !== 'nakshatra') continue
    if (r.fact_subject === 'LAGNA' && r.fact_key === 'nakshatra') continue
    const deg = lon.get(`${r.ayanamsha_id}|${r.fact_subject}`)
    out.push({
      ayanamsha_id: r.ayanamsha_id,
      fact_key: positionFactKey(r.fact_subject, r.fact_key),
      value: r.fact_value_text,
      ...(deg !== undefined ? { degrees: deg } : {}),
    })
  }
  return out
}

/**
 * The cross-check for the graha_position subjects on a served positions page. `identityOnly` (the always-on
 * compact form) compares only Lagna sign / Moon sign / Moon nakshatra; otherwise (`include_cross_check:true`)
 * every served graha's sign and nakshatra. Never throws.
 */
export async function fetchPositionsCrossCheck(
  chartId: string,
  primaryId: string,
  opts: { subjects: readonly string[]; identityOnly: boolean; buildIds?: readonly string[] | null; scope?: CrossCheckScope },
): Promise<AyanamshaCrossCheck> {
  try {
    const subjects = [...new Set(opts.subjects)].sort()
    const params: unknown[] = [chartId, [...AYANAMSHA_SERVE_ORDER], subjects]
    let fence = ''
    if (opts.buildIds && opts.buildIds.length > 0) {
      params.push([...opts.buildIds])
      fence = ` AND build_id = ANY($${params.length}::uuid[])`
    }
    const res = await query<PositionReadRow>(
      `SELECT ayanamsha_id, fact_subject, fact_key, fact_value_text, fact_value_num
         FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id = ANY($2::text[]) AND fact_category = 'graha_position'
          AND fact_subject = ANY($3::text[]) AND fact_key IN ('sign', 'nakshatra', 'longitude_sidereal')${fence}
        ORDER BY ayanamsha_id, fact_subject, fact_key, fact_id`,
      params,
    )
    const specs: CrossCheckFactSpec[] = []
    const want = (subject: string, field: 'sign' | 'nakshatra'): void => {
      if (subject === 'LAGNA' && field === 'nakshatra') return
      if (opts.identityOnly && !(subject === 'LAGNA' || subject === 'MOON')) return
      if (opts.identityOnly && subject === 'LAGNA' && field !== 'sign') return
      specs.push({ key: positionFactKey(subject, field), label: positionFactLabel(subject, field) })
    }
    // Lagna, then the grahas in subject-code order of the page (deterministic); identity facts first.
    const rank = (s: string): number => (s === 'LAGNA' ? 0 : s === 'MOON' ? 1 : 2)
    const ordered = [...subjects].sort((a, b) => rank(a) - rank(b) || (a < b ? -1 : a > b ? 1 : 0))
    for (const s of ordered) { want(s, 'sign'); want(s, 'nakshatra') }
    return buildAyanamshaCrossCheck(positionPageRowsToCrossCheckRows(res.rows), primaryId, {
      facts: specs,
      scope: opts.scope ?? (opts.identityOnly ? 'identity_facts' : 'requested_facts'),
    })
  } catch (err) {
    console.error('[ayanamsha_cross_check] positions cross-check read failed (non-fatal; the primary answer is unaffected):', err)
    return { not_available: true, reason: 'cross_check_read_failed', heading: CROSS_CHECK_HEADING, primary_id: primaryId }
  }
}
