/**
 * tools/kala_views/now.ts — ṢAḌ-DARŚANA W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 · §2 file map
 * · §3 W0.4 "Eight facades over EXISTING substrate").
 * ==========================================================================
 * `kala_now_get` — VIEW 1: NOW ("What is my temporal state?"), per
 * KALA_SIX_VIEWS_DESIGN_v1_0.md §1.
 *
 * THIN FACADE for the base NOW state — it calls the SAME two registry
 * capabilities the existing `kala_windows_get` (register_p1_aliases.ts, →
 * `marsys://tool/L3/query_temporal_activation`) and the snapshot half of `kala_bundle_get`
 * (tools/retrieval/kala_temporal.ts, → `marsys://tool/L3/query_temporal_view`) already call,
 * and re-presents their EXISTING rows through the elevated envelope (`lib/kala_envelope.ts`)
 * + the shared prose engine (`lib/argument_composer.ts`). No new join, no new field, no new
 * computation — every claim in the composed reading traces to a field the underlying
 * capability already returns (§N.5 / B.10).
 *
 * W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1) ADDS two [J]-kind JOINS over existing substrate
 * (still no new astrological computation, no new migration — see the "W1 item 8 + item 28"
 * doc-comment above `dualOutput` below for the exact provenance of each field):
 *   - item 8  `gochara_dual_reference`: every graha's CURRENT transit house, counted from
 *     BOTH natal Moon and natal Lagna at once (no silent single-reference default).
 *   - item 28 `dasha_lord_transit_condition`: the currently-running Vimśottarī MD/AD lord's
 *     OWN current transit sign/house/dignity (see ahead.ts for the forward half).
 *   - item 1-lite `dasha_sandhi`: a band around every currently-active MD/AD period's start
 *     AND end boundary, computed purely from that period's own already-computed span (see the
 *     "W1 item 1-lite" doc-comment above `computeDashaSandhi` below for the exact documented
 *     band-width convention and its lite simplification). Full daśā-sandhi calendar (all
 *     levels, both directions) is item 1-full (wave W3), not this facade's job.
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §1 (NOW content + clarity contract),
 * KALA_SUPREME_ELEVATION_v1_0.md (v1.2) §5 (envelope E3/E4/E5), §11 (item 43 tri-plane).
 *
 * What is genuinely NOT computed here yet (honestly disclosed via `coverage`, never
 * silently dropped): per-ingress transit moorti — a named W3 build item in the brief, not
 * this facade's job.
 *
 * W1 JOIN ADDITIONS (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1, items 32 + 29): diśā-śūla +
 * gulika-kālam window membership + chandrāṣṭama + horā lord + janma-tithi/vara/nakṣatra
 * resonance. Every one of these is a JOIN, not a new computation (§N.5 / B.10):
 *   - diśā-śūla / gulika-kālam / horā all read the SAME date-parameterized panchāṅga the
 *     already-wired `call_panchanga_service` (marsys://tool/L0/call_panchanga_service →
 *     panchang.py /api/compute/panchanga) already computes for any date — this facade
 *     only adds a static vara→direction lookup (diśā-śūla; mirrors the identical
 *     DISHA_SHUL_TABLE already live in panchang_engine/shastra_tables.py and cited in the
 *     ga_panchanga_writer L1 emitter — not invented here) and simple UTC-instant window-
 *     membership comparisons (gulika-kālam / horā — "is `now` inside this already-computed
 *     window") — both squarely the "simple date/time comparison logic" the brief allows
 *     for [J] items, never a new astrological computation.
 *   - chandrāṣṭama reads `native_context.moon_sign_id` (birth Moon rāśi, already computed
 *     by panchang.py's `_fetch_native_context` from the chart's own birth data) against
 *     `panchang.planets.moon.sign_id` (today's transit Moon rāśi, same call) — a single
 *     house-count comparison (classical Chāndra Bala rule, Muhūrta Chintāmaṇi §4; mirrors
 *     platform/src/lib/panchang/chandra_bala.ts's identical formula, inlined here rather
 *     than cross-package-imported per this file's own established no-cross-file-coupling
 *     convention — see the header note above).
 *   - janma-tithi/vara/nakṣatra resonance ("today is your janma-nakṣatra day") is a
 *     documented classical concept, not invented for this pass — see
 *     KALA_SIX_VIEWS_DESIGN_v2_0.md §NOW ("janma-tithi/vara/nakṣatra resonance") and
 *     KALA_SUPREME_ELEVATION_v1_0.md §9 Chart-personal factor family. It compares TODAY's
 *     tithi/vara/nakṣatra id (from the same panchāṅga call) against the native's OWN birth
 *     tithi/vara/nakṣatra id, read verbatim from the L1-authoritative `chart_facts` rows
 *     (marsys://tool/L1/get_panchanga → panchanga_tithi/panchanga_vara/
 *     panchanga_nakshatra_moon, FORENSIC-anchored) — never re-derived (§N.5).
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import {
  makeKalaEnvelope,
  fetchCalibrationMaturity,
  buildKalaFreshness,
  resolveFieldSnapshot,
  pointerTo,
  isNoLever,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  type ArgumentReading,
  type ArgumentEvidence,
  type ArgumentVerdict,
  type QuestionFrame,
  type TriPlanePointers,
  type DrillPointerLike,
  type KalaCoverageEntry,
  type FieldSnapshotState,
  type CalibrationMaturityResolution,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { autoDetectTrimmableSections, finalizeMcpBudget } from '../../lib/response_budget.js'
import { buildSukshmaBoundaryIntervals, type SukshmaBoundaryInterval } from '../../lib/kala_uncertainty.js'
import { resolveChartFactsAyanamsha } from '../../lib/ayanamsha.js'

// ── Infrastructure (self-contained proxy helper — mirrors the established per-file
// pattern in register_p1_aliases.ts / tools/retrieval/kala_temporal.ts / registry_bridge.ts;
// this file does not import their module-local helpers to avoid coupling this new lane's
// facade to files owned/being edited by sibling lanes in the same campaign) ─────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

/**
 * Calls a registry capability via /api/retrieval/capability. NEVER throws — a transport
 * failure or malformed envelope both resolve to `{ content: null, ok: false }` so the
 * caller can serve an honest `honest_empty` coverage entry instead of crashing the whole
 * facade over one degraded sub-call (mirrors tools/retrieval/kala_temporal.ts's
 * `fetchCapabilityRows` resilience contract).
 *
 * Defensive double-unwrap: /api/retrieval/capability responds `{ ok, content: <result> }`,
 * and every CapabilityDescriptor handler itself returns `{ content: <payload>, is_error }`.
 * This only unwraps the second layer when the shape actually matches that contract (has an
 * `is_error` key) — never mis-unwraps a legitimately content-shaped payload lacking one.
 */
async function callRegistryCapability(
  uri: string,
  args: Record<string, unknown>,
  principal: Principal,
): Promise<{ content: Record<string, unknown> | null; ok: boolean }> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
        'X-MCP-User': principal.user_uid,
        'X-MCP-Key-Id': principal.key_id,
      },
      body: JSON.stringify({ uri, args }),
      signal: AbortSignal.timeout(20_000),
    })
    if (!res.ok) return { content: null, ok: false }
    const data = (await res.json()) as { ok: boolean; content?: unknown }
    if (!data.ok) return { content: null, ok: false }
    const outer = data.content
    if (outer && typeof outer === 'object' && !Array.isArray(outer) && 'is_error' in (outer as Record<string, unknown>)) {
      const wrapper = outer as { content?: unknown; is_error?: boolean }
      const inner = wrapper.content
      return {
        content: inner && typeof inner === 'object' ? (inner as Record<string, unknown>) : null,
        ok: wrapper.is_error !== true,
      }
    }
    return { content: outer && typeof outer === 'object' ? (outer as Record<string, unknown>) : null, ok: true }
  } catch {
    return { content: null, ok: false }
  }
}

// ── W1 item 8 (dual-reference gochara) + item 28 (daśā-lord transit condition) —
// SHAD_DARSHANA_BRIEF_v2_0.md §3 W1. Both are [J]-kind JOINS over EXISTING substrate
// (no new migration, no new astrological computation): item 8 reuses the EXACT
// house-counting formula `get_av_transit_gating.ts` (marsys://tool/L1/get_av_transit_gating)
// already ships as `houseFromSign` — mirrored here (not imported — platform-mcp cannot
// import platform's registry-layer TS) and applied against TWO natal reference points
// (Moon + Lagna) instead of that capability's single lagna-only parametrization; item 28
// joins the already-computed "which lord is running today" answer
// (marsys://tool/L3/query_active_dashas) against the already-computed daily transit series
// (marsys://tool/L0/query_planet_transit) and the classical dignity reference table
// (bg_dignity_reference, 9 rows, global — read via the SAME direct-SQL route
// register_p1_reference.ts's `ref_dignity_reference_get` already uses). No value here is
// invented: every field traces to an existing table/capability's own output (§N.5 / B.10).

const GOCHARA_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] as const

/** Mirrors get_av_transit_gating.ts's SIGN_NAMES (Aries..Pisces, sidereal, 1-indexed). */
const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

/** Mirrors get_av_transit_gating.ts's `houseFromSign` EXACTLY (same formula, same
 *  semantics: 1-indexed house count of `signNumber` counted from `refSignNumber`).
 *  Duplicated per this lane's established anti-coupling convention (see file header) —
 *  platform-mcp cannot import platform's registry-layer TS module. */
function houseFromSign(signNumber: number, refSignNumber: number): number {
  return ((signNumber - refSignNumber + 12) % 12) + 1
}

interface NatalReferenceSigns {
  lagna_sign_number: number | null
  lagna_fact_id: string | null
  moon_sign_number: number | null
  moon_fact_id: string | null
  ok: boolean
}

/** graha_sign_attributes (chart_facts) rows for LAGNA/MOON, fact_key='sign_num' — the SAME
 *  category get_dignity.ts (marsys://tool/L1/get_dignity) already serves as one of its 6
 *  DIGNITY_CATEGORIES. Confirmed subject codes: 'LAGNA' (get_av_transit_gating.ts), 'MOON'
 *  (ga_sensitive_degree writer tests). */
async function fetchNatalReferenceSigns(
  chartId: string,
  ayanamshaId: string,
  principal: Principal,
): Promise<NatalReferenceSigns> {
  const resp = await callRegistryCapability(
    'marsys://tool/L1/get_dignity',
    { chart_id: chartId, ayanamsha_id: ayanamshaId, categories: ['graha_sign_attributes'] },
    principal,
  )
  if (!resp.ok || !resp.content) {
    return { lagna_sign_number: null, lagna_fact_id: null, moon_sign_number: null, moon_fact_id: null, ok: false }
  }
  const rows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const find = (subject: string) =>
    rows.find((r) => r['fact_subject'] === subject && r['fact_key'] === 'sign_num')
  const lagna = find('LAGNA')
  const moon = find('MOON')
  return {
    lagna_sign_number: typeof lagna?.['fact_value_num'] === 'number' ? (lagna['fact_value_num'] as number) : null,
    lagna_fact_id: typeof lagna?.['fact_id'] === 'string' ? (lagna['fact_id'] as string) : null,
    moon_sign_number: typeof moon?.['fact_value_num'] === 'number' ? (moon['fact_value_num'] as number) : null,
    moon_fact_id: typeof moon?.['fact_id'] === 'string' ? (moon['fact_id'] as string) : null,
    ok: true,
  }
}

/**
 * Why a transit lookup produced no row — the distinction whose ABSENCE caused the ṢAḌ-DARŚANA
 * W1 items 8/28 false-positive coverage claim (Verifier live-acceptance rejection, 2026-07-30).
 *
 * `marsys://tool/L0/query_planet_transit` is a `ToolCapability` whose handler returns the
 * sidecar payload verbatim on success and its OWN `{ ok: false, error, count: 0, rows: [] }`
 * envelope on failure. Both arrive at this facade over HTTP 200 with `{ ok: true, content }`,
 * so `rows: []` ALONE cannot distinguish "this graha genuinely has no ephemeris row for this
 * date" from "the upstream call failed". The prior code read only `resp.ok` (the transport
 * layer), so a 401'd sidecar call — every production call, see query_planet_transit.ts's
 * header — was indistinguishable from a genuine empty and was reported as `reachable: true`
 * / `state: "computed"` with all nine grahas' fields null.
 *
 * `persistent` is the ND-4 half: a deterministic upstream error must never be worded as
 * transient "unreachable this call", because a caller who retries learns nothing.
 */
export interface TransitLookupFailure {
  kind: 'dispatch_unreachable' | 'upstream_error'
  detail: string
  /** True when the failure is a deterministic upstream defect (retrying will not help). */
  persistent: boolean
}

interface PlanetTransitSnapshot {
  planet: string
  sign_number: number | null
  degree_in_sign: number | null
  nakshatra_number: number | null
  is_retrograde: boolean | null
  /** The call completed without error — a `true` here with all-null fields means a GENUINE
   *  empty (no ephemeris row for this graha/date), not a masked failure. */
  ok: boolean
  failure: TransitLookupFailure | null
}

const NULL_TRANSIT_FIELDS = {
  sign_number: null,
  degree_in_sign: null,
  nakshatra_number: null,
  is_retrograde: null,
} as const

