/**
 * reading_checklist.ts — ŚODHANA T5 (PŪRTI) shared receipt legs
 * ==============================================================
 * The "Offer Law" fix (MC-012/028/034 + MC-030/031/033): three classical
 * legs that were computed-but-never-joined into a domain reading, plus a
 * served `reading_checklist` receipt that names WHICH classical units this
 * response actually served — and, for every absent box, WHY (not computed /
 * not joined / salience-floored / not yet available).
 *
 * All three legs are SERVING-ONLY (B.10): they read already-produced L1/L3
 * facts (chart_facts sensitive_degree_check, the KP cuspal facts via the
 * frozen getKpCuspsCapability, and the kala_gochara_windows forecast field).
 * No computation is reimplemented; nothing is written. §N.5 — every leg
 * references real fact_ids/rows, never restates a computed value as its own.
 *
 * WHY THESE FACTS WERE INVISIBLE (the campaign root cause): rare fired-state
 * sensitive-degree facts (e.g. Mars in puṣkara on 482012f1 — the ONLY graha
 * in puṣkara on the chart, and the lagneśa/Indu-lagna lord) and the KP cuspal
 * wealth chain were floored below routine "dignity: neutral" descriptor rows
 * by salience priors, so no ranked/salience surface surfaced them. These legs
 * surface them STRUCTURALLY (a dedicated slot per classical unit), not by
 * re-tuning a fragile prior — a caller never has to ask for them by name.
 */
import { query } from '@/lib/db/client'

// ── The checklist vocabulary (design §28.6, generalized) ──────────────────────

/** The honest state of one classical unit in a served response. */
export type ChecklistState =
  | 'served' //               this unit's data is present in THIS response
  | 'empty_for_this_chart' //  computed, but no rows fired/exist for this chart (a finding, not a gap)
  | 'not_computed' //          the underlying L1/L2/L3 asset does not exist for this chart yet
  | 'not_joined' //            the data exists but this instrument does not fold it in (drill handle given)
  | 'salience_floored' //      exists + reachable but ranked below the served cut on salience surfaces
  | 'not_yet_available' //     the producing asset is being built in a parallel track (T6 yogi/avayogi)

export interface ChecklistUnit {
  unit: string
  state: ChecklistState
  detail?: string
  /** Live drill handle (tool name) a caller invokes to hydrate this unit when not served inline. */
  drill?: string
  count?: number
}

/**
 * A response is `non_exhaustive: 'salience_sampled'` whenever not every checklist
 * unit reached `served` / `empty_for_this_chart` (an honest negative is exhaustive
 * for that unit). Returns the disclosure value + the count of unserved units.
 */
export function checklistExhaustiveness(units: ChecklistUnit[]): {
  exhaustive: boolean
  non_exhaustive: false | 'salience_sampled'
  units_served: number
  units_total: number
  units_unserved: string[]
} {
  const settled = new Set<ChecklistState>(['served', 'empty_for_this_chart'])
  const unserved = units.filter(u => !settled.has(u.state)).map(u => u.unit)
  const exhaustive = unserved.length === 0
  return {
    exhaustive,
    non_exhaustive: exhaustive ? false : 'salience_sampled',
    units_served: units.length - unserved.length,
    units_total: units.length,
    units_unserved: unserved,
  }
}

// ── Leg 1: fired sensitive-degree checks (MC-030) ─────────────────────────────

/** sensitive_degree_check fact_subject code → classical graha display name. */
const SENSITIVE_SUBJECT_TO_GRAHA: Record<string, string> = {
  SUN: 'Sun', MOON: 'Moon', MAR: 'Mars', MER: 'Mercury', JUP: 'Jupiter',
  VEN: 'Venus', SAT: 'Saturn', RAH_MEAN: 'Rahu', KET_MEAN: 'Ketu',
}

/** The high-information check types — rare fired states that carry decisive weight
 *  (a fired one is a genuine event, not a routine descriptor). kartari is included:
 *  papa/shubha-kartari is a real bracketing yoga on the graha. */
export const HIGH_SIGNAL_SENSITIVE_CHECKS = [
  'pushkara', 'gandanta', 'mrityu_bhaga', 'kartari',
] as const

export interface SensitiveDegreeFiring {
  graha: string
  graha_code: string
  check_type: string
  state: string | null
  fact_id: string
  detail: Record<string, unknown> | null
}

export interface SensitiveDegreeResult {
  /** rows that actually FIRED (the rare, high-information events) */
  firings: SensitiveDegreeFiring[]
  /** number of high-signal check rows examined (fired + not-fired) */
  checked: number
  /** true if any sensitive_degree_check rows exist for this chart (the asset is built) */
  available: boolean
  fact_ids: string[]
}

