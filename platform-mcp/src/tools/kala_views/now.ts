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
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §1 (NOW content + clarity contract),
 * KALA_SUPREME_ELEVATION_v1_0.md (v1.2) §5 (envelope E3/E4/E5), §11 (item 43 tri-plane).
 *
 * What is genuinely NOT computed here yet (honestly disclosed via `coverage`, never
 * silently dropped): daśā-sandhi bands, per-ingress transit moorti — named W3 build items
 * in the brief, not this facade's job.
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
  noLelCalibrationMaturity,
  buildKalaFreshness,
  buildFieldSnapshotIdStub,
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
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { autoDetectTrimmableSections, finalizeMcpBudget } from '../../lib/response_budget.js'

// ── Infrastructure (self-contained proxy helper — mirrors the established per-file
// pattern in register_p1_aliases.ts / tools/retrieval/kala_temporal.ts / registry_bridge.ts;
// this file does not import their module-local helpers to avoid coupling this new lane's
// facade to files owned/being edited by sibling lanes in the same campaign) ─────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function normalizeAyanamsha(id?: string): string {
  return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha'
}

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

interface PlanetTransitSnapshot {
  planet: string
  sign_number: number | null
  degree_in_sign: number | null
  nakshatra_number: number | null
  is_retrograde: boolean | null
  ok: boolean
}