/** Single-day snapshot (start_date=end_date=dateISO) via the EXISTING L0 ephemeris
 *  capability (marsys://tool/L0/query_planet_transit — the same substrate
 *  ref_planet_transit_get / query_planet_transit already serve; sidereal-first,
 *  default ayanamsha lahiri_chitrapaksha). Never throws; classifies its own failure mode
 *  (see `TransitLookupFailure`) instead of collapsing every outcome to an empty row. */
async function fetchPlanetTransitSnapshot(
  planet: string,
  dateISO: string,
  principal: Principal,
): Promise<PlanetTransitSnapshot> {
  const resp = await callRegistryCapability(
    'marsys://tool/L0/query_planet_transit',
    { planet, start_date: dateISO, end_date: dateISO },
    principal,
  )
  if (!resp.ok || !resp.content) {
    return {
      planet, ...NULL_TRANSIT_FIELDS, ok: false,
      failure: {
        kind: 'dispatch_unreachable',
        detail: `retrieval-capability dispatch for marsys://tool/L0/query_planet_transit failed (${planet} @ ${dateISO})`,
        persistent: false,
      },
    }
  }
  // The capability's own failure envelope — NOT a genuine empty (see TransitLookupFailure).
  const upstreamOk = resp.content['ok']
  const upstreamError = resp.content['error']
  if (upstreamOk === false || typeof upstreamError === 'string') {
    return {
      planet, ...NULL_TRANSIT_FIELDS, ok: false,
      failure: {
        kind: 'upstream_error',
        detail:
          typeof upstreamError === 'string'
            ? upstreamError
            : 'query_planet_transit reported ok:false without an error string',
        persistent: true,
      },
    }
  }
  const row = (resp.content['rows'] as Array<Record<string, unknown>> | undefined)?.[0]
  // Genuine empty: the call succeeded, the ephemeris simply has no row for this graha/date.
  if (!row) return { planet, ...NULL_TRANSIT_FIELDS, ok: true, failure: null }
  return {
    planet,
    sign_number: typeof row['sign_number'] === 'number' ? (row['sign_number'] as number) : null,
    degree_in_sign: typeof row['degree_in_sign'] === 'number' ? (row['degree_in_sign'] as number) : null,
    nakshatra_number: typeof row['nakshatra_number'] === 'number' ? (row['nakshatra_number'] as number) : null,
    is_retrograde: typeof row['is_retrograde'] === 'boolean' ? (row['is_retrograde'] as boolean) : null,
    ok: true,
    failure: null,
  }
}

/** The shared coverage-reason builder for both transit-backed joins (items 8 + 28), so the
 *  persistent-vs-transient wording (ND-4) is stated in exactly ONE place. */
function transitFailureReason(failure: TransitLookupFailure): string {
  return failure.persistent
    ? `L0 ephemeris capability (query_planet_transit) returned a PERSISTENT upstream error — ` +
      `this is a deterministic upstream failure, not transient unreachability, and retrying ` +
      `this call will reproduce it: ${failure.detail}`
    : `L0 ephemeris capability (query_planet_transit) could not be dispatched this call ` +
      `(transient): ${failure.detail}`
}

export interface GocharaDualReferenceRow {
  planet: string
  transit_sign_number: number | null
  transit_sign_name: string | null
  degree_in_sign: number | null
  is_retrograde: boolean | null
  house_from_moon: number | null
  house_from_lagna: number | null
}

/** Item 8 (SHAD_DARSHANA_BRIEF_v2_0.md item 8, wave W1): for every classical graha, the
 *  house it is CURRENTLY transiting counted from BOTH natal reference points at once
 *  (Moon — the primary classical gochara reference; Lagna — the secondary/confirmatory
 *  reference), served side by side rather than the caller silently defaulting to one. Pure
 *  arithmetic over two already-computed facts (natal reference sign + transiting sign) —
 *  no new astrological computation (§N.5/B.10), no subjective grading (Gate W1: objective
 *  fields only, no favorable/unfavorable judgment call). */
async function computeGocharaDualReference(
  asOfDate: string,
  natal: NatalReferenceSigns,
  principal: Principal,
): Promise<{
  rows: GocharaDualReferenceRow[]
  transitReachable: boolean
  transitFailure: TransitLookupFailure | null
  /** THE earned-signal detector (CLAUDE.md §N.8) for item 8: how many of the nine served rows
   *  actually carry a transit sign. `coverage`/`*_reachable` are derived from THIS, not from
   *  "the HTTP call returned 200" — the substitution that produced the false-positive claim. */
  rowsWithTransitData: number
}> {
  const snapshots = await Promise.all(GOCHARA_PLANETS.map((p) => fetchPlanetTransitSnapshot(p, asOfDate, principal)))
  const transitReachable = snapshots.some((s) => s.ok)
  const transitFailure = snapshots.find((s) => s.failure != null)?.failure ?? null
  const rowsWithTransitData = snapshots.filter((s) => s.sign_number != null).length
  const rows: GocharaDualReferenceRow[] = snapshots.map((s) => ({
    planet: s.planet,
    transit_sign_number: s.sign_number,
    transit_sign_name: s.sign_number ? (SIGN_NAMES[s.sign_number - 1] ?? null) : null,
    degree_in_sign: s.degree_in_sign,
    is_retrograde: s.is_retrograde,
    house_from_moon:
      s.sign_number != null && natal.moon_sign_number != null ? houseFromSign(s.sign_number, natal.moon_sign_number) : null,
    house_from_lagna:
      s.sign_number != null && natal.lagna_sign_number != null ? houseFromSign(s.sign_number, natal.lagna_sign_number) : null,
  }))
  return { rows, transitReachable, transitFailure, rowsWithTransitData }
}

// ── W3 item 16 (Kota-Chakra) + item 17 (Sudarśana-Chakra year-wheel) —
// SHAD_DARSHANA_BRIEF_v2_0.md §3 W3, Lane w3-kota-sudarshana. Both are [N]-kind NEW
// COMPUTATIONS with their own per-chart writers (ka_kota_chakra / ka_sudarshana_varsha,
// migrations 520/521) and asset_registry rows — unlike the [J]-kind joins above, this facade
// only READS already-computed rows from those writers' tables via the registry capabilities
// query_kota_chakra / query_sudarshana_varsha; it never recomputes the ring/progression math
// here (§N.5). Only the CURRENT row(s) are served on NOW — the forward horizon (upcoming
// ring changes / future varsha years) is kala_ahead_get's job, a documented follow-on the
// same query capabilities already support (paging the non-current rows) but which is not
// wired into ahead.ts in this PR.

export interface KotaChakraRow {
  graha: string
  nakshatra_name: string
  count_from_janma: number
  kota_ring: string
  is_natural_malefic: boolean
  posture: string
  severity: string
  window_start: string
  window_end: string
  start_truncated: boolean
  end_truncated: boolean
  ring_table_citation: string
  uncited_extension: boolean
}

/** item 16: current Kota-Chakra ring occupancy per graha (one row per graha whose current
 *  ring-run contains `asOfDate`). Honest-empty (not a masked failure) when the writer has
 *  not yet built this chart, or the scanned horizon does not cover `asOfDate`. */
async function fetchKotaChakraNow(
  chartId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ reachable: boolean; rows: KotaChakraRow[] }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_kota_chakra',
    { chart_id: chartId, as_of: asOfDate },
    principal,
  )
  if (!resp.ok || !resp.content) return { reachable: false, rows: [] }
  const rawRows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const rows: KotaChakraRow[] = rawRows
    .filter((r) => r['is_current'] === true)
    .map((r) => ({
      graha: String(r['graha']),
      nakshatra_name: String(r['nakshatra_name']),
      count_from_janma: Number(r['count_from_janma']),
      kota_ring: String(r['kota_ring']),
      is_natural_malefic: Boolean(r['is_natural_malefic']),
      posture: String(r['posture']),
      severity: String(r['severity']),
      window_start: String(r['window_start']),
      window_end: String(r['window_end']),
      start_truncated: Boolean(r['start_truncated']),
      end_truncated: Boolean(r['end_truncated']),
      ring_table_citation: String(r['ring_table_citation']),
      uncited_extension: Boolean(r['uncited_extension']),
    }))
  return { reachable: true, rows }
}

export interface SudarshanaVarshaYearNow {
  varsha_year: number
  window_start: string
  window_end: string
  jl_active_sign_name: string
  cl_active_sign_name: string
  sl_active_sign_name: string
  tri_lagna_convergence: boolean
}

/** item 17: the CURRENT varsha year's tri-lagna progressed signs. `current: null` (with
 *  `reachable: true`) is a genuine honest-empty — e.g. asOfDate predates birth, or exceeds
 *  the 120-year built horizon — never fabricated. */
async function fetchSudarshanaVarshaNow(
  chartId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ reachable: boolean; current: SudarshanaVarshaYearNow | null }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_sudarshana_varsha',
    { chart_id: chartId, as_of: asOfDate },
    principal,
  )
  if (!resp.ok || !resp.content) return { reachable: false, current: null }
  const rawRows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const currentRaw = rawRows.find((r) => r['is_current'] === true)
  if (!currentRaw) return { reachable: true, current: null }
  return {
    reachable: true,
    current: {
      varsha_year: Number(currentRaw['varsha_year']),
      window_start: String(currentRaw['window_start']),
      window_end: String(currentRaw['window_end']),
      jl_active_sign_name: String(currentRaw['jl_active_sign_name']),
      cl_active_sign_name: String(currentRaw['cl_active_sign_name']),
      sl_active_sign_name: String(currentRaw['sl_active_sign_name']),
      tri_lagna_convergence: Boolean(currentRaw['tri_lagna_convergence']),
    },
  }
}

// ── W3 item 4 (Moorti-nirṇaya) + item 5 (Vedha application + Sarvatobhadra —
// closes R-19) — SHAD_DARSHANA_BRIEF_v2_0.md §3 W3, Lane w3-moorti-vedha. Both are new
// per-chart writers (ka_moorti_nirnaya / ka_vedha_gochara, migrations 525/526) served
// read-only here via query_moorti_nirnaya / query_vedha_gochara (§N.5 — this facade never
// recomputes the moorti/vedha arithmetic). Only the CURRENT row(s) are served on NOW; the
// forward horizon is kala_ahead_get's job (a documented follow-on, not wired in this PR,
// matching kota_chakra/sudarshana_varsha's own precedent).

export interface MoortiNirnayaRow {
  graha: string
  target_sign_name: string
  window_start: string
  window_end: string
  moorti_computed: boolean
  moorti_name: string | null
  quality_tier: number | null
  phala_brief: string | null
  moorti_classical_citation: string | null
}

/** item 4: current Moorti-nirṇaya row per graha (one row per graha whose current
 *  sign-occupancy window contains `asOfDate`). Honest-empty (not a masked failure) when the
 *  writer has not yet built this chart, or the scanned horizon does not cover `asOfDate`.
 *  `moorti_computed=false` rows (an unverified/truncated ingress — see writer docstring)
 *  carry null moorti fields verbatim, never backfilled. */
async function fetchMoortiNirnayaNow(
  chartId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ reachable: boolean; rows: MoortiNirnayaRow[] }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_moorti_nirnaya',
    { chart_id: chartId, as_of: asOfDate },
    principal,
  )
  if (!resp.ok || !resp.content) return { reachable: false, rows: [] }
  const rawRows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const rows: MoortiNirnayaRow[] = rawRows
    .filter((r) => r['is_current'] === true)
    .map((r) => ({
      graha: String(r['graha']),
      target_sign_name: String(r['target_sign_name']),
      window_start: String(r['window_start']),
      window_end: String(r['window_end']),
      moorti_computed: Boolean(r['moorti_computed']),
      moorti_name: r['moorti_name'] != null ? String(r['moorti_name']) : null,
      quality_tier: r['quality_tier'] != null ? Number(r['quality_tier']) : null,
      phala_brief: r['phala_brief'] != null ? String(r['phala_brief']) : null,
      moorti_classical_citation: r['moorti_classical_citation'] != null ? String(r['moorti_classical_citation']) : null,
    }))
  return { reachable: true, rows }
}

export interface VedhaGocharaRow {
  vedha_kind: 'house_vedha' | 'sarvatobhadra' | 'latta'
  graha: string
  window_start: string
  window_end: string
  classical_citation: string
  uncited_extension: boolean
  /** ADJUDICATION-11 Part 3: populated only on vedha_kind='sarvatobhadra' rows
   *  ('db_sourced_grid' | 'algorithmic_approximation'); null on house_vedha/latta. */
  grid_basis: string | null
  /** ADJUDICATION-11 Part 3: the bg_sarvatobhadra_grid school_tag that supplied this row's
   *  pairing, when grid_basis='db_sourced_grid' via that table specifically; null otherwise
   *  (including every row as of this writing, since that table is registered empty). */
  grid_school_tag: string | null
  detail: Record<string, unknown>
}

/** item 5 (closes R-19, CLOSED-PARTIAL-BY-DESIGN per ADJUDICATION-11): current vedha rows
 *  (house_vedha, sarvatobhadra, and latta kinds, never conflated — §N.6) whose window
 *  contains `asOfDate`. Honest-empty when the writer has not yet built this chart, or no
 *  vedha-checkable transit / sarvatobhadra-dwelling / latta-affliction is currently active —
 *  an empty result here is the classically NORMAL case (most days carry no active vedha),
 *  not a failure. */
