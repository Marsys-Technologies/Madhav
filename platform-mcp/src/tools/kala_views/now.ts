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

  const [windowsResp, darshanaResp, natalRefSigns] = await Promise.all([
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
    gochara_dual_reference: gocharaDual.rows,
    dasha_lord_transit_condition: dashaLordCondition.rows,
    drill_pointers: drillPointers,
    provenance_envelope: {
      source: 'kala_now_get',
      assets: [
        'kala_activation (ka_kalasutra)', 'kala_bhavishya (forward-window fallback)', 'kala_darshana',
        'get_dignity (graha_sign_attributes)', 'query_planet_transit (L0 ephemeris)',
        'query_active_dashas (L3, EL-33)', 'bg_dignity_reference (L0)',
      ],
      chart_id: chartId,
      as_of_date: asOfDate,
      computed_at: new Date().toISOString(),
      source_citation: SOURCE_CITATION,
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

Output includes: reading (structured argument) + reading_prose (composed text) + windows + \
darshana + gochara_dual_reference + dasha_lord_transit_condition + tri_plane \
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
