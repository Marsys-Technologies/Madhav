/**
 * tools/kala_views/ahead.ts — ṢAḌ-DARŚANA W0.4 (SHAD_DARSHANA_BRIEF_v2_0.md §0.4 · §2 file map
 * · §3 W0.4 "Eight facades over EXISTING substrate").
 * ==========================================================================
 * `kala_ahead_get` — VIEW 2: AHEAD ("What is coming?"), per
 * KALA_SIX_VIEWS_DESIGN_v1_0.md §2.
 *
 * THIN FACADE — this file computes NOTHING new. It calls the SAME two registry
 * capabilities the existing `kala_windows_get` (forward-dated) and `kala_projections_get`
 * (register_p1_aliases.ts, → `marsys://tool/L3/query_temporal_activation` /
 * `marsys://tool/L3/query_projections`) already call, and re-presents their EXISTING rows
 * through the elevated envelope (`lib/kala_envelope.ts`) + the shared prose engine
 * (`lib/argument_composer.ts`). The only "grading" applied — mapping a projection's
 * pre-computed `probability_tier` (tier_1_high/tier_2_moderate/tier_3_speculative, already
 * computed by kala_bhavishya's writer) onto `ArgumentEvidence.strength` — is a direct,
 * lossless relabeling of an EXISTING categorical field, not a new computation (§N.5 / B.10).
 *
 * Design authority: KALA_SIX_VIEWS_DESIGN_v1_0.md §2 (AHEAD content + clarity contract),
 * KALA_SUPREME_ELEVATION_v1_0.md (v1.2) §5 (envelope E3/E4/E5), §11 (item 43 tri-plane).
 *
 * W1 (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1) ADDS `dasha_lord_transit_condition_forward` —
 * item 28's forward half: the currently-running Vimśottarī MD/AD lord's transit condition
 * projected to this call's horizon boundary (`date_to`). See the "W1 item 28 (forward
 * half)" doc-comment above `dualOutput` below for the exact provenance chain; see now.ts
 * for item 28's current half and item 8 (dual-reference gochara, NOW-only).
 *
 * What is genuinely NOT computed here yet (honestly disclosed via `coverage`, never
 * silently dropped): Law-3 promise-gating (PACT chain — "pressure without delivery" is not
 * yet applied to these raw windows), the sky-event calendar (ingresses/stations/eclipses/
 * returns), Tithi-Praveśa — all named W2/W3 build items in the brief, not this facade's job.
 *
 * W1 JOIN ADDITION (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1, item 32 half): upcoming gulika-kālam
 * windows over the forward horizon. A pure JOIN (§N.5 / B.10) — reads the SAME
 * date-parameterized panchāṅga `call_panchanga_service` (marsys://tool/L0/
 * call_panchanga_service, mode=range → panchang.py /api/compute/panchanga/range) already
 * computes for any date range, extracting the already-computed `gulika_kalam` Timing per
 * day. The range endpoint hard-caps at 31 days per call (a sidecar-load guard, not this
 * facade's choice) — capped here at the next 30 days regardless of `horizon_years`, since
 * gulika-kālam is an intrinsically daily/short-horizon election concept; this cap is
 * disclosed on the served object, never silently truncated.
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
  type ArgumentFalsifier,
  type QuestionFrame,
  type TriPlanePointers,
  type DrillPointerLike,
  type KalaCoverageEntry,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
import { autoDetectTrimmableSections, finalizeMcpBudget } from '../../lib/response_budget.js'

// ── Infrastructure (self-contained proxy helper — see now.ts's identical header note on
// why this is duplicated rather than shared: avoids coupling this lane's facade to files
// owned/being edited by sibling lanes in the same concurrent campaign) ─────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const AYANAMSHA_ALIAS: Record<string, string> = {
  lahiri: 'lahiri_chitrapaksha', LAHIRI: 'lahiri_chitrapaksha', Lahiri: 'lahiri_chitrapaksha',
  lahiri_chitrapaksha: 'lahiri_chitrapaksha', true_chitra: 'lahiri_chitrapaksha',
}
function normalizeAyanamsha(id?: string): string {
  return id ? (AYANAMSHA_ALIAS[id] ?? id) : 'lahiri_chitrapaksha'
}

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

// ── W1 item 28 (daśā-lord transit condition, FORWARD half) — SHAD_DARSHANA_BRIEF_v2_0.md
// §3 W1. [J]-kind JOIN over EXISTING substrate (no new migration, no new astrological
// computation): identifies the currently-running Vimśottarī MD/AD lord chain TODAY (the
// SAME identification query now.ts's item 28 uses — a lord's identity does not re-derive
// per horizon date; only its transit snapshot moves), then snapshots that SAME lord's
// transit position at the AHEAD horizon boundary (`date_to`) instead of today — see
// now.ts's "W1 item 8 + item 28" doc-comment for the full provenance chain (this is a
// self-contained duplicate of that file's item-28 half, per this lane's established
// anti-coupling convention: platform-mcp facades do not share module-local helpers across
// files owned/edited by sibling lanes in the same campaign).

/** Mirrors get_av_transit_gating.ts's SIGN_NAMES (Aries..Pisces, sidereal, 1-indexed). */
const SIGN_NAMES = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

