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
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '@/lib/retrieval/address_resolver'
import { CANONICAL_DOMAINS } from '@/lib/domain_vocabulary'

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

/** sensitive_degree_check fact_subject code → classical graha display name.
 *  Values sourced from the graha SSoT (address_resolver.grahaCodeOf +
 *  GRAHA_CODE_TO_NAME) rather than hardcoded literals — ADHIṢṬHĀNA Lane A2. */
const SENSITIVE_SUBJECT_TO_GRAHA: Record<string, string> = Object.fromEntries(
  ['SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN']
    .map(code => [code, GRAHA_CODE_TO_NAME[grahaCodeOf(code)]]),
)

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

// ── F-107 (PARIŚEṢA-V4, CL-20): the domain → classical-varga registry ─────────
// MOVED here from register_d8_assess_domain.ts (which now re-exports it, so every
// existing import path and the Lane-E CI rule keep working unchanged). It lives in
// this leaf module so BOTH assess_* (register_d8) and judgment_query (register_d9)
// can read ONE registry rather than each carrying its own copy — register_d8 already
// imports SHASTRA_MAP from register_d9, so a direct d9→d8 import would be a cycle,
// and a second local copy would be a GA.1-class registry disagreement (CLAUDE.md §B.8).
//
// NOTE the deliberate asymmetry this registry makes visible: SHASTRA_MAP (register_d9)
// gives each domain exactly ONE *operative* varga — the one whose bhāveśa/kāraka dignity
// is weighted into judgment_query's verdict. This registry gives the FULL classical varga
// set for the domains that have more than one. Wealth is the case that matters: BPHS
// Ch.6-7 assigns dhana (accumulated wealth) to D2 Horā and lābha (gains/income) to D11
// Rudrāṃśa/Ekādaśāṃśa — two distinct arthas, two distinct vargas. judgment_query weights
// only D2. That is a real, defensible scoping choice; what was NOT acceptable was leaving
// it undisclosed, so callers could read a D2-weighted verdict as a full cross-varga
// wealth judgment (F-107).

// ── F-164 (+ F-158) — live-read replacement for the wrapper-local operative-varga literal ──
// DOMAIN_DIRECT_VARGAS (below) and two prose literals (query_mechanisms.ts's varga_scope
// note, register_d9_judgment.ts's cross_varga_convergence_not_computed flag text) all
// hand-copied a wealth ['D1','D2','D9','D11']-shaped literal that had drifted from the live
// source (brahma_vichara_constants.operative_vargas, migrations/435_ga_vichara.sql) — and
// the drift was not wealth-only: career was missing D9, health was missing D9, relationship
// was missing D7, and wealth itself was missing D9 (F-107's GA-5 review finding on #1419).
// Fixed by reading the constants row live and caching it — this is chart-agnostic global
// config (same for every chart), safe to cache for the process lifetime — and FAILING LOUDLY
// if the row is ever missing, never silently falling back to a stale literal (§N.7 item 3).
export interface OperativeVargaEntry {
  vargas: string[]
  provisional: boolean
  houses: number[]
  karaka: string
}

// SHASTRA_MAP's signal_domain vocabulary (wealth, career, relationship, health) disagrees
// with brahma_vichara_constants.operative_vargas' OWN domain-key vocabulary (wealth, career,
// MARRIAGE, health, general) for exactly one domain. Translated here, once — never smuggled
// into a second hand-copy again. Exported so F-160 (chart_vichara.varga_ratification's
// `domain` column uses the SAME vocabulary) can reuse it rather than re-deriving.
export const SIGNAL_DOMAIN_TO_VICHARA_DOMAIN: Record<string, string> = {
  wealth: 'wealth',
  career: 'career',
  relationship: 'marriage',
  health: 'health',
}

let operativeVargaConstantsCache: Record<string, OperativeVargaEntry> | null = null
let operativeVargaConstantsLoading: Promise<Record<string, OperativeVargaEntry>> | null = null

/**
 * Live read of brahma_vichara_constants.operative_vargas — the RAW registry row, in ITS
 * OWN domain-key vocabulary (wealth/career/marriage/health/general), each entry INCLUDING
 * D1. Cached after the first successful read (global config, not per-chart — never varies
 * by chart_id/ayanamsha_id). Throws if the constants row is missing rather than degrading
 * to a stale hardcoded literal — an honest 500 beats a silently wrong varga set (§N.7 item 3).
 */
