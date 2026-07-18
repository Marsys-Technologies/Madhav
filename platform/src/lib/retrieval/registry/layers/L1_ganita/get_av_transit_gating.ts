/**
 * get_av_transit_gating — L1 Gaṇita sign-keyed Aṣṭakavarga transit-gating + kakṣyā serving surface
 * ====================================================================================================
 * Doctrine Campaign D-3 (Kāla Taraṅga + Three-Lock), Lane T-1 — "FIRST capability; sidecar-independent".
 *
 * Consumes the sign-keyed Aṣṭakavarga facts shipped in D-1.5b Lane B-2
 * (`ga_strength_writer.py` → chart_facts categories `ashtakavarga_bindu_sign` and
 * `ashtakavarga_kakshya_boundary`, declared in `ga_writers/CHART_FACTS_SCHEMA.json`).
 *
 * TWO modes, one capability (mirrors the `family` facet pattern used by get_vichara.ts):
 *
 * mode='sav_bav_gating' (default) — SAV (Samudaya/Sarva Ashtakavarga, fact_subject
 *   'SARVA-SIGN_N') and BAV (Bhinnashtakavarga, per-graha fact_subject '{GRAHA}-SIGN_N')
 *   bindu counts per sign, each row carrying a classical average-based damp/amplify
 *   classification a caller can use to weight a transit-timing window. The classical
 *   mean SAV bindu count is 337/12 ≈ 28.08 bindus/sign (7 grahas × 8-house Parashari grid);
 *   this capability classifies `damping` below the mean band, `amplifying` above it, and
 *   `neutral` in between — never a bare pass/fail so the caller can see the raw count.
 *
 * mode='kakshya_windows' — dated kakṣyā (1/8th-sign, 3.75°) sub-windows for a transiting
 *   planet crossing a target sidereal sign across a date range, tagging each contiguous
 *   segment with its classical kakṣyā lord (Saturn→Jupiter→Mars→Sun→Venus→Mercury→Moon→
 *   Lagna, the fixed Parashari order the kakshya_boundary facts already encode). Built
 *   from BRAHMA's L0 daily ephemeris (tropical) converted to sidereal via a documented
 *   Lahiri mean-rate approximation (see `estimateLahiriAyanamshaDeg` below) — the raw
 *   `ephemeris_daily` cache stores tropical rows only (verified live this pass; no
 *   pre-computed sidereal cache exists), so this conversion is the honest alternative to
 *   an [EXTERNAL_COMPUTATION_REQUIRED] stub. A slow planet (Saturn/Jupiter) yields
 *   multi-week kakṣyā windows, not the brief's illustrative "~3.4-day" figure — that
 *   figure only holds for a ~1°/day mover (Sun/Mercury/Venus/Mars-ish); this capability
 *   computes the REAL per-planet duration from the planet's own daily speed rather than
 *   asserting a fixed day-count. Retrograde loops can re-enter an already-exited kakṣhya —
 *   each contiguous calendar span is reported as its own window row (never collapsed).
 *
 * CR-87 discipline: chart_id (per_chart scope) is a REQUIRED input with no default; for
 * kakshya_windows, planet/sign_number/start_date/end_date are also required — nothing in
 * this handler silently falls back to a cached or default chart/planet/date.
 */
import type { CapabilityDescriptor, ToolResult } from '../../types'
import { query } from '@/lib/db/client'