/** Single-day snapshot (start_date=end_date=dateISO) via the EXISTING L0 ephemeris
 *  capability (marsys://tool/L0/query_planet_transit — the same substrate
 *  ref_planet_transit_get / query_planet_transit already serve; sidereal-first,
 *  default ayanamsha lahiri_chitrapaksha). */
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
  const row = resp.ok ? (resp.content?.['rows'] as Array<Record<string, unknown>> | undefined)?.[0] : undefined
  if (!row) return { planet, sign_number: null, degree_in_sign: null, nakshatra_number: null, is_retrograde: null, ok: resp.ok }
  return {
    planet,
    sign_number: typeof row['sign_number'] === 'number' ? (row['sign_number'] as number) : null,
    degree_in_sign: typeof row['degree_in_sign'] === 'number' ? (row['degree_in_sign'] as number) : null,
    nakshatra_number: typeof row['nakshatra_number'] === 'number' ? (row['nakshatra_number'] as number) : null,
    is_retrograde: typeof row['is_retrograde'] === 'boolean' ? (row['is_retrograde'] as boolean) : null,
    ok: true,
  }
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
): Promise<{ rows: GocharaDualReferenceRow[]; transitReachable: boolean }> {
  const snapshots = await Promise.all(GOCHARA_PLANETS.map((p) => fetchPlanetTransitSnapshot(p, asOfDate, principal)))
  const transitReachable = snapshots.some((s) => s.ok)
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
  return { rows, transitReachable }
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
): Promise<{ rows: DashaLordTransitCondition[]; chainReachable: boolean; transitReachable: boolean }> {
  const chain = await fetchActiveVimshottariChain(chartId, ayanamshaId, identifyAsOfDate, principal)
  if (!chain.ok || chain.entries.length === 0) {
    return { rows: [], chainReachable: chain.ok, transitReachable: true }
  }
  const uniqueGrahas = Array.from(new Set(chain.entries.map((e) => e.lord_graha).filter(Boolean)))
  const [snapshots, dignities] = await Promise.all([
    Promise.all(uniqueGrahas.map((g) => fetchPlanetTransitSnapshot(g, snapshotDate, principal))),
    Promise.all(uniqueGrahas.map((g) => fetchDignityReference(g, principal))),
  ])
  const snapshotByGraha = new Map(snapshots.map((s) => [s.planet, s]))
  const dignityByGraha = new Map(uniqueGrahas.map((g, i) => [g, dignities[i] ?? null]))
  const transitReachable = snapshots.some((s) => s.ok)

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
  return { rows, chainReachable: chain.ok, transitReachable }
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
    const label = (top?.signature_classes ?? []).join('/') || 'unlabeled'
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
      `${(f.signature_classes ?? []).join('/') || 'activation'} window ` +
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

export interface KalaNowResult {
  tool: 'kala_now_get'
  chart_id: string
  as_of_date: string
  reading: ArgumentReading
  reading_prose: string
  question_frame: QuestionFrame | null
  field_snapshot_id: string
  tri_plane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: ReturnType<typeof buildKalaFreshness>
  calibration_maturity: ReturnType<typeof noLelCalibrationMaturity>
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
  drill_pointers: DrillPointerLike[]
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
    natal_panchanga_reachable: boolean
    gochara_dual_reference_reachable: boolean
    dasha_lord_transit_condition_reachable: boolean
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
  const ayanamshaId = normalizeAyanamsha(args.ayanamsha_id)
  const asOfDate = args.as_of ?? new Date().toISOString().slice(0, 10)

  const [windowsResp, darshanaResp, natalRefSigns, panchangaResp, natalPanchangaResp] = await Promise.all([
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

  let chandrashtama: ChandrashtamaResult | null = null
  const transitMoon = panchang?.planets?.['moon']
  if (panchangaReachable && nativeContext != null && transitMoon != null) {
    const house = houseFromNatalMoon(nativeContext.moon_sign_id, transitMoon.sign_id)
    chandrashtama = {
      is_chandrashtama: house === 8,
      house_from_natal_moon: house,
      natal_moon_sign_id: nativeContext.moon_sign_id,
      transit_moon_sign_id: transitMoon.sign_id,
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
  const [gocharaDual, dashaLordCondition] = await Promise.all([
    computeGocharaDualReference(asOfDate, natalRefSigns, principal),
    computeDashaLordTransitCondition(chartId, ayanamshaId, asOfDate, asOfDate, natalRefSigns.lagna_sign_number, principal),
  ])

  const reading = buildNowReading({ asOfDate, windowFamilies, darshana, windowsOk, darshanaOk })
  const composed = composeArgument(reading)

  const triPlane: TriPlanePointers = {
    // NOW IS the interpretation plane — null is the contractually-legal value here
    // (kala_envelope.ts: "null only legal when this object IS the interpretation plane").
    interpretation_ref: null,
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
    darshanaOk
      ? computedCoverage('kala_darshana_confluence')
      : honestEmptyCoverage('kala_darshana_confluence', 'L3 Kāla registry unreachable this call.'),
    notInCorpusCoverage(
      'dasha_sandhi_bands',
      'Junction-turbulence flags not yet computed for any chart — SHAD_DARSHANA_BRIEF_v2_0.md item 1 (wave W3).',
    ),
    notInCorpusCoverage(
      'transit_moorti',
      'Per-ingress moorti-nirṇaya not yet computed — SHAD_DARSHANA_BRIEF_v2_0.md item 4 (wave W3).',
    ),
    dishaShula
      ? computedCoverage('disha_shula')
      : honestEmptyCoverage('disha_shula', panchangaOk ? "Today's vara could not be resolved from the panchāṅga service response." : 'L0 panchāṅga service unreachable this call.'),
    gulikaKalamNow
      ? computedCoverage('gulika_kalam_now')
      : honestEmptyCoverage('gulika_kalam_now', panchangaOk ? 'gulika_kalam window absent from the panchāṅga service response.' : 'L0 panchāṅga service unreachable this call.'),
    chandrashtama
      ? computedCoverage('chandrashtama')
      : honestEmptyCoverage(
          'chandrashtama',
          panchangaOk
            ? 'native_context (birth Moon rāśi) or transit Moon position unavailable from the panchāṅga service response.'
            : 'L0 panchāṅga service unreachable this call.',
        ),
    horaNow
      ? computedCoverage('hora_now')
      : honestEmptyCoverage('hora_now', panchangaOk ? 'horā ladder absent from the panchāṅga service response.' : 'L0 panchāṅga service unreachable this call.'),
    janmaResonance
      ? computedCoverage('janma_resonance')
      : honestEmptyCoverage(
          'janma_resonance',
          !panchangaOk
            ? 'L0 panchāṅga service unreachable this call.'
            : !natalPanchangaOk
              ? 'L1 natal panchāṅga facts (get_panchanga) unreachable this call.'
              : 'Natal tithi/vara/nakṣatra facts or today\'s panchāṅga anga ids unavailable.',
        ),
    natalRefSigns.ok && gocharaDual.transitReachable
      ? computedCoverage('dual_reference_gochara')
      : honestEmptyCoverage(
          'dual_reference_gochara',
          !natalRefSigns.ok
            ? 'L1 natal reference-sign lookup (get_dignity/graha_sign_attributes) unreachable this call.'
            : 'L0 ephemeris registry unreachable this call.',
        ),
    dashaLordCondition.chainReachable && dashaLordCondition.transitReachable && dashaLordCondition.rows.length > 0
      ? computedCoverage('dasha_lord_current_transit_condition')
      : honestEmptyCoverage(
          'dasha_lord_current_transit_condition',
          !dashaLordCondition.chainReachable
            ? 'L3 active-dasha registry (query_active_dashas) unreachable this call.'
            : dashaLordCondition.rows.length === 0
              ? 'No active Vimśottarī MD/AD chain resolved for this chart/date — honest empty, not fabricated.'
              : 'L0 ephemeris registry unreachable this call for the active lord(s).',
        ),
  ]

  const drillPointers: DrillPointerLike[] = [triPlane.prediction_ref, triPlane.intervention_ref].filter(
    (p): p is DrillPointerLike => p != null && !isNoLever(p),
  )

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: args.question_frame ?? null,
    fieldSnapshotId: buildFieldSnapshotIdStub({ chart_id: chartId, ayanamsha_id: ayanamshaId, as_of: asOfDate }),
    triPlane,
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  return {
    tool: 'kala_now_get',
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
    drill_pointers: drillPointers,
    provenance_envelope: {
      source: 'kala_now_get',
      assets: [
        'kala_activation (ka_kalasutra)', 'kala_bhavishya (forward-window fallback)', 'kala_darshana',
        'call_panchanga_service (panchang.py, engine-direct)', 'get_panchanga (L1 chart_facts, natal panchāṅga)',
        'get_dignity (graha_sign_attributes)', 'query_planet_transit (L0 ephemeris)',
        'query_active_dashas (L3, EL-33)', 'bg_dignity_reference (L0)',
      ],
      chart_id: chartId,
      as_of_date: asOfDate,
      computed_at: new Date().toISOString(),
      source_citation: SOURCE_CITATION,
      panchanga_reachable: panchangaReachable,
      natal_panchanga_reachable: natalPanchangaOk,
      windows_reachable: windowsOk,
      darshana_reachable: darshanaOk,
      gochara_dual_reference_reachable: natalRefSigns.ok && gocharaDual.transitReachable,
      dasha_lord_transit_condition_reachable: dashaLordCondition.chainReachable && dashaLordCondition.transitReachable,
    },
  }
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
snapshot already serve — no new computation. W1 adds two JOINS over existing substrate: \
gochara_dual_reference (item 8 — every graha's current transit house counted from BOTH \
natal Moon AND natal Lagna, side by side) and dasha_lord_transit_condition (item 28 — the \
currently-running Vimśottarī MD/AD lord's own current transit sign/house/dignity; see \
kala_ahead_get for the forward-horizon half). Honestly discloses (via \`coverage\`) which \
richer NOW concepts (daśā-sandhi bands, per-ingress transit moorti) are not yet joined into \
this view.

W1 joins (objective, raw flags — no favorable/unfavorable grading): disha_shula (today's \
diśā-śūla travel-avoid direction), gulika_kalam_now (today's gulika-kālam window + whether \
the current moment is inside it), chandrashtama (transit Moon's house from natal Moon + \
whether it is house 8), hora_now (current planetary-hour lord + window), janma_resonance \
(whether today's vara/nakṣatra/tithi match the native's own birth vara/nakṣatra/tithi).

Output includes: reading (structured argument) + reading_prose (composed text) + windows + \
darshana + disha_shula + gulika_kalam_now + chandrashtama + hora_now + janma_resonance + \
gochara_dual_reference + dasha_lord_transit_condition + tri_plane (→ kala_ahead_get for \
what's coming, → kala_elect_get for when to act) + coverage + drill_pointers.

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