export async function getOperativeVargaConstants(): Promise<Record<string, OperativeVargaEntry>> {
  if (operativeVargaConstantsCache) return operativeVargaConstantsCache
  if (!operativeVargaConstantsLoading) {
    operativeVargaConstantsLoading = (async () => {
      const res = await query<{ value_jsonb: Record<string, unknown> }>(
        `SELECT value_jsonb FROM brahma_vichara_constants WHERE constant_key = $1`,
        ['operative_vargas'],
      )
      const row = res.rows[0]
      if (!row?.value_jsonb) {
        throw new Error(
          "F-164: brahma_vichara_constants row 'operative_vargas' is missing — refusing to " +
          'silently fall back to a stale hardcoded varga literal (CLAUDE.md §N.7 item 3). ' +
          'Verify migration 435_ga_vichara.sql has been applied.',
        )
      }
      operativeVargaConstantsCache = row.value_jsonb as unknown as Record<string, OperativeVargaEntry>
      return operativeVargaConstantsCache
    })().catch(err => {
      // Do not cache a failure forever — the next call gets a fresh retry.
      operativeVargaConstantsLoading = null
      throw err
    })
  }
  return operativeVargaConstantsLoading
}

/** Domain → the full classical varga set for that domain (superset of SHASTRA_MAP's
 *  single operative varga), MINUS D1 (D1 is the reference, never a voter — mirrors
 *  ga_vichara_writer.py:582-583's rule). Consumed directly from L1 by assess_* (EL-45);
 *  disclosed but NOT weighted by judgment_query (F-107).
 *
 *  F-164: this used to be a hand-copied literal. It now starts EMPTY and is populated
 *  in place by `ensureDomainDirectVargasLoaded()` — every existing `DOMAIN_DIRECT_VARGAS
 *  [domain]` read site keeps working unchanged, PROVIDED the request's handler awaits
 *  `ensureDomainDirectVargasLoaded()` at least once before any synchronous read (both
 *  `register_d8_assess_domain.ts`'s `buildVargaAnalysisDirect` and `register_d9_judgment.ts`'s
 *  per-domain handler do this — see their call sites). An unloaded read honestly returns
 *  `undefined`/`[]` rather than a stale value; it never silently ships wrong data. */
export const DOMAIN_DIRECT_VARGAS: Record<string, string[]> = {}

/**
 * F-164 — hydrates DOMAIN_DIRECT_VARGAS in place from the live constants row. Cheap to call
 * on every request (the underlying constants read is cached after the first success).
 */
export async function ensureDomainDirectVargasLoaded(): Promise<Record<string, string[]>> {
  const constants = await getOperativeVargaConstants()
  for (const [signalDomain, vicharaDomain] of Object.entries(SIGNAL_DOMAIN_TO_VICHARA_DOMAIN)) {
    const entry = constants[vicharaDomain]
    DOMAIN_DIRECT_VARGAS[signalDomain] = (entry?.vargas ?? []).filter(v => v !== 'D1')
  }
  return DOMAIN_DIRECT_VARGAS
}

/** Domains carrying a dedicated special-lagna leg. Indu Lagna (Jaimini; computed from
 *  the 9th-lord kalās of Lagna + Moon) is the wealth-strength lagna — a wealth indicator
 *  independent of the 2nd/11th house-and-lord reading. Stored two_pass_verified in
 *  chart_facts (fact_category='special_lagna', fact_subject='INDU_LAGNA'). Unrelated to
 *  brahma_vichara_constants (a special lagna is not a varga and casts no ratification
 *  vote — F-107) — left as a static registry, not part of this pass's live-read scope. */
export const DOMAIN_INDU_LAGNA = new Set(['wealth'])

/**
 * F-107 — which classical vargas a domain has that judgment_query does NOT weight into
 * its verdict, given the single operative varga SHASTRA_MAP assigns it. Empty array when
 * the operative varga already covers the domain's whole classical varga set. Reads
 * DOMAIN_DIRECT_VARGAS synchronously — callers MUST await `ensureDomainDirectVargasLoaded()`
 * at least once per request first (F-164).
 */