/** Mirrors get_av_transit_gating.ts's `houseFromSign` EXACTLY (same formula/semantics). */
function houseFromSign(signNumber: number, refSignNumber: number): number {
  return ((signNumber - refSignNumber + 12) % 12) + 1
}

/** LAGNA-only natal reference (item 8's dual-Moon-reference lives in now.ts; AHEAD's
 *  forward daśā-lord condition only needs the single Lagna house reference). Reads the
 *  SAME chart_facts category (graha_sign_attributes) get_dignity.ts already serves. */
async function fetchNatalLagnaSign(
  chartId: string,
  ayanamshaId: string,
  principal: Principal,
): Promise<{ lagna_sign_number: number | null; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L1/get_dignity',
    { chart_id: chartId, ayanamsha_id: ayanamshaId, categories: ['graha_sign_attributes'] },
    principal,
  )
  if (!resp.ok || !resp.content) return { lagna_sign_number: null, ok: false }
  const rows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const lagna = rows.find((r) => r['fact_subject'] === 'LAGNA' && r['fact_key'] === 'sign_num')
  return {
    lagna_sign_number: typeof lagna?.['fact_value_num'] === 'number' ? (lagna['fact_value_num'] as number) : null,
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

/** Single-day snapshot via the EXISTING L0 ephemeris capability
 *  (marsys://tool/L0/query_planet_transit) — same substrate ref_planet_transit_get already
 *  serves; sidereal-first, default ayanamsha lahiri_chitrapaksha. */
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

interface DignityReferenceRow {
  graha: string
  exaltation_sign: string | null
  debilitation_sign: string | null
  own_signs: string[] | null
}

/** Reads the SAME structured global reference table (bg_dignity_reference, 9 rows) that
 *  `ref_dignity_reference_get` (register_p1_reference.ts) already serves by planet, via the
 *  same direct-SQL platform route (`/api/mcp/db/query`). Read-only, global, no chart_id. */
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

type DashaLordDignityState = 'exalted' | 'debilitated' | 'own_sign' | 'neutral' | null

function classifyDashaLordDignity(signName: string | null, dignity: DignityReferenceRow | null): DashaLordDignityState {
  if (!signName || !dignity) return null
  if (dignity.exaltation_sign === signName) return 'exalted'
  if (dignity.debilitation_sign === signName) return 'debilitated'
  if (dignity.own_signs?.includes(signName)) return 'own_sign'
  return 'neutral'
}

export interface DashaLordForwardTransitCondition {
  level_name: string
  lord_graha: string
  lord_natal_sign: string | null
  identified_as_of_date: string
  forward_as_of_date: string
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

/** "Which daśā am I running TODAY?" via the EXISTING L3 convenience face
 *  (marsys://tool/L3/query_active_dashas, EL-33/DR-14), filtered to Vimśottarī level ≤2. The
 *  identification date is ALWAYS today (not the forward horizon boundary) — a lord's
 *  identity is a today-fact; only its transit condition is projected forward. */
async function fetchActiveVimshottariChain(
  chartId: string,
  ayanamshaId: string,
  identifyAsOfDate: string,
  principal: Principal,
): Promise<{ entries: ActiveDashaChainEntry[]; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_active_dashas',
    { chart_id: chartId, date: identifyAsOfDate, ayanamsha_id: ayanamshaId, systems: 'vimshottari', max_level: 2 },
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

/** Item 28 forward half (SHAD_DARSHANA_BRIEF_v2_0.md item 28, wave W1): the currently-
 *  running MD/AD lord's OWN transit condition projected to the AHEAD horizon boundary
 *  (`forwardAsOfDate`) — sign/house-from-lagna/dignity vs. classical exaltation-
 *  debilitation-own-sign. Dedupes when MD and AD share the same graha. */
async function computeDashaLordForwardTransitCondition(
  chartId: string,
  ayanamshaId: string,
  identifyAsOfDate: string,
  forwardAsOfDate: string,
  lagnaSignNumber: number | null,
  principal: Principal,
): Promise<{ rows: DashaLordForwardTransitCondition[]; chainReachable: boolean; transitReachable: boolean }> {
  const chain = await fetchActiveVimshottariChain(chartId, ayanamshaId, identifyAsOfDate, principal)
  if (!chain.ok || chain.entries.length === 0) {
    return { rows: [], chainReachable: chain.ok, transitReachable: true }
  }
  const uniqueGrahas = Array.from(new Set(chain.entries.map((e) => e.lord_graha).filter(Boolean)))
  const [snapshots, dignities] = await Promise.all([
    Promise.all(uniqueGrahas.map((g) => fetchPlanetTransitSnapshot(g, forwardAsOfDate, principal))),
    Promise.all(uniqueGrahas.map((g) => fetchDignityReference(g, principal))),
  ])
  const snapshotByGraha = new Map(snapshots.map((s) => [s.planet, s]))
  const dignityByGraha = new Map(uniqueGrahas.map((g, i) => [g, dignities[i] ?? null]))
  const transitReachable = snapshots.some((s) => s.ok)

  const rows: DashaLordForwardTransitCondition[] = chain.entries.map((entry) => {
    const snap = snapshotByGraha.get(entry.lord_graha)
    const signName = snap?.sign_number ? (SIGN_NAMES[snap.sign_number - 1] ?? null) : null
    const dignityRow = dignityByGraha.get(entry.lord_graha) ?? null
    return {
      level_name: entry.level_name,
      lord_graha: entry.lord_graha,
      lord_natal_sign: entry.lord_sign,
      identified_as_of_date: identifyAsOfDate,
      forward_as_of_date: forwardAsOfDate,
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

function dualOutput(data: unknown, toolName = 'kala_ahead_get') {
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

// ── Row shapes (read verbatim from query_temporal_activation / query_projections —
// never re-derived) ─────────────────────────────────────────────────────────────────

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

interface ProjectionFamily {
  window_start: string | null
  window_end: string | null
  domain: string | null
  member_count: number | string
  member_ids?: string[]
  member_signal_ids?: string[]
  probability_tier: 'tier_1_high' | 'tier_2_moderate' | 'tier_3_speculative' | null
  max_effective_score?: number | null
  narrative?: unknown
  source_citation?: string | null
  [key: string]: unknown
}

const TIER_TO_STRENGTH: Record<string, ArgumentEvidence['strength']> = {
  tier_1_high: 'strong',
  tier_2_moderate: 'moderate',
  tier_3_speculative: 'weak',
}
const TIER_LABEL: Record<string, string> = {
  tier_1_high: 'high probability',
  tier_2_moderate: 'moderate probability',
  tier_3_speculative: 'speculative',
}

// ── W1 item 32 join shapes (read verbatim from call_panchanga_service mode=range —
// never re-derived; §N.5) ────────────────────────────────────────────────────────────

interface PanchangTiming {
  label: string
  start_utc: string | null
  end_utc: string | null
  [key: string]: unknown
}

interface PanchangDayPayload {
  date: string
  inauspicious?: PanchangTiming[]
  [key: string]: unknown
}

export interface GulikaKalamAheadWindow {
  date: string
  window_start_utc: string | null
  window_end_utc: string | null
}

const GULIKA_AHEAD_MAX_DAYS = 30 // call_panchanga_service mode=range hard-caps date_to-date_from at 30 days (31 inclusive)

// ── The reading (template-over-computed-data — B.10; no generative call) ───────────

function buildAheadReading(params: {
  horizonLabel: string
  windowFamilies: WindowFamily[]
  projectionFamilies: ProjectionFamily[]
  windowsOk: boolean
  projectionsOk: boolean
}): ArgumentReading {
  const { horizonLabel, windowFamilies, projectionFamilies, windowsOk, projectionsOk } = params
  const topProjection = projectionFamilies[0]

  const thesisParts: string[] = []
  if (!projectionsOk && !windowsOk) {
    thesisParts.push(`Forward temporal data could not be reached for the next ${horizonLabel}.`)
  } else {
    if (windowFamilies.length > 0) {
      thesisParts.push(`${windowFamilies.length} forward-dated temporal window(s) identified over the next ${horizonLabel}.`)
    } else if (windowsOk) {
      thesisParts.push(`No forward-dated temporal window is currently computed over the next ${horizonLabel}.`)
    }
    if (topProjection) {
      const tierLabel = topProjection.probability_tier ? TIER_LABEL[topProjection.probability_tier] : 'ungraded'
      thesisParts.push(
        `${projectionFamilies.length} probabilistic projection(s) over the next ${horizonLabel}; leading: ` +
          `${topProjection.domain ?? 'unlabeled domain'} (${tierLabel}, window ${topProjection.window_start ?? '?'}..${topProjection.window_end ?? '?'}).`,
      )
    } else if (projectionsOk) {
      thesisParts.push(`No probabilistic projection is currently computed over the next ${horizonLabel}.`)
    }
  }

  const evidence: ArgumentEvidence[] = projectionFamilies.slice(0, 4).map((p) => ({
    claim:
      `${p.domain ?? 'unlabeled domain'} projection, window ${p.window_start ?? '?'}..${p.window_end ?? '?'}` +
      (p.probability_tier ? ` (${TIER_LABEL[p.probability_tier]})` : ''),
    fact_ids: [...(p.member_signal_ids ?? []), ...(p.member_ids ?? [])],
    strength: p.probability_tier ? TIER_TO_STRENGTH[p.probability_tier] : undefined,
  }))

  const tierCounts = projectionFamilies.reduce(
    (acc, p) => {
      if (p.probability_tier === 'tier_1_high') acc.tier1++
      else if (p.probability_tier === 'tier_2_moderate') acc.tier2++
      else if (p.probability_tier === 'tier_3_speculative') acc.tier3++
      return acc
    },
    { tier1: 0, tier2: 0, tier3: 0 },
  )

  const verdict: ArgumentVerdict = {
    statement:
      projectionFamilies.length > 0
        ? `${tierCounts.tier1} high, ${tierCounts.tier2} moderate, ${tierCounts.tier3} speculative forward window(s) identified over the next ${horizonLabel}.`
        : windowFamilies.length > 0
          ? `${windowFamilies.length} forward-dated temporal window(s) identified; no graded probabilistic projection available.`
          : 'No forward temporal window or projection is currently identified.',
    tier: 'structural_prior',
  }

  const falsifier: ArgumentFalsifier | null = topProjection
    ? {
        statement: `No ${topProjection.domain ?? 'projected'} event of this class materializes in the leading window`,
        resolves_by: topProjection.window_end ?? null,
      }
    : null

  return {
    thesis: thesisParts.join(' ') || `No forward temporal state could be assembled for the next ${horizonLabel}.`,
    evidence,
    dissent: [],
    verdict,
    falsifier,
  }
}

// ── Core compute (exported for tests) ───────────────────────────────────────────────

export interface KalaAheadResult {
  tool: 'kala_ahead_get'
  chart_id: string
  horizon_years: number
  reading: ArgumentReading
  reading_prose: string
  question_frame: QuestionFrame | null
  field_snapshot_id: string
  tri_plane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: ReturnType<typeof buildKalaFreshness>
  calibration_maturity: ReturnType<typeof noLelCalibrationMaturity>
  windows: WindowFamily[]
  projections: ProjectionFamily[]
  gulika_kalam_ahead: GulikaKalamAheadWindow[]
  gulika_kalam_ahead_horizon_days: number
  // Item 28 (wave W1): currently-running Vimśottarī MD/AD lord's transit condition
  // projected to this call's horizon boundary (date_to) — the forward half of now.ts's
  // dasha_lord_transit_condition (same lord identity, later snapshot date).
  dasha_lord_transit_condition_forward: DashaLordForwardTransitCondition[]
  drill_pointers: DrillPointerLike[]
  provenance_envelope: {
    source: string
    assets: string[]
    chart_id: string
    horizon_years: number
    domain: string | null
    computed_at: string
    source_citation: string
    gulika_kalam_reachable: boolean
    windows_reachable: boolean
    projections_reachable: boolean
    dasha_lord_transit_condition_forward_reachable: boolean
  }
}

const SOURCE_CITATION =
  'kala_activation / kala_activation_predicates (forward-dated) / kala_bhavishya (L3 Kāla, ' +
  'orchestrator-built) via Brahma retrieval registry — same substrate as kala_windows_get ' +
  '(forward-dated) / kala_projections_get, re-presented on the ṢAḌ-DARŚANA elevated envelope.'

export async function computeKalaAhead(
  chartId: string,
  args: {
    ayanamsha_id?: string
    horizon_years?: number
    domain?: string
    max_items?: number
    question_frame?: QuestionFrame | null
  },
  principal: Principal,
): Promise<KalaAheadResult> {
  const ayanamshaId = normalizeAyanamsha(args.ayanamsha_id)
  const horizonYears = args.horizon_years ?? 5
  const maxItems = args.max_items ?? 20
  const today = new Date()
  const dateFrom = today.toISOString().slice(0, 10)
  const dateTo = new Date(today.getTime() + horizonYears * 365 * 86400000).toISOString().slice(0, 10)
  const horizonLabel = `${horizonYears} year(s)`

  // item 32 join: gulika-kālam is bounded by call_panchanga_service's own 31-day range cap
  // (a sidecar-load guard) regardless of the requested horizon_years.
  const gulikaDateTo = new Date(today.getTime() + GULIKA_AHEAD_MAX_DAYS * 86400000).toISOString().slice(0, 10)

  const [windowsResp, projectionsResp, natalLagna, gulikaResp] = await Promise.all([
    callRegistryCapability(
      'marsys://tool/L3/query_temporal_activation',
      {
        chart_id: chartId,
        ayanamsha_id: ayanamshaId,
        date_from: dateFrom,
        date_to: dateTo,
        top_k: maxItems,
        ...(args.domain ? { domain: args.domain } : {}),
      },
      principal,
    ),
    callRegistryCapability(
      'marsys://tool/L3/query_projections',
      {
        chart_id: chartId,
        horizon_years: horizonYears,
        limit: maxItems,
        ...(args.domain ? { domain: args.domain } : {}),
      },
      principal,
    ),
    fetchNatalLagnaSign(chartId, ayanamshaId, principal),
    callRegistryCapability(
      'marsys://tool/L0/call_panchanga_service',
      { mode: 'range', date_from: dateFrom, date_to: gulikaDateTo },
      principal,
    ),
  ])

  const windowsOk = windowsResp.ok
  const rawFamilies = (windowsResp.content?.['window_families'] as WindowFamily[] | undefined) ?? []
  const rawForward = (windowsResp.content?.['forward_windows'] as WindowFamily[] | undefined) ?? []
  const windowFamilies = rawFamilies.length > 0 ? rawFamilies : rawForward

  const projectionsOk = projectionsResp.ok
  const projectionFamilies =
    (projectionsResp.content?.['projection_families'] as ProjectionFamily[] | undefined) ?? []

  // item 32 join: extract the already-computed gulika_kalam Timing per day from the
  // range-mode panchāṅga response — never re-derived (§N.5).
  const gulikaOk = gulikaResp.ok
  const gulikaDays = (gulikaResp.content?.['panchangs'] as PanchangDayPayload[] | undefined) ?? []
  const gulikaKalamAhead: GulikaKalamAheadWindow[] = gulikaDays
    .map((day) => {
      const entry = (day.inauspicious ?? []).find((t) => t.label === 'gulika_kalam')
      return entry ? { date: day.date, window_start_utc: entry.start_utc, window_end_utc: entry.end_utc } : null
    })
    .filter((w): w is GulikaKalamAheadWindow => w != null)

  // Item 28 forward half — identifies today's active MD/AD lord, snapshots it at dateTo.
  const dashaLordForward = await computeDashaLordForwardTransitCondition(
    chartId, ayanamshaId, dateFrom, dateTo, natalLagna.lagna_sign_number, principal,
  )

  const reading = buildAheadReading({ horizonLabel, windowFamilies, projectionFamilies, windowsOk, projectionsOk })
  const composed = composeArgument(reading)

  const triPlane: TriPlanePointers = {
    interpretation_ref: pointerTo(
      'kala_explain_get',
      'Why these forward windows fire — drivers and classical grounds behind each projection',
    ),
    // AHEAD IS the prediction plane — null is the contractually-legal value here.
    prediction_ref: null,
    intervention_ref: pointerTo('kala_elect_get', 'When exactly to act inside these forward windows'),
  }

  const coverage: KalaCoverageEntry[] = [
    windowsOk
      ? computedCoverage('forward_temporal_windows')
      : honestEmptyCoverage('forward_temporal_windows', 'L3 Kāla registry unreachable this call.'),
    projectionsOk
      ? computedCoverage('probabilistic_projections')
      : honestEmptyCoverage('probabilistic_projections', 'L3 Kāla registry unreachable this call.'),
    notInCorpusCoverage(
      'promise_gated_forecasting',
      'Law-3 PACT gating ("pressure without delivery") is not yet applied to these raw windows — SHAD_DARSHANA_BRIEF_v2_0.md §2.2 (wave W2/W3).',
    ),
    natalLagna.ok && dashaLordForward.chainReachable && dashaLordForward.transitReachable && dashaLordForward.rows.length > 0
      ? computedCoverage('dasha_lord_forward_transit_condition')
      : honestEmptyCoverage(
          'dasha_lord_forward_transit_condition',
          !dashaLordForward.chainReachable
            ? 'L3 active-dasha registry (query_active_dashas) unreachable this call.'
            : dashaLordForward.rows.length === 0
              ? 'No active Vimśottarī MD/AD chain resolved for this chart as of today — honest empty, not fabricated.'
              : 'L0 ephemeris or L1 natal-reference registry unreachable this call for the active lord(s).',
        ),
    notInCorpusCoverage(
      'sky_event_calendar',
      'Ingress/station/eclipse-to-natal/return event calendar not yet computed — SHAD_DARSHANA_BRIEF_v2_0.md item 3 (wave W3).',
    ),
    notInCorpusCoverage(
      'tithi_pravesa',
      'Lunar-return annual chart not yet computed — SHAD_DARSHANA_BRIEF_v2_0.md item 13 (wave W3).',
    ),
    gulikaKalamAhead.length > 0
      ? computedCoverage('gulika_kalam_ahead')
      : gulikaOk
        ? honestEmptyCoverage('gulika_kalam_ahead', 'No gulika_kalam window resolved for any day in the forward horizon.')
        : honestEmptyCoverage('gulika_kalam_ahead', 'L0 panchāṅga range service unreachable this call.'),
  ]

  const drillPointers: DrillPointerLike[] = [triPlane.interpretation_ref, triPlane.intervention_ref].filter(
    (p): p is DrillPointerLike => p != null && !isNoLever(p),
  )

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: args.question_frame ?? null,
    fieldSnapshotId: buildFieldSnapshotIdStub({
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      date_from: dateFrom,
      date_to: dateTo,
    }),
    triPlane,
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null }),
    calibrationMaturity: noLelCalibrationMaturity(),
  })

  return {
    tool: 'kala_ahead_get',
    chart_id: chartId,
    horizon_years: horizonYears,
    ...envelope,
    reading_prose: composed.full_text,
    windows: windowFamilies,
    projections: projectionFamilies,
    gulika_kalam_ahead: gulikaKalamAhead,
    gulika_kalam_ahead_horizon_days: GULIKA_AHEAD_MAX_DAYS,
    dasha_lord_transit_condition_forward: dashaLordForward.rows,
    drill_pointers: drillPointers,
    provenance_envelope: {
      source: 'kala_ahead_get',
      assets: [
        'kala_activation (ka_kalasutra, forward-dated)', 'kala_bhavishya (ka_bhavishya_lekha)',
        'call_panchanga_service (panchang.py, engine-direct, mode=range)',
        'get_dignity (graha_sign_attributes)', 'query_planet_transit (L0 ephemeris)',
        'query_active_dashas (L3, EL-33)', 'bg_dignity_reference (L0)',
      ],
      chart_id: chartId,
      horizon_years: horizonYears,
      domain: args.domain ?? null,
      computed_at: new Date().toISOString(),
      source_citation: SOURCE_CITATION,
      gulika_kalam_reachable: gulikaOk,
      windows_reachable: windowsOk,
      projections_reachable: projectionsOk,
      dasha_lord_transit_condition_forward_reachable:
        natalLagna.ok && dashaLordForward.chainReachable && dashaLordForward.transitReachable,
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
      'forward window — domain/entity/horizon/intent_verb/stakes/comparison_target. The chart ' +
      'is always implicit (chart_id); this is the only per-question input. W0: accepted and ' +
      'echoed verbatim — full relevance-scoring/reading-conditioning on this param is a ' +
      'later-wave elevation (E4 full).',
  )

const InputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')."),
  horizon_years: z.number().int().min(1).max(20).optional().describe('Forecast horizon in years (default: 5).'),
  domain: z.string().optional().describe('Filter to one life domain (e.g. career, wealth, relationship, health).'),
  max_items: z
    .number()
    .int()
    .min(1)
    .max(200)
    .optional()
    .describe('Max windows/projections to return per array (default: 20).'),
  question_frame: QuestionFrameSchema,
})

const TOOL_NAME = 'kala_ahead_get'

const TOOL_DESCRIPTION = `\
What is coming? Returns dated, shaped forward-looking temporal state for a chart — \
forward-dated temporal-activation windows (kala_activation, falling back to kala_bhavishya \
when none are dated within range) and probabilistic projections (kala_bhavishya, \
probability_tier-graded, family-collapsed) — composed into an argument-shaped reading \
(thesis → evidence → verdict → falsifier) on the ṢAḌ-DARŚANA elevated envelope \
(question_frame, field_snapshot_id, tri_plane pointers, 3-state coverage, freshness \
attestation, calibration_maturity).

THIN FACADE (W0): re-presents the SAME substrate kala_windows_get (forward-dated) and \
kala_projections_get already serve — no new computation; probability_tier is read \
verbatim from kala_bhavishya, never re-graded. W1 adds dasha_lord_transit_condition_forward \
(item 28 — the currently-running Vimśottarī MD/AD lord's own transit sign/house/dignity \
projected to this call's horizon boundary; see kala_now_get for the current-date half). \
Honestly discloses (via \`coverage\`) which richer AHEAD concepts (Law-3 promise-gated \
forecasting, the sky-event calendar, Tithi-Praveṣa) are not yet joined into this view.

W1 join (objective, raw data — no favorable/unfavorable grading): gulika_kalam_ahead — the \
daily gulika-kālam window for each of the next ${GULIKA_AHEAD_MAX_DAYS} days (bounded by the \
underlying panchāṅga range service's own 31-day cap, independent of horizon_years).

Output includes: reading (structured argument) + reading_prose (composed text) + windows + \
projections + gulika_kalam_ahead + dasha_lord_transit_condition_forward + tri_plane \
(→ kala_explain_get for why, → kala_elect_get for when to act) + coverage + drill_pointers.

Requires: chart_id (UUID). Successor to kala_projections_get for "what is coming" queries \
per SHAD_DARSHANA_BRIEF_v2_0.md §7 rail ("AHEAD supersedes ka_bhavishya... by REPLACEMENT") \
— kala_projections_get and kala_windows_get remain live (not retired).`

export function registerKalaAheadGetTool(server: McpServer, principal: Principal): void {
  server.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {
    const input = InputSchema.parse(params)
    if (!input.chart_id) return errOut(TOOL_NAME, 'chart_id is required')
    try {
      const result = await computeKalaAhead(
        input.chart_id,
        {
          ayanamsha_id: input.ayanamsha_id,
          horizon_years: input.horizon_years,
          domain: input.domain,
          max_items: input.max_items,
          question_frame: input.question_frame ?? null,
        },
        principal,
      )
      return dualOutput(result, TOOL_NAME)
    } catch (err) {
      return errOut(TOOL_NAME, err instanceof Error ? err.message : String(err), { chart_id: input.chart_id })
    }
  })
}