async function fetchVedhaGocharaNow(
  chartId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ reachable: boolean; rows: VedhaGocharaRow[] }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_vedha_gochara',
    { chart_id: chartId, as_of: asOfDate },
    principal,
  )
  if (!resp.ok || !resp.content) return { reachable: false, rows: [] }
  const rawRows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const rows: VedhaGocharaRow[] = rawRows
    .filter((r) => r['is_current'] === true)
    .map((r) => ({
      vedha_kind: String(r['vedha_kind']) as 'house_vedha' | 'sarvatobhadra' | 'latta',
      graha: String(r['graha']),
      window_start: String(r['window_start']),
      window_end: String(r['window_end']),
      classical_citation: String(r['classical_citation']),
      uncited_extension: Boolean(r['uncited_extension']),
      grid_basis: r['grid_basis'] != null ? String(r['grid_basis']) : null,
      grid_school_tag: r['grid_school_tag'] != null ? String(r['grid_school_tag']) : null,
      detail: (r['detail'] as Record<string, unknown> | undefined) ?? {},
    }))
  return { reachable: true, rows }
}

// ── W3 item 13 (Tithi-Praveśa, lunar-return annual chart) — SHAD_DARSHANA_BRIEF_v2_0.md
// §3 W3, Lane w3-tithi-pravesha. New per-chart writer (ka_tithi_pravesha, migration 531)
// served read-only here via query_tithi_pravesha (§N.5 — this facade never recomputes the
// lunar-return root-find). Only the CURRENT praveśa-year row is served on NOW; the forward
// horizon is kala_ahead_get's job (a documented follow-on, not wired in this PR, matching
// kota_chakra/sudarshana_varsha's own precedent).

export interface TithiPraveshaYearNow {
  pravesha_year: number
  window_start: string
  window_end: string
  pravesha_lagna_sign_name: string | null
  pravesha_lagna_degree: number | null
  verification_pass_status: string
  classical_source_citation: string
}

/** item 13: the CURRENT praveśa year's lunar-return annual chart summary. `current: null`
 *  (with `reachable: true`) is a genuine honest-empty — e.g. asOfDate predates birth, or
 *  exceeds the 120-year built horizon — never fabricated. */
async function fetchTithiPraveshaNow(
  chartId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ reachable: boolean; current: TithiPraveshaYearNow | null }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_tithi_pravesha',
    { chart_id: chartId, as_of: asOfDate },
    principal,
  )
  if (!resp.ok || !resp.content) return { reachable: false, current: null }
  const rawRows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const currentRaw = rawRows.find((r) => r['is_current'] === true)
  if (!currentRaw) return { reachable: true, current: null }
  return {
    reachable: true,
    current: {
      pravesha_year: Number(currentRaw['pravesha_year']),
      window_start: String(currentRaw['window_start']),
      window_end: String(currentRaw['window_end']),
      pravesha_lagna_sign_name: currentRaw['pravesha_lagna_sign_name'] != null ? String(currentRaw['pravesha_lagna_sign_name']) : null,
      pravesha_lagna_degree: currentRaw['pravesha_lagna_degree'] != null ? Number(currentRaw['pravesha_lagna_degree']) : null,
      verification_pass_status: String(currentRaw['verification_pass_status']),
      classical_source_citation: String(currentRaw['classical_source_citation']),
    },
  }
}

interface DignityReferenceRow {
  graha: string
  exaltation_sign: string | null
  debilitation_sign: string | null
  own_signs: string[] | null
}

/** Reads the SAME structured global reference table (bg_dignity_reference, 9 rows, one per
 *  graha — migration 250/298) that `ref_dignity_reference_get` (register_p1_reference.ts)
 *  already serves by planet — via the same direct-SQL platform route
 *  (`/api/mcp/db/query`), self-contained per this lane's anti-coupling convention (not
 *  imported from register_p1_reference.ts). Read-only, global, no chart_id. */
async function fetchDignityReference(graha: string, principal: Principal): Promise<DignityReferenceRow | null> {
  try {
    const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-mcp-internal-token': MCP_INTERNAL_TOKEN,
        'x-mcp-user': principal.user_uid,
        'x-mcp-key-id': principal.key_id,
      },
      body: JSON.stringify({
        sql: `SELECT graha, exaltation_sign, debilitation_sign, own_signs FROM bg_dignity_reference WHERE LOWER(graha) = LOWER($1)`,
        params: [graha],
      }),
      signal: AbortSignal.timeout(10_000),
    })
    if (!res.ok) return null
    const data = (await res.json()) as { rows?: Array<Record<string, unknown>> }
    const row = data.rows?.[0]
    if (!row) return null
    return {
      graha: String(row['graha'] ?? graha),
      exaltation_sign: typeof row['exaltation_sign'] === 'string' ? (row['exaltation_sign'] as string) : null,
      debilitation_sign: typeof row['debilitation_sign'] === 'string' ? (row['debilitation_sign'] as string) : null,
      own_signs: Array.isArray(row['own_signs']) ? (row['own_signs'] as string[]) : null,
    }
  } catch {
    return null
  }
}

export type DashaLordDignityState = 'exalted' | 'debilitated' | 'own_sign' | 'neutral' | null

function classifyDashaLordDignity(signName: string | null, dignity: DignityReferenceRow | null): DashaLordDignityState {
  if (!signName || !dignity) return null
  if (dignity.exaltation_sign === signName) return 'exalted'
  if (dignity.debilitation_sign === signName) return 'debilitated'
  if (dignity.own_signs?.includes(signName)) return 'own_sign'
  return 'neutral'
}

export interface DashaLordTransitCondition {
  level_name: string
  lord_graha: string
  lord_natal_sign: string | null
  as_of_date: string
  transit_sign_number: number | null
  transit_sign_name: string | null
  degree_in_sign: number | null
  nakshatra_number: number | null
  is_retrograde: boolean | null
  house_from_lagna: number | null
  dignity: DashaLordDignityState
  dignity_basis: { exaltation_sign: string | null; debilitation_sign: string | null; own_signs: string[] | null } | null
}

interface ActiveDashaChainEntry {
  level_n: number
  level_name: string
  lord_graha: string
  lord_sign: string | null
}

/** "Which daśā am I running?" via the EXISTING L3 convenience face
 *  (marsys://tool/L3/query_active_dashas, EL-33/DR-14) — filtered to Vimśottarī level ≤2
 *  (Mahā/Antar) at a single date. Never re-derives the active chain; reads it verbatim. */
async function fetchActiveVimshottariChain(
  chartId: string,
  ayanamshaId: string,
  dateISO: string,
  principal: Principal,
): Promise<{ entries: ActiveDashaChainEntry[]; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_active_dashas',
    { chart_id: chartId, date: dateISO, ayanamsha_id: ayanamshaId, systems: 'vimshottari', max_level: 2 },
    principal,
  )
  if (!resp.ok || !resp.content) return { entries: [], ok: false }
  const systems = (resp.content['systems'] as Array<Record<string, unknown>> | undefined) ?? []
  const vimshottari = systems.find((s) => s['system_id'] === 'vimshottari')
  const chain = (vimshottari?.['active_chain'] as Array<Record<string, unknown>> | undefined) ?? []
  return {
    ok: true,
    entries: chain.map((c) => ({
      level_n: typeof c['level_n'] === 'number' ? (c['level_n'] as number) : 0,
      level_name: typeof c['level_name'] === 'string' ? (c['level_name'] as string) : `L${c['level_n']}`,
      lord_graha: String(c['lord_graha'] ?? ''),
      lord_sign: typeof c['lord_sign'] === 'string' ? (c['lord_sign'] as string) : null,
    })),
  }
}

/** Item 28 (SHAD_DARSHANA_BRIEF_v2_0.md item 28, wave W1): for the currently-running
 *  Mahādaśā and Antardaśā lord, report its OWN transit condition at `snapshotDate`
 *  (sign/house-from-lagna/dignity vs. classical exaltation-debilitation-own-sign) — a
 *  Law-2-concurrence-relevant signal ("is the period lord itself well-placed right now").
 *  JOIN over three existing substrates (active-dasha chain + daily ephemeris + classical
 *  dignity reference); dedupes when MD and AD share the same graha. */
async function computeDashaLordTransitCondition(
  chartId: string,
  ayanamshaId: string,
  identifyAsOfDate: string,
  snapshotDate: string,
  lagnaSignNumber: number | null,
  principal: Principal,
): Promise<{
  rows: DashaLordTransitCondition[]
  chainReachable: boolean
  transitReachable: boolean
  transitFailure: TransitLookupFailure | null
  /** Earned-signal detector (CLAUDE.md §N.8) for item 28 — see computeGocharaDualReference. */
  rowsWithTransitData: number
}> {
  const chain = await fetchActiveVimshottariChain(chartId, ayanamshaId, identifyAsOfDate, principal)
  if (!chain.ok || chain.entries.length === 0) {
    return { rows: [], chainReachable: chain.ok, transitReachable: true, transitFailure: null, rowsWithTransitData: 0 }
  }
  const uniqueGrahas = Array.from(new Set(chain.entries.map((e) => e.lord_graha).filter(Boolean)))
  const [snapshots, dignities] = await Promise.all([
    Promise.all(uniqueGrahas.map((g) => fetchPlanetTransitSnapshot(g, snapshotDate, principal))),
    Promise.all(uniqueGrahas.map((g) => fetchDignityReference(g, principal))),
  ])
  const snapshotByGraha = new Map(snapshots.map((s) => [s.planet, s]))
  const dignityByGraha = new Map(uniqueGrahas.map((g, i) => [g, dignities[i] ?? null]))
  const transitReachable = snapshots.some((s) => s.ok)
  const transitFailure = snapshots.find((s) => s.failure != null)?.failure ?? null

  const rows: DashaLordTransitCondition[] = chain.entries.map((entry) => {
    const snap = snapshotByGraha.get(entry.lord_graha)
    const signName = snap?.sign_number ? (SIGN_NAMES[snap.sign_number - 1] ?? null) : null
    const dignityRow = dignityByGraha.get(entry.lord_graha) ?? null
    return {
      level_name: entry.level_name,
      lord_graha: entry.lord_graha,
      lord_natal_sign: entry.lord_sign,
      as_of_date: snapshotDate,
      transit_sign_number: snap?.sign_number ?? null,
      transit_sign_name: signName,
      degree_in_sign: snap?.degree_in_sign ?? null,
      nakshatra_number: snap?.nakshatra_number ?? null,
      is_retrograde: snap?.is_retrograde ?? null,
      house_from_lagna:
        snap?.sign_number != null && lagnaSignNumber != null ? houseFromSign(snap.sign_number, lagnaSignNumber) : null,
      dignity: classifyDashaLordDignity(signName, dignityRow),
      dignity_basis: dignityRow
        ? { exaltation_sign: dignityRow.exaltation_sign, debilitation_sign: dignityRow.debilitation_sign, own_signs: dignityRow.own_signs }
        : null,
    }
  })
  const rowsWithTransitData = rows.filter((r) => r.transit_sign_number != null).length
  return { rows, chainReachable: chain.ok, transitReachable, transitFailure, rowsWithTransitData }
}