export function corroboratingVargasNotWeighted(domain: string, operativeVarga: string): string[] {
  return (DOMAIN_DIRECT_VARGAS[domain] ?? []).filter(v => v !== operativeVarga)
}

// ── F-160 — the real varga_confirmed detector ─────────────────────────────────────────
// `judgment_query`'s old `varga_confirmed` was a bare `chart_divisionals` placement-row
// presence check — never "does the varga RATIFY the D1 direction". The real detector is
// chart_vichara.varga_ratification's per-graha agree/oppose vote
// (ga_vichara_writer.py::build_varga_ratification_rows). Extracted to its own function
// (rather than inlined in register_d9_judgment.ts's giant handler) so it is unit-testable
// against a single mocked query, independent of judgment_query's dozen other DB calls.
export type VargaRatificationRelation = 'agree' | 'oppose' | 'abstain' | 'abstain_missing' | 'no_row'

export interface VargaRatificationSubjectResult {
  role: string
  subject: string
  relation: VargaRatificationRelation
}

export interface VargaRatificationResult {
  /** Aggregated across all subjects: 'oppose' (any subject opposes) beats 'agree' (any
   *  subject agrees) beats 'abstain' beats 'abstain_missing' beats 'no_row' — a genuine
   *  contradiction is the most decisive finding and must never be masked by another
   *  subject's agreement. */
  relation: VargaRatificationRelation
  per_subject: VargaRatificationSubjectResult[]
  /** value_jsonb.domain_provisional from whichever row supplied one (all rows for a given
   *  domain carry the same value) — null when no row was found at all. */
  domain_provisional: boolean | null
  /** false only when the query itself threw — distinct from a genuinely empty/no-vote
   *  result (a domain outside brahma_vichara_constants' scope, e.g. 'character', is an
   *  honest 'no_row' with ok:true, not a failure). */
  ok: boolean
}

/**
 * Live read of chart_vichara.varga_ratification for one bhāva's bhāveśa/kāraka(s) against
 * ONE operative varga, for the given signal_domain (translated to
 * brahma_vichara_constants' own domain-key vocabulary via SIGNAL_DOMAIN_TO_VICHARA_DOMAIN).
 * Never throws — a query failure degrades to the honest 'no_row' state for every subject
 * (the caller emits its own judgment_flag on catch; this function's job is just the read +
 * aggregation, mirroring fetchKpCuspChain/fetchSensitiveDegreeFirings's non-fatal-degrade
 * convention above).
 */
export async function fetchVargaRatification(
  chart_id: string,
  ayanamsha_id: string,
  signalDomain: string,
  varga: string,
  subjects: Array<{ role: string; code: string }>,
): Promise<VargaRatificationResult> {
  const per_subject: VargaRatificationSubjectResult[] = subjects.map(s => ({
    role: s.role, subject: s.code, relation: 'no_row' as VargaRatificationRelation,
  }))
  let domain_provisional: boolean | null = null
  let ok = true
  try {
    const vicharaDomain = SIGNAL_DOMAIN_TO_VICHARA_DOMAIN[signalDomain] ?? signalDomain
    const subjectCodes = Array.from(new Set(subjects.map(s => s.code)))
    if (subjectCodes.length > 0) {
      const res = await query<{ subject: string; value_jsonb: Record<string, unknown> | null }>(
        `SELECT subject, value_jsonb FROM chart_vichara
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND vichara_family = 'varga_ratification'
           AND domain = $3 AND subject = ANY($4)`,
        [chart_id, ayanamsha_id, vicharaDomain, subjectCodes],
      )
      const bySubject = new Map(res.rows.map(r => [r.subject, r.value_jsonb]))
      for (const entry of per_subject) {
        const valueJsonb = bySubject.get(entry.subject)
        const perVarga = (valueJsonb?.['per_varga'] as Record<string, unknown> | undefined)?.[varga] as
          { relation?: string } | undefined
        entry.relation = (perVarga?.relation as VargaRatificationRelation | undefined) ?? 'no_row'
        if (typeof valueJsonb?.['domain_provisional'] === 'boolean') {
          domain_provisional = valueJsonb['domain_provisional'] as boolean
        }
      }
    }
  } catch {
    // Non-fatal: every subject stays 'no_row' (honest unknown) — `ok:false` lets the caller
    // distinguish this genuine failure from a domain that legitimately has no ratification
    // vote (out of brahma_vichara_constants' scope), which is also 'no_row' but ok:true.
    ok = false
  }
  const relation: VargaRatificationRelation =
    per_subject.some(s => s.relation === 'oppose') ? 'oppose'
    : per_subject.some(s => s.relation === 'agree') ? 'agree'
    : per_subject.some(s => s.relation === 'abstain') ? 'abstain'
    : per_subject.some(s => s.relation === 'abstain_missing') ? 'abstain_missing'
    : 'no_row'
  return { relation, per_subject, domain_provisional, ok }
}

