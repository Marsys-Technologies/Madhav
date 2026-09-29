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
import { resolvedBuildFenceIds, resolvedRowsBuildId, ExplicitEmptyBuildFenceError, classifyBuildFence, type BuildFence, type ChartServedGeneration, type UnresolvedGenerationReason } from '../generation/served_generation'

// ── The checklist vocabulary (design §28.6, generalized) ──────────────────────

/** The honest state of one classical unit in a served response. */
export type ChecklistState =
  | 'served' //               this unit's data is present in THIS response
  | 'empty_for_this_chart' //  computed, but no rows fired/exist for this chart (a finding, not a gap)
  | 'not_applicable' //        this classical unit does not apply to the resolved domain
  | 'not_computed' //          the underlying L1/L2/L3 asset does not exist for this chart yet
  | 'not_joined' //            the data exists but this instrument does not fold it in (drill handle given)
  | 'salience_floored' //      exists + reachable but ranked below the served cut on salience surfaces
  | 'not_yet_available' //     the producing asset is being built in a parallel track (T6 yogi/avayogi)
  | 'source_unproven' //       a required source leg could not be proven for this response
  | 'source_incomplete' //     a fixed-shape required source leg was missing or duplicated
  | 'materially_trimmed' //    response budgeting removed material evidence from this unit

export interface ChecklistUnit {
  unit: string
  state: ChecklistState
  detail?: string
  /** Live drill handle (tool name) a caller invokes to hydrate this unit when not served inline. */
  drill?: string
  count?: number
}

/**
 * v2 is deliberately an exact set, rather than a response-controlled denominator.
 * A handler may disclose that a unit is not applicable, but it may not omit it and
 * then call a smaller self-selected checklist complete.
 */
export const JUDGMENT_READING_CHECKLIST_V2_UNITS = [
  'bhava_bhavesha_from_lagna',
  'bhava_bhavesha_from_chandra',
  'karakas',
  'operative_varga',
  'corroborating_vargas',
  'ashtakavarga',
  'special_lagnas',
  'sensitive_degree_firings',
  'kp_cusp_chain',
  'yogi_avayogi',
  'bearing_yogas',
  'bearing_afflictions',
  'notably_absent_yogas',
  'dasha_levels',
  'gochara_sweep',
  'tajaka',
] as const

export const JUDGMENT_READING_CHECKLIST_V2_CONTRACT = {
  contract_id: 'judgment-reading-checklist-v2',
  required_units: JUDGMENT_READING_CHECKLIST_V2_UNITS,
} as const

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
  const settled = new Set<ChecklistState>(['served', 'empty_for_this_chart', 'not_applicable'])
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

// ── Wealth completion: source-receipt fence ────────────────────────────────────

/**
 * The finite producer set behind the Batch 5A wealth pivots.  Every served
 * cross-varga, Ashtakavarga, special-lagna, or yogi/avayogi row must belong to
 * the chart's served generation (each producer's own writing run) and each
 * producer must still have its current output-digest receipt.  This is a consumption boundary only: it
 * neither dispatches nor repairs a producer.
 */
export const WEALTH_READING_REQUIRED_ASSETS = [
  'ga_structural',
  'ga_vichara',
  'ga_sensitive',
  'ga_sensitive_degree',
  'ga_strength',
] as const

export interface WealthReadingSourceFenceAsset {
  asset_id: typeof WEALTH_READING_REQUIRED_ASSETS[number]
  /** The asset's receipt resolves to the chart's served generation (proven, fresh, current
   *  spec, completed run, provable writing run). Name retained for wire compatibility. */
  receipt_matches_selected_build: boolean
  /** The typed served-generation refusal when the receipt does not resolve, else null. */
  served_generation_reason: UnresolvedGenerationReason | null
  replacement_in_progress: boolean
}

export interface WealthReadingSourceFence {
  /** False only when the snapshot query itself failed. */
  ok: boolean
  /** True only when every named producer resolves to the chart's served generation and no
   * replacement can have invalidated it. */
  ready: boolean
  assets: WealthReadingSourceFenceAsset[]
}

interface SourceReceiptFenceAsset {
  asset_id: string
  receipt_matches_selected_build: boolean
  served_generation_reason: UnresolvedGenerationReason | null
  replacement_in_progress: boolean
}

interface SourceReceiptFence {
  ok: boolean
  ready: boolean
  assets: SourceReceiptFenceAsset[]
}

/**
 * Reads all five producer receipt states and their replacement fences from a
 * single statement snapshot.  A current asset-output digest spec is joined to
 * each receipt, so a source revision (notably ga_strength's wealth AV spec)
 * requires a rebuilt receipt before it can be served.  A planned/running/
 * paused producer or a terminal mutation at/after the selected receipt stays
 * unavailable unless that run itself carries a fresh, proven current receipt.
 */