// ── Item 24-lite (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1 "24-lite... Sūkṣma boundaries as
// intervals"; design authority KALA_SIX_VIEWS_DESIGN_v2_0.md §A.1 "below PD"): the
// CURRENTLY-RUNNING Sūkṣma-level (level_n=4) Vimśottarī period's own start/end boundary
// timestamps, already computed and stored in `chart_dashas` (marsys://tool/L1/get_dashas,
// `fields=all` for `start_iso`/`end_iso`/`duration_days`) — re-presented with the
// documented lite-v0 interval convention from `lib/kala_uncertainty.ts`. NO new
// computation: this reads the exact row `get_dashas` already serves and bounds it.
async function fetchSukshmaBoundaryUncertainty(
  chartId: string,
  ayanamshaId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ intervals: SukshmaBoundaryInterval[]; reachable: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L1/get_dashas',
    { chart_id: chartId, ayanamsha_id: ayanamshaId, system: 'vimshottari', level: 4, as_of_date: asOfDate, fields: 'all' },
    principal,
  )
  if (!resp.ok) return { intervals: [], reachable: false }
  const rows = (resp.content?.['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const row = rows[0]
  if (!row) return { intervals: [], reachable: true }
  return {
    intervals: buildSukshmaBoundaryIntervals({
      system_id: String(row['system_id'] ?? 'vimshottari'),
      lord_graha: String(row['lord_graha'] ?? ''),
      start_iso: typeof row['start_iso'] === 'string' ? (row['start_iso'] as string) : null,
      end_iso: typeof row['end_iso'] === 'string' ? (row['end_iso'] as string) : null,
      duration_days: (row['duration_days'] as number | string | null | undefined) ?? null,
    }),
    reachable: true,
  }
}

// ── W1 item 1-lite (daśā-sandhi bands) — SHAD_DARSHANA_BRIEF_v2_0.md §3 W1: "sandhi bands
// from existing period spans; full calendar W3". [J]-kind JOIN: pure interval arithmetic over
// the SAME already-computed start_date/end_date bounds `query_active_dashas` already returns
// for the active Vimśottarī Mahādaśā/Antardaśā chain (no new astrological computation, no new
// migration — §N.5/B.10). Self-contained fetch (not reusing `fetchActiveVimshottariChain`
// above, which discards start_date/end_date for item 28's purposes) per this file's own
// established anti-coupling convention (see file header): a second, independent call to the
// same capability rather than widening a shared helper's return shape underneath item 28.
//
// Band-width convention (documented, not fabricated — KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2:
// "sandhi flags with configurable orb (last/first ~3% of period span) at every level"): for
// EACH period boundary (a period's start date and its end date), the band is ± round(3% ×
// that period's OWN span in days) around the boundary. LITE SIMPLIFICATION, stated plainly on
// the served `band_convention` field: the classical formulation straddles a boundary with the
// LAST 3% of the outgoing period and the FIRST 3% of the incoming period (two different
// spans); this lite pass uses the SAME period's own span on both sides of each of its two
// boundaries (its own start and its own end) rather than fetching the adjacent period, since
// only ONE query_active_dashas call (the currently active chain) is available at W1 without a
// second query per boundary. The full two-period asymmetric daśā-sandhi calendar (all levels,
// both directions) is item 1-full (wave W3) — SHAD_DARSHANA_BRIEF_v2_0.md item 1.

const SANDHI_BAND_FRACTION = 0.03 // KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2's documented "~3%"
const SANDHI_BAND_CONVENTION =
  'LITE convention (item 1-lite, wave W1): each daśā-period boundary (its own start date AND ' +
  'its own end date) carries a band of ± round(3% × that period\'s own span in days), per ' +
  'KALA_SIX_VIEWS_DESIGN_v1_0.md §1.2 ("configurable orb, last/first ~3% of period span"). ' +
  'Simplification: uses the SAME period\'s span on both sides of each boundary rather than the ' +
  'full classical asymmetric last-outgoing/first-incoming convention (which needs the adjacent ' +
  'period too) — that full two-period, all-level, both-direction calendar is item 1-full (W3). ' +
  'Scope: bands levels 1–4 of the active Vimśottarī chain (Mahādaśā, Antardaśā, Pratyantardaśā, ' +
  'Sūkṣmadaśā). Level 5 (Prāṇa-daśā) is NEVER computed for any chart by design ' +
  '(ga_dashas_writer.py "CRITICAL OVERRIDE 1... ZERO level_n=5") — see sukshma_boundary_uncertainty ' +
  'convention for the same reasoning applied to the Sūkṣma-boundary uncertainty field.'

interface ActiveDashaBoundaryEntry {
  level_n: number
  level_name: string
  lord_graha: string
  start_date: string | null
  end_date: string | null
}

/** Self-contained duplicate of `fetchActiveVimshottariChain`'s query, capturing start_date/
 *  end_date (which that function discards) — the raw bounds `query_active_dashas` already
 *  returns per active-chain entry, never re-derived. */
async function fetchVimshottariMdAdBoundaries(
  chartId: string,
  ayanamshaId: string,
  dateISO: string,
  principal: Principal,
): Promise<{ entries: ActiveDashaBoundaryEntry[]; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_active_dashas',
    { chart_id: chartId, date: dateISO, ayanamsha_id: ayanamshaId, systems: 'vimshottari', max_level: 4 },
    principal,
  )
  if (!resp.ok || !resp.content) return { entries: [], ok: false }
  const systems = (resp.content['systems'] as Array<Record<string, unknown>> | undefined) ?? []
  const vimshottari = systems.find((s) => s['system_id'] === 'vimshottari')
  const chain = (vimshottari?.['active_chain'] as Array<Record<string, unknown>> | undefined) ?? []
  return {
    ok: true,
    entries: chain.map((c) => ({
      level_n: typeof c['level_n'] === 'number' ? (c['level_n'] as number) : 0,
      level_name: typeof c['level_name'] === 'string' ? (c['level_name'] as string) : `L${c['level_n']}`,
      lord_graha: String(c['lord_graha'] ?? ''),
      start_date: typeof c['start_date'] === 'string' ? (c['start_date'] as string) : null,
      end_date: typeof c['end_date'] === 'string' ? (c['end_date'] as string) : null,
    })),
  }
}

export interface DashaSandhiBand {
  level_n: number
  level_name: string
  lord_graha: string
  boundary_kind: 'period_start' | 'period_end'
  boundary_date: string
  band_start_date: string
  band_end_date: string
  band_width_days: number
  is_now_within_band: boolean
}

export interface DashaSandhiResult {
  as_of_date: string
  band_convention: string
  bands: DashaSandhiBand[]
}

const MS_PER_DAY = 86_400_000

function daysBetween(fromISO: string, toISO: string): number {
  return Math.round((Date.parse(toISO) - Date.parse(fromISO)) / MS_PER_DAY)
}