/**
 * Fired high-signal sensitive-degree checks for a chart. Surfaces the rare firings
 * (pushkara / gandanta / mṛtyu-bhāga / kartari) chart-wide — NOT domain-scoped —
 * because a fired sensitive degree on a chart-critical graha (e.g. lagneśa Mars in
 * puṣkara) bears on every domain that graha touches, and is exactly the class of
 * fact salience priors bury. Reads the FROZEN L1 fact (`fact_value_jsonb->>'fired'`),
 * never recomputes (§N.5).
 */
export async function fetchSensitiveDegreeFirings(
  chart_id: string,
  ayanamsha_id: string,
): Promise<SensitiveDegreeResult> {
  const out: SensitiveDegreeResult = { firings: [], checked: 0, available: false, fact_ids: [] }
  try {
    const res = await query<{
      fact_id: string; fact_subject: string; fact_key: string
      fact_value_text: string | null; fact_value_jsonb: Record<string, unknown> | null
    }>(
      `SELECT fact_id, fact_subject, fact_key, fact_value_text, fact_value_jsonb
         FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND fact_category = 'sensitive_degree_check'
          AND fact_key = ANY($3)`,
      [chart_id, ayanamsha_id, [...HIGH_SIGNAL_SENSITIVE_CHECKS]],
    )
    out.available = res.rows.length > 0
    out.checked = res.rows.length
    for (const r of res.rows) {
      const jsonb = r.fact_value_jsonb ?? null
      const fired = jsonb ? jsonb['fired'] === true : false
      if (!fired) continue
      out.firings.push({
        graha: SENSITIVE_SUBJECT_TO_GRAHA[r.fact_subject] ?? r.fact_subject,
        graha_code: r.fact_subject,
        check_type: r.fact_key,
        state: r.fact_value_text,
        fact_id: r.fact_id,
        detail: jsonb,
      })
      out.fact_ids.push(r.fact_id)
    }
    // Surface the most decisive firings first: mṛtyu-bhāga (maraka), then gandanta
    // (junction danger), then puṣkara (the rare beneficence), then kartari.
    const order: Record<string, number> = { mrityu_bhaga: 0, gandanta: 1, pushkara: 2, kartari: 3 }
    out.firings.sort((a, b) => (order[a.check_type] ?? 9) - (order[b.check_type] ?? 9))
  } catch {
    // non-fatal: the whole leg degrades to an honest not-computed state upstream.
  }
  return out
}

// ── Leg 2: KP cuspal chain (MC-031) ───────────────────────────────────────────

/** Domain → the KP bhava cusps whose sub-lord chain + significators are decisive
 *  for that domain (KP paddhati: the cuspal sub-lord is the final arbiter of a
 *  house's promise). Wealth = 2nd (accumulated) + 11th (gains); career = 10th
 *  (karma) + 6th (service/competition); others map to their primary + a supporting
 *  bhāva. Cusps 2/6/10/11 are the campaign-named wealth/career chain (MC-031). */
export const DOMAIN_KP_CUSPS: Record<string, number[]> = {
  wealth: [2, 11], finance: [2, 11],
  career: [10, 6], vocation: [10, 6],
  relationship: [7, 2], marriage: [7, 2], partnership: [7, 2],
  health: [1, 6], vitality: [1, 6],
  progeny: [5, 9], children: [5, 9],
  education: [4, 5], vidya: [4, 5],
  spirituality: [9, 5],
  moksha: [12, 8], liberation: [12, 8],
  character: [1, 10], buddhi: [1, 10],
  residence: [4, 11], property: [4, 11], home: [4, 11],
}

export interface KpCuspLink {
  house: number
  sign: unknown
  sign_lord: unknown
  star_lord: unknown
  sub_lord: unknown
  sub_sub_lord: unknown
  significators: unknown
  fact_ids: string[]
}

export interface KpCuspResult {
  cusps: KpCuspLink[]
  available: boolean
  fact_ids: string[]
  note: string
}

/**
 * KP cuspal sub-lord chain for the domain's decisive cusps. Reuses the FROZEN
 * getKpCuspsCapability (single-source, §19) rather than re-querying the four KP
 * fact categories — never a parallel KP resolver here. Returns only the requested
 * cusps, compacted to the chain + significators (the decisive KP fields).
 */