const SIDECAR_URL = (process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001').replace(/\/$/, '')
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

const AV_BINDU_SIGN_CATEGORY = 'ashtakavarga_bindu_sign'
const AV_KAKSHYA_CATEGORY = 'ashtakavarga_kakshya_boundary'

const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

// ── SAV classification (classical mean-based, not a single hardcoded pair) ────────────
// Classical 7-graha Parashari Ashtakavarga total across all 12 signs is fixed per graha's
// own bindu table; the SARVA (samudaya) total per chart sums to a fixed grand total
// (337 in the classical reference tables), giving a per-sign mean of 337/12 ≈ 28.08.
// A ~2-bindu band around the mean is treated as neutral; below the band damps a transit
// window, above it amplifies. This reproduces both brief type specimens (27→damping,
// 34→amplifying) from the general rule rather than hardcoding those two numbers.
export const SAV_MEAN_BINDUS = 337 / 12 // ≈ 28.08
export const SAV_NEUTRAL_BAND = 1 // +/- around the mean (27 -> damping, 34 -> amplifying, per brief specimens)

export function classifySavBindus(bindus: number): 'damping' | 'amplifying' | 'neutral' {
  if (bindus < SAV_MEAN_BINDUS - SAV_NEUTRAL_BAND) return 'damping'
  if (bindus > SAV_MEAN_BINDUS + SAV_NEUTRAL_BAND) return 'amplifying'
  return 'neutral'
}

export function houseFromSign(signNumber: number, lagnaSignNumber: number): number {
  return ((signNumber - lagnaSignNumber + 12) % 12) + 1
}

// ── Sidereal conversion (documented Lahiri mean-rate approximation) ───────────────────
// N.C. Lahiri ayanamsha ≈ 23.8531° at epoch 2000-01-01, precessing at the IAU/Newcomb mean
// rate of ~50.29 arcsec/year. This is the standard linear approximation (error well under
// 0.01° across the campaign's date ranges) — NOT a Swiss-Ephemeris-grade nutation-aware
// value. Adequate for kakshya-boundary attribution (3.75° cells); a caller needing
// sub-arcminute sidereal precision should route through a dedicated ephemeris service.
const LAHIRI_AYANAMSHA_DEG_AT_2000 = 23.8531
const LAHIRI_PRECESSION_DEG_PER_YEAR = 50.29 / 3600

export function estimateLahiriAyanamshaDeg(dateISO: string): number {
  const d = new Date(`${dateISO}T00:00:00Z`)
  const year = d.getUTCFullYear()
  const startOfYear = Date.UTC(year, 0, 1)
  const startOfNextYear = Date.UTC(year + 1, 0, 1)
  const yearFrac = year + (d.getTime() - startOfYear) / (startOfNextYear - startOfYear)
  return LAHIRI_AYANAMSHA_DEG_AT_2000 + (yearFrac - 2000) * LAHIRI_PRECESSION_DEG_PER_YEAR
}

export interface TropicalTransitRow {
  date: string
  tropical_longitude: number
  speed_dps?: number
  is_retrograde?: boolean
}

export interface SiderealTransitRow {
  date: string
  sidereal_longitude: number
  sign_number: number
  degree_in_sign: number
  speed_dps?: number
  is_retrograde?: boolean
}

export function toSidereal(row: TropicalTransitRow): SiderealTransitRow {
  const ayanamsha = estimateLahiriAyanamshaDeg(row.date)
  const sidereal_longitude = ((row.tropical_longitude - ayanamsha) % 360 + 360) % 360
  const sign_number = Math.floor(sidereal_longitude / 30) + 1
  const degree_in_sign = sidereal_longitude - (sign_number - 1) * 30
  return {
    date: row.date, sidereal_longitude, sign_number, degree_in_sign,
    speed_dps: row.speed_dps, is_retrograde: row.is_retrograde,
  }
}

export interface KakshyaBoundary {
  index: number
  lord: string
  start_deg: number
  end_deg: number
}

export interface KakshyaWindow {
  kakshya_index: number
  lord: string
  start_deg: number
  end_deg: number
  sign_number: number
  entry_date: string
  exit_date: string | null // null = still inside this kakshya at the queried end_date
  day_count: number
  is_retrograde_segment: boolean
}

/** Which kakshya (1-8, per the fixed 3.75deg grid) a degree-in-sign falls in. */
export function kakshyaIndexForDegree(degreeInSign: number, boundaries: KakshyaBoundary[]): number | null {
  for (const b of boundaries) {
    // end-inclusive on the final kakshya only, else half-open [start, end)
    const isLast = b.index === boundaries.length
    if (degreeInSign >= b.start_deg && (isLast ? degreeInSign <= b.end_deg : degreeInSign < b.end_deg)) {
      return b.index
    }
  }
  return null
}

/**
 * Walk a chronological daily transit series (already restricted/relevant to one sidereal
 * sign) and emit contiguous kakshya sub-windows. A planet that retrogrades back into an
 * earlier kakshya produces a NEW window row for the re-entry — segments are never merged
 * across a direction change or a gap.
 */
export function buildKakshyaWindows(
  siderealRows: SiderealTransitRow[],
  boundaries: KakshyaBoundary[],
  targetSignNumber: number,
): KakshyaWindow[] {
  const windows: KakshyaWindow[] = []
  let current: KakshyaWindow | null = null

  for (const row of siderealRows) {
    if (row.sign_number !== targetSignNumber) {
      if (current) { windows.push(current); current = null }
      continue
    }
    const idx = kakshyaIndexForDegree(row.degree_in_sign, boundaries)
    if (idx === null) { if (current) { windows.push(current); current = null }; continue }
    const retro = !!row.is_retrograde

    if (current && current.kakshya_index === idx && current.is_retrograde_segment === retro) {
      current.exit_date = row.date
      current.day_count += 1
    } else {
      if (current) windows.push(current)
      const b: KakshyaBoundary | undefined = boundaries.find((x) => x.index === idx)
      current = {
        kakshya_index: idx,
        lord: b?.lord ?? 'unknown',
        start_deg: b?.start_deg ?? 0,
        end_deg: b?.end_deg ?? 0,
        sign_number: targetSignNumber,
        entry_date: row.date,
        exit_date: row.date,
        day_count: 1,
        is_retrograde_segment: retro,
      }
    }
  }
  if (current) windows.push(current)
  return windows
}

// ── Capability ──────────────────────────────────────────────────────────────────────

export const getAvTransitGatingCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_av_transit_gating',
  type: 'tool',
  layer: 'L1',
  name: 'get_av_transit_gating',
  description: [
    'D-3 Kāla Taraṅga Lane T-1: sign-keyed Aṣṭakavarga transit-gating + kakṣyā sub-windows',
    'for a chart. mode="sav_bav_gating" (default) serves SAV (samudaya/sarva) and BAV',
    '(bhinnashtakavarga, per-graha) bindu counts per sign, each classified damping/',
    'amplifying/neutral against the classical mean (~28.08 bindus/sign) — used to damp or',
    'amplify a timing window when a transiting planet crosses that sign. mode=',
    '"kakshya_windows" returns dated ~3.75-degree kakṣyā sub-arcs (8 per sign, fixed',
    'Saturn->Jupiter->Mars->Sun->Venus->Mercury->Moon->Lagna lordship order) a transiting',
    'planet crosses across a date range, each tagged with its kakṣyā lord and entry/exit',
    'dates (from BRAHMA daily ephemeris, tropical->sidereal via a documented Lahiri',
    'mean-rate approximation — not Swiss-Ephemeris-grade). Duration per kakṣyā window is',
    "computed from the ACTUAL transiting planet's speed, not a fixed day-count.",
  ].join(' '),
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha for the chart_facts lookup (default 'lahiri_chitrapaksha')." },
    mode:         { type: 'string', description: "'sav_bav_gating' (default) or 'kakshya_windows'.", enum: ['sav_bav_gating', 'kakshya_windows'] },
    // sav_bav_gating facets
    sign_number:  { type: 'number', description: 'sav_bav_gating: filter to one sidereal sign (1=Aries..12=Pisces). Omit for all 12.' },
    house:        { type: 'number', description: 'sav_bav_gating: filter by house number (1-12) instead of sign; resolved via the chart LAGNA sign.' },
    graha:        { type: 'string', description: 'sav_bav_gating: filter BAV to one graha (e.g. "Jupiter"). Omit for all + SAV.' },
    // kakshya_windows required facets (no defaults — CR-87)
    planet:       { type: 'string', description: 'kakshya_windows (required): transiting planet, e.g. "Saturn", "Jupiter".' },
    target_sign:  { type: 'number', description: 'kakshya_windows (required): target SIDEREAL sign number (1-12) to compute sub-windows for.' },
    start_date:   { type: 'string', description: 'kakshya_windows (required): YYYY-MM-DD.' },
    end_date:     { type: 'string', description: 'kakshya_windows (required): YYYY-MM-DD.' },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: false },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },
  density_contract: {
    paginated: false,
    facets: ['mode', 'sign_number', 'house', 'graha', 'planet', 'target_sign', 'start_date', 'end_date'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : 'lahiri_chitrapaksha'
    const mode = (args['mode'] ? String(args['mode']) : 'sav_bav_gating') as 'sav_bav_gating' | 'kakshya_windows'

    if (mode === 'kakshya_windows') {
      return handleKakshyaWindows(chart_id, ayanamsha_id, args)
    }
    return handleSavBavGating(chart_id, ayanamsha_id, args)
  },
}