function addDays(dateISO: string, days: number): string {
  const d = new Date(`${dateISO}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

function isDateWithinInclusive(dateISO: string, startISO: string, endISO: string): boolean {
  const d = Date.parse(dateISO)
  return d >= Date.parse(startISO) && d <= Date.parse(endISO)
}

function buildBoundaryBand(
  entry: ActiveDashaBoundaryEntry,
  boundaryKind: 'period_start' | 'period_end',
  asOfDate: string,
): DashaSandhiBand | null {
  if (!entry.start_date || !entry.end_date) return null
  const spanDays = daysBetween(entry.start_date, entry.end_date)
  if (spanDays <= 0) return null
  const bandWidthDays = Math.max(1, Math.round(spanDays * SANDHI_BAND_FRACTION))
  const boundaryDate = boundaryKind === 'period_start' ? entry.start_date : entry.end_date
  const bandStart = addDays(boundaryDate, -bandWidthDays)
  const bandEnd = addDays(boundaryDate, bandWidthDays)
  return {
    level_n: entry.level_n,
    level_name: entry.level_name,
    lord_graha: entry.lord_graha,
    boundary_kind: boundaryKind,
    boundary_date: boundaryDate,
    band_start_date: bandStart,
    band_end_date: bandEnd,
    band_width_days: bandWidthDays,
    is_now_within_band: isDateWithinInclusive(asOfDate, bandStart, bandEnd),
  }
}

/** Item 1-lite (SHAD_DARSHANA_BRIEF_v2_0.md item 1, wave W1): a band around every currently-
 *  active Vimśottarī Mahādaśā/Antardaśā period's start AND end boundary, computed purely from
 *  the period's own already-computed span — see the doc-comment above for the full band-width
 *  convention and its documented lite simplification. */
async function computeDashaSandhi(
  chartId: string,
  ayanamshaId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ result: DashaSandhiResult | null; chainReachable: boolean }> {
  const chain = await fetchVimshottariMdAdBoundaries(chartId, ayanamshaId, asOfDate, principal)
  if (!chain.ok) return { result: null, chainReachable: false }
  if (chain.entries.length === 0) return { result: null, chainReachable: true }

  const bands: DashaSandhiBand[] = []
  for (const entry of chain.entries) {
    const startBand = buildBoundaryBand(entry, 'period_start', asOfDate)
    const endBand = buildBoundaryBand(entry, 'period_end', asOfDate)
    if (startBand) bands.push(startBand)
    if (endBand) bands.push(endBand)
  }
  if (bands.length === 0) return { result: null, chainReachable: true }

  return {
    result: { as_of_date: asOfDate, band_convention: SANDHI_BAND_CONVENTION, bands },
    chainReachable: true,
  }
}

function dualOutput(data: unknown, toolName = 'kala_now_get') {
  let finalData: unknown = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const sections = autoDetectTrimmableSections(obj, toolName)
    finalData = finalizeMcpBudget(obj, { maxKb: 40, sections })
  }
  const structuredContent = { type: 'object' as const, object: finalData }
  const json = JSON.stringify(finalData)
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

function errOut(tool: string, msg: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: msg, tool, ...extra }, tool), isError: true as const }
}

// ── Window-family shape (query_temporal_activation's `window_families` /
// `forward_windows` rows — read verbatim, never re-derived) ────────────────────────

interface WindowFamily {
  window_start: string | null
  window_end: string | null
  window_peak?: string | null
  member_count: number
  member_signal_ids?: string[]
  signature_classes?: string[]
  domains?: string[]
  max_orb_strength?: number
  [key: string]: unknown
}

const WINDOW_CLASS_GLOSS: Readonly<Record<string, string>> = {
  CLASSIFY_RESIDUAL: 'residual pattern',
  DIGNITY: 'planetary dignity',
  DISPOSITOR_RELATIONAL: 'dispositor relationship',
  DOSHA: 'affliction pattern',
  SUBSYSTEM: 'supporting subsystem',
  YOGA: 'yoga pattern',
  dasha_ingress: 'daśā ingress',
  dasha_transit_conjunction: 'daśā–transit conjunction',
}

function formatWindowClasses(classes: string[] | null | undefined): string {
  if (!classes || classes.length === 0) return 'unlabeled'
  return classes
    .map((value) => WINDOW_CLASS_GLOSS[value] ?? value.replace(/[_-]+/g, ' ').toLowerCase())
    .join(' + ')
}

interface DarshanaRow {
  effective_score: number | null
  net_label: string | null
  window_start?: string | null
  window_end?: string | null
  obstruction_summary?: unknown
  narrative?: unknown
  [key: string]: unknown
}

// ── W1 item 32/29 join shapes (read verbatim from call_panchanga_service /
// get_panchanga — never re-derived; §N.5) ──────────────────────────────────────────

interface PanchangAnga {
  id: number
  name: string
  end_utc: string | null
  [key: string]: unknown
}

interface PanchangTiming {
  label: string
  start_utc: string | null
  end_utc: string | null
  [key: string]: unknown
}

interface PanchangPlanetState {
  name: string
  sign_id: number
  sign_name: string
  nakshatra_id: number
  nakshatra_name: string
  [key: string]: unknown
}

interface PanchangPayload {
  tithi?: PanchangAnga
  nakshatra?: PanchangAnga
  vara?: PanchangAnga
  inauspicious?: PanchangTiming[]
  hora?: PanchangTiming[]
  planets?: Record<string, PanchangPlanetState>
  [key: string]: unknown
}

interface NativeContext {
  chart_id: string
  moon_sign_id: number
  moon_sign_name: string
  birth_nakshatra_id: number
  birth_nakshatra_name: string
  [key: string]: unknown
}

interface NatalPanchangaFactRow {
  fact_id: string
  fact_category: string
  ayanamsha_id: string
  fact_key: string
  fact_value_num: number | null
  fact_value_text: string | null
  [key: string]: unknown
}

// Diśā-śūla (Disha Vasa): vara_id → direction to avoid for travel. Mirrors
// panchang_engine/shastra_tables.py's DISHA_SHUL_TABLE verbatim (Source: DP published
// tables) — not a new rule; ga_panchanga_writer._emit_disha_shul emits the identical
// mapping for the BIRTH-moment vara (a natal fact); this is the same classical table
// applied to TODAY's vara (a daily-varying join, not a natal fact).
const DISHA_SHUL_TABLE: Record<number, string> = {
  1: 'West', 2: 'East', 3: 'North', 4: 'North', 5: 'South', 6: 'West', 7: 'East',
}

function findTimingByLabel(timings: PanchangTiming[] | undefined, label: string): PanchangTiming | null {
  return (timings ?? []).find((t) => t.label === label) ?? null
}

/** `null` is the honest value when the [start,end) instant window cannot be evaluated
 *  (either bound missing, or unparsable) — never defaulted to true/false (B.10). */
function isNowWithinWindow(startUtc: string | null | undefined, endUtc: string | null | undefined, nowIso: string): boolean | null {
  if (!startUtc || !endUtc) return null
  const start = Date.parse(startUtc)
  const end = Date.parse(endUtc)
  const now = Date.parse(nowIso)
  if (Number.isNaN(start) || Number.isNaN(end) || Number.isNaN(now)) return null
  return now >= start && now < end
}

/** Finds the hora Timing whose [start,end) contains `nowIso`, and extracts the lord name
 *  from its `hora_<planet>` label (panchang_engine/timings.py compute_hora — never
 *  re-derived, only parsed back out of the label the engine already emitted). */
function findCurrentHora(horaList: PanchangTiming[] | undefined, nowIso: string): { entry: PanchangTiming; lord: string } | null {
  const now = Date.parse(nowIso)
  if (Number.isNaN(now)) return null
  for (const entry of horaList ?? []) {
    const start = entry.start_utc ? Date.parse(entry.start_utc) : NaN
    const end = entry.end_utc ? Date.parse(entry.end_utc) : NaN
    if (Number.isNaN(start) || Number.isNaN(end)) continue
    if (now >= start && now < end) {
      const planet = entry.label.startsWith('hora_') ? entry.label.slice('hora_'.length) : entry.label
      const lord = planet.length > 0 ? planet[0]!.toUpperCase() + planet.slice(1) : planet
      return { entry, lord }
    }
  }
  return null
}

/** Chāndra Bala house-count (Muhūrta Chintāmaṇi §4) — transit Moon's house from natal
 *  Moon rāśi, 1-indexed, same-sign = house 1. Chandrāṣṭama = house 8. Mirrors
 *  platform/src/lib/panchang/chandra_bala.ts's identical formula (inlined per this file's
 *  no-cross-package-import convention). */
function houseFromNatalMoon(nativeMoonSignId: number, transitMoonSignId: number): number {
  const nativeIdx = nativeMoonSignId - 1
  const transitIdx = transitMoonSignId - 1
  return ((transitIdx - nativeIdx + 12) % 12) + 1
}

// panchanga_tithi/panchanga_vara are ayanamsha-INVARIANT (single row); panchanga_nakshatra_moon
// carries one row per ayanamsha — pin to the chart's resolved ayanamsha so a multi-ayanamsha
// chart doesn't silently pick whichever row sorts first (the fact-category-pin-lint class
// of defect this codebase's §N.7 explicitly guards against).
function pickNatalPanchangaNum(
  rows: NatalPanchangaFactRow[], category: string, factKey: string, ayanamshaId: string,
): { value: number | null; fact_id: string | null } {
  const row = rows.find(
    (r) => r.fact_category === category && r.fact_key === factKey &&
      (r.ayanamsha_id === ayanamshaId || r.ayanamsha_id === 'INVARIANT'),
  )
  return { value: row?.fact_value_num ?? null, fact_id: row?.fact_id ?? null }
}

function pickNatalPanchangaText(
  rows: NatalPanchangaFactRow[], category: string, factKey: string, ayanamshaId: string,
): string | null {
  return rows.find(
    (r) => r.fact_category === category && r.fact_key === factKey &&
      (r.ayanamsha_id === ayanamshaId || r.ayanamsha_id === 'INVARIANT'),
  )?.fact_value_text ?? null
}

// ── The reading (template-over-computed-data — B.10; no generative call) ───────────

function buildNowReading(params: {
  asOfDate: string
  windowFamilies: WindowFamily[]
  darshana: DarshanaRow | null
  windowsOk: boolean
  darshanaOk: boolean
}): ArgumentReading {
  const { asOfDate, windowFamilies, darshana, windowsOk, darshanaOk } = params
  const top = windowFamilies[0]

  const thesisParts: string[] = []
  if (!windowsOk) {
    thesisParts.push(
      `Temporal activation windows could not be reached for ${asOfDate} — serving what is available.`,
    )
  } else if (windowFamilies.length === 0) {
    thesisParts.push(`No temporal activation window is active for this chart as of ${asOfDate}.`)
  } else {
    const label = formatWindowClasses(top?.signature_classes)
    const orb = typeof top?.max_orb_strength === 'number' ? top.max_orb_strength.toFixed(2) : 'n/a'
    thesisParts.push(
      `${windowFamilies.length} temporal activation window(s) active as of ${asOfDate}; strongest: ` +
        `${label} (orb strength ${orb}, ${top?.member_count ?? 0} contributing signal(s)).`,
    )
  }
  if (darshanaOk && darshana) {
    thesisParts.push(
      `Kāla-Darshana confluence: ${darshana.net_label ?? 'unlabeled'} (effective_score ${darshana.effective_score ?? 'n/a'}).`,
    )
  } else if (darshanaOk && !darshana) {
    thesisParts.push('No Kāla-Darshana confluence window is active today.')
  }

  const evidence: ArgumentEvidence[] = windowFamilies.slice(0, 3).map((f) => ({
    claim:
      `${formatWindowClasses(f.signature_classes)} window ` +
      `${f.window_start ?? '?'}..${f.window_end ?? '?'}` +
      (f.domains && f.domains.length > 0 ? ` touching ${f.domains.join(', ')}` : ''),
    fact_ids: f.member_signal_ids ?? [],
  }))

  const verdict: ArgumentVerdict = {
    statement:
      darshanaOk && darshana
        ? `Kāla state: ${darshana.net_label ?? 'unlabeled'}.`
        : windowFamilies.length > 0
          ? `${windowFamilies.length} structural activation window(s) currently bear on this chart.`
          : 'No structural activation currently bears on this chart.',
    tier: 'structural_prior',
  }

  return {
    thesis: thesisParts.join(' ') || `No temporal state could be assembled for ${asOfDate}.`,
    evidence,
    dissent: [],
    verdict,
    falsifier: null,
  }
}

// ── W1 item 32/29 result shapes ─────────────────────────────────────────────────

export interface DishaShulaResult {
  vara_id: number
  vara_name: string
  avoid_direction: string
  source_citation: string
}

export interface GulikaKalamNowResult {
  window_start_utc: string | null
  window_end_utc: string | null
  is_active_now: boolean | null
  checked_at_utc: string
  not_meaningful_reason: string | null
}

export interface HoraNowResult {
  hora_lord: string | null
  window_start_utc: string | null
  window_end_utc: string | null
  checked_at_utc: string
  not_meaningful_reason: string | null
}

export interface ChandrashtamaResult {
  is_chandrashtama: boolean
  house_from_natal_moon: number
  natal_moon_sign_id: number
  transit_moon_sign_id: number
  /**
   * §N.5 authority disclosure (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30). The natal Moon rāśi
   * is now taken from the L1-authoritative `chart_facts` row this facade ALREADY fetches for
   * item 8 (`get_dignity` / graha_sign_attributes MOON / fact_key='sign_num') — L1 is the
   * authority over every L2+ derivation, and an L2+ surface must reference the L1 fact rather
   * than a re-derivation of it.
   *
   * `panchanga_native_context` is the fallback, used only when the L1 fact is unavailable. It
   * is a genuine RE-DERIVATION: `_fetch_native_context` recomputes the birth Moon from
   * `charts.birth_date` via `compute_panchang(birth_date, …)` — passing the birth DATE with no
   * birth TIME. The Moon moves ~13°/day, so for a native born near a rāśi cusp that
   * re-derivation can land in the adjoining sign and disagree with L1. This native is exactly
   * such a case: Moon in Pūrva Bhādrapada, whose span straddles the Aquarius/Pisces boundary
   * (Aquarius 20°00' – Pisces 3°20'). Hence the L1-first ordering and the explicit source
   * label — never a silent choice between two disagreeing authorities.
   */
  natal_moon_sign_source: 'l1_chart_facts' | 'panchanga_native_context'
  /** The L1 fact_id backing `natal_moon_sign_id` when source is `l1_chart_facts` (§N.5 —
   *  the claim references the fact, it does not restate it). */
  natal_moon_sign_fact_id: string | null
  /** Cross-check, never a substitute: does the panchāṅga service's re-derived birth Moon rāśi
   *  agree with L1's? `null` when one of the two is unavailable to compare. A `false` here is
   *  a real, disclosed divergence between two computations of the same quantity. */
  native_context_agrees_with_l1: boolean | null
}

export interface JanmaResonanceFlag {
  today_id: number | null
  today_name: string | null
  birth_id: number | null
  birth_name: string | null
  birth_fact_id: string | null
  resonance: boolean | null
}

export interface JanmaResonanceResult {
  vara: JanmaResonanceFlag
  nakshatra: JanmaResonanceFlag
  tithi: JanmaResonanceFlag
}

// ── Core compute (exported for tests — mirrors computeKalaTemporalBundle's shape) ──

// ── SM-γ C4: GocharaNarrativeBlock ────────────────────────────────────────────
// Added behind SM_GAMMA_C4_ENABLED env flag (C4.1). All fields come from
// existing substrate: moon_primary from computeGocharaDualReference (already
// run above); active_windows from gochara_forecast_get (callRegistryCapability,
// same pattern as every other sub-call in this file). No new DB query, no new
// computation (§N.5 / B.10).

export interface GocharaNarrativeMoonPrimary {
  description: string
  house_from_lagna: number | null
  house_from_moon: number | null
  current_sign: string | null
  is_retrograde: boolean | null
}

export interface GocharaNarrativeWindow {
  event_class: string
  window_start: string
  window_end: string
  peak_date: string
  valence: string
  signed_intensity: number
  coverage_tier: 'thin' | 'moderate' | 'rich' | null
}

export interface GocharaNarrativeBlock {
  moon_primary: GocharaNarrativeMoonPrimary
  active_windows: GocharaNarrativeWindow[]
  field_gochara_alignment: 'aligned' | 'divergent' | 'insufficient_data'
  narrative_tier: 'rich' | 'moderate' | 'thin'
}

/** Derives the coverage_tier from calibration_state — mirrors the Serving Density Principle
 *  (§N.6): 'calibrated' → 'rich', 'provisional' → 'moderate', else 'thin'. Never fabricated. */
function deriveCoverageTier(
  calibrationState: unknown,
): 'thin' | 'moderate' | 'rich' | null {
  if (typeof calibrationState !== 'string') return null
  if (calibrationState === 'calibrated') return 'rich'
  if (calibrationState === 'provisional') return 'moderate'
  if (calibrationState === 'uncalibrated') return 'thin'
  return null
}

/** Gain-aligned house numbers from Lagna (classical upachaya + dhana houses for gain/income) */
const GAIN_ALIGNED_HOUSES = new Set([1, 2, 5, 9, 10, 11])
/** Loss-aligned house numbers from Lagna (dushtana + maraka houses) */
const LOSS_ALIGNED_HOUSES = new Set([6, 8, 12])

/** Returns true when the Moon's house-from-Lagna is semantically aligned with the dominant
 *  valence of the active gochara windows (e.g. Moon in 11th (gains) + gain-valence windows). */
function isAligned(houseFromLagna: number | null, dominantValence: string | null): boolean {
  if (houseFromLagna == null || dominantValence == null) return false
  if (dominantValence === 'gain' && GAIN_ALIGNED_HOUSES.has(houseFromLagna)) return true
  if (dominantValence === 'loss' && LOSS_ALIGNED_HOUSES.has(houseFromLagna)) return true
  return false
}

/** Fetches current-date gochara forecast windows for the given chart via callRegistryCapability.
 *  Returns an empty array (never throws) on any failure — the narrative block uses
 *  `field_gochara_alignment = 'insufficient_data'` in that case. */
async function fetchGocharaForecastWindows(
  chartId: string,
  asOfDate: string,
  principal: Principal,
): Promise<GocharaNarrativeWindow[]> {
  // A ±90-day window around asOfDate captures windows active "now" without fetching
  // multi-year history. Mirrors gochara_forecast_get's own overlap semantics:
  // window_end >= start AND window_start <= end.
  const startDate = asOfDate
  const endParsed = new Date(`${asOfDate}T00:00:00Z`)
  endParsed.setUTCDate(endParsed.getUTCDate() + 90)
  const endDate = endParsed.toISOString().slice(0, 10)

  const resp = await callRegistryCapability(
    'marsys://tool/L4/gochara_forecast_get',
    {
      chart_id: chartId,
      date_range: { start: startDate, end: endDate },
      limit: 20,
    },
    principal,
  )
  if (!resp.ok || !resp.content) return []
  const rawWindows = (resp.content['windows'] as Array<Record<string, unknown>> | undefined) ?? []
  return rawWindows
    .filter((w) => typeof w['event_class'] === 'string')
    .map((w) => ({
      event_class: String(w['event_class']),
      window_start: typeof w['window_start'] === 'string' ? String(w['window_start']) : asOfDate,
      window_end: typeof w['window_end'] === 'string' ? String(w['window_end']) : asOfDate,
      peak_date: typeof w['peak_date'] === 'string' ? String(w['peak_date']) : asOfDate,
      valence: typeof w['valence'] === 'string' ? String(w['valence']) : 'neutral',
      signed_intensity: typeof w['signed_intensity'] === 'number' ? (w['signed_intensity'] as number) : 0,
      coverage_tier: deriveCoverageTier(w['calibration_state']),
    }))
}

/** Builds the SM-γ C4 GocharaNarrativeBlock. Called only when SM_GAMMA_C4_ENABLED is on.
 *  Sources: gocharaDual (already computed above for item 8) + live gochara forecast fetch.
 *  Never throws — returns a minimal `insufficient_data` block on any missing piece. */
async function buildGocharaNarrativeBlock(
  chartId: string,
  asOfDate: string,
  gocharaDual: { rows: GocharaDualReferenceRow[]; rowsWithTransitData: number },
  natalRefSigns: NatalReferenceSigns,
  principal: Principal,
): Promise<GocharaNarrativeBlock> {
  // Moon row from the already-computed dual-reference (no second transit fetch needed).
  const moonRow = gocharaDual.rows.find((r) => r.planet === 'Moon') ?? null
  const moonTransitAvailable = moonRow != null && moonRow.transit_sign_number != null

  // moon_primary — sourced entirely from the dual-reference already in scope (§N.5).
  const moonPrimary: GocharaNarrativeMoonPrimary = {
    description: moonTransitAvailable && moonRow
      ? `Moon in ${moonRow.transit_sign_name ?? 'unknown'} transiting ` +
        `${moonRow.house_from_lagna != null ? `house ${moonRow.house_from_lagna} from Lagna` : 'unknown house'}`
      : '',
    house_from_lagna: moonRow?.house_from_lagna ?? null,
    house_from_moon: moonTransitAvailable ? 1 : null,  // Moon from itself is always house 1
    current_sign: moonRow?.transit_sign_name ?? null,
    is_retrograde: moonRow?.is_retrograde ?? null,
  }

  // Active gochara windows — fetched via callRegistryCapability (no new DB query).
  const activeWindows = await fetchGocharaForecastWindows(chartId, asOfDate, principal)

  // field_gochara_alignment — requires both Moon transit and at least one window.
  let fieldGocharaAlignment: 'aligned' | 'divergent' | 'insufficient_data'
  if (!moonTransitAvailable || activeWindows.length === 0) {
    fieldGocharaAlignment = 'insufficient_data'
  } else {
    // Dominant valence: most-common valence across active windows.
    const valenceCounts: Record<string, number> = {}
    for (const w of activeWindows) {
      valenceCounts[w.valence] = (valenceCounts[w.valence] ?? 0) + 1
    }
    const dominantValence = Object.entries(valenceCounts)
      .sort((a, b) => b[1] - a[1])[0]?.[0] ?? null
    fieldGocharaAlignment = isAligned(moonPrimary.house_from_lagna, dominantValence) ? 'aligned' : 'divergent'
  }

  // narrative_tier — driven by Moon transit quality + window count.
  let narrativeTier: 'rich' | 'moderate' | 'thin'
  if (moonTransitAvailable && activeWindows.length >= 2) {
    narrativeTier = 'rich'
  } else if (moonTransitAvailable && activeWindows.length >= 1) {
    narrativeTier = 'moderate'
  } else {
    narrativeTier = 'thin'
  }

  return {
    moon_primary: moonPrimary,
    active_windows: activeWindows,
    field_gochara_alignment: fieldGocharaAlignment,
    narrative_tier: narrativeTier,
  }
}

export interface KalaNowResult {
  tool: 'kala_now_get'
  chart_id: string
  as_of_date: string
  reading: ArgumentReading
  reading_prose: string
  question_frame: QuestionFrame | null
  field_snapshot_id: string
  field_snapshot_state: FieldSnapshotState
  field_snapshot_reason: string | null
  tri_plane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: ReturnType<typeof buildKalaFreshness>
  calibration_maturity: CalibrationMaturityResolution
  windows: WindowFamily[]
  darshana: DarshanaRow | null
  disha_shula: DishaShulaResult | null
  gulika_kalam_now: GulikaKalamNowResult | null
  chandrashtama: ChandrashtamaResult | null
  hora_now: HoraNowResult | null
  janma_resonance: JanmaResonanceResult | null
  // Item 8 (wave W1): dual-reference (Moon + Lagna) gochara house-count, one row per graha.
  gochara_dual_reference: GocharaDualReferenceRow[]
  // Item 28 (wave W1): currently-running Vimśottarī MD/AD lord's OWN current transit condition.
  dasha_lord_transit_condition: DashaLordTransitCondition[]
  // Item 24-lite (wave W1): Sūkṣma-level ("below PD") boundary intervals on the currently-
  // running Sūkṣma period, per the documented lite-v0 convention (kala_uncertainty.ts).
  sukshma_boundary_uncertainty: SukshmaBoundaryInterval[]
  // Item 1-lite (wave W1): bands around the currently-active MD/AD period boundaries.
  dasha_sandhi: DashaSandhiResult | null
  // Item 16 (wave W3): current Kota-Chakra ring occupancy per graha.
  kota_chakra: KotaChakraRow[]
  // Item 17 (wave W3): current Sudarśana-Chakra varsha year (tri-lagna progressed signs).
  sudarshana_varsha: SudarshanaVarshaYearNow | null
  // Item 4 (wave W3): current Moorti-nirṇaya per graha (transit quality).
  moorti_nirnaya: MoortiNirnayaRow[]
  // Item 5 (wave W3, closes R-19): current vedha rows (house_vedha + sarvatobhadra).
  vedha_gochara: VedhaGocharaRow[]
  // Item 13 (wave W3): current Tithi-Praveśa (lunar-return annual chart) praveśa year.
  tithi_pravesha: TithiPraveshaYearNow | null
  drill_pointers: DrillPointerLike[]
  // SM-γ C4.1: unified NOW narrative (flag-guarded — absent when SM_GAMMA_C4_ENABLED is off).
  gochara_narrative?: GocharaNarrativeBlock
  provenance_envelope: {
    source: string
    assets: string[]
    chart_id: string
    as_of_date: string
    computed_at: string
    source_citation: string
    windows_reachable: boolean
    darshana_reachable: boolean
    panchanga_reachable: boolean
    /** The specific, disclosed reason the OPTIONAL birth-chart overlay failed, if it did
     *  (ND-4) — `null` when it hydrated fine or was not requested. */
    panchanga_native_context_error: string | null
    natal_panchanga_reachable: boolean
    gochara_dual_reference_reachable: boolean
    /** Earned-signal counterpart to the boolean above (§N.8): how many served rows actually
     *  carry a transit sign. A `*_reachable: true` with 0 here would be a contradiction. */
    gochara_dual_reference_rows_with_transit_data: number
    dasha_lord_transit_condition_reachable: boolean
    dasha_lord_transit_condition_rows_with_transit_data: number
    sukshma_boundary_uncertainty_reachable: boolean
    dasha_sandhi_reachable: boolean
    kota_chakra_reachable: boolean
    sudarshana_varsha_reachable: boolean
    moorti_nirnaya_reachable: boolean
    vedha_gochara_reachable: boolean
    tithi_pravesha_reachable: boolean
  }
}

const SOURCE_CITATION =
  'kala_activation / kala_activation_predicates / kala_bhavishya (forward-window fallback) / ' +
  'kala_darshana (L3 Kāla, orchestrator-built) via Brahma retrieval registry — same substrate ' +
  'as kala_windows_get / kala_bundle_get, re-presented on the ṢAḌ-DARŚANA elevated envelope.'

export async function computeKalaNow(
  chartId: string,
  args: { ayanamsha_id?: string; as_of?: string; question_frame?: QuestionFrame | null },
  principal: Principal,
): Promise<KalaNowResult> {
  const ayanamshaId = resolveChartFactsAyanamsha(args.ayanamsha_id)
  const asOfDate = args.as_of ?? new Date().toISOString().slice(0, 10)

  const [windowsResp, darshanaResp, natalRefSigns, panchangaResp, natalPanchangaResp, kotaChakraNow, sudarshanaVarshaNow, moortiNirnayaNow, vedhaGocharaNow, tithiPraveshaNow] = await Promise.all([
    callRegistryCapability(
      'marsys://tool/L3/query_temporal_activation',
      { chart_id: chartId, ayanamsha_id: ayanamshaId, as_of: asOfDate, top_k: 20 },
      principal,
    ),
    callRegistryCapability(
      'marsys://tool/L3/query_temporal_view',
      { chart_id: chartId, active_on: asOfDate, limit: 1 },
      principal,
    ),
    fetchNatalReferenceSigns(chartId, ayanamshaId, principal),
    // item 32/29 join source: date-parameterized panchāṅga (today's vara/tithi/nakshatra,
    // gulika-kālam window, horā ladder, transit Moon sign) + native_context (birth Moon
    // sign, when chart_id resolves) — engine-direct, Swiss-Ephemeris-backed compute.
    callRegistryCapability(
      'marsys://tool/L0/call_panchanga_service',
      { mode: 'single', date: asOfDate, chart_id: chartId },
      principal,
    ),
    // item 29 janma-resonance source: the native's OWN birth tithi/vara/nakshatra, read
    // verbatim from L1 chart_facts (never re-derived — §N.5).
    callRegistryCapability(
      'marsys://tool/L1/get_panchanga',
      { chart_id: chartId, categories: ['panchanga_tithi', 'panchanga_vara', 'panchanga_nakshatra_moon'] },
      principal,
    ),
    // item 16 (W3): current Kota-Chakra ring occupancy per graha.
    fetchKotaChakraNow(chartId, asOfDate, principal),
    // item 17 (W3): current Sudarśana-Chakra varsha year.
    fetchSudarshanaVarshaNow(chartId, asOfDate, principal),
    // item 4 (W3): current Moorti-nirṇaya per graha.
    fetchMoortiNirnayaNow(chartId, asOfDate, principal),
    // item 5 (W3, closes R-19): current vedha rows (house_vedha + sarvatobhadra).
    fetchVedhaGocharaNow(chartId, asOfDate, principal),
    // item 13 (W3): current Tithi-Praveśa (lunar-return annual chart) year.
    fetchTithiPraveshaNow(chartId, asOfDate, principal),
  ])

  const windowsOk = windowsResp.ok
  const rawFamilies = (windowsResp.content?.['window_families'] as WindowFamily[] | undefined) ?? []
  // query_temporal_activation itself falls back to kala_bhavishya `forward_windows` when
  // `activations`/`window_families` are empty (its own honest-empty discipline) — re-present
  // whichever the capability actually populated, never re-deriving the choice ourselves.
  const rawForward = (windowsResp.content?.['forward_windows'] as WindowFamily[] | undefined) ?? []
  const windowFamilies = rawFamilies.length > 0 ? rawFamilies : rawForward

  const darshanaOk = darshanaResp.ok
  const darshanaRows = (darshanaResp.content?.['rows'] as DarshanaRow[] | undefined) ?? []
  const darshana = darshanaRows[0] ?? null

  // ── item 32/29 joins ──────────────────────────────────────────────────────────────
  const nowIso = new Date().toISOString()
  const isAsOfRealNow = args.as_of == null || args.as_of === new Date().toISOString().slice(0, 10)
  const NOT_TODAY_REASON =
    'as_of is not the current real-world date — instant window-membership (is this window ' +
    'active right now) is only meaningful when reading the actual present moment.'

  const panchangaOk = panchangaResp.ok
  const panchang = panchangaResp.content?.['panchang'] as PanchangPayload | undefined
  const nativeContext = panchangaResp.content?.['native_context'] as NativeContext | null | undefined
  const panchangaReachable = panchangaOk && panchang != null
  // ND-4 (ṢAḌ-DARŚANA W1 verify-reopen): the specific, disclosed reason the OPTIONAL birth-chart
  // overlay failed, when it did — passed through verbatim from call_panchanga_service (which
  // gets it from routers/panchang.py's now-fail-soft native_context hydration). Before this
  // fix, an overlay failure 500'd the whole endpoint and every dependent field was reported as
  // "L0 panchāṅga service unreachable this call" — wording that named a transient outage for
  // what was in fact a deterministic upstream defect reproducible on every call.
  const nativeContextError = panchangaResp.content?.['native_context_error']
  const nativeContextErrorDetail = typeof nativeContextError === 'string' && nativeContextError.length > 0
    ? nativeContextError
    : null
  /** The honest, non-misleading reason string for any panchāṅga-backed field that came up
   *  empty. Distinguishes a genuine dispatch failure from a present-but-incomplete payload —
   *  and never calls a persistent defect "unreachable this call". */
  const panchangaReason = (missingWhat: string): string =>
    panchangaOk
      ? `${missingWhat} — the L0 panchāṅga service WAS reached and answered this call; this ` +
        `specific field was absent from its response.`
      : 'L0 panchāṅga service (call_panchanga_service, mode=single) dispatch failed this call. ' +
        'If this reproduces on every call for every chart and date, it is a persistent defect, ' +
        'not transient unreachability — check the capability handler and sidecar route, not retry.'

  let dishaShula: DishaShulaResult | null = null
  if (panchangaReachable && panchang?.vara) {
    const direction = DISHA_SHUL_TABLE[panchang.vara.id]
    if (direction) {
      dishaShula = {
        vara_id: panchang.vara.id,
        vara_name: panchang.vara.name,
        avoid_direction: direction,
        source_citation:
          'Diśā-śūla (Disha Vasa) vara→direction table — DP published tables, ' +
          'panchang_engine/shastra_tables.py DISHA_SHUL_TABLE (same table ga_panchanga_writer ' +
          'emits for the birth-moment vara as panchanga_disha_shul).',
      }
    }
  }

  let gulikaKalamNow: GulikaKalamNowResult | null = null
  if (panchangaReachable) {
    const gulika = findTimingByLabel(panchang?.inauspicious, 'gulika_kalam')
    if (gulika) {
      gulikaKalamNow = {
        window_start_utc: gulika.start_utc,
        window_end_utc: gulika.end_utc,
        is_active_now: isAsOfRealNow ? isNowWithinWindow(gulika.start_utc, gulika.end_utc, nowIso) : null,
        checked_at_utc: nowIso,
        not_meaningful_reason: isAsOfRealNow ? null : NOT_TODAY_REASON,
      }
    }
  }

  let horaNow: HoraNowResult | null = null
  if (panchangaReachable) {
    if (isAsOfRealNow) {
      const current = findCurrentHora(panchang?.hora, nowIso)
      horaNow = current
        ? {
            hora_lord: current.lord,
            window_start_utc: current.entry.start_utc,
            window_end_utc: current.entry.end_utc,
            checked_at_utc: nowIso,
            not_meaningful_reason: null,
          }
        : { hora_lord: null, window_start_utc: null, window_end_utc: null, checked_at_utc: nowIso, not_meaningful_reason: null }
    } else {
      horaNow = { hora_lord: null, window_start_utc: null, window_end_utc: null, checked_at_utc: nowIso, not_meaningful_reason: NOT_TODAY_REASON }
    }
  }

  // §N.5: L1 `chart_facts` is the authority for the NATAL Moon rāśi — this facade already
  // fetched it above (natalRefSigns, for item 8), so chandrāṣṭama references that fact instead
  // of the panchāṅga service's own re-derivation. native_context is kept strictly as a
  // disclosed cross-check + fallback. See ChandrashtamaResult's doc-comment for why this
  // ordering matters concretely for THIS native (Pūrva Bhādrapada straddles a rāśi cusp).
  let chandrashtama: ChandrashtamaResult | null = null
  const transitMoon = panchang?.planets?.['moon']
  const natalMoonFromL1 = natalRefSigns.ok ? natalRefSigns.moon_sign_number : null
  const natalMoonFromNativeContext = nativeContext?.moon_sign_id ?? null
  const natalMoonSignId = natalMoonFromL1 ?? natalMoonFromNativeContext
  if (panchangaReachable && transitMoon != null && natalMoonSignId != null) {
    const house = houseFromNatalMoon(natalMoonSignId, transitMoon.sign_id)
    chandrashtama = {
      is_chandrashtama: house === 8,
      house_from_natal_moon: house,
      natal_moon_sign_id: natalMoonSignId,
      transit_moon_sign_id: transitMoon.sign_id,
      natal_moon_sign_source: natalMoonFromL1 != null ? 'l1_chart_facts' : 'panchanga_native_context',
      natal_moon_sign_fact_id: natalMoonFromL1 != null ? natalRefSigns.moon_fact_id : null,
      native_context_agrees_with_l1:
        natalMoonFromL1 != null && natalMoonFromNativeContext != null
          ? natalMoonFromL1 === natalMoonFromNativeContext
          : null,
    }
  }

  const natalPanchangaOk = natalPanchangaResp.ok
  const natalRows = (natalPanchangaResp.content?.['rows'] as NatalPanchangaFactRow[] | undefined) ?? []
  let janmaResonance: JanmaResonanceResult | null = null
  if (panchangaReachable && natalPanchangaOk && natalRows.length > 0 && panchang?.vara && panchang?.tithi && panchang?.nakshatra) {
    const birthVara = pickNatalPanchangaNum(natalRows, 'panchanga_vara', 'number', ayanamshaId)
    const birthTithi = pickNatalPanchangaNum(natalRows, 'panchanga_tithi', 'number_in_lunar_month', ayanamshaId)
    const birthNakshatra = pickNatalPanchangaNum(natalRows, 'panchanga_nakshatra_moon', 'number', ayanamshaId)
    janmaResonance = {
      vara: {
        today_id: panchang.vara.id,
        today_name: panchang.vara.name,
        birth_id: birthVara.value,
        birth_name: pickNatalPanchangaText(natalRows, 'panchanga_vara', 'name', ayanamshaId),
        birth_fact_id: birthVara.fact_id,
        resonance: birthVara.value != null ? birthVara.value === panchang.vara.id : null,
      },
      nakshatra: {
        today_id: panchang.nakshatra.id,
        today_name: panchang.nakshatra.name,
        birth_id: birthNakshatra.value,
        birth_name: pickNatalPanchangaText(natalRows, 'panchanga_nakshatra_moon', 'name', ayanamshaId),
        birth_fact_id: birthNakshatra.fact_id,
        resonance: birthNakshatra.value != null ? birthNakshatra.value === panchang.nakshatra.id : null,
      },
      tithi: {
        today_id: panchang.tithi.id,
        today_name: panchang.tithi.name,
        birth_id: birthTithi.value,
        birth_name: pickNatalPanchangaText(natalRows, 'panchanga_tithi', 'name', ayanamshaId),
        birth_fact_id: birthTithi.fact_id,
        resonance: birthTithi.value != null ? birthTithi.value === panchang.tithi.id : null,
      },
    }
  }

  // Item 8 + item 28 — depend on natalRefSigns, so run after the Promise.all above.
  // Item 24-lite and item 1-lite are both independent of natalRefSigns but are batched
  // alongside them (same await point) rather than the earlier Promise.all, purely to keep
  // each lane's diff additive and low-conflict against sibling W1 lanes editing the same file.
  const C4_ENABLED = process.env['SM_GAMMA_C4_ENABLED'] === 'true' || process.env['SM_GAMMA_C4_ENABLED'] === '1'

  const [gocharaDual, dashaLordCondition, sukshmaBoundaryUncertainty, dashaSandhi] = await Promise.all([
    computeGocharaDualReference(asOfDate, natalRefSigns, principal),
    computeDashaLordTransitCondition(chartId, ayanamshaId, asOfDate, asOfDate, natalRefSigns.lagna_sign_number, principal),
    fetchSukshmaBoundaryUncertainty(chartId, ayanamshaId, asOfDate, principal),
    computeDashaSandhi(chartId, ayanamshaId, asOfDate, principal),
  ])

  const reading = buildNowReading({ asOfDate, windowFamilies, darshana, windowsOk, darshanaOk })
  const composed = composeArgument(reading)

  const triPlane: TriPlanePointers = {
    // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30). This slot was a bare `null`, justified
    // as "NOW IS the interpretation plane". That was wrong on the facts: NOW reports a
    // temporal STATE, and the interpretive ground for that state — the drivers and classical
    // reasons behind it — is served by `kala_explain_get`, which is registered, live, and
    // already the interpretation_ref target of the sibling `kala_ahead_get`. A bare null here
    // was a dead end on a plane that genuinely HAS a lever, which is precisely what item 43's
    // no-dead-end contract exists to prevent (Elevation §11).
    interpretation_ref: pointerTo(
      'kala_explain_get',
      'Why this NOW state reads as it does — the drivers and classical grounds behind the active windows and confluence',
    ),
    prediction_ref: pointerTo(
      'kala_ahead_get',
      'Forward-dated windows and probabilistic projections building on this NOW state',
    ),
    intervention_ref: pointerTo(
      'kala_elect_get',
      'Election windows for undertakings, informed by this NOW state',
    ),
  }

  const coverage: KalaCoverageEntry[] = [
    windowsOk
      ? computedCoverage('temporal_activation_windows')
      : honestEmptyCoverage('temporal_activation_windows', 'L3 Kāla registry unreachable this call.'),
    // Honesty-inversion fix (defect 2, PARĪKṢAKA live-production pass, pre-existing since
    // commit 2cba21c5 / PR #940): `darshanaOk` only meant "the registry call succeeded" —
    // it said nothing about whether a row actually came back, so a reachable-but-zero-rows
    // response (chart 1c826d5a) claimed `computed` while `darshana` was null. Matches the
    // established convention immediately below (`dashaSandhi.result ? computed :
    // honest_empty(...)`) and story.ts's `lel_pinning_per_chapter` (fetch-succeeded-zero-rows
    // gets its own honest_empty reason, distinct from unreachable) — same fetch-succeeded-
    // but-empty shape, same vocabulary, not a third pattern. The prose disclosure at
    // `darshanaOk && !darshana` (buildNowReading, above) already narrates this honestly and
    // is unchanged — only this machine-readable coverage state was wrong.
    darshanaOk && darshana
      ? computedCoverage('kala_darshana_confluence')
      : honestEmptyCoverage(
          'kala_darshana_confluence',
          !darshanaOk
            ? 'L3 Kāla registry unreachable this call.'
            : 'The L3 Kāla darshana registry fetch succeeded but returned zero rows for this chart/date — no darshana confluence window is active today.',
        ),
    dashaSandhi.result
      ? computedCoverage('dasha_sandhi')
      : honestEmptyCoverage(
          'dasha_sandhi',
          !dashaSandhi.chainReachable
            ? 'L3 active-dasha registry (query_active_dashas) unreachable this call.'
            : 'No active Vimśottarī MD/AD chain resolved for this chart/date — honest empty, not fabricated. Full daśā-sandhi calendar (all levels, both directions) is item 1-full (wave W3).',
        ),
    notInCorpusCoverage(
      'transit_moorti',
      'Per-ingress moorti-nirṇaya not yet computed — SHAD_DARSHANA_BRIEF_v2_0.md item 4 (wave W3).',
    ),
    dishaShula
      ? computedCoverage('disha_shula')
      : honestEmptyCoverage('disha_shula', panchangaReason("Today's vara could not be resolved")),
    gulikaKalamNow
      ? computedCoverage('gulika_kalam_now')
      : honestEmptyCoverage('gulika_kalam_now', panchangaReason('gulika_kalam window absent')),
    chandrashtama
      ? computedCoverage('chandrashtama')
      : honestEmptyCoverage(
          'chandrashtama',
          panchangaOk
            ? natalMoonSignId == null
              ? 'Natal Moon rāśi unavailable from BOTH authorities: L1 chart_facts ' +
                '(get_dignity/graha_sign_attributes MOON) did not resolve, and the panchāṅga ' +
                'service\'s native_context overlay was absent' +
                (nativeContextErrorDetail ? ` — overlay reported: ${nativeContextErrorDetail}.` : '.')
              : panchangaReason('transit Moon position absent')
            : panchangaReason('transit Moon position absent'),
        ),
    horaNow
      ? computedCoverage('hora_now')
      : honestEmptyCoverage('hora_now', panchangaReason('horā ladder absent')),
    janmaResonance
      ? computedCoverage('janma_resonance')
      : honestEmptyCoverage(
          'janma_resonance',
          !panchangaOk
            ? panchangaReason("today's tithi/vara/nakṣatra unavailable")
            : !natalPanchangaOk
              ? 'L1 natal panchāṅga facts (get_panchanga) could not be dispatched this call.'
              : 'Natal tithi/vara/nakṣatra facts or today\'s panchāṅga anga ids unavailable.',
        ),
    // Earned-signal detector (CLAUDE.md §N.8), items 8 + 28: `computed` now requires at least
    // one served row to actually CARRY a transit sign. The prior predicate asked only "did the
    // capability dispatch return 200" — which was true even while all nine grahas' fields were
    // null, producing the false-positive `state: "computed"` the Verifier rejected. A
    // `computed` claim must be falsifiable by the data it describes.
    natalRefSigns.ok && gocharaDual.rowsWithTransitData > 0
      ? computedCoverage('dual_reference_gochara')
      : honestEmptyCoverage(
          'dual_reference_gochara',
          !natalRefSigns.ok
            ? 'L1 natal reference-sign lookup (get_dignity/graha_sign_attributes) could not be dispatched this call.'
            : gocharaDual.transitFailure
              ? transitFailureReason(gocharaDual.transitFailure)
              : `L0 ephemeris answered but returned no transit row for any of the ${GOCHARA_PLANETS.length} ` +
                `grahas on ${asOfDate} — genuine empty for this date, not a masked failure.`,
        ),
    dashaLordCondition.chainReachable && dashaLordCondition.rowsWithTransitData > 0
      ? computedCoverage('dasha_lord_current_transit_condition')
      : honestEmptyCoverage(
          'dasha_lord_current_transit_condition',
          !dashaLordCondition.chainReachable
            ? 'L3 active-dasha registry (query_active_dashas) could not be dispatched this call.'
            : dashaLordCondition.rows.length === 0
              ? 'No active Vimśottarī MD/AD chain resolved for this chart/date — honest empty, not fabricated.'
              : dashaLordCondition.transitFailure
                ? transitFailureReason(dashaLordCondition.transitFailure)
                : `L0 ephemeris answered but returned no transit row for the active lord(s) on ${asOfDate} — ` +
                  'genuine empty for this date, not a masked failure.',
        ),
    // Item 24-lite: Sūkṣma-level (level_n=4, "below PD") boundary intervals on the
    // currently-running period, per the documented lite-v0 convention (kala_uncertainty.ts).
    sukshmaBoundaryUncertainty.reachable && sukshmaBoundaryUncertainty.intervals.length > 0
      ? computedCoverage('sukshma_boundary_uncertainty')
      : honestEmptyCoverage(
          'sukshma_boundary_uncertainty',
          !sukshmaBoundaryUncertainty.reachable
            ? 'L1 dasha registry (get_dashas) unreachable this call.'
            : 'No Sūkṣma-level (level_n=4) daśā row resolved for this chart/date — this chart may not be built to Sūkṣma depth, or as_of_date falls outside the built range.',
        ),
    // Item 16 (wave W3): Kota-Chakra fort chart.
    kotaChakraNow.reachable && kotaChakraNow.rows.length > 0
      ? computedCoverage('kota_chakra')
      : honestEmptyCoverage(
          'kota_chakra',
          !kotaChakraNow.reachable
            ? 'L3 registry (query_kota_chakra) could not be dispatched this call.'
            : `ka_kota_chakra has not built this chart, or its scanned horizon does not cover ${asOfDate} — honest empty, not fabricated.`,
        ),
    // Item 17 (wave W3): Sudarśana-Chakra year-wheel.
    sudarshanaVarshaNow.reachable && sudarshanaVarshaNow.current != null
      ? computedCoverage('sudarshana_varsha')
      : honestEmptyCoverage(
          'sudarshana_varsha',
          !sudarshanaVarshaNow.reachable
            ? 'L3 registry (query_sudarshana_varsha) could not be dispatched this call.'
            : `ka_sudarshana_varsha has not built this chart, or ${asOfDate} falls outside the birth..birth+120y built horizon — honest empty, not fabricated.`,
        ),
    // Item 4 (wave W3): Moorti-nirṇaya per graha.
    moortiNirnayaNow.reachable && moortiNirnayaNow.rows.length > 0
      ? computedCoverage('moorti_nirnaya')
      : honestEmptyCoverage(
          'moorti_nirnaya',
          !moortiNirnayaNow.reachable
            ? 'L3 registry (query_moorti_nirnaya) could not be dispatched this call.'
            : `ka_moorti_nirnaya has not built this chart, or its scanned horizon does not cover ${asOfDate} — honest empty, not fabricated.`,
        ),
    // Item 5 (wave W3, closes R-19): vedha application (house_vedha + sarvatobhadra). An
    // empty result is the classically NORMAL state on most days (no vedha-checkable transit
    // or sarvatobhadra-vedha dwelling currently active) — this coverage entry cannot
    // distinguish that from "chart not yet built", matching the same honest ambiguity
    // kota_chakra/sudarshana_varsha already carry (see their own coverage messages above).
    vedhaGocharaNow.reachable && vedhaGocharaNow.rows.length > 0
      ? computedCoverage('vedha_gochara')
      : honestEmptyCoverage(
          'vedha_gochara',
          !vedhaGocharaNow.reachable
            ? 'L3 registry (query_vedha_gochara) could not be dispatched this call.'
            : `ka_vedha_gochara has not built this chart, or no vedha-checkable transit / `
              + `sarvatobhadra-vedha dwelling is currently active for ${asOfDate} — honest `
              + 'empty (the classically normal state on most days), not fabricated.',
        ),
    // Item 13 (wave W3): Tithi-Praveśa (lunar-return annual chart). `current: null` is
    // honest-empty — e.g. asOfDate predates birth, or exceeds the 120-year built horizon.
    tithiPraveshaNow.reachable && tithiPraveshaNow.current != null
      ? computedCoverage('tithi_pravesha')
      : honestEmptyCoverage(
          'tithi_pravesha',
          !tithiPraveshaNow.reachable
            ? 'L3 registry (query_tithi_pravesha) could not be dispatched this call.'
            : `ka_tithi_pravesha has not built this chart, or ${asOfDate} falls outside the `
              + 'built 120-year praveśa-year horizon — honest empty, not fabricated.',
        ),
    // E6 per-view elevation for NOW: state_delta — field diff against previous inflection point.
    // KALA_SUPREME_ELEVATION_v1_0.md §6: NOW elevation = "state_delta: what changed since the
    // last significant configuration (field diff against previous inflection point)."
    // SHAD_DARSHANA_CLOSE_v1_0.md §2 E6 disposition: VERIFIED-FIXED (lite); the state_delta
    // sub-elevation is the W3 depth portion. No authoritative state-delta rows are currently
    // available for this chart, so this facade discloses that gap rather than a build-status guess.
    honestEmptyCoverage(
      'state_delta',
      'E6 per-view elevation for NOW (KALA_SUPREME_ELEVATION_v1_0.md §6): the field diff ' +
      'against the previous inflection point (what changed since the last significant ' +
      'configuration) has no authoritative state-delta result for this chart. The facade ' +
      'therefore serves an honest empty rather than inferring a diff from other timing rows. ' +
      'SHAD_DARSHANA_CLOSE_v1_0.md §2 E6 disposition: VERIFIED-FIXED (lite); state_delta is ' +
      'the W3 depth remainder, not yet computed.',
    ),
  ]

  const drillPointers: DrillPointerLike[] = [
    triPlane.interpretation_ref,
    triPlane.prediction_ref,
    triPlane.intervention_ref,
  ].filter((p): p is DrillPointerLike => p != null && !isNoLever(p))

  // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
  const fieldSnapshot = await resolveFieldSnapshot(chartId, principal)

  // SM-γ C4.1: build the unified NOW narrative block when flag is on.
  const gocharaNarrative: GocharaNarrativeBlock | undefined = C4_ENABLED
    ? await buildGocharaNarrativeBlock(chartId, asOfDate, gocharaDual, natalRefSigns, principal)
    : undefined

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: args.question_frame ?? null,
    fieldSnapshot,
    triPlane,
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: fieldSnapshot.field_content_hash }),
    calibrationMaturity: await fetchCalibrationMaturity(chartId, principal),
  })

  const baseResult = {
    tool: 'kala_now_get' as const,
    chart_id: chartId,
    as_of_date: asOfDate,
    ...envelope,
    reading_prose: composed.full_text,
    windows: windowFamilies,
    darshana,
    disha_shula: dishaShula,
    gulika_kalam_now: gulikaKalamNow,
    chandrashtama,
    hora_now: horaNow,
    janma_resonance: janmaResonance,
    gochara_dual_reference: gocharaDual.rows,
    dasha_lord_transit_condition: dashaLordCondition.rows,
    sukshma_boundary_uncertainty: sukshmaBoundaryUncertainty.intervals,
    dasha_sandhi: dashaSandhi.result,
    kota_chakra: kotaChakraNow.rows,
    sudarshana_varsha: sudarshanaVarshaNow.current,
    moorti_nirnaya: moortiNirnayaNow.rows,
    vedha_gochara: vedhaGocharaNow.rows,
    tithi_pravesha: tithiPraveshaNow.current,
    drill_pointers: drillPointers,
    provenance_envelope: {
      source: 'kala_now_get',
      assets: [
        'kala_activation (ka_kalasutra)', 'kala_bhavishya (forward-window fallback)', 'kala_darshana',
        'call_panchanga_service (panchang.py, engine-direct)', 'get_panchanga (L1 chart_facts, natal panchāṅga)',
        'get_dignity (graha_sign_attributes)', 'query_planet_transit (L0 ephemeris)',
        'query_active_dashas (L3, EL-33)', 'bg_dignity_reference (L0)', 'get_dashas (chart_dashas, level_n=4)',
        'kala_kota_chakra (ka_kota_chakra, item 16)', 'kala_sudarshana_varsha (ka_sudarshana_varsha, item 17)',
        'kala_moorti_nirnaya (ka_moorti_nirnaya, item 4)', 'kala_vedha_gochara (ka_vedha_gochara, item 5, closes R-19)',
        'kala_tithi_pravesha (ka_tithi_pravesha, item 13)',
      ],
      chart_id: chartId,
      as_of_date: asOfDate,
      computed_at: new Date().toISOString(),
      source_citation: SOURCE_CITATION,
      panchanga_reachable: panchangaReachable,
      panchanga_native_context_error: nativeContextErrorDetail,
      natal_panchanga_reachable: natalPanchangaOk,
      windows_reachable: windowsOk,
      darshana_reachable: darshanaOk,
      // §N.8: these two now assert what they NAME — that the join actually produced transit
      // data — not merely that a dispatch returned 200 with an empty body.
      gochara_dual_reference_reachable: natalRefSigns.ok && gocharaDual.rowsWithTransitData > 0,
      gochara_dual_reference_rows_with_transit_data: gocharaDual.rowsWithTransitData,
      dasha_lord_transit_condition_reachable:
        dashaLordCondition.chainReachable && dashaLordCondition.rowsWithTransitData > 0,
      dasha_lord_transit_condition_rows_with_transit_data: dashaLordCondition.rowsWithTransitData,
      sukshma_boundary_uncertainty_reachable: sukshmaBoundaryUncertainty.reachable,
      dasha_sandhi_reachable: dashaSandhi.chainReachable,
      kota_chakra_reachable: kotaChakraNow.reachable,
      sudarshana_varsha_reachable: sudarshanaVarshaNow.reachable,
      moorti_nirnaya_reachable: moortiNirnayaNow.reachable,
      vedha_gochara_reachable: vedhaGocharaNow.reachable,
      tithi_pravesha_reachable: tithiPraveshaNow.reachable,
    },
  }

  // SM-γ C4.1: conditionally add gochara_narrative (flag-guarded — zero footprint when off).
  if (C4_ENABLED && gocharaNarrative !== undefined) {
    return { ...baseResult, gochara_narrative: gocharaNarrative }
  }
  return baseResult
}