export async function fetchKpCuspChain(
  chart_id: string,
  ayanamsha_id: string,
  houses: number[],
): Promise<KpCuspResult> {
  const out: KpCuspResult = {
    cusps: [], available: false, fact_ids: [],
    note: 'KP cuspal sub-lord chain (Krishnamurti Paddhati): the cusp sub-lord is the ' +
      'final arbiter of a bhāva\'s promise; its significators name the grahas that will ' +
      'deliver (or deny) the matter. Served for this domain\'s decisive cusps (MC-031).',
  }
  try {
    const { getKpCuspsCapability } = await import('./L1_ganita/get_kp_cusps')
    const res = await getKpCuspsCapability.handler({ chart_id, ayanamsha_id }, undefined)
    if (res.is_error) return out
    const c = res.content as Record<string, unknown>
    const allCusps = Array.isArray(c['cusps']) ? (c['cusps'] as Record<string, unknown>[]) : []
    out.available = allCusps.length > 0
    const want = new Set(houses)
    for (const cusp of allCusps) {
      if (!want.has(Number(cusp['house']))) continue
      const fact_ids = Array.isArray(cusp['fact_ids']) ? (cusp['fact_ids'] as string[]) : []
      out.cusps.push({
        house: Number(cusp['house']),
        sign: cusp['sign'] ?? null,
        sign_lord: cusp['sign_lord'] ?? null,
        star_lord: cusp['star_lord'] ?? null,
        sub_lord: cusp['sub_lord'] ?? null,
        sub_sub_lord: cusp['sub_sub_lord'] ?? null,
        significators: cusp['significators'] ?? null,
        fact_ids,
      })
      for (const f of fact_ids) out.fact_ids.push(f)
    }
    out.cusps.sort((a, b) => houses.indexOf(a.house) - houses.indexOf(b.house))
  } catch {
    // non-fatal: leg degrades to honest not-computed upstream.
  }
  return out
}

// ── Leg 3: gochara forecast sweep (MC-033) ────────────────────────────────────

export interface GocharaSweepWindow {
  event_class: string
  temporal_shape: string | null
  window_start: string | null
  window_end: string | null
  peak_date: string | null
  valence: string | null
  is_adverse: boolean | null
}

export interface GocharaSweepResult {
  domain_covered: boolean
  upcoming_window_count: number
  windows: GocharaSweepWindow[]
  valence_breakdown: Record<string, number>
  window_range: { start: string; end: string }
  note: string
  available: boolean
}

/**
 * Forward-looking gochara (transit) sweep for a domain, joined into the reading by
 * default (MC-033: the sweep was never folded into a domain reading). Reads the
 * kala_gochara_windows signed-intensity field (D-5 G-4) domain-scoped via
 * brahma_event_ontology — READ-ONLY (the table + its writer are untouchable rails);
 * returns a COMPACT summary (top windows by |intensity| + a valence tally), never a
 * full window dump. The raw signed_intensity magnitudes are the D-5 lambda field's
 * own units and are intentionally NOT surfaced here (drill gochara_forecast_get).
 */
export async function fetchGocharaSweep(
  chart_id: string,
  signal_domain: string,
  as_of_date: string,
  horizon_years = 3,
): Promise<GocharaSweepResult> {
  const start = as_of_date
  const endD = new Date(as_of_date + 'T00:00:00Z')
  endD.setUTCFullYear(endD.getUTCFullYear() + horizon_years)
  const end = endD.toISOString().slice(0, 10)
  const out: GocharaSweepResult = {
    domain_covered: false,
    upcoming_window_count: 0,
    windows: [],
    valence_breakdown: {},
    window_range: { start, end },
    available: false,
    note: 'Forward gochara (transit) sweep over the kala_gochara_windows signed-intensity ' +
      'field, domain-scoped (MC-033). Compact top-by-magnitude summary + valence tally; ' +
      'drill gochara_forecast_get for the full window set with signed intensities.',
  }
  try {
    // Coverage probe: does this chart carry ANY gochara windows in the domain at all?
    const covRes = await query<{ n: string }>(
      `SELECT COUNT(*)::text AS n
         FROM kala_gochara_windows w
         JOIN brahma_event_ontology eo ON eo.event_class_id = w.event_class
        WHERE w.chart_id = $1 AND eo.domain = $2`,
      [chart_id, signal_domain],
    )
    const domainTotal = Number(covRes.rows[0]?.n ?? 0)
    out.available = true // the query ran; table is reachable
    out.domain_covered = domainTotal > 0
    if (!out.domain_covered) return out

    const res = await query<{
      event_class: string; temporal_shape: string | null
      window_start: string | null; window_end: string | null; peak_date: string | null
      valence: string | null; is_adverse: boolean | null
    }>(
      `SELECT w.event_class, w.temporal_shape, w.window_start, w.window_end, w.peak_date,
              w.valence, w.is_adverse
         FROM kala_gochara_windows w
         JOIN brahma_event_ontology eo ON eo.event_class_id = w.event_class
        WHERE w.chart_id = $1 AND eo.domain = $2
          AND w.window_end >= $3 AND w.window_start <= $4
        ORDER BY ABS(w.signed_intensity) DESC NULLS LAST
        LIMIT 200`,
      [chart_id, signal_domain, start, end],
    )
    out.upcoming_window_count = res.rows.length
    for (const r of res.rows) {
      const v = r.valence ?? 'unknown'
      out.valence_breakdown[v] = (out.valence_breakdown[v] ?? 0) + 1
    }
    out.windows = res.rows.slice(0, 5).map(r => ({
      event_class: r.event_class,
      temporal_shape: r.temporal_shape,
      window_start: r.window_start,
      window_end: r.window_end,
      peak_date: r.peak_date,
      valence: r.valence,
      is_adverse: r.is_adverse,
    }))
  } catch {
    // non-fatal: leg degrades to honest not-computed upstream.
  }
  return out
}