async function fetchSourceReceiptFence(
  chart_id: string,
  generation: ChartServedGeneration,
  requiredAssets: readonly string[],
): Promise<SourceReceiptFence> {
  const unavailable = (ok: boolean): SourceReceiptFence => ({
    ok,
    ready: false,
    assets: requiredAssets.map(asset_id => ({
      asset_id,
      receipt_matches_selected_build: false,
      served_generation_reason: null,
      replacement_in_progress: false,
    })),
  })
  try {
    const res = await query<{
      asset_id: string
      receipt_matches_selected_build: boolean
      replacement_in_progress: boolean
    }>(
      `WITH required_assets AS (
         SELECT unnest($1::text[]) AS asset_id
       ), selected_receipts AS (
         SELECT DISTINCT ON (receipt.asset_id)
                receipt.asset_id,
                receipt.observed_at
           FROM asset_provenance_receipts receipt
           JOIN asset_freshness freshness
             ON freshness.asset_id = receipt.asset_id
            AND freshness.scope_key = receipt.scope_key
            AND freshness.partition_key = receipt.partition_key
            AND freshness.receipt_version = receipt.receipt_version
           JOIN asset_output_digest_specs digest_spec
             ON digest_spec.asset_id = receipt.asset_id
            AND digest_spec.spec_sha256 = receipt.output_digest_spec_sha256
            AND digest_spec.retired_at IS NULL
          WHERE receipt.asset_id = ANY($1::text[])
            AND receipt.chart_id = $2::uuid
            AND receipt.receipt_state = 'proven'
            AND freshness.freshness_state = 'fresh'
          -- The fence compares against the OLDEST eligible partition receipt: an attempt that
          -- ended after it may have rewritten that partition's rows even if a newer partition
          -- receipt exists.
          ORDER BY receipt.asset_id, receipt.observed_at ASC
       )
       SELECT required_asset.asset_id,
              selected.asset_id IS NOT NULL AS receipt_matches_selected_build,
              EXISTS (
                SELECT 1
                  FROM build_run_assets fenced_asset
                  JOIN build_runs fenced_run ON fenced_run.id = fenced_asset.run_id
                 WHERE fenced_run.chart_id = $2::uuid
                   AND fenced_asset.asset_id = required_asset.asset_id
                   AND (
                     fenced_run.state IN ('planned', 'running', 'paused')
                     OR (
                       -- A queued row that a terminal run never dispatched cannot have
                       -- mutated served rows; it is orphan hygiene, not replacement work.
                       NOT (fenced_asset.state = 'queued' AND fenced_asset.started_at IS NULL)
                       AND selected.observed_at IS NOT NULL
                       AND COALESCE(fenced_asset.ended_at, fenced_run.ended_at) >= selected.observed_at
                       AND NOT EXISTS (
                         SELECT 1
                           FROM asset_provenance_receipts proven_receipt
                           JOIN asset_freshness proven_freshness
                             ON proven_freshness.asset_id = proven_receipt.asset_id
                            AND proven_freshness.scope_key = proven_receipt.scope_key
                            AND proven_freshness.partition_key = proven_receipt.partition_key
                            AND proven_freshness.receipt_version = proven_receipt.receipt_version
                           JOIN asset_output_digest_specs proven_spec
                             ON proven_spec.asset_id = proven_receipt.asset_id
                            AND proven_spec.spec_sha256 = proven_receipt.output_digest_spec_sha256
                            AND proven_spec.retired_at IS NULL
                          WHERE proven_receipt.asset_id = fenced_asset.asset_id
                            AND proven_receipt.chart_id = $2::uuid
                            AND proven_receipt.build_id = fenced_run.id
                            AND proven_receipt.receipt_state = 'proven'
                            AND proven_freshness.freshness_state = 'fresh'
                       )
                     )
                   )
              ) AS replacement_in_progress
         FROM required_assets required_asset
         LEFT JOIN selected_receipts selected ON selected.asset_id = required_asset.asset_id
        ORDER BY required_asset.asset_id ASC`,
      [[...requiredAssets], chart_id],
    )
    const byAsset = new Map(res.rows.map(row => [row.asset_id, row]))
    const assets = requiredAssets.map(asset_id => {
      const row = byAsset.get(asset_id)
      // Each producer is fenced to its OWN served generation, never to one chart-wide run:
      // the five wealth producers are routinely rebuilt by separate single-asset runs.
      const binding = generation.assets[asset_id]
      return {
        asset_id,
        receipt_matches_selected_build: row?.receipt_matches_selected_build === true && binding?.state === 'resolved',
        served_generation_reason: binding === undefined ? 'no_chart_receipt' as const
          : binding.state === 'unresolved' ? binding.reason : null,
        replacement_in_progress: row?.replacement_in_progress === true,
      }
    })
    return {
      ok: true,
      ready: assets.every(asset => asset.receipt_matches_selected_build && !asset.replacement_in_progress),
      assets,
    }
  } catch {
    return unavailable(false)
  }
}

export async function fetchWealthReadingSourceFence(
  chart_id: string,
  generation: ChartServedGeneration,
): Promise<WealthReadingSourceFence> {
  const fence = await fetchSourceReceiptFence(chart_id, generation, WEALTH_READING_REQUIRED_ASSETS)
  return {
    ...fence,
    assets: fence.assets.map(asset => ({
      ...asset,
      asset_id: asset.asset_id as typeof WEALTH_READING_REQUIRED_ASSETS[number],
    })),
  }
}

/** ga_tajaka is an independent annual producer, so it has its own current-spec receipt
 * fence rather than borrowing the natal wealth pivot's five-producer fence. */