// ── Input schema + registration ─────────────────────────────────────────────────

const QuestionFrameSchema = z
  .object({
    domain: z.string().optional(),
    entity: z.string().optional(),
    horizon: z.string().optional(),
    intent_verb: z.string().optional(),
    stakes: z.string().optional(),
    comparison_target: z.string().optional(),
  })
  .optional()
  .describe(
    'Optional question-frame (Elevation §5 E4): the caller\'s specific angle on this chart\'s ' +
      'NOW state — domain/entity/horizon/intent_verb/stakes/comparison_target. The chart is ' +
      'always implicit (chart_id); this is the only per-question input. W0: accepted and echoed ' +
      'verbatim in the response — full relevance-scoring/reading-conditioning on this param is a ' +
      'later-wave elevation (E4 full).',
  )

const InputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
  as_of: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional()
    .describe('Point-in-time date YYYY-MM-DD to read as "now" (default: today).'),
  question_frame: QuestionFrameSchema,
})

const TOOL_NAME = 'kala_now_get'

const TOOL_DESCRIPTION = `\
What is my temporal state right now? Returns the current layered Kāla clock state for a \
chart — active temporal-activation windows (kala_activation, orb-strength ranked) and the \
current Kāla-Darshana confluence (kala_darshana: effective_score + net_label) — composed \
into an argument-shaped reading (thesis → evidence → verdict) on the ṢAḌ-DARŚANA elevated \
envelope (question_frame, field_snapshot_id, tri_plane pointers, 3-state coverage, \
freshness attestation, calibration_maturity).

THIN FACADE (W0): re-presents the SAME substrate kala_windows_get and kala_bundle_get's \
snapshot already serve — no new computation. W1 adds three JOINS over existing substrate: \
gochara_dual_reference (item 8 — every graha's current transit house counted from BOTH \
natal Moon AND natal Lagna, side by side), dasha_lord_transit_condition (item 28 — the \
currently-running Vimśottarī MD/AD lord's own current transit sign/house/dignity; see \
kala_ahead_get for the forward-horizon half), and dasha_sandhi (item 1-lite — a band around \
every currently-active MD/AD period's start AND end boundary, derived from that period's own \
already-computed span; see \`band_convention\` on the field for the documented ~3% orb rule \
and its lite simplification — the full two-period, all-level daśā-sandhi calendar is item \
1-full, wave W3). Honestly discloses (via \`coverage\`) which richer NOW concepts \
(per-ingress transit moorti) are not yet joined into this view.

W1 joins (objective, raw flags — no favorable/unfavorable grading): disha_shula (today's \
diśā-śūla travel-avoid direction), gulika_kalam_now (today's gulika-kālam window + whether \
the current moment is inside it), chandrashtama (transit Moon's house from natal Moon + \
whether it is house 8), hora_now (current planetary-hour lord + window), janma_resonance \
(whether today's vara/nakṣatra/tithi match the native's own birth vara/nakṣatra/tithi), \
sukshma_boundary_uncertainty (item 24-lite — the currently-running Sūkṣma-level daśā \
period's own start/end boundary instants, each served with an honest ± interval per a \
documented lite-v0 convention, NOT the full birth-time/ayanāṁśa error-propagation model — \
see kala_uncertainty.ts).

W3 adds two NEW COMPUTATIONS (own per-chart writers, read-only from this facade — §N.5): \
kota_chakra (item 16 — every graha's CURRENT Kota-Chakra ring, i.e. its nakshatra-count-from- \
janma classified into stambha/durgantara/prakara/bahya, with entry/exit window and an \
attack/defence reading) and sudarshana_varsha (item 17 — the CURRENT varsha year's tri-lagna \
progressed signs, i.e. where Janma/Chandra/Sūrya Lagna each stand this year of life, plus \
whether all three currently coincide).

W3 (Lane w3-moorti-vedha) adds two more: moorti_nirnaya (item 4 — the CURRENT classical gold/ \
silver/copper/iron transit quality per graha, resolved from the Moon's nakshatra at the \
ingress moment against the REAL, cited bg_transit_moorti table) and vedha_gochara (item 5, \
closes defect R-19 — CURRENT vedha/obstruction rows, both house_vedha, REAL cited BPHS/ \
Phaladeepika house-level rule, and sarvatobhadra, an honestly disclosed algorithmic \
approximation pending corpus ingestion — never conflated, see vedha_kind/uncited_extension \
on every row).

W3 (Lane w3-tithi-pravesha) adds one more: tithi_pravesha (item 13 — the CURRENT praveśa \
year's Tithi-Praveśa lunar-return annual chart, the Moon-anchored counterpart to Tājika \
Vārṣaphala: the instant the transiting Moon returns to its exact natal sidereal longitude \
nearest this year's solar-birthday anniversary, plus the resulting Praveśa Lagna).

Output includes: reading (structured argument) + reading_prose (composed text) + windows + \
darshana + disha_shula + gulika_kalam_now + chandrashtama + hora_now + janma_resonance + \
gochara_dual_reference + dasha_lord_transit_condition + sukshma_boundary_uncertainty + \
dasha_sandhi + kota_chakra + sudarshana_varsha + moorti_nirnaya + vedha_gochara + \
tithi_pravesha + tri_plane \
(→ kala_ahead_get for what's coming, → kala_elect_get for when to act) + coverage + \
drill_pointers.

Requires: chart_id (UUID). Successor to kala_windows_get for "what is my state now" queries \
— kala_windows_get remains live (not retired).`

export function registerKalaNowGetTool(server: McpServer, principal: Principal): void {
  server.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {
    const input = InputSchema.parse(params)
    if (!input.chart_id) return errOut(TOOL_NAME, 'chart_id is required')
    try {
      const result = await computeKalaNow(
        input.chart_id,
        { ayanamsha_id: input.ayanamsha_id, as_of: input.as_of, question_frame: input.question_frame ?? null },
        principal,
      )
      return dualOutput(result, TOOL_NAME)
    } catch (err) {
      return errOut(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id: input.chart_id })
    }
  })
}