async function handleSavBavGating(
  chart_id: string, ayanamsha_id: string, args: Record<string, unknown>,
): Promise<ToolResult> {
  try {
    // 1. LAGNA sign number (for house resolution).
    const lagnaRes = await query<{ fact_value_num: number }>(
      `SELECT fact_value_num FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2
         AND fact_category = 'graha_sign_attributes' AND fact_subject = 'LAGNA' AND fact_key = 'sign_num'
       LIMIT 1`,
      [chart_id, ayanamsha_id],
    )
    const lagnaSignNumber = lagnaRes.rows[0]?.fact_value_num ?? null

    // 2. All ashtakavarga_bindu_sign rows for this chart/ayanamsha.
    const rowsRes = await query<{ fact_subject: string; fact_value_num: number; fact_id: string }>(
      `SELECT fact_id, fact_subject, fact_value_num
       FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = $3
       ORDER BY fact_subject`,
      [chart_id, ayanamsha_id, AV_BINDU_SIGN_CATEGORY],
    )

    if (rowsRes.rows.length === 0) {
      return {
        content: {
          chart_id, mode: 'sav_bav_gating', rows: [], total: 0,
          empty_reason: `No ${AV_BINDU_SIGN_CATEGORY} facts for chart ${chart_id} (ayanamsha ${ayanamsha_id}). ` +
            'This asset ships from D-1.5b Lane B-2 (ga_strength_writer.py) — verify the chart has been rebuilt since.',
          provenance: { tables: ['chart_facts'], fact_category: AV_BINDU_SIGN_CATEGORY },
        },
        is_error: false,
      }
    }

    // Parse `{GRAHA|SARVA}-SIGN_N` subjects into a per-sign structure.
    type SignBucket = { sav_bindus: number | null; bav: Record<string, number>; fact_ids: string[] }
    const bySign = new Map<number, SignBucket>()
    for (let s = 1; s <= 12; s++) bySign.set(s, { sav_bindus: null, bav: {}, fact_ids: [] })

    for (const r of rowsRes.rows) {
      const m = /^(.+)-SIGN_(\d+)$/.exec(r.fact_subject)
      if (!m) continue
      const [, subjectCode, signStr] = m
      const signNumber = Number(signStr)
      const bucket = bySign.get(signNumber)
      if (!bucket) continue
      bucket.fact_ids.push(r.fact_id)
      if (subjectCode === 'SARVA') bucket.sav_bindus = r.fact_value_num
      else bucket.bav[subjectCode] = r.fact_value_num
    }

    const signFilter = args['sign_number'] ? Number(args['sign_number']) : null
    const houseFilter = args['house'] ? Number(args['house']) : null
    const grahaFilter = args['graha'] ? String(args['graha']).toUpperCase().slice(0, 3) : null

    const rows = Array.from(bySign.entries())
      .map(([signNumber, bucket]) => {
        const house = lagnaSignNumber ? houseFromSign(signNumber, lagnaSignNumber) : null
        return {
          sign_number: signNumber,
          sign_name: SIGN_NAMES[signNumber - 1],
          house,
          sav_bindus: bucket.sav_bindus,
          sav_classification: bucket.sav_bindus !== null ? classifySavBindus(bucket.sav_bindus) : null,
          bav: grahaFilter
            ? Object.fromEntries(Object.entries(bucket.bav).filter(([k]) => k === grahaFilter))
            : bucket.bav,
          fact_ids: bucket.fact_ids,
        }
      })
      .filter((r) => (signFilter ? r.sign_number === signFilter : true))
      .filter((r) => (houseFilter ? r.house === houseFilter : true))

    return {
      content: {
        chart_id, mode: 'sav_bav_gating', ayanamsha_id,
        lagna_sign_number: lagnaSignNumber,
        classification_basis: {
          mean_sav_bindus: SAV_MEAN_BINDUS,
          neutral_band: SAV_NEUTRAL_BAND,
          note: 'damping < mean-band < neutral < mean+band < amplifying; raw sav_bindus always served alongside.',
        },
        rows,
        total: rows.length,
        filters: { sign_number: signFilter, house: houseFilter, graha: grahaFilter },
        provenance: { tables: ['chart_facts'], fact_category: AV_BINDU_SIGN_CATEGORY },
      },
      is_error: false,
    }
  } catch (err) {
    return { content: { error: String(err), chart_id }, is_error: true }
  }
}