/** The served varga_confirmed mark for a VargaRatificationResult. 'oppose' gets a mark
 *  DISTINCT from a bare ✗ — it is itself a finding (the varga actively contradicts D1), not
 *  an absence of evidence. 'abstain'/'abstain_missing'/'no_row' are an honest unknown, never
 *  defaulted to ✓ or ✗ (F-160). */
export function vargaConfirmedMark(varga: string, relation: VargaRatificationRelation): string {
  if (relation === 'agree') return `${varga}✓ (varga_ratification: agrees with D1)`
  if (relation === 'oppose') return `${varga}✗! (varga_ratification: CONTRADICTS D1 — see varga_ratification_per_subject)`
  return `${varga}? (varga did not vote)`
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
  is_past_peak: boolean | null   // null when peak_date is null (honest "can't tell")
}

export interface GocharaSweepResult {
  domain_covered: boolean
  // GA-5 review finding on #1384: this counts every window matching the overlap query,
  // INCLUDING already-peaked ones -- it is a raw match count, not "still upcoming" in the
  // literal sense the name suggests. past_peak_window_count below is a SUBSET of this
  // number, not a disjoint sibling count -- see the served `note` field for the same
  // disclosure in the response itself.
  upcoming_window_count: number
  past_peak_window_count: number
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
    past_peak_window_count: 0,
    windows: [],
    valence_breakdown: {},
    window_range: { start, end },
    available: false,
    note: 'Forward gochara (transit) sweep over the kala_gochara_windows signed-intensity ' +
      'field, domain-scoped (MC-033). Compact top-by-magnitude summary + valence tally; ' +
      'drill gochara_forecast_get for the full window set with signed intensities. ' +
      'upcoming_window_count is every window matching this overlap query -- past_peak_window_count ' +
      'is a SUBSET of it (windows whose peak already fell before as_of_date), not a separate ' +
      'count; a window can be counted in both fields at once. Check each windows[] entry\'s ' +
      'own is_past_peak before treating it as still-actionable timing.',
  }
  try {
    // Coverage probe: does this chart carry ANY gochara windows in the domain at all?
    // ADJUDICATION-6 (migration 527): scoped to the chart's currently-authoritative
    // generation — an absent kala_gochara_authority row means 'v1' by definition, so
    // this is byte-identical to the pre-527 query until a 2.0 writer lands rows and a
    // chart's authority is actually flipped.
    const covRes = await query<{ n: string }>(
      `SELECT COUNT(*)::text AS n
         FROM kala_gochara_windows w
         JOIN brahma_event_ontology eo ON eo.event_class_id = w.event_class
        WHERE w.chart_id = $1 AND eo.domain = $2
          AND w.generation = COALESCE(
                (SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = w.chart_id),
                'v1')`,
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
          AND w.generation = COALESCE(
                (SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = w.chart_id),
                'v1')
        ORDER BY ABS(w.signed_intensity) DESC NULLS LAST
        LIMIT 200`,
      [chart_id, signal_domain, start, end],
    )
    out.upcoming_window_count = res.rows.length
    const isPastPeak = (peakDate: string | null): boolean | null =>
      peakDate === null ? null : peakDate < start
    out.past_peak_window_count = res.rows.filter(r => isPastPeak(r.peak_date) === true).length
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
      is_past_peak: isPastPeak(r.peak_date),
    }))
  } catch {
    // non-fatal: leg degrades to honest not-computed upstream.
  }
  return out
}

// ── F-165 (PARIŚEṢA-V4): domain-population structural-emptiness disclosure ──────────────
//
// F-57 fixed VOCABULARY correctness: is `resolved_signal_domain` a real member of the
// canonical 13-domain vocabulary. This is a DIFFERENT axis, POPULATION: does either source
// table that judgment_query's threat layer reads (bodha_msr_signals / bodha_mechanisms) carry
// ANY row at all — of any valence — tagged with that domain, for this chart. 'general' is
// vocabulary-exact and canonical, and (measured live against the canonical chart 482012f1 on
// 2026-08-22) carries ZERO bodha_msr_signals rows; bodha_mechanisms carries rows for only 1 of
// the 13 canonical domains ('wealth'). Neither fact is visible from is_exact/is_canonical
// alone, so an `afflictions_empty` result for either domain reads as a genuine all-clear when
// it is actually "this store has never been populated for this tag" — conflating the two axes
// is exactly the flattening §N.6 forbids.
//
// The counts here are ALWAYS a real live query against the two source tables for this specific
// chart_id/ayanamsha_id/signal_domain — never a hardcoded list of domains known (at plan time)
// to be empty. A hardcoded list is a constant that drifts the moment either store gains rows
// for a previously-empty domain (§N.7 item 3), and would itself be the §N.8 defect this finding
// closes: a signal ("this domain is unpopulated") whose detector never actually re-measures the
// claim it makes.
export interface DomainStructuralCoverageResult {
  /** Total bodha_msr_signals rows tagged with this domain, ANY valence (not just malefic/mixed). */
  msr_signals: number
  /** Total bodha_mechanisms rows tagged with this domain, ANY valence. */
  mechanisms: number
  /** How many of the 13 canonical domains bodha_mechanisms carries at least one row for, chart-wide. */
  mechanisms_domain_coverage: number
  /** Size of the canonical domain vocabulary (13) — the denominator for mechanisms_domain_coverage. */
  total_canonical_domains: number
  /** true iff BOTH source tables carry zero rows for this domain — the F-165 disclosure trigger. */
  structurally_unpopulated: boolean
  /** true iff the coverage query actually ran; false means "could not measure", not "measured zero". */
  available: boolean
}

export async function fetchDomainStructuralCoverage(
  chart_id: string,
  ayanamsha_id: string,
  signal_domain: string,
): Promise<DomainStructuralCoverageResult> {
  const out: DomainStructuralCoverageResult = {
    msr_signals: 0,
    mechanisms: 0,
    mechanisms_domain_coverage: 0,
    total_canonical_domains: CANONICAL_DOMAINS.length,
    structurally_unpopulated: false,
    available: false,
  }
  try {
    const res = await query<{ msr_count: number; mech_count: number; mech_domain_coverage: number }>(
      `WITH msr AS (
         SELECT count(*)::int AS c FROM bodha_msr_signals
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND $3 = ANY(domains_affected_array)
       ), mech AS (
         SELECT count(*)::int AS c FROM bodha_mechanisms
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND $3 = ANY(domains_affected_array)
       ), mech_domains AS (
         SELECT count(DISTINCT d)::int AS c FROM (
           SELECT unnest(domains_affected_array) AS d FROM bodha_mechanisms
            WHERE chart_id = $1 AND ayanamsha_id = $2
         ) s
       )
       SELECT msr.c AS msr_count, mech.c AS mech_count, mech_domains.c AS mech_domain_coverage
         FROM msr, mech, mech_domains`,
      [chart_id, ayanamsha_id, signal_domain],
    )
    const row = res.rows[0]
    if (row) {
      out.msr_signals = row.msr_count
      out.mechanisms = row.mech_count
      out.mechanisms_domain_coverage = row.mech_domain_coverage
      out.structurally_unpopulated = row.msr_count === 0 && row.mech_count === 0
      out.available = true
    }
  } catch {
    // non-fatal: leg degrades to "could not measure" (available: false) — never a fabricated
    // zero or a fabricated "populated" claim (B.10).
  }
  return out
}