export async function fetchTajakaSourceFence(
  chart_id: string,
  generation: ChartServedGeneration,
): Promise<SourceReceiptFence> {
  return fetchSourceReceiptFence(chart_id, generation, ['ga_tajaka'])
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
  build_id?: BuildFence,
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
          AND fact_key = ANY($3)
          ${build_id ? 'AND build_id = ANY($4::uuid[])' : ''}`,
      build_id
        ? [chart_id, ayanamsha_id, [...HIGH_SIGNAL_SENSITIVE_CHECKS], resolvedBuildFenceIds(build_id, 'reading_checklist.fetchSensitiveDegreeFirings')]
        : [chart_id, ayanamsha_id, [...HIGH_SIGNAL_SENSITIVE_CHECKS]],
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
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
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
  build_id?: BuildFence,
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
           AND domain = $3 AND subject = ANY($4)
           ${build_id ? 'AND build_id = ANY($5::uuid[])' : ''}`,
        build_id
          ? [chart_id, ayanamsha_id, vicharaDomain, subjectCodes, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchVargaRatification')]
          : [chart_id, ayanamsha_id, vicharaDomain, subjectCodes],
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
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
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

export const WEALTH_CORROBORATING_VARGAS = ['D9', 'D11'] as const
export const WEALTH_ASHTAKAVARGA_VARGAS = ['D2', 'D9', 'D11'] as const
export const WEALTH_ASHTAKAVARGA_HOUSES = [2, 11] as const
export const WEALTH_SPECIAL_LAGNAS = ['INDU_LAGNA', 'SREE_LAGNA', 'HORA_LAGNA'] as const
export const WEALTH_SPECIAL_LAGNA_KEYS = [
  'longitude_sidereal', 'sign', 'sign_lord', 'nakshatra', 'nakshatra_lord', 'pada', 'house_d1',
] as const
export const WEALTH_YOGI_SUBJECT_KEYS = {
  YOGI: ['point_longitude', 'sign', 'nakshatra', 'assigned_graha'],
  AVAYOGI: ['point_longitude', 'sign', 'nakshatra', 'assigned_graha'],
  DUPLICATE_YOGI: ['sign', 'assigned_graha'],
  SAHAYOGI: ['sign', 'assigned_graha'],
} as const

export interface WealthCorroboratingVargaResult {
  state: 'served' | 'source_incomplete' | 'source_unproven'
  rows: Array<{ role: string; subject: string; varga: typeof WEALTH_CORROBORATING_VARGAS[number]; relation: VargaRatificationRelation; source_id: string; constituent_fact_ids: string[] }>
  fact_ids: string[]
}

/** Fixed-shape wealth corroboration: two named actors times D9/D11.  The caller must
 * establish the shared selected-build receipt fence before calling this reader. */
export async function fetchWealthCorroboratingVargas(
  chart_id: string,
  ayanamsha_id: string,
  subjects: Array<{ role: string; code: string }>,
  build_id: BuildFence,
): Promise<WealthCorroboratingVargaResult> {
  const uniqueSubjects = [...new Map(subjects.map(subject => [subject.code, subject])).values()]
  const codes = uniqueSubjects.map(subject => subject.code)
  if (codes.length === 0) return { state: 'source_incomplete', rows: [], fact_ids: [] }
  try {
    const res = await query<{ id: string; subject: string; value_jsonb: Record<string, unknown> | null; constituent_fact_ids: string[] | null }>(
      `SELECT id::text AS id, subject, value_jsonb, constituent_fact_ids
         FROM chart_vichara
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND build_id = ANY($3::uuid[]) AND vichara_family = 'varga_ratification'
          AND domain = 'wealth' AND subject = ANY($4)
        ORDER BY subject ASC, id ASC`,
      [chart_id, ayanamsha_id, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchWealthCorroboratingVargas'), codes],
    )
    const bySubject = new Map<string, typeof res.rows>()
    for (const row of res.rows) bySubject.set(row.subject, [...(bySubject.get(row.subject) ?? []), row])
    const rows: WealthCorroboratingVargaResult['rows'] = []
    for (const subject of uniqueSubjects) {
      const matches = bySubject.get(subject.code) ?? []
      if (matches.length !== 1) return { state: 'source_incomplete', rows: [], fact_ids: [] }
      const row = matches[0]!
      const perVarga = row.value_jsonb?.['per_varga'] as Record<string, { relation?: string }> | undefined
      for (const varga of WEALTH_CORROBORATING_VARGAS) {
        const relation = perVarga?.[varga]?.relation
        if (!['agree', 'oppose', 'abstain', 'abstain_missing', 'no_row'].includes(String(relation))) {
          return { state: 'source_incomplete', rows: [], fact_ids: [] }
        }
        rows.push({ role: subject.role, subject: subject.code, varga, relation: relation as VargaRatificationRelation, source_id: row.id, constituent_fact_ids: row.constituent_fact_ids ?? [] })
      }
    }
    return { state: 'served', rows, fact_ids: [...new Set(rows.flatMap(row => row.constituent_fact_ids))].sort() }
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
    return { state: 'source_unproven', rows: [], fact_ids: [] }
  }
}

export interface WealthAshtakavargaResult {
  state: 'served' | 'source_incomplete' | 'source_unproven'
  rows: Array<{ fact_id: string; fact_category: string; fact_subject: string; fact_key: string; fact_value_num: number | null }>
}

/** Exact D2/D9/D11 wealth slice: SARVA bindus for houses 2/11 and pinda rows for the
 * resolved wealth actors. Missing/duplicate natural keys are corrupt/incomplete, never a
 * zero-value substitute. The caller establishes the shared receipt fence. */
export async function fetchWealthAshtakavarga(
  chart_id: string,
  ayanamsha_id: string,
  actor_codes: string[],
  build_id: BuildFence,
): Promise<WealthAshtakavargaResult> {
  const actors = [...new Set(actor_codes)]
  if (actors.length === 0) return { state: 'source_incomplete', rows: [] }
  try {
    const res = await query<WealthAshtakavargaResult['rows'][number]>(
      `SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_num
         FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND build_id = ANY($3::uuid[])
          AND (
            (fact_category = 'ashtakavarga_bindu_per_varga'
             AND fact_subject = ANY($4) AND fact_key = ANY($5))
            OR
            (fact_category = 'ashtakavarga_pinda_sarva_per_varga'
             AND fact_subject = ANY($6) AND fact_key = ANY($5))
          )
        ORDER BY fact_category ASC, fact_subject ASC, fact_key ASC, fact_id ASC`,
      [chart_id, ayanamsha_id, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchWealthAshtakavarga'),
        WEALTH_ASHTAKAVARGA_HOUSES.map(house => `SARVA-HOUSE_${house}`),
        [...WEALTH_ASHTAKAVARGA_VARGAS], actors],
    )
    const expected = new Set<string>()
    for (const varga of WEALTH_ASHTAKAVARGA_VARGAS) {
      for (const house of WEALTH_ASHTAKAVARGA_HOUSES) expected.add(`ashtakavarga_bindu_per_varga|SARVA-HOUSE_${house}|${varga}`)
      for (const actor of actors) expected.add(`ashtakavarga_pinda_sarva_per_varga|${actor}|${varga}`)
    }
    const observed = new Set<string>()
    for (const row of res.rows) {
      const key = `${row.fact_category}|${row.fact_subject}|${row.fact_key}`
      if (!expected.has(key) || observed.has(key)) return { state: 'source_incomplete', rows: [] }
      observed.add(key)
    }
    return observed.size === expected.size
      ? { state: 'served', rows: res.rows }
      : { state: 'source_incomplete', rows: [] }
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
    return { state: 'source_unproven', rows: [] }
  }
}

export interface WealthSpecialLagnaResult {
  state: 'served' | 'source_incomplete' | 'source_unproven'
  rows: Array<{
    fact_id: string
    fact_subject: typeof WEALTH_SPECIAL_LAGNAS[number]
    fact_key: typeof WEALTH_SPECIAL_LAGNA_KEYS[number]
    fact_value_num: number | null
    fact_value_text: string | null
  }>
}

/** Fixed wealth special-lagna receipt: Indu, Sree, and Hora each need the complete
 * longitude/placement atom set from ga_sensitive's selected build. A floored native
 * computation, a missing atom, or a duplicate atom is incomplete evidence, never a
 * silently partial lagna reading. The caller establishes the shared receipt fence. */
export async function fetchWealthSpecialLagnas(
  chart_id: string,
  ayanamsha_id: string,
  build_id: BuildFence,
): Promise<WealthSpecialLagnaResult> {
  try {
    const res = await query<WealthSpecialLagnaResult['rows'][number] & { verification_pass_status: string | null }>(
      `SELECT fact_id, fact_subject, fact_key, fact_value_num, fact_value_text, verification_pass_status
         FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND build_id = ANY($3::uuid[])
          AND fact_category = 'special_lagna'
          AND fact_subject = ANY($4) AND fact_key = ANY($5)
        ORDER BY fact_subject ASC, fact_key ASC, fact_id ASC`,
      [chart_id, ayanamsha_id, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchWealthSpecialLagnas'), [...WEALTH_SPECIAL_LAGNAS], [...WEALTH_SPECIAL_LAGNA_KEYS]],
    )
    const expected = new Set<string>()
    for (const lagna of WEALTH_SPECIAL_LAGNAS) {
      for (const key of WEALTH_SPECIAL_LAGNA_KEYS) expected.add(`${lagna}|${key}`)
    }
    const observed = new Set<string>()
    for (const row of res.rows) {
      const identity = `${row.fact_subject}|${row.fact_key}`
      if (!expected.has(identity) || observed.has(identity) || row.verification_pass_status !== 'two_pass_verified') {
        return { state: 'source_incomplete', rows: [] }
      }
      if ((row.fact_key === 'longitude_sidereal' || row.fact_key === 'pada' || row.fact_key === 'house_d1')
        ? row.fact_value_num == null
        : row.fact_value_text == null) {
        return { state: 'source_incomplete', rows: [] }
      }
      observed.add(identity)
    }
    return observed.size === expected.size
      ? { state: 'served', rows: res.rows }
      : { state: 'source_incomplete', rows: [] }
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
    return { state: 'source_unproven', rows: [] }
  }
}

export interface WealthYogiAvayogiResult {
  state: 'served' | 'source_incomplete' | 'source_unproven'
  rows: Array<{
    fact_id: string
    fact_subject: keyof typeof WEALTH_YOGI_SUBJECT_KEYS
    fact_key: string
    fact_value_num: number | null
    fact_value_text: string | null
  }>
}

/** Fixed yogi-system receipt: the primary Yogi/Avayogi placements and their duplicate/
 * Sahayogi corroboration are a 12-atom ga_sensitive_degree result, not a best-effort
 * list. Missing, duplicate, floored, or non-verified atoms therefore fail closed. */
export async function fetchWealthYogiAvayogi(
  chart_id: string,
  ayanamsha_id: string,
  build_id: BuildFence,
): Promise<WealthYogiAvayogiResult> {
  const subjects = Object.keys(WEALTH_YOGI_SUBJECT_KEYS) as Array<keyof typeof WEALTH_YOGI_SUBJECT_KEYS>
  const keys = [...new Set(subjects.flatMap(subject => WEALTH_YOGI_SUBJECT_KEYS[subject]))]
  try {
    const res = await query<WealthYogiAvayogiResult['rows'][number] & { verification_pass_status: string | null }>(
      `SELECT fact_id, fact_subject, fact_key, fact_value_num, fact_value_text, verification_pass_status
         FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND build_id = ANY($3::uuid[])
          AND fact_category = 'sensitive_point_yogi'
          AND fact_subject = ANY($4) AND fact_key = ANY($5)
        ORDER BY fact_subject ASC, fact_key ASC, fact_id ASC`,
      [chart_id, ayanamsha_id, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchWealthYogiAvayogi'), subjects, keys],
    )
    const expected = new Set<string>()
    for (const subject of subjects) {
      for (const key of WEALTH_YOGI_SUBJECT_KEYS[subject]) expected.add(`${subject}|${key}`)
    }
    const observed = new Set<string>()
    for (const row of res.rows) {
      const identity = `${row.fact_subject}|${row.fact_key}`
      if (!expected.has(identity) || observed.has(identity) || row.verification_pass_status !== 'two_pass_verified') {
        return { state: 'source_incomplete', rows: [] }
      }
      if (row.fact_key === 'point_longitude' ? row.fact_value_num == null : row.fact_value_text == null) {
        return { state: 'source_incomplete', rows: [] }
      }
      observed.add(identity)
    }
    return observed.size === expected.size
      ? { state: 'served', rows: res.rows }
      : { state: 'source_incomplete', rows: [] }
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
    return { state: 'source_unproven', rows: [] }
  }
}

export interface WealthTajakaResult {
  state: 'served' | 'source_incomplete' | 'source_unproven'
  row: {
    varsha_id: string
    varsha_year: number
    varsha_start_iso: string
    varsha_end_iso: string
    year_lord_method: string
    year_lord: string
    candidate_lord_jsonb: Record<string, unknown> | null
    muntha_position_jsonb: Record<string, unknown> | null
    applicable_tajik_yogas_array: string[] | null
    verification_pass_status: string
    citation_ref: string
    citation_human: string
  } | null
}

/** One annual Tājika row is selected by the caller's explicit as-of date. There is no
 * oldest/current heuristic here: selected build + ayanāṃśa + half-open annual window
 * must yield exactly one two-pass-verified Vārṣaphala record. */
export async function fetchWealthTajaka(
  chart_id: string,
  ayanamsha_id: string,
  build_id: BuildFence,
  as_of_date: string,
): Promise<WealthTajakaResult> {
  try {
    const res = await query<NonNullable<WealthTajakaResult['row']>>(
      `SELECT varsha_id::text AS varsha_id, varsha_year, varsha_start_iso::text, varsha_end_iso::text,
              year_lord_method, year_lord, candidate_lord_jsonb, muntha_position_jsonb,
              applicable_tajik_yogas_array, verification_pass_status, citation_ref, citation_human
         FROM l1_tajik_varsha_year_lords
        WHERE chart_id = $1::uuid AND ayanamsha_id = $2 AND build_id = ANY($3::uuid[])
          AND varsha_start_iso <= $4::date AND varsha_end_iso > $4::date
        ORDER BY varsha_year ASC, varsha_id ASC`,
      [chart_id, ayanamsha_id, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchWealthTajaka'), as_of_date],
    )
    if (res.rows.length !== 1) return { state: 'source_incomplete', row: null }
    const row = res.rows[0]!
    if (row.verification_pass_status !== 'two_pass_verified'
      || row.year_lord_method !== 'tajik_classical'
      || !row.varsha_id || !Number.isInteger(row.varsha_year)
      || !row.varsha_start_iso || !row.varsha_end_iso || !row.year_lord
      || row.candidate_lord_jsonb == null || row.muntha_position_jsonb == null
      || !row.citation_ref || !row.citation_human) {
      return { state: 'source_incomplete', row: null }
    }
    return { state: 'served', row }
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
    return { state: 'source_unproven', row: null }
  }
}

// ── NMB-CAND-v1 (OSR-009 / OSR-012 / OSR-015): the serve-time wealth-yoga formation band ──
//
// The band is derived at SERVE time by the python sidecar route
// `POST /api/compute/yoga_formation_band` (routers/yoga_formation_band.py) from the served
// generation's L1 facts and ga_yoga_firings using the shipped L1 evaluators. Nothing is stored.
// Present is decided only by L1 `ga_yoga_firings`; the route adds the leg-level derivation of
// NON-firings. This reader is fenced to the served generation of the producing assets
// (`ga_yoga` + the assets that write the chart_facts the evaluators read: `ga_positions`),
// each behind its own fresh, proven receipt.
//
// Packet v1.2 NARROWING: `near_miss` is not a v1 state. The route serves present / absent /
// indeterminate only, so `notably_absent_yogas` is an empty array BY DESIGN and formation-gap
// detection is not claimed. Any unproven leg -- fence, generation, sidecar failure, malformed or
// non-six response, or ANY indeterminate candidate -- is `source_unproven`: never an empty finding
// that could be read as settled, never `not_computed` (N.7 item 6: an honest null beats an
// invented judgment).

export const NEAR_MISS_CANDIDATE_SET_VERSION = 'NMB-CAND-v1'
export const NEAR_MISS_ELIGIBILITY_RULE_VERSION = 'NMB-ELIG-v1'
export const NEAR_MISS_BAND_VERSION = 'NMB-BAND-v1'
/** ga_yoga writes the firings; ga_positions writes the graha_position facts the evaluators read
 *  (`ChartState` categories -- packet v1.1 section 6). `bo_laksana` is NOT in this fence. */
export const NEAR_MISS_REQUIRED_ASSETS = ['ga_yoga', 'ga_positions'] as const
/** The closed candidate set (packet section 2). A band that is not exactly this set is unproven. */
export const NEAR_MISS_CANDIDATE_IDS = [
  'dhana_yoga_house_lords',
  'dhana_yoga_2_11',
  'dhana_yoga_5_9',
  'dhana_yoga_lagna_2',
  'dhana_yoga_9_11',
  'dhana_yoga_2_5_9_11',
] as const
/** The five canonical stored ayanamsha ids (mirrors ga_yoga_writer.CANONICAL_AYANAMSHAS). The
 *  ayanamsha fan-out is bounded to this closed set: unknown ids are ignored, never forwarded. */
export const NEAR_MISS_CANONICAL_AYANAMSHAS = [
  'lahiri_chitrapaksha', 'true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical',
] as const
/** `near_miss` is NOT a band state (packet v1.2): a route row carrying it is invalid. */
export type NearMissBandState = 'present' | 'absent' | 'indeterminate'
const NEAR_MISS_BAND_STATES: readonly NearMissBandState[] = ['present', 'absent', 'indeterminate']
const NEAR_MISS_SIDECAR_TIMEOUT_MS = 8000
/** In-process route-result cache: 60 s, at most 64 entries, successful responses only. */
export const NEAR_MISS_ROUTE_CACHE_TTL_MS = 60_000
export const NEAR_MISS_ROUTE_CACHE_MAX_ENTRIES = 64

export const NEAR_MISS_NOTE =
  'Formation-gap detection is not claimed: this band reports only the present / absent / indeterminate ' +
  'status of the closed wealth-yoga candidate set, so an empty notably_absent_yogas array is NOT a finding ' +
  'that no yoga is nearly formed.'
export const NEAR_MISS_OVERLAP_NOTE =
  'Candidate rows are overlapping statuses of one wealth-yoga family, not independent findings: ' +
  'dhana_yoga_2_5_9_11 subsumes dhana_yoga_2_11, dhana_yoga_5_9 and dhana_yoga_9_11, and ' +
  'dhana_yoga_house_lords overlaps all of them. Do not sum the rows into a yoga count.'
export const NEAR_MISS_SOURCE_NOTE =
  "The catalogue citation 'Ch.41 Dhana Yoga adhyaya' carries no verse. Only the 5th/9th lord pair is " +
  'directly in BPHS Ch.41 sloka 16; the 2nd/11th, lagna/2nd, 9th/11th and any-pair candidates rest on ' +
  'general Parashari sambandha (conjunction, exchange, mutual aspect) and translator notes, not on Ch.41 text.'

export interface BandCandidateStatus {
  candidate_id: string
  yoga_name: string | null
  state: NearMissBandState
  reason: string | null
  overlaps: string[]
  contradicting_present_siblings: string[]
  l1_firing_ids: number[]
}

export interface NotablyAbsentYogasResult {
  /** `empty_for_this_chart`: every candidate determinate (present/absent) -- and still NO formation-gap
   *  claim. `source_unproven`: anything unproven, including any indeterminate candidate. */
  state: 'empty_for_this_chart' | 'source_unproven'
  /** Why the source is unproven (null when settled). */
  reason: string | null
  /** ALWAYS empty (packet v1.2): no near_miss rows exist in v1. */
  notably_absent_yogas: never[]
  band_coverage: Record<NearMissBandState | 'near_miss', number> & { total: number }
  near_miss_capable_candidates: 0
  formation_gap_detection: 'not_claimed'
  note: string
  overlap_note: string
  overlaps: Record<string, string[]>
  classical_sources: { catalog_citation_carries_verse: false; directly_in_bphs_ch41_sloka_16: string[]; note: string }
  candidate_statuses: BandCandidateStatus[]
  /** Indeterminate candidates are served AS indeterminate (never folded into absent). */
  indeterminate: Array<{ candidate_id: string; reason: string | null }>
  /** true when any compared neighbour differs; false ONLY when every neighbour was compared and agrees;
   *  null when any neighbour could not be compared or there was no comparable neighbour. */
  ayanamsha_sensitive: boolean | null
  ayanamsha_sensitive_by_candidate: Record<string, boolean | null>
  ayanamsha_sensitive_candidates: string[]
  ayanamsha_unchecked: string[]
  ayanamsha_sensitivity_note: string | null
  candidate_set_version: string
  eligibility_rule_version: string
  band_version: string
  served_build_ids: string[]
  fact_ids: string[]
}

const EMPTY_COVERAGE = (): NotablyAbsentYogasResult['band_coverage'] =>
  ({ present: 0, near_miss: 0, absent: 0, indeterminate: 0, total: 0 })

function baseResult(): Omit<NotablyAbsentYogasResult, 'state' | 'reason'> {
  return {
    notably_absent_yogas: [],
    band_coverage: EMPTY_COVERAGE(),
    near_miss_capable_candidates: 0,
    formation_gap_detection: 'not_claimed',
    note: NEAR_MISS_NOTE,
    overlap_note: NEAR_MISS_OVERLAP_NOTE,
    overlaps: {},
    classical_sources: { catalog_citation_carries_verse: false, directly_in_bphs_ch41_sloka_16: ['dhana_yoga_5_9'], note: NEAR_MISS_SOURCE_NOTE },
    candidate_statuses: [],
    indeterminate: [],
    ayanamsha_sensitive: null,
    ayanamsha_sensitive_by_candidate: {},
    ayanamsha_sensitive_candidates: [],
    ayanamsha_unchecked: [],
    ayanamsha_sensitivity_note: null,
    candidate_set_version: NEAR_MISS_CANDIDATE_SET_VERSION,
    eligibility_rule_version: NEAR_MISS_ELIGIBILITY_RULE_VERSION,
    band_version: NEAR_MISS_BAND_VERSION,
    served_build_ids: [],
    fact_ids: [],
  }
}

export function unprovenBand(reason: string): NotablyAbsentYogasResult {
  return { ...baseResult(), state: 'source_unproven', reason }
}

const isRecord = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === 'object' && !Array.isArray(v)
const asNumberArray = (v: unknown): number[] => Array.isArray(v) ? v.filter((x): x is number => typeof x === 'number') : []
const asStringArray = (v: unknown): string[] => Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : []

/** Validate one route response against the request that produced it. Returns a candidate map, or a reason. */
function validateBandResponse(
  raw: unknown, expect: { chart_id: string; ayanamsha_id: string; served_build_ids: readonly string[] },
): { ok: true; candidates: Map<string, Record<string, unknown>>; response: Record<string, unknown> } | { ok: false; reason: string } {
  if (!isRecord(raw)) return { ok: false, reason: 'band_response_malformed' }
  if (raw['candidate_set_version'] !== NEAR_MISS_CANDIDATE_SET_VERSION
    || raw['eligibility_rule_version'] !== NEAR_MISS_ELIGIBILITY_RULE_VERSION
    || raw['band_version'] !== NEAR_MISS_BAND_VERSION) return { ok: false, reason: 'band_version_mismatch' }
  if (raw['tolerance'] !== 'none') return { ok: false, reason: 'band_tolerance_not_none' }
  if (raw['chart_id'] !== expect.chart_id || raw['ayanamsha_id'] !== expect.ayanamsha_id) {
    return { ok: false, reason: 'band_scope_mismatch' }
  }
  const echoed = asStringArray(raw['served_build_ids']).slice().sort()
  const sent = [...expect.served_build_ids].sort()
  if (echoed.length !== sent.length || echoed.some((b, i) => b !== sent[i])) return { ok: false, reason: 'band_generation_mismatch' }
  const list = Array.isArray(raw['candidates']) ? raw['candidates'] : null
  if (!list || list.length !== NEAR_MISS_CANDIDATE_IDS.length) {
    return { ok: false, reason: `band_rows_incomplete:${list?.length ?? 0}/${NEAR_MISS_CANDIDATE_IDS.length}` }
  }
  const byId = new Map<string, Record<string, unknown>>()
  for (const c of list) {
    if (!isRecord(c) || typeof c['candidate_id'] !== 'string' || byId.has(c['candidate_id'])
      || !NEAR_MISS_BAND_STATES.includes(c['state'] as NearMissBandState)) return { ok: false, reason: 'band_row_invalid' }
    byId.set(c['candidate_id'], c)
  }
  const closed = new Set<string>(NEAR_MISS_CANDIDATE_IDS)
  if (byId.size !== closed.size || [...byId.keys()].some(id => !closed.has(id))) {
    return { ok: false, reason: 'band_candidate_set_mismatch' }
  }
  return { ok: true, candidates: byId, response: raw }
}

/**
 * Interpret the route response for the resolved ayanamsha. Pure: every provenance decision
 * (fence, generation, transport) is made by the caller; this decides only whether the response is
 * a complete, valid NMB-CAND-v1 band and what it says. `others` are the responses for the other
 * ayanamshas (null = could not be evaluated) used only for the sensitivity fields.
 */
export function interpretYogaBandResponse(
  raw: unknown,
  expect: { chart_id: string; ayanamsha_id: string; served_build_ids: readonly string[] },
  others: ReadonlyArray<{ ayanamsha_id: string; raw: unknown | null }> = [],
): NotablyAbsentYogasResult {
  const mine = validateBandResponse(raw, expect)
  if (!mine.ok) return unprovenBand(mine.reason)

  const sensitive: string[] = []
  const unchecked: string[] = []
  let compared = 0
  for (const other of others) {
    const checked = other.raw === null ? null
      : validateBandResponse(other.raw, { ...expect, ayanamsha_id: other.ayanamsha_id })
    if (!checked || !checked.ok) { unchecked.push(other.ayanamsha_id); continue }
    compared += 1
    for (const id of NEAR_MISS_CANDIDATE_IDS) {
      if (checked.candidates.get(id)!['state'] !== mine.candidates.get(id)!['state'] && !sensitive.includes(id)) sensitive.push(id)
    }
  }
  // false is asserted ONLY when every neighbour was actually compared (and at least one was).
  const ayanamshaSensitive: boolean | null =
    sensitive.length > 0 ? true : (unchecked.length > 0 || compared === 0 ? null : false)
  const byCandidate: Record<string, boolean | null> = {}
  for (const id of NEAR_MISS_CANDIDATE_IDS) {
    byCandidate[id] = sensitive.includes(id) ? true : unchecked.length ? null : compared === 0 ? null : false
  }

  const coverage = EMPTY_COVERAGE()
  const statuses: BandCandidateStatus[] = []
  const indeterminate: NotablyAbsentYogasResult['indeterminate'] = []
  const overlaps: Record<string, string[]> = {}
  const factIds = new Set<string>()
  for (const id of NEAR_MISS_CANDIDATE_IDS) {
    const cand = mine.candidates.get(id)!
    const state = cand['state'] as NearMissBandState
    coverage[state] += 1
    coverage.total += 1
    const reason = typeof cand['reason'] === 'string' ? cand['reason'] : null
    if (state === 'indeterminate') indeterminate.push({ candidate_id: id, reason })
    overlaps[id] = asStringArray(cand['overlaps']).sort()
    statuses.push({
      candidate_id: id,
      yoga_name: typeof cand['yoga_name'] === 'string' ? cand['yoga_name'] : null,
      state,
      reason,
      overlaps: overlaps[id]!,
      contradicting_present_siblings: asStringArray(cand['contradicting_present_siblings']).sort(),
      l1_firing_ids: asNumberArray(cand['l1_firing_ids']),
    })
    for (const f of asStringArray(cand['constituent_fact_ids'])) factIds.add(f)
  }
  const noNeighbourNote = compared === 0
    ? 'no neighbouring ayanamsha could be compared, so ayanamsha sensitivity is unknown (null), not false'
    : null
  return {
    ...baseResult(),
    // An indeterminate candidate means the band did not settle: never read as an exhaustive negative.
    state: indeterminate.length > 0 ? 'source_unproven' : 'empty_for_this_chart',
    reason: indeterminate.length > 0 ? 'band_indeterminate' : null,
    band_coverage: coverage,
    overlaps,
    candidate_statuses: statuses,
    indeterminate,
    ayanamsha_sensitive: ayanamshaSensitive,
    ayanamsha_sensitive_by_candidate: byCandidate,
    ayanamsha_sensitive_candidates: sensitive,
    ayanamsha_unchecked: unchecked,
    ayanamsha_sensitivity_note: noNeighbourNote,
    served_build_ids: [...expect.served_build_ids].sort(),
    fact_ids: [...factIds].sort(),
  }
}

// ── Route transport: bounded, cached, key-logged ─────────────────────────────

const routeCache = new Map<string, { at: number; value: unknown }>()
let warnedMissingSidecarKey = false

/** Test seam: clears the route-result cache and the once-only key warning. */
export function resetYogaBandRouteStateForTests(): void {
  routeCache.clear()
  warnedMissingSidecarKey = false
}

const routeCacheKey = (chart_id: string, ayanamsha_id: string, builds: readonly string[]) =>
  `${chart_id}|${ayanamsha_id}|${[...builds].sort().join(',')}`

function routeCacheGet(key: string, now: number): unknown | undefined {
  const hit = routeCache.get(key)
  if (!hit) return undefined
  if (now - hit.at > NEAR_MISS_ROUTE_CACHE_TTL_MS) { routeCache.delete(key); return undefined }
  return hit.value
}

function routeCacheSet(key: string, value: unknown, now: number): void {
  routeCache.delete(key)
  if (routeCache.size >= NEAR_MISS_ROUTE_CACHE_MAX_ENTRIES) {
    for (const [k, v] of routeCache) if (now - v.at > NEAR_MISS_ROUTE_CACHE_TTL_MS) routeCache.delete(k)
    while (routeCache.size >= NEAR_MISS_ROUTE_CACHE_MAX_ENTRIES) {
      const oldest = routeCache.keys().next().value
      if (oldest === undefined) break
      routeCache.delete(oldest)
    }
  }
  routeCache.set(key, { at: now, value })
}

async function callYogaBandRoute(chart_id: string, ayanamsha_id: string, served_build_ids: readonly string[]): Promise<unknown> {
  const cacheKey = routeCacheKey(chart_id, ayanamsha_id, served_build_ids)
  const cached = routeCacheGet(cacheKey, Date.now())
  if (cached !== undefined) return cached
  const sidecarUrl = (process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001').replace(/\/$/, '')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const key = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''
  if (key) headers['x-api-key'] = key
  else if (!warnedMissingSidecarKey) {
    warnedMissingSidecarKey = true
    console.warn('[yoga_formation_band] PYTHON_SIDECAR_API_KEY is empty: the sidecar route fails closed (503), so the formation band will be source_unproven until it is set on the web service')
  }
  const res = await fetch(`${sidecarUrl}/api/compute/yoga_formation_band`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ chart_id, ayanamsha_id, served_build_ids }),
    signal: AbortSignal.timeout(NEAR_MISS_SIDECAR_TIMEOUT_MS),
  })
  if (!res.ok) throw new Error(`sidecar ${res.status}`)
  const body: unknown = await res.json()
  routeCacheSet(cacheKey, body, Date.now())  // successful responses only: every failure threw above
  return body
}

/** The other CANONICAL ayanamshas that have graha_position facts in the served facts build (pinned
 *  category+key). Bounded: only the closed canonical set, deduplicated, own id excluded (max 4). */
async function otherServedAyanamshas(chart_id: string, ayanamsha_id: string, factsBuildId: string): Promise<string[]> {
  const res = await query<{ ayanamsha_id: string }>(
    `SELECT DISTINCT ayanamsha_id
       FROM chart_facts
      WHERE chart_id = $1::uuid AND build_id = $2::uuid
        AND fact_category = 'graha_position' AND fact_key = 'sign'
        AND ayanamsha_id <> $3
      ORDER BY ayanamsha_id ASC`,
    [chart_id, factsBuildId, ayanamsha_id],
  )
  const canonical = new Set<string>(NEAR_MISS_CANONICAL_AYANAMSHAS)
  const out: string[] = []
  for (const r of res.rows) {
    if (canonical.has(r.ayanamsha_id) && r.ayanamsha_id !== ayanamsha_id && !out.includes(r.ayanamsha_id)) out.push(r.ayanamsha_id)
  }
  return out.slice(0, NEAR_MISS_CANONICAL_AYANAMSHAS.length - 1)
}

/**
 * Serve the wealth-yoga formation band for the resolved ayanamsha. Fenced to the served
 * generation of `ga_yoga` + `ga_positions` (each: proven fresh receipt, current spec, resolved
 * binding, no replacement in flight). Any failure is `source_unproven` with the reason; the
 * returned `notably_absent_yogas` is always empty (packet v1.2).
 */
export async function fetchNotablyAbsentYogas(
  chart_id: string,
  ayanamsha_id: string,
  generation: ChartServedGeneration,
): Promise<NotablyAbsentYogasResult> {
  if (!(NEAR_MISS_CANONICAL_AYANAMSHAS as readonly string[]).includes(ayanamsha_id)) {
    return unprovenBand('ayanamsha_not_canonical')
  }
  const fence = await fetchSourceReceiptFence(chart_id, generation, NEAR_MISS_REQUIRED_ASSETS)
  if (!fence.ok) return unprovenBand('source_fence_unavailable')
  const blocked = fence.assets.filter(a => !a.receipt_matches_selected_build || a.replacement_in_progress)
  if (blocked.length > 0) {
    return unprovenBand(`source_fence_unproven:${blocked.map(a => a.asset_id).sort().join(',')}`)
  }
  const rowsBuilds = NEAR_MISS_REQUIRED_ASSETS.map(asset => resolvedRowsBuildId(generation, asset))
  if (rowsBuilds.some(b => b === null)) return unprovenBand('generation_unresolved')
  const servedBuildIds = [...new Set(rowsBuilds as string[])].sort()
  const expect = { chart_id, ayanamsha_id, served_build_ids: servedBuildIds }
  let mine: unknown
  try {
    mine = await callYogaBandRoute(chart_id, ayanamsha_id, servedBuildIds)
  } catch {
    return unprovenBand('sidecar_unavailable')
  }
  const primary = interpretYogaBandResponse(mine, expect)
  if (primary.state === 'source_unproven' && primary.reason !== 'band_indeterminate') return primary

  // Ayanamsha sensitivity: re-evaluate the SAME generation under every other served canonical
  // ayanamsha. A failed neighbour leaves sensitivity unknown (null), never asserted false.
  const factsBuild = resolvedRowsBuildId(generation, 'ga_positions')!
  let neighbours: string[] | null = null
  try { neighbours = await otherServedAyanamshas(chart_id, ayanamsha_id, factsBuild) } catch { neighbours = null }
  if (neighbours === null) {
    return interpretYogaBandResponse(mine, expect, [{ ayanamsha_id: 'other_ayanamshas_lookup_failed', raw: null }])
  }
  const others = await Promise.all(neighbours.map(async other => {
    try { return { ayanamsha_id: other, raw: await callYogaBandRoute(chart_id, other, servedBuildIds) } }
    catch { return { ayanamsha_id: other, raw: null } }
  }))
  return interpretYogaBandResponse(mine, expect, others)
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
  build_id?: BuildFence,
): Promise<KpCuspResult> {
  const out: KpCuspResult = {
    cusps: [], available: false, fact_ids: [],
    note: 'KP cuspal sub-lord chain (Krishnamurti Paddhati): the cusp sub-lord is the ' +
      'final arbiter of a bhāva\'s promise; its significators name the grahas that will ' +
      'deliver (or deny) the matter. Served for this domain\'s decisive cusps (MC-031).',
  }
  try {
    const { getKpCuspsCapability } = await import('./L1_ganita/get_kp_cusps')
    const res = await getKpCuspsCapability.handler(
      { chart_id, ayanamsha_id, ...(build_id ? { build_id } : {}) },
      undefined,
    )
    if (res.is_error) {
      // get_kp_cusps refuses outright (never silently returns zero rows) on an
      // explicit-empty fence — that refusal must propagate as a refusal here too, not
      // degrade into "no cusp data" for a leg its own docstring calls "the final arbiter
      // of a bhāva's promise".
      const code = (res.content as Record<string, unknown> | undefined)?.['code']
      if (code === 'explicit_empty_build_fence') throw new ExplicitEmptyBuildFenceError('reading_checklist.fetchKpCuspChain')
      return out
    }
    const c = res.content as Record<string, unknown>
    // The child echoes the fence it applied; refuse a payload fenced to anything else.
    // (build_id cannot be explicit-empty here — the is_error branch above already refused
    // that case — so a plain, non-throwing normalize is correct for this equality check.)
    const normalizeForCompare = (value: unknown): string[] | null => {
      const fence = classifyBuildFence(value)
      return fence.kind === 'resolved' ? [...fence.build_ids] : null
    }
    if (build_id && JSON.stringify(normalizeForCompare(c['build_id'])?.slice().sort() ?? null)
      !== JSON.stringify(normalizeForCompare(build_id)?.slice().sort() ?? null)) return out
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
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
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
  // P-2 (WP7): '4.x' provenance/qualification columns carried through the
  // 200-row SQL cap and the 5-window display trim. All null on v1 rows
  // (honest-null convention, same as the pre-existing nullable fields).
  peak_basis: string | null
  generation: string | null
  completeness_state: string | null   // F06 states; null = pre-'4.x' row
  contact_ids: string[]               // parsed from active_sentences jsonb; [] when none
  is_confirmed: boolean               // completeness_state in the confirmed set
                                      // AND peak_basis passes the argmax check
}

// P-2: mirrors services/gochara_v3/peak_basis_vocab.py GENUINE_PEAK_BASES (and
// platform-mcp register_gochara_windows.ts:372) — a LOCATED-extremum basis.
const GENUINE_PEAK_BASES: ReadonlySet<string> = new Set(['gochara_lambda_v3_argmax'])

// P-2: F06 confirmed set. The WP6 writer vocab (gochara_kernel/episodes.py,
// gochara_v3/interval_solver.py) uses 'qualified'; the P-2 packet fixture uses
// 'confirmed'. Both count as confirmed; 'unqualified'/'unavailable'/null never do.
const CONFIRMED_COMPLETENESS_STATES: ReadonlySet<string> = new Set(['confirmed', 'qualified'])

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
  // P-2 (WP7): §N.6 density layering — never let the raw page count read as
  // N confirmed timing windows. Counts are over the SERVED page (windows[]),
  // same "in_page" discipline as summarizeResolutionDisclosure in
  // platform-mcp register_gochara_windows.ts.
  confirmed_rows_in_page: number
  context_only_rows_in_page: number
  catalog_only_note: string | null
  provenance: { generation: string | null; manifest_id: string | null }
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
    confirmed_rows_in_page: 0,
    context_only_rows_in_page: 0,
    catalog_only_note: null,
    provenance: { generation: null, manifest_id: null },
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
      peak_basis: string | null; generation: string | null
      active_sentences: unknown; completeness_state: string | null
    }>(
      `SELECT w.event_class, w.temporal_shape, w.window_start, w.window_end, w.peak_date,
              w.valence, w.is_adverse,
              w.peak_basis,
              w.generation,
              w.active_sentences,
              w.completeness_state
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
    out.windows = res.rows.slice(0, 5).map(r => {
      // P-2: parse the '4.x' window↔contact id list (active_sentences jsonb,
      // [] / NULL / unexpected shapes all degrade to [] — Q01 is answered by
      // id when present, never fabricated when absent).
      const contactIds = Array.isArray(r.active_sentences)
        ? r.active_sentences.filter((x): x is string => typeof x === 'string')
        : []
      const isConfirmed =
        r.completeness_state !== null &&
        CONFIRMED_COMPLETENESS_STATES.has(r.completeness_state) &&
        r.peak_basis !== null &&
        GENUINE_PEAK_BASES.has(r.peak_basis)
      return {
        event_class: r.event_class,
        temporal_shape: r.temporal_shape,
        window_start: r.window_start,
        window_end: r.window_end,
        peak_date: r.peak_date,
        valence: r.valence,
        is_adverse: r.is_adverse,
        is_past_peak: isPastPeak(r.peak_date),
        peak_basis: r.peak_basis,
        generation: r.generation,
        completeness_state: r.completeness_state,
        contact_ids: contactIds,
        is_confirmed: isConfirmed,
      }
    })
    // P-2 (§N.6): confirmed-vs-context counts over the served page. The trim
    // above takes the first N rows in stored rank order — never re-rank or
    // re-admit (H-5: admission upstream is cap-free, so serve-time trim is
    // legal display layering, not truncation-as-absence).
    out.confirmed_rows_in_page = out.windows.filter(w => w.is_confirmed).length
    out.context_only_rows_in_page = out.windows.length - out.confirmed_rows_in_page
    out.catalog_only_note =
      out.context_only_rows_in_page === 0
        ? null
        : `${out.context_only_rows_in_page} of ${out.windows.length} served row(s) are context-only ` +
          '(unqualified/unavailable completeness, or a non-argmax peak_basis) -- not confirmed ' +
          'timing windows; do not read window_start/window_end/peak_date on these rows as a ' +
          'confirmed timing claim. See each row\'s is_confirmed / completeness_state / peak_basis.'
    if (out.context_only_rows_in_page > 0) {
      out.note += ` ${out.context_only_rows_in_page} of the served rows are context-only, ` +
        'not confirmed timing windows -- see catalog_only_note and each row\'s is_confirmed.'
    }
    // P-2: provenance of the served page. generation is read off the rows
    // themselves (mixed-generation pages are impossible under the
    // authority-scoped predicate); manifest_id is a '4.x' publication-ledger
    // field not joined here — P-4 owns the manifest read capability, so this
    // stays null rather than guessing.
    out.provenance = {
      generation: res.rows.find(r => r.generation !== null)?.generation ?? null,
      manifest_id: null,
    }
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
  build_id?: BuildFence,
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
            ${build_id ? 'AND build_id = ANY($4::uuid[])' : ''}
       ), mech AS (
         SELECT count(*)::int AS c FROM bodha_mechanisms
          WHERE chart_id = $1 AND ayanamsha_id = $2 AND $3 = ANY(domains_affected_array)
            ${build_id ? 'AND build_id = ANY($4::uuid[])' : ''}
       ), mech_domains AS (
         SELECT count(DISTINCT d)::int AS c FROM (
           SELECT unnest(domains_affected_array) AS d FROM bodha_mechanisms
            WHERE chart_id = $1 AND ayanamsha_id = $2
              ${build_id ? 'AND build_id = ANY($4::uuid[])' : ''}
         ) s
       )
       SELECT msr.c AS msr_count, mech.c AS mech_count, mech_domains.c AS mech_domain_coverage
         FROM msr, mech, mech_domains`,
      build_id
        ? [chart_id, ayanamsha_id, signal_domain, resolvedBuildFenceIds(build_id, 'reading_checklist.fetchDomainStructuralCoverage')]
        : [chart_id, ayanamsha_id, signal_domain],
    )
    const row = res.rows[0]
    if (row) {
      out.msr_signals = row.msr_count
      out.mechanisms = row.mech_count
      out.mechanisms_domain_coverage = row.mech_domain_coverage
      out.structurally_unpopulated = row.msr_count === 0 && row.mech_count === 0
      out.available = true
    }
  } catch (error) {
    if (error instanceof ExplicitEmptyBuildFenceError) throw error
    // non-fatal: leg degrades to "could not measure" (available: false) — never a fabricated
    // zero or a fabricated "populated" claim (B.10).
  }
  return out
}