async function handleKakshyaWindows(
  chart_id: string, ayanamsha_id: string, args: Record<string, unknown>,
): Promise<ToolResult> {
  const planet = args['planet'] ? String(args['planet']) : ''
  const target_sign = args['target_sign'] ? Number(args['target_sign']) : null
  const start_date = args['start_date'] ? String(args['start_date']) : ''
  const end_date = args['end_date'] ? String(args['end_date']) : ''

  if (!planet || !target_sign || !start_date || !end_date) {
    return {
      content: {
        error: 'mode=kakshya_windows requires planet, target_sign, start_date, end_date — none default.',
        chart_id,
      },
      is_error: true,
    }
  }

  try {
    // 1. Kakshya boundary facts (chart-scoped storage, universal 0-30deg grid + lord order).
    const boundaryRes = await query<{ fact_subject: string; fact_key: string; fact_value_num: number | null; fact_value_text: string | null }>(
      `SELECT fact_subject, fact_key, fact_value_num, fact_value_text
       FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = $3`,
      [chart_id, ayanamsha_id, AV_KAKSHYA_CATEGORY],
    )
    if (boundaryRes.rows.length === 0) {
      return {
        content: {
          chart_id, mode: 'kakshya_windows', windows: [], total: 0,
          empty_reason: `No ${AV_KAKSHYA_CATEGORY} facts for chart ${chart_id} (ayanamsha ${ayanamsha_id}).`,
          provenance: { tables: ['chart_facts'], fact_category: AV_KAKSHYA_CATEGORY },
        },
        is_error: false,
      }
    }
    const boundaryMap = new Map<number, Partial<KakshyaBoundary>>()
    for (const r of boundaryRes.rows) {
      const m = /^KAKSHYA_(\d+)$/.exec(r.fact_subject)
      if (!m) continue
      const idx = Number(m[1])
      const b = boundaryMap.get(idx) ?? { index: idx }
      if (r.fact_key === 'lord') b.lord = r.fact_value_text ?? undefined
      if (r.fact_key === 'start_deg') b.start_deg = r.fact_value_num ?? undefined
      if (r.fact_key === 'end_deg') b.end_deg = r.fact_value_num ?? undefined
      boundaryMap.set(idx, b)
    }
    const boundaries = Array.from(boundaryMap.values())
      .filter((b): b is KakshyaBoundary => b.lord !== undefined && b.start_deg !== undefined && b.end_deg !== undefined)
      .sort((a, b) => a.index - b.index)

    // 2. Daily tropical transit series from the BRAHMA sidecar (no pre-computed sidereal
    //    cache exists — verified live this pass; ephemeris_daily stores ayanamsha_id='tropical' only).
    const params = new URLSearchParams({ planet, start_date, end_date })
    const sidecarHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
    // forward the sidecar API key when configured (the sidecar's verify_api_key dependency
    // 401s on a missing/mismatched x-api-key when PYTHON_SIDECAR_API_KEY is set) — same fix
    // pattern as query_planet_position.ts / call_service_wrappers.ts (WP-1.7); this handler
    // predated that fix and never inherited it (D-3 T-6, live-confirmed 401 root cause).
    if (SIDECAR_API_KEY) sidecarHeaders['x-api-key'] = SIDECAR_API_KEY
    const res = await fetch(`${SIDECAR_URL}/brahmagyan/ephemeris/planet_transit?${params}`, {
      headers: sidecarHeaders,
    })
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return { content: { error: `sidecar ${res.status}: ${msg}`, chart_id }, is_error: true }
    }
    const sidecarData = await res.json() as { ok?: boolean; rows?: TropicalTransitRow[]; error?: string }
    if (sidecarData.ok === false || !sidecarData.rows) {
      return { content: { error: sidecarData.error ?? 'sidecar returned no rows', chart_id }, is_error: true }
    }

    const sidereal = sidecarData.rows.map(toSidereal)
    const windows = buildKakshyaWindows(sidereal, boundaries, target_sign)

    return {
      content: {
        chart_id, mode: 'kakshya_windows', ayanamsha_id, planet, target_sign,
        start_date, end_date,
        windows,
        total: windows.length,
        ...(windows.length === 0
          ? { empty_reason: `${planet} does not transit sidereal sign ${target_sign} between ${start_date} and ${end_date} per the tropical->sidereal (Lahiri mean-rate) conversion.` }
          : {}),
        sidereal_conversion_note:
          'tropical_longitude from BRAHMA ephemeris_daily converted via a Lahiri mean-rate ' +
          'linear approximation (23.8531deg @ 2000.0 + 50.29"/yr) — NOT Swiss-Ephemeris-grade ' +
          'nutation-aware sidereal. Adequate for 3.75deg kakshya-cell attribution; boundary-day ' +
          'attribution near a cell edge carries ~1-day uncertainty.',
        provenance: {
          tables: ['chart_facts'], fact_category: AV_KAKSHYA_CATEGORY,
          external_source: 'BRAHMA ephemeris_daily (tropical) via python-sidecar /brahmagyan/ephemeris/planet_transit',
        },
      },
      is_error: false,
    }
  } catch (err) {
    return { content: { error: String(err), chart_id }, is_error: true }
  }
}
