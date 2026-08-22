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
 *
 * W1 JOIN ADDITION (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1, item 30): `mudda_dasha_varsha` —
 * KALA_SIX_VIEWS_DESIGN_v2_0.md §E: "Mudda daśā inside each varsha (the Tājika micro-clock,
 * already computed as one of the 8 systems, never joined)". A pure JOIN over TWO
 * already-computed substrates — the current varsha (Tājika annual) context
 * (`marsys://tool/L1/get_tajik`, the SAME table `ganita_tajaka_get` serves) and the active
 * Mudda daśā chain for the same date (`marsys://tool/L3/query_active_dashas`, system_id=
 * 'mudda' — the SAME capability the Vimśottarī joins elsewhere already call, one of the 9
 * systems `chart_dashas` already carries). See the "W1 item 30" doc-comment above
 * `computeMuddaDashaVarsha` below for the exact provenance chain.
 *
 * W1 JOIN ADDITION (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1, item 2): `recurrence_ladder` — the
 * recurrence-ladder serving item. KALA_SIX_VIEWS_DESIGN_v1_0.md §2.2 names this concept as
 * "already in `activation_predicted_dates_jsonb` — Saturn-AD re-fires 2032–33, 2047–50…) —
 * served as first-class future windows" and the item's own registry line names the column as
 * living on `bodha_msr_signals` (L2 Bodha, an "L3-fill hook" reserved NULL at L2 build time
 * per `platform/migrations/325_l2_bodha_enriched_schema.sql` / `bo_laksana.py`).
 * **Production-state check performed before writing this join (never assumed)**: a direct
 * query against `bodha_msr_signals.activation_predicted_dates_jsonb` on BOTH canonical charts
 * confirms it is genuinely **100% NULL** (0 of 49,608 rows on 482012f1; 0 of 49,980 on
 * 1c826d5a) — the L2 hook has never been populated by any writer, exactly as this item's
 * brief anticipated as a live possibility. Per the brief's own instruction ("do NOT build a
 * NEW computation to populate this column yourself... surface whatever recurrence-ladder
 * structure already exists"), a further check of the L3 substrate this SAME facade already
 * queries (`marsys://tool/L3/query_temporal_activation`, backed by `kala_activation`, the
 * `ka_kalasutra` writer's own table) found that table carries its OWN
 * `activation_predicted_dates_jsonb` column under the identical name — and THAT one is
 * genuinely populated (323,571 of 332,723 rows non-empty on 482012f1) with exactly the
 * recurrence-ladder shape the design doc describes (a dasha-timeline-derived sequence of
 * {date, point_kind: period_start/peak/end, strength, trigger, graha} entries spanning
 * decades). `ka_kalasutra.py`'s own docstring and its `_derive_activation_dates` /
 * `services.ka_temporal` fallback logic are the writer that actually fills this ladder; so
 * this join reads it from the RAW `activations` array already present in the SAME
 * `query_temporal_activation` response `windowsResp` this file already fetches for
 * `window_families`/`forward_windows` above — zero new registry calls, zero new migration,
 * zero new astrological computation (§N.5/B.10). The genuinely-NULL L2 hook is reported
 * honestly (not silently glossed over) in this join's inline commentary and in the PR/session
 * report; it is not fabricated, and no new writer is built to populate it (that would be
 * scope creep into a different asset's job, per the item's own instruction). See the
 * `computeRecurrenceLadder` doc-comment below for the exact per-signal collapse logic.
 *
 * E6-lite ADDITION (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1: "proactive 90-day digest preset on
 * AHEAD (D4)"): `digest_90d` — a curated, bounded-horizon SELECTION over fields this facade
 * already computes (window_families, projection_families, gulika_kalam_ahead,
 * recurrence_ladder, mudda_dasha_varsha) for the fixed next-90-days window from today. No new
 * computation, no new registry call — pure filter + template-composed summary (B.10). Per the
 * campaign's own Night-1 ledger note (brief §3 W1 Gate): "ritual rows are NOT expected here —
 * Mode 1 arrives at W4; a ritual-free W1 digest is the correct state" — this digest carries an
 * explicit `ritual_opportunities_note` saying so rather than silently omitting the concept.
 * See `buildAheadDigest90d` below.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import { autofileAheadWindows, type AheadAutofileResult } from '../../lib/ahead_autofile.js'
import {
  makeKalaEnvelope,
  fetchCalibrationMaturity,
  buildKalaFreshness,
  resolveFieldSnapshot,
  pointerTo,
  explainPointerTo,
  noLeverPointer,
  isNoLever,
  computedCoverage,
  honestEmptyCoverage,
  notInCorpusCoverage,
  type ArgumentReading,
  type ArgumentEvidence,
  type ArgumentDissent,
  type ArgumentVerdict,
  type ArgumentFalsifier,
  type QuestionFrame,
  type TriPlanePointers,
  type DrillPointerLike,
  type CalibrationMaturityResolution,
  type KalaCoverageEntry,
  type FieldSnapshotState,
} from '../../lib/kala_envelope.js'
import { composeArgument } from '../../lib/argument_composer.js'
// F-110 (CL-15): the promise-join helper's FIRST production caller. See the PromiseGate
// block below and 00_ARCHITECTURE/briefs/parisesa/F110_PACT_GATING_DESIGN_CONTRACT_v1_0.md.
// F-176 (PARISESA-V4): `computePromiseGate` + its types were extracted verbatim into
// `promise_gate.ts` so `kala_windows_get`/`kala_projections_get` can share the SAME gate —
// see that module's header for the full account. This file's behavior is byte-identical
// pre/post extraction (kala_ahead_get_f110_promise_gate.test.ts mocks at the `fetch` layer,
// so it exercises this exact code path unmodified).
import {
  computePromiseGate,
  type PromiseGate,
} from './promise_gate.js'
import { autoDetectTrimmableSections, finalizeMcpBudget } from '../../lib/response_budget.js'
// ṢAḌ-DARŚANA W4 (Lane R, Elevation §6 D4): Mode-1 ritual-opportunity rows join the
// 90-day digest. `fetchLatticeSubstrate` is the FROZEN engine's own fetcher and
// `scoreMode1Opportunities` terminates at that same engine — the ONE-ENGINE RULE holds
// through this path too; nothing here re-implements adjudication or grading.
import { fetchLatticeSubstrate } from '../../lib/kala_lattice_query.js'
import { scoreMode1Opportunities } from '../../lib/kala_ritual_resonance.js'
import { resolveChartFactsAyanamsha } from '../../lib/ayanamsha.js'

// ── Infrastructure (self-contained proxy helper — see now.ts's identical header note on
// why this is duplicated rather than shared: avoids coupling this lane's facade to files
// owned/being edited by sibling lanes in the same concurrent campaign) ─────────────────

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

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

/**
 * Why a transit lookup produced no row. Mirrors now.ts's `TransitLookupFailure` exactly (this
 * file duplicates rather than imports, per the established anti-coupling convention in the
 * header) — see now.ts for the full root-cause note on the ṢAḌ-DARŚANA W1 item 28
 * false-positive coverage claim this type exists to make impossible.
 */
export interface TransitLookupFailure {
  kind: 'dispatch_unreachable' | 'upstream_error'
  detail: string
  /** True when the failure is a deterministic upstream defect (retrying will not help) — the
   *  ND-4 half: a persistent defect must never be worded as transient unreachability. */
  persistent: boolean
}

interface PlanetTransitSnapshot {
  planet: string
  sign_number: number | null
  degree_in_sign: number | null
  nakshatra_number: number | null
  is_retrograde: boolean | null
  /** The call completed without error — `true` with all-null fields means a GENUINE empty. */
  ok: boolean
  failure: TransitLookupFailure | null
}

const NULL_TRANSIT_FIELDS = {
  sign_number: null,
  degree_in_sign: null,
  nakshatra_number: null,
  is_retrograde: null,
} as const

/** Single-day snapshot via the EXISTING L0 ephemeris capability
 *  (marsys://tool/L0/query_planet_transit) — same substrate ref_planet_transit_get already
 *  serves; sidereal-first, default ayanamsha lahiri_chitrapaksha. Never throws; classifies its
 *  own failure mode instead of collapsing every outcome to an indistinguishable empty row. */
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
  // The capability's OWN failure envelope (`{ ok: false, error, rows: [] }`) arrives over the
  // same HTTP 200 as a success — reading only the transport layer is what made a 401'd sidecar
  // call indistinguishable from a genuine empty.
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

/** Persistent-vs-transient coverage wording (ND-4), stated in exactly one place. */
function transitFailureReason(failure: TransitLookupFailure): string {
  return failure.persistent
    ? `L0 ephemeris capability (query_planet_transit) returned a PERSISTENT upstream error — ` +
      `this is a deterministic upstream failure, not transient unreachability, and retrying ` +
      `this call will reproduce it: ${failure.detail}`
    : `L0 ephemeris capability (query_planet_transit) could not be dispatched this call ` +
      `(transient): ${failure.detail}`
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
  // Item 31 (period-echo mining) needs the CURRENT period's own exact bounds — query_active_
  // dashas already returns these (its own DashaRow.start_date/end_date) — read verbatim, never
  // re-derived (§N.5). Optional (may be absent on a malformed row) rather than defaulted to a
  // fabricated date.
  start_date: string | null
  end_date: string | null
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
      start_date: typeof c['start_date'] === 'string' ? (c['start_date'] as string) : null,
      end_date: typeof c['end_date'] === 'string' ? (c['end_date'] as string) : null,
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
): Promise<{
  rows: DashaLordForwardTransitCondition[]
  chainReachable: boolean
  transitReachable: boolean
  transitFailure: TransitLookupFailure | null
  /** Earned-signal detector (CLAUDE.md §N.8): how many served rows actually carry a transit
   *  sign. `coverage`/`*_reachable` derive from THIS, not from "the dispatch returned 200". */
  rowsWithTransitData: number
  /** The raw active-chain entries this call already fetched (level_n/lord_graha/start_date/
   *  end_date) — exposed so item 31 (period-echo mining, below) can reuse the SAME dispatch
   *  rather than re-querying query_active_dashas a second time for the same date. */
  chain: ActiveDashaChainEntry[]
}> {
  const chain = await fetchActiveVimshottariChain(chartId, ayanamshaId, identifyAsOfDate, principal)
  if (!chain.ok || chain.entries.length === 0) {
    return {
      rows: [], chainReachable: chain.ok, transitReachable: true, transitFailure: null,
      rowsWithTransitData: 0, chain: chain.entries,
    }
  }
  const uniqueGrahas = Array.from(new Set(chain.entries.map((e) => e.lord_graha).filter(Boolean)))
  const [snapshots, dignities] = await Promise.all([
    Promise.all(uniqueGrahas.map((g) => fetchPlanetTransitSnapshot(g, forwardAsOfDate, principal))),
    Promise.all(uniqueGrahas.map((g) => fetchDignityReference(g, principal))),
  ])
  const snapshotByGraha = new Map(snapshots.map((s) => [s.planet, s]))
  const dignityByGraha = new Map(uniqueGrahas.map((g, i) => [g, dignities[i] ?? null]))
  const transitReachable = snapshots.some((s) => s.ok)
  const transitFailure = snapshots.find((s) => s.failure != null)?.failure ?? null

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
  const rowsWithTransitData = rows.filter((r) => r.transit_sign_number != null).length
  return { rows, chainReachable: chain.ok, transitReachable, transitFailure, rowsWithTransitData, chain: chain.entries }
}

// ── W1 item 30 (Mudda daśā joined to the varsha plane) — SHAD_DARSHANA_BRIEF_v2_0.md §3 W1.
// [J]-kind JOIN over TWO already-computed substrates (no new astrological computation, no new
// migration — §N.5/B.10): KALA_SIX_VIEWS_DESIGN_v2_0.md §E ("AHEAD — add: ... Mudda daśā
// inside each varsha (the Tājika micro-clock, already computed as one of the 8 systems, never
// joined)"):
//   - marsys://tool/L1/get_tajik (l1_tajik_varsha_year_lords — the SAME table ganita_tajaka_get
//     already serves): resolves the varsha (Tājika annual) context — varsha_year, year_lord,
//     Muntha sign/house — for the date in question, via that capability's own `varsha_date`
//     "current year" convenience.
//   - marsys://tool/L3/query_active_dashas (system_id='mudda' — Mudda is one of the 9 daśā
//     systems `chart_dashas` already carries per query_active_dashas.ts's EXPECTED_SYSTEMS;
//     the SAME capability now.ts/ahead.ts already call for 'vimshottari' elsewhere in this
//     campaign, parametrized to a different system_id): the currently-active Mudda
//     Mahādaśā/Antardaśā chain for the SAME date.
// Every field traces verbatim to one of these two existing capabilities' own output.

/**
 * ṢAḌ-DARŚANA W1 verify-reopen fix (item 30, Root Cause C), 2026-07-30.
 *
 * The Muntha fields were read as FLAT columns `muntha_sign` / `muntha_house` on the
 * `l1_tajik_varsha_year_lords` row. Those columns DO NOT EXIST — verified against the live
 * schema (`information_schema.columns`) and against a live `ganita_tajaka_get` response. The
 * Muntha is stored as a single JSONB column, `muntha_position_jsonb`, shaped:
 *
 *   { lord, sign, degree, house_from_natal_lagna, house_from_varsha_lagna }
 *
 * e.g. for the canonical chart's varsha 43 (2026-02-05 → 2027-02-05):
 *   { lord: "Venus", sign: "Libra", degree: 12.4311,
 *     house_from_natal_lagna: 7, house_from_varsha_lagna: 10 }
 *
 * So the data was real, two-pass-verified and sitting right there — the reader simply asked
 * for key names the writer never emits, and `typeof row['muntha_sign'] === 'string'` quietly
 * produced `null` on every chart. The null then leaked into served prose as "Muntha in
 * unknown" in the 90-day digest, with NO coverage entry disclosing the gap.
 *
 * Both house counts are now carried (they are genuinely different classical quantities: from
 * the NATAL lagna and from the VARSHA/annual lagna). `muntha_house` is retained as the
 * house-from-natal-lagna value — the reading a bare "Muntha house" means in Tājika, and the
 * one `citation_human` itself reports ("Muntha Libra (7H from Lagna, lord Venus)").
 */
interface MunthaPosition {
  sign: string | null
  degree: number | null
  lord: string | null
  house_from_natal_lagna: number | null
  house_from_varsha_lagna: number | null
}

interface TajikVarshaRow {
  varsha_year: number | null
  varsha_start_iso: string | null
  varsha_end_iso: string | null
  year_lord: string | null
  muntha_sign: string | null
  muntha_house: number | null
  muntha_degree: number | null
  muntha_lord: string | null
  muntha_house_from_varsha_lagna: number | null
}

/** Reads `muntha_position_jsonb` verbatim — never re-derived (§N.5). Returns all-null when the
 *  column is absent/malformed rather than inventing a shape (B.10). */
function parseMunthaPosition(raw: unknown): MunthaPosition {
  const empty: MunthaPosition = {
    sign: null, degree: null, lord: null,
    house_from_natal_lagna: null, house_from_varsha_lagna: null,
  }
  if (raw == null || typeof raw !== 'object' || Array.isArray(raw)) return empty
  const m = raw as Record<string, unknown>
  return {
    sign: typeof m['sign'] === 'string' ? (m['sign'] as string) : null,
    degree: typeof m['degree'] === 'number' ? (m['degree'] as number) : null,
    lord: typeof m['lord'] === 'string' ? (m['lord'] as string) : null,
    house_from_natal_lagna:
      typeof m['house_from_natal_lagna'] === 'number' ? (m['house_from_natal_lagna'] as number) : null,
    house_from_varsha_lagna:
      typeof m['house_from_varsha_lagna'] === 'number' ? (m['house_from_varsha_lagna'] as number) : null,
  }
}

/** Reads the current (or `dateISO`-containing) varsha row from l1_tajik_varsha_year_lords via
 *  the EXISTING marsys://tool/L1/get_tajik capability (register_p1_ganita.ts's
 *  ganita_tajaka_get already serves this same table) — never re-derived. */
async function fetchTajikVarshaForDate(
  chartId: string,
  ayanamshaId: string,
  dateISO: string,
  principal: Principal,
): Promise<{ row: TajikVarshaRow | null; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L1/get_tajik',
    { chart_id: chartId, ayanamsha_id: ayanamshaId, varsha_date: dateISO, include_varsha: true, include_hadda: false, limit: 1 },
    principal,
  )
  if (!resp.ok || !resp.content) return { row: null, ok: false }
  const rows = (resp.content['varsha_year_lords'] as { rows?: Array<Record<string, unknown>> } | undefined)?.rows ?? []
  const row = rows[0]
  if (!row) return { row: null, ok: true }
  // Root Cause C: read the Muntha out of `muntha_position_jsonb` (the real, live column) —
  // NOT the flat `muntha_sign`/`muntha_house` keys, which no writer has ever emitted. A
  // flat-column fallback is deliberately NOT added: inventing a second accepted shape would
  // mask the next occurrence of exactly this defect.
  const muntha = parseMunthaPosition(row['muntha_position_jsonb'])
  return {
    ok: true,
    row: {
      varsha_year: typeof row['varsha_year'] === 'number' ? (row['varsha_year'] as number) : null,
      varsha_start_iso: typeof row['varsha_start_iso'] === 'string' ? (row['varsha_start_iso'] as string) : null,
      varsha_end_iso: typeof row['varsha_end_iso'] === 'string' ? (row['varsha_end_iso'] as string) : null,
      year_lord: typeof row['year_lord'] === 'string' ? (row['year_lord'] as string) : null,
      muntha_sign: muntha.sign,
      muntha_house: muntha.house_from_natal_lagna,
      muntha_degree: muntha.degree,
      muntha_lord: muntha.lord,
      muntha_house_from_varsha_lagna: muntha.house_from_varsha_lagna,
    },
  }
}

export interface MuddaChainEntry {
  level_n: number
  level_name: string
  lord_graha: string
  lord_sign: string | null
  start_date: string | null
  end_date: string | null
}

/** Reads the active Mudda daśā chain (system_id='mudda') for `dateISO` via the SAME
 *  marsys://tool/L3/query_active_dashas capability the Vimśottarī joins elsewhere in this
 *  campaign already call, parametrized to `systems: 'mudda'` instead — never re-derived. */
async function fetchActiveMuddaChain(
  chartId: string,
  ayanamshaId: string,
  dateISO: string,
  principal: Principal,
): Promise<{ entries: MuddaChainEntry[]; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_active_dashas',
    { chart_id: chartId, date: dateISO, ayanamsha_id: ayanamshaId, systems: 'mudda', max_level: 2 },
    principal,
  )
  if (!resp.ok || !resp.content) return { entries: [], ok: false }
  const systems = (resp.content['systems'] as Array<Record<string, unknown>> | undefined) ?? []
  const mudda = systems.find((s) => s['system_id'] === 'mudda')
  const chain = (mudda?.['active_chain'] as Array<Record<string, unknown>> | undefined) ?? []
  return {
    ok: true,
    entries: chain.map((c) => ({
      level_n: typeof c['level_n'] === 'number' ? (c['level_n'] as number) : 0,
      level_name: typeof c['level_name'] === 'string' ? (c['level_name'] as string) : `L${c['level_n']}`,
      lord_graha: String(c['lord_graha'] ?? ''),
      lord_sign: typeof c['lord_sign'] === 'string' ? (c['lord_sign'] as string) : null,
      start_date: typeof c['start_date'] === 'string' ? (c['start_date'] as string) : null,
      end_date: typeof c['end_date'] === 'string' ? (c['end_date'] as string) : null,
    })),
  }
}

export interface MuddaDashaVarshaJoin {
  varsha_year: number | null
  varsha_start_iso: string | null
  varsha_end_iso: string | null
  year_lord: string | null
  /** Muntha rāśi, read verbatim from `muntha_position_jsonb.sign` (§N.5). */
  muntha_sign: string | null
  /** Muntha house counted from the NATAL lagna (`muntha_position_jsonb.house_from_natal_lagna`)
   *  — the reading a bare "Muntha house" denotes in Tājika. */
  muntha_house: number | null
  /** Muntha degree within its rāśi (`muntha_position_jsonb.degree`). */
  muntha_degree: number | null
  /** Muntha dispositor (`muntha_position_jsonb.lord`) — the Munthesa, one of the five Vārṣeśa
   *  candidate offices this same row's `candidate_lord_jsonb` scores. */
  muntha_lord: string | null
  /** Muntha house counted from the VARSHA (annual) lagna — a genuinely different classical
   *  quantity from `muntha_house`, served side by side rather than silently collapsed. */
  muntha_house_from_varsha_lagna: number | null
  as_of_date: string
  mudda_chain: Array<{ level_n: number; level_name: string; lord_graha: string; lord_sign: string | null; start_date: string | null; end_date: string | null }>
}

/** Item 30 (SHAD_DARSHANA_BRIEF_v2_0.md item 30, wave W1): joins the current varsha (Tājika
 *  annual) context with the active Mudda daśā chain for the SAME date — a pure [J] join over
 *  two already-computed substrates, no new computation. Honest-empty when either source is
 *  unreachable or resolves to nothing (never fabricated). */
async function computeMuddaDashaVarsha(
  chartId: string,
  ayanamshaId: string,
  asOfDate: string,
  principal: Principal,
): Promise<{ result: MuddaDashaVarshaJoin | null; tajikReachable: boolean; muddaReachable: boolean }> {
  const [varsha, mudda] = await Promise.all([
    fetchTajikVarshaForDate(chartId, ayanamshaId, asOfDate, principal),
    fetchActiveMuddaChain(chartId, ayanamshaId, asOfDate, principal),
  ])
  if (!varsha.ok || !varsha.row || !mudda.ok || mudda.entries.length === 0) {
    return { result: null, tajikReachable: varsha.ok, muddaReachable: mudda.ok }
  }
  return {
    result: {
      varsha_year: varsha.row.varsha_year,
      varsha_start_iso: varsha.row.varsha_start_iso,
      varsha_end_iso: varsha.row.varsha_end_iso,
      year_lord: varsha.row.year_lord,
      muntha_sign: varsha.row.muntha_sign,
      muntha_house: varsha.row.muntha_house,
      muntha_degree: varsha.row.muntha_degree,
      muntha_lord: varsha.row.muntha_lord,
      muntha_house_from_varsha_lagna: varsha.row.muntha_house_from_varsha_lagna,
      as_of_date: asOfDate,
      mudda_chain: mudda.entries.map((e) => ({
        level_n: e.level_n,
        level_name: e.level_name,
        lord_graha: e.lord_graha,
        lord_sign: e.lord_sign,
        start_date: e.start_date,
        end_date: e.end_date,
      })),
    },
    tajikReachable: true,
    muddaReachable: true,
  }
}

// ── W3 item 31 (period-echo mining, hypothesis-framed) — SHAD_DARSHANA_BRIEF_v2_0.md §3 W3,
// v2 §I.31 / KALA_SIX_VIEWS_DESIGN_v2_0.md §E ("AHEAD — add: ... period-echo mining — 'the
// last time a Saturn sub-period ran (2001–2004), the log shows X' — LEL-verified resonance of
// same-lord sub-periods, served as narrative hypothesis with falsifier, never as law
// (statistically tiny n, honestly labeled — but it is exactly how a great jyotiṣī actually
// reasons)").
//
// FIELD-INDEPENDENCE FINDING (pre-build investigation; both canonical charts checked LIVE
// against the production DB before writing any code — SHAD_DARSHANA_STATE.md's own W3
// next-action lists item 31 among the lanes to dispatch NOW, separately from items 33/34 which
// it explicitly marks "field-dependent, wait for the field"). This item does NOT require the
// W2 kala_field (still empty in production — Gate W2 is blocked on the N_e priors ruling, so
// ka_kshetra writes zero field rows; see SHAD_DARSHANA_STATE.md's "Gate W2" ledger row). It
// joins two substrates that already exist per-chart, both pre-dating W2:
//   (a) chart_dashas (marsys://tool/L1/get_dashas, lord_graha + level facets) — same-lord
//       recurrence of Vimśottarī Mahādaśā/Antardaśā periods across the chart's full built span
//       (verified live: both canonical charts carry ~11-13 Antardaśā occurrences per lord,
//       i.e. the built table spans more than one 120-year Vimśottarī cycle);
//   (b) life_events (marsys://tool/L5/lel_query — the SAME capability STORY's item-10
//       per-chapter LEL pinning already reads), joined by date-range overlap — exactly
//       STORY's `pinLelEventsToChapter` pattern, no new computation about the events
//       themselves (§N.5/B.10).
// LEL is native-only (verified live: `life_events` carries 63 rows for chart 482012f1 and
// ZERO for chart_id=1c826d5a) — so on the second canonical chart this facade correctly reports
// the STRUCTURAL echo (same-lord recurrence) with `lel_event_count: 0` on every candidate,
// never a fabricated biographical corroboration.
//
// PRE-BIRTH EXCLUSION. `chart_dashas` genuinely carries rows from BEFORE the native's birth
// (the balance-of-daśā Mahādaśā active at birth starts before the birth date, and the built
// table extends the classical 120-year cycle in both directions — verified live: chart
// 482012f1 carries Saturn Antardaśā rows from 1953 and 1962, 22-31 years before the 1984 birth
// date). Citing one of those as a period "the native lived through" would itself be a
// fabrication, so every candidate is floored at the native's own birth year — read from the
// SAME birth-anchored first chapter (parva_index=1) STORY's file-header doc-comment already
// establishes as the birth-anchored chapter (marsys://tool/L3/query_life_arc, top_k=1), never
// a second birth-date source.
//
// HYPOTHESIS DISCIPLINE (LAW ZERO). Every entry is served under `hypothesis` +
// `confidence_basis` + `falsifier` — never as a verdict or prediction. A level with zero
// qualifying prior same-lord occurrences reports `insufficient_data` honestly. This is the
// STRUCTURALLY EXPECTED, not exceptional, outcome at the Mahādaśā level: Vimśottarī's 120-year
// cycle gives each lord exactly one Mahādaśā per cycle, so a lived MD lord essentially never
// repeats within a human lifetime — verified live on both canonical charts (every MD-level
// lord_graha carries at most 1-2 built rows, and the second occurrence, when present, falls
// 100+ years in the future). Antardaśā-level repeats are the astrologically live case (up to 9
// occurrences of a given lord per 120-year cycle, one per Mahādaśā).

interface DashaEchoRow {
  lord_graha: string
  level_n: number
  start_date: string
  end_date: string
}

const PERIOD_ECHO_LEVEL_NAME: Record<number, string> = { 1: 'Mahadasha', 2: 'Antardasha' }
const PERIOD_ECHO_WINDOW_START = '1900-01-01'
const PERIOD_ECHO_WINDOW_END = '2100-12-31'

/** Every past occurrence of `lordGraha` at `levelN` (Vimśottarī) across the chart's full built
 *  span, via the SAME `marsys://tool/L1/get_dashas` capability `query_dasha_periods`/
 *  `ganita_dasha_periods_get` already serve — no new computation, no new migration. */
async function fetchDashaPeriodsByLordLevel(
  chartId: string,
  ayanamshaId: string,
  lordGraha: string,
  levelN: number,
  principal: Principal,
): Promise<{ rows: DashaEchoRow[]; ok: boolean }> {
  const resp = await callRegistryCapability(
    'marsys://tool/L1/get_dashas',
    {
      chart_id: chartId,
      ayanamsha_id: ayanamshaId,
      system: 'vimshottari',
      level: levelN,
      lord_graha: lordGraha,
      window_start: PERIOD_ECHO_WINDOW_START,
      window_end: PERIOD_ECHO_WINDOW_END,
      fields: 'compact',
      limit: 50,
    },
    principal,
  )
  if (!resp.ok || !resp.content) return { rows: [], ok: false }
  const rawRows = (resp.content['rows'] as Array<Record<string, unknown>> | undefined) ?? []
  const rows: DashaEchoRow[] = rawRows
    .filter((r) => typeof r['start_date'] === 'string' && typeof r['end_date'] === 'string')
    .map((r) => ({
      lord_graha: typeof r['lord_graha'] === 'string' ? (r['lord_graha'] as string) : lordGraha,
      level_n: typeof r['level_n'] === 'number' ? (r['level_n'] as number) : levelN,
      start_date: r['start_date'] as string,
      end_date: r['end_date'] as string,
    }))
  return { rows, ok: true }
}

/** Birth-year floor — see the pre-birth-exclusion doc-comment above. Reads the birth-anchored
 *  first chapter (`parva_index=1`, lowest ordinal, per `ORDER BY parva_index`) via the SAME
 *  `marsys://tool/L3/query_life_arc` capability STORY already calls; `top_k: 1` so this is a
 *  single bounded row, not the full life-arc fetch. */
async function fetchBirthYearFloor(chartId: string, principal: Principal): Promise<number | null> {
  const resp = await callRegistryCapability(
    'marsys://tool/L3/query_life_arc',
    { chart_id: chartId, include_lel_events: false, top_k: 1, offset: 0 },
    principal,
  )
  if (!resp.ok || !resp.content) return null
  const parvas = (resp.content['parvas'] as Array<Record<string, unknown>> | undefined) ?? []
  const first = parvas[0]
  return typeof first?.['start_year'] === 'number' ? (first['start_year'] as number) : null
}

/** Minimal local LEL row shape for period-echo purposes — a DELIBERATE local duplicate of
 *  story.ts's `RawLelEvent` (this lane's established anti-coupling convention: see this
 *  file's header note on why `callRegistryCapability` itself is duplicated rather than
 *  shared — platform-mcp facades do not reach into a sibling lane's private module). */
interface RawLelEventEcho {
  event_id: string
  event_date: string
  category: string
  domain: string
  event_type: string
  description: string
  source_citation: string
  shape?: 'point' | 'interval' | 'chain'
  interval_start?: string | null
  interval_end?: string | null
}

const LEL_ECHO_PAGE_LIMIT = 50
const LEL_ECHO_MAX_PAGES = 10

/** Fetches the WHOLE LEL corpus for a chart via `marsys://tool/L5/lel_query`, paginated to
 *  exhaustion — a local duplicate of story.ts's `fetchAllChartLelEvents` (item 10), same
 *  capability, same pagination discipline, same never-throws contract: an LEL outage must not
 *  take this view down, and is reported honestly via `fetchError`, never silently swallowed
 *  (B.10). CIRCULARITY GUARD (brief §7 rail): this is a serving-layer read that terminates at
 *  THIS response — nothing here is written to any table or consumed by any other writer,
 *  exactly the boundary story.ts's own CIRCULARITY GUARD note documents for its LEL read. */
async function fetchAllChartLelEventsForEcho(
  chartId: string,
  principal: Principal,
): Promise<{ events: RawLelEventEcho[]; fetchError: string | null }> {
  const events: RawLelEventEcho[] = []
  let offset = 0
  try {
    for (let page = 0; page < LEL_ECHO_MAX_PAGES; page++) {
      const resp = await callRegistryCapability(
        'marsys://tool/L5/lel_query',
        { chart_id: chartId, limit: LEL_ECHO_PAGE_LIMIT, offset },
        principal,
      )
      // NOTE: this file's local `callRegistryCapability` (unlike shared.ts's
      // `callKalaRegistryCap` story.ts uses) swallows a dispatch failure into
      // `{ ok: false, content: null }` rather than throwing — so a failed dispatch must be
      // detected HERE, not assumed to surface via the catch block below. Treating `!resp.ok`
      // the same as "zero events" would make a genuine outage indistinguishable from a
      // genuinely-empty LEL corpus (B.10).
      if (!resp.ok || !resp.content) {
        return {
          events,
          fetchError: `marsys://tool/L5/lel_query dispatch failed (page offset=${offset})`,
        }
      }
      const pageEvents = (resp.content['events'] as RawLelEventEcho[] | undefined) ?? []
      events.push(...pageEvents)
      const hasMore = resp.content['has_more'] === true
      if (pageEvents.length === 0 || !hasMore) break
      offset += pageEvents.length
    }
    return { events, fetchError: null }
  } catch (err) {
    return { events, fetchError: String(err) }
  }
}

/** An LEL event's effective date span — mirrors story.ts's `lelEventSpan` exactly (interval
 *  events use their real bounds; every other shape collapses to a single-day span, never a
 *  fabricated wider bound for a point event). */
function lelEventSpanEcho(event: RawLelEventEcho): { start: string; end: string } {
  if (event.shape === 'interval' && event.interval_start && event.interval_end) {
    return { start: event.interval_start, end: event.interval_end }
  }
  return { start: event.event_date, end: event.event_date }
}

function truncateEchoDescription(s: string): string {
  return s.length > 200 ? `${s.slice(0, 197)}...` : s
}

export interface PeriodEchoLelEvent {
  event_id: string
  event_date: string
  category: string
  domain: string
  description: string
  source_citation: string
}

export interface PeriodEchoCandidate {
  start_date: string
  end_date: string
  lel_event_count: number
  lel_events_sample: PeriodEchoLelEvent[]
}

export interface PeriodEchoEntry {
  level_n: number
  level_name: string
  lord_graha: string
  current_period: { start_date: string; end_date: string }
  same_lord_past_occurrence_count: number
  lel_corroborated_occurrence_count: number
  candidates: PeriodEchoCandidate[]
  /** Explicit hypothesis prose, or `null` when `status: 'insufficient_data'` — NEVER a
   *  prediction/verdict (LAW ZERO). */
  hypothesis: string | null
  confidence_basis: string
  falsifier: string
  status: 'hypothesis_served' | 'insufficient_data'
  insufficient_data_reason: string | null
}

/** Item 31's core: for ONE currently-active chain entry (Mahādaśā or Antardaśā), finds every
 *  COMPLETED prior occurrence of the SAME lord at the SAME level in the native's own lived
 *  timeline (birth-floored, ends before the current period started), joins each to the LEL
 *  corpus by date-range overlap, and composes an explicit, falsifiable hypothesis — never a
 *  prediction. Template-composed prose only (campaign rail: "the argument composer is
 *  template-over-computed-data; no generative call in any serving path"). */
async function computePeriodEchoForLevel(
  chartId: string,
  ayanamshaId: string,
  levelN: number,
  currentLordGraha: string,
  currentStart: string,
  currentEnd: string,
  birthYearFloor: number | null,
  lelEvents: RawLelEventEcho[],
  lelFetchError: string | null,
  principal: Principal,
): Promise<PeriodEchoEntry> {
  const levelName = PERIOD_ECHO_LEVEL_NAME[levelN] ?? `L${levelN}`
  const currentPeriod = { start_date: currentStart, end_date: currentEnd }
  const { rows, ok } = await fetchDashaPeriodsByLordLevel(chartId, ayanamshaId, currentLordGraha, levelN, principal)

  if (!ok) {
    return {
      level_n: levelN, level_name: levelName, lord_graha: currentLordGraha, current_period: currentPeriod,
      same_lord_past_occurrence_count: 0, lel_corroborated_occurrence_count: 0, candidates: [], hypothesis: null,
      confidence_basis: 'N=0 comparisons — L1 dasha registry (get_dashas) unreachable this call.',
      falsifier: 'not applicable — no hypothesis served',
      status: 'insufficient_data',
      insufficient_data_reason: 'L1 dasha registry (marsys://tool/L1/get_dashas) unreachable this call.',
    }
  }

  // Birth-floor unresolved: withhold ENTIRELY rather than risk citing a pre-birth row as a
  // "lived" past occurrence — this must gate BEFORE filtering, not only the zero-rows branch,
  // otherwise a genuinely pre-birth row could slip through un-excluded whenever the floor call
  // fails but the lord-level query still returns rows (verified live: chart_dashas DOES carry
  // pre-birth rows for both canonical charts — see the item-31 doc-comment above).
  if (birthYearFloor == null) {
    return {
      level_n: levelN, level_name: levelName, lord_graha: currentLordGraha, current_period: currentPeriod,
      same_lord_past_occurrence_count: 0, lel_corroborated_occurrence_count: 0, candidates: [], hypothesis: null,
      confidence_basis: 'N=0 comparisons — birth-year floor unresolved.',
      falsifier: 'not applicable — no hypothesis served',
      status: 'insufficient_data',
      insufficient_data_reason:
        `No prior ${currentLordGraha} ${levelName} occurrence could be safely checked: the birth-year ` +
        'floor could not be resolved (marsys://tool/L3/query_life_arc unreachable), and citing a row ' +
        'without confirming it postdates the native\'s birth risks citing a pre-birth period — served ' +
        'insufficient_data rather than take that risk.',
    }
  }

  const birthFloorDate = `${birthYearFloor}-01-01`
  const pastRows = rows.filter((r) => {
    if (r.end_date >= currentStart) return false // only genuinely COMPLETED prior occurrences
    if (r.start_date < birthFloorDate) return false // never cite a pre-birth row
    return true
  })

  if (pastRows.length === 0) {
    const reason =
      `No prior ${currentLordGraha} ${levelName} occurrence in the native's own lived timeline ` +
      `(since ${birthYearFloor}) precedes the current period. ` +
      (levelName === 'Mahadasha'
        ? "Expected: Vimśottarī's 120-year cycle gives each lord exactly one Mahādaśā per cycle, so a " +
          'repeat within a human lifetime is structurally rare.'
        : "This is the first time this lord has run this period at this level in the native's life.")
    return {
      level_n: levelN, level_name: levelName, lord_graha: currentLordGraha, current_period: currentPeriod,
      same_lord_past_occurrence_count: 0, lel_corroborated_occurrence_count: 0, candidates: [], hypothesis: null,
      confidence_basis: 'N=0 same-lord prior occurrences found in the native\'s lived timeline.',
      falsifier: 'not applicable — no hypothesis served',
      status: 'insufficient_data',
      insufficient_data_reason: reason,
    }
  }

  const candidates: PeriodEchoCandidate[] = pastRows
    .map((r) => {
      const pinned = lelFetchError
        ? []
        : lelEvents.filter((ev) => {
            const span = lelEventSpanEcho(ev)
            return span.start <= r.end_date && span.end >= r.start_date
          })
      return {
        start_date: r.start_date,
        end_date: r.end_date,
        lel_event_count: pinned.length,
        lel_events_sample: pinned.slice(0, 3).map((ev) => ({
          event_id: ev.event_id,
          event_date: ev.event_date,
          category: ev.category,
          domain: ev.domain,
          description: truncateEchoDescription(ev.description),
          source_citation: ev.source_citation,
        })),
      }
    })
    .sort((a, b) => b.lel_event_count - a.lel_event_count || b.start_date.localeCompare(a.start_date))

  const lelCorroboratedCount = candidates.filter((c) => c.lel_event_count > 0).length
  const topCandidates = candidates.slice(0, 3)
  const hypothesisParts = topCandidates.map((c) =>
    c.lel_event_count > 0
      ? `${c.start_date} to ${c.end_date} (${c.lel_event_count} logged life event(s): ${c.lel_events_sample.map((e) => e.domain).join('; ')})`
      : `${c.start_date} to ${c.end_date} (no logged life events on file)`,
  )

  const hypothesis =
    `Hypothesis: the current ${currentLordGraha} ${levelName} (${currentStart} to ${currentEnd}) may echo ` +
    `${currentLordGraha}'s prior ${levelName}${topCandidates.length > 1 ? ' periods' : ' period'} — ` +
    `${hypothesisParts.join('; ')} — because both share the same daśā lord at the same level. This is a ` +
    'structural resonance hypothesis, not a prediction: the sample size is small and no cohort-normalized ' +
    "calibration backs it yet (that is W2's mi_bhara job, per SHAD_DARSHANA_BRIEF_v2_0.md §3 W2 stage 9)."

  const lelNote = lelFetchError
    ? ` LEL fetch failed (${lelFetchError}) — every lel_event_count above is UNAVAILABLE, not a confirmed zero.`
    : ''

  return {
    level_n: levelN,
    level_name: levelName,
    lord_graha: currentLordGraha,
    current_period: currentPeriod,
    same_lord_past_occurrence_count: pastRows.length,
    lel_corroborated_occurrence_count: lelCorroboratedCount,
    candidates,
    hypothesis,
    confidence_basis:
      `N=${pastRows.length} same-lord prior ${levelName} occurrence(s) found in the native's lived timeline; ` +
      `${lelCorroboratedCount} of ${pastRows.length} carry ≥ 1 logged LEL life event within their span.` +
      lelNote,
    falsifier:
      `If the native's actual experience during ${currentStart}–${currentEnd} does NOT resemble the ` +
      'domains/themes logged for the cited prior occurrence(s), this hypothesis is falsified — record the ' +
      'divergence via mimamsa_outcome_record.',
    status: 'hypothesis_served',
    insufficient_data_reason: null,
  }
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

// ── F-110 (CL-15, TIER1-CORRECTNESS): PACT promise gate ─────────────────────────────
//
// THE DEFECT. For the identical chart/domain/date this tool served a `tier_1_high`
// relationship projection narrated "High probability (>=70% convergence, clear
// activation)" with `dissent: []`, while `pact_query`/`kala_upaya_get` on the SAME server
// held `pact_status: 'denied_at_promise'` on 63 cited L1 facts — "the rāśi checklist does
// not promise this matter". Which verdict a real person received was decided entirely by
// which tool the consuming LLM happened to pick, and the natural tool for "when will I
// marry" was the one that omitted the denial.
//
// WHAT IS AND IS NOT TOUCHED (§N.5 / §N.7 — the load-bearing distinction):
//   - `probability_tier`, `narrative`, `max_effective_score` are L3-computed
//     (ka_bhavishya_lekha) and pass through BYTE-IDENTICAL. This facade does not and must
//     not re-grade them (this file's own header contract; MSR_COMPUTED_VALUE_DRIFT trap).
//   - `reading.thesis` / `reading.verdict.statement` / `reading.dissent` /
//     `evidence[].strength` are THIS FILE's own compositions (`buildAheadReading`,
//     `TIER_TO_STRENGTH`). §N.7 governs them, and this file may not author the word
//     "strong" — nor the empty array `dissent: []`, which asserts that no dissent exists —
//     while the server holds a contradicting classical verdict. Correcting the narration
//     is NOT re-grading the tier.
//
// STAGE SCOPE (§4.2 of the design contract) — a naive wiring would apply any `denied_at_*`
// to every forward window, which would be a second correctness defect:
//   - denied_at_promise / denied_at_confirmation rest on natal + varga facts. Timeless →
//     they validly gate the WHOLE forward horizon.
//   - denied_at_activation is evaluated AS OF ONE DATE. It says nothing about a window in
//     2030 and MUST NOT gate it.
//   - chain_pending_activation / chain_incomplete_infra are not denials at all (R-22).
//
// Full investigation, rejected alternatives (tier downgrade / suppression), and the three
// items escalated for a native ruling:
// `00_ARCHITECTURE/briefs/parisesa/F110_PACT_GATING_DESIGN_CONTRACT_v1_0.md`.
//
// F-176 (PARISESA-V4): `computePromiseGate` + `PromiseGate` (and its scope/state types) now
// live in `./promise_gate.js`, shared with `kala_windows_get`/`kala_projections_get`
// (register_p1_aliases.ts) — see that module's header. This file calls it with its own local
// `callRegistryCapability`, so the call below is byte-identical in behavior to the pre-
// extraction inline version.

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

// ── W1 item 2 (recurrence-ladder serving) — SHAD_DARSHANA_BRIEF_v2_0.md §3 W1. [J]-kind
// JOIN over the RAW `activations` array the SAME `query_temporal_activation` call above
// already returns (see the file-header doc-comment for the full production-state
// investigation: `bodha_msr_signals.activation_predicted_dates_jsonb` — the L2 hook the
// item is literally named after — is genuinely 100% NULL on both canonical charts; the
// populated substrate this join actually reads is `kala_activation.activation_predicted_
// dates_jsonb`, the L3 `ka_kalasutra` table's own same-named column). No new registry call,
// no new migration, no new astrological computation (§N.5/B.10). ────────────────────────

/** Shape of one point inside a raw `activation_predicted_dates_jsonb` array element. The
 *  dasha-timeline path (`services.ka_temporal`) emits the full shape below; the older
 *  convergence-peak fallback (`_derive_activation_dates` in ka_kalasutra.py) emits only
 *  {date, strength, trigger} — every other field is optional here for that reason. */
interface RecurrenceLadderPointRaw {
  date?: string
  strength?: number | null
  trigger?: string | null
  graha?: string | null
  point_kind?: string | null
  [key: string]: unknown
}

/** Raw row shape from `query_temporal_activation`'s `activations` array (never re-derived —
 *  read verbatim from the SAME SQL projection that already backs `window_families`). */
interface RawActivationRow {
  signal_id?: string
  signature_class?: string | null
  orb_strength?: number | null
  source_citation?: string | null
  activation_predicted_dates_jsonb?: RecurrenceLadderPointRaw[] | null
  domains_affected_array?: string[] | null
  [key: string]: unknown
}

export interface RecurrenceLadderPoint {
  date: string
  point_kind: string | null
  strength: number | null
  trigger: string | null
  graha: string | null
}

export interface RecurrenceLadderEntry {
  signal_id: string
  signature_class: string | null
  domains_affected: string[]
  max_orb_strength: number | null
  source_citation: string | null
  /** Only points with `date >= today` — the forward half of the ladder (AHEAD is a
   *  forward-looking view). Sorted ascending. */
  future_points: RecurrenceLadderPoint[]
  /** Total points in the ladder (past + future) — honest disclosure of how much of the
   *  full recurrence history this signal's ladder carries, even though only the future
   *  half is surfaced in `future_points`. */
  total_points_in_ladder: number
}

/**
 * Item 2: collapses the raw per-predicate `activations` rows into one recurrence-ladder
 * entry per `signal_id` (several predicate rows can share byte-identical ladders for the
 * same signal — a predicate-count artifact, not a real distinction — so this keeps only the
 * highest-`orb_strength` row per signal, exactly the same "collapse duplicated rows into
 * one family" pattern `query_temporal_activation.ts`'s own `window_families` already uses,
 * applied here to a different grouping key). Drops signals whose ladder is entirely in the
 * past relative to `todayISO` (nothing forward to serve) — never fabricates a future point.
 */
function computeRecurrenceLadder(
  rawActivations: RawActivationRow[],
  todayISO: string,
  maxItems: number,
): { entries: RecurrenceLadderEntry[]; anyLadderPresent: boolean } {
  const bySignal = new Map<string, RecurrenceLadderEntry>()
  let anyLadderPresent = false

  for (const row of rawActivations) {
    const signalId = typeof row['signal_id'] === 'string' ? (row['signal_id'] as string) : null
    const rawDates = row['activation_predicted_dates_jsonb']
    if (!signalId || !Array.isArray(rawDates) || rawDates.length === 0) continue
    anyLadderPresent = true

    const orb = typeof row['orb_strength'] === 'number' ? (row['orb_strength'] as number) : null
    const existing = bySignal.get(signalId)
    if (existing && (existing.max_orb_strength ?? -Infinity) >= (orb ?? -Infinity)) continue

    const points: RecurrenceLadderPoint[] = (rawDates as RecurrenceLadderPointRaw[])
      .filter((p): p is RecurrenceLadderPointRaw & { date: string } => typeof p?.date === 'string')
      .map((p) => ({
        date: p.date,
        point_kind: typeof p.point_kind === 'string' ? p.point_kind : null,
        strength: typeof p.strength === 'number' ? p.strength : null,
        trigger: typeof p.trigger === 'string' ? p.trigger : null,
        graha: typeof p.graha === 'string' ? p.graha : null,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
    const futurePoints = points.filter((p) => p.date >= todayISO)

    bySignal.set(signalId, {
      signal_id: signalId,
      signature_class: typeof row['signature_class'] === 'string' ? (row['signature_class'] as string) : null,
      domains_affected: Array.isArray(row['domains_affected_array']) ? (row['domains_affected_array'] as string[]) : [],
      max_orb_strength: orb,
      source_citation: typeof row['source_citation'] === 'string' ? (row['source_citation'] as string) : null,
      future_points: futurePoints,
      total_points_in_ladder: points.length,
    })
  }

  const entries = [...bySignal.values()]
    .filter((e) => e.future_points.length > 0)
    .sort((a, b) => {
      const aNext = a.future_points[0]?.date ?? '9999-99-99'
      const bNext = b.future_points[0]?.date ?? '9999-99-99'
      return aNext.localeCompare(bNext) || (b.max_orb_strength ?? 0) - (a.max_orb_strength ?? 0)
    })
    .slice(0, maxItems)

  return { entries, anyLadderPresent }
}

// ── E6-lite (90-day digest preset on AHEAD, D4) — SHAD_DARSHANA_BRIEF_v2_0.md §3 W1. Pure
// SELECTION over fields this facade already computes above — no new registry call, no new
// computation, template-composed prose only (B.10). ─────────────────────────────────────

export interface AheadDigestItem {
  // 'ritual_opportunity' added at ṢAḌ-DARŚANA W4 (Lane R, the Elevation §6 D4 clause):
  // Mode-1 (window, rite) pairs join the digest now that Mode 1 exists. The digest stays a
  // SELECTION over already-computed rows — Mode 1 is computed by the ritual path and joined
  // here, never recomputed inside ahead.ts.
  kind: 'temporal_window' | 'probabilistic_projection' | 'gulika_kalam' | 'recurrence_ladder_point' | 'mudda_dasha_varsha' | 'ritual_opportunity'
  label: string
  window_or_date: string
  detail: string
  fact_ids: string[]
}

/** One already-computed Mode-1 opportunity, in the minimal shape this digest needs.
 *  Structurally identical to the fields `RitualOpportunity` exposes — declared locally so
 *  `ahead.ts` takes no import-graph dependency on Lane R's scorer for a SELECTION step. */
export interface AheadRitualOpportunityInput {
  window: { start_utc: string; end_utc: string }
  rite: { rite_class: string | null; planet: string | null; citation: string | null }
  score_vector: { composite: number | null; factors_present: string[]; factors_absent: string[] }
}

export interface AheadDigest90d {
  as_of_date: string
  digest_to_date: string
  horizon_days: 90
  items: AheadDigestItem[]
  item_count: number
  ritual_opportunities_note: string
}

/** True when a window/point `[start, end]` (either bound may stand in for the other when
 *  only one is known) overlaps the fixed `[asOf, to]` digest horizon. */
function overlapsDigestWindow(
  windowStart: string | null | undefined,
  windowEnd: string | null | undefined,
  asOf: string,
  to: string,
): boolean {
  if (!windowStart && !windowEnd) return false
  const start = windowStart ?? (windowEnd as string)
  const end = windowEnd ?? (windowStart as string)
  return end >= asOf && start <= to
}

/**
 * ṢAḌ-DARŚANA W4 (Lane R, the Elevation §6 D4 clause) REPLACED THIS NOTE'S SEMANTICS.
 *
 * At W1 it was a standing placeholder naming W4 as future work. Post-W4 its survival
 * UNCHANGED would itself be the gate failure (design §9 G8: "the W1 placeholder note
 * surviving unchanged — its presence post-W4 is itself the FAIL"). It is now either the
 * EMPTY STRING (rows are present, so no note is needed) or an honest-empty statement
 * NAMING THE HORIZON ACTUALLY SEARCHED — dates, not "the horizon".
 */
function ritualOpportunitiesNote(
  rows: AheadRitualOpportunityInput[] | null,
  asOfDate: string,
  digestToDate: string,
): string {
  if (rows !== null && rows.length > 0) return ''
  if (rows === null) {
    return (
      `No ritual-opportunity rows were joined into this digest: the Mode-1 opportunity scan was ` +
      `not supplied to this call, so the horizon ${asOfDate} .. ${digestToDate} was NOT searched ` +
      `for them. This is an unsearched horizon, not an empty one — the two are different claims.`
    )
  }
  return (
    `No ritual opportunity was found in ${asOfDate} .. ${digestToDate} — the horizon WAS searched ` +
    `(kala_ritual_get Mode 1, over the muhūrta lattice's auspicious combination-yoga spans) and ` +
    `returned nothing for this chart. An honest empty over a named, searched horizon.`
  )
}

/**
 * E6-lite: builds the fixed 90-day-forward digest by SELECTING (never computing) from the
 * already-assembled window/projection/gulika/recurrence-ladder/mudda-varsha fields above,
 * bounded to `[asOfDate, digestToDate]`. Each surface contributes at most a small, curated
 * number of items — the daily gulika-kālam windows collapse to ONE summary item (not 30
 * daily rows) and each recurrence-ladder signal collapses to ONE item naming its nearest
 * in-window occurrence, consistent with the design's "family-collapsed, never 25
 * photocopies" horizon-preset discipline (KALA_SIX_VIEWS_DESIGN_v1_0.md §2.3).
 */
function buildAheadDigest90d(params: {
  asOfDate: string
  digestToDate: string
  windowFamilies: WindowFamily[]
  projectionFamilies: ProjectionFamily[]
  gulikaKalamAhead: GulikaKalamAheadWindow[]
  recurrenceLadder: RecurrenceLadderEntry[]
  muddaDashaVarsha: MuddaDashaVarshaJoin | null
  /** W4 D4: already-computed Mode-1 rows to SELECT from. `null` means the scan was not
   *  supplied to this call — distinct from `[]`, which means it ran and found nothing. */
  ritualOpportunities?: AheadRitualOpportunityInput[] | null
}): AheadDigest90d {
  const { asOfDate, digestToDate, windowFamilies, projectionFamilies, gulikaKalamAhead, recurrenceLadder, muddaDashaVarsha } = params
  const ritualOpportunities = params.ritualOpportunities ?? null
  const items: AheadDigestItem[] = []

  for (const w of windowFamilies) {
    if (!overlapsDigestWindow(w.window_start, w.window_end, asOfDate, digestToDate)) continue
    items.push({
      kind: 'temporal_window',
      label: `${w.domains && w.domains.length > 0 ? w.domains.join('/') : 'unlabeled domain'} temporal window`,
      window_or_date: `${w.window_start ?? '?'}..${w.window_end ?? '?'}`,
      detail:
        `${w.member_count} corroborating signal(s)` +
        (w.signature_classes && w.signature_classes.length > 0 ? `, classes: ${w.signature_classes.join(', ')}` : ''),
      fact_ids: w.member_signal_ids ?? [],
    })
  }

  for (const p of projectionFamilies) {
    if (!overlapsDigestWindow(p.window_start, p.window_end, asOfDate, digestToDate)) continue
    const tierLabel = p.probability_tier ? TIER_LABEL[p.probability_tier] : 'ungraded'
    items.push({
      kind: 'probabilistic_projection',
      label: `${p.domain ?? 'unlabeled domain'} projection (${tierLabel})`,
      window_or_date: `${p.window_start ?? '?'}..${p.window_end ?? '?'}`,
      detail: `${p.member_count} member signal(s)`,
      fact_ids: [...(p.member_signal_ids ?? []), ...(p.member_ids ?? [])],
    })
  }

  if (gulikaKalamAhead.length > 0) {
    const dates = [...gulikaKalamAhead.map((g) => g.date)].sort()
    items.push({
      kind: 'gulika_kalam',
      label: 'Daily gulika-kālam avoidance windows',
      window_or_date: `${dates[0]}..${dates[dates.length - 1]}`,
      detail:
        `${gulikaKalamAhead.length} daily window(s) available over this span — see ` +
        `gulika_kalam_ahead for the per-day timing.`,
      fact_ids: [],
    })
  }

  for (const entry of recurrenceLadder) {
    const within = entry.future_points.filter((pt) => pt.date <= digestToDate)
    const next = within[0]
    if (!next) continue
    items.push({
      kind: 'recurrence_ladder_point',
      label:
        `Recurrence ladder: ${entry.signature_class ?? 'unclassified'} signal` +
        (entry.domains_affected.length > 0 ? ` (${entry.domains_affected.join('/')})` : ''),
      window_or_date: next.date,
      detail:
        `${within.length} of ${entry.future_points.length} forward recurrence point(s) fall within this window` +
        (next.point_kind ? `; next is a ${next.point_kind}` : '') +
        (next.strength != null ? ` (strength ${next.strength})` : ''),
      fact_ids: [entry.signal_id],
    })
  }

  if (muddaDashaVarsha) {
    const currentMudda = muddaDashaVarsha.mudda_chain[0]
    // Root Cause C, prose half (ṢAḌ-DARŚANA W1 verify-reopen): this line used to emit
    // "Muntha in unknown" / "Year-lord unknown" whenever the underlying value was null —
    // a bare "unknown" reads to a caller as an astrological finding ("the Muntha's placement
    // is unknown") rather than as a serving gap, which is the prose-leak class B.10/§N.8
    // forbid. Absent clauses are now OMITTED entirely (the `coverage` entry is where a gap is
    // disclosed, in machine-readable form — never smuggled into narration), and when nothing
    // at all resolved the item says so in those words.
    const clauses: string[] = []
    if (muddaDashaVarsha.year_lord) clauses.push(`Year-lord ${muddaDashaVarsha.year_lord}`)
    if (muddaDashaVarsha.muntha_sign) {
      clauses.push(
        `Muntha in ${muddaDashaVarsha.muntha_sign}` +
          (muddaDashaVarsha.muntha_house != null ? ` (${muddaDashaVarsha.muntha_house}H from natal lagna)` : '') +
          (muddaDashaVarsha.muntha_lord ? `, lord ${muddaDashaVarsha.muntha_lord}` : ''),
      )
    }
    if (currentMudda) clauses.push(`active Mudda ${currentMudda.level_name} lord ${currentMudda.lord_graha}`)
    items.push({
      kind: 'mudda_dasha_varsha',
      label: 'Current varsha (Tājika annual) + Mudda daśā',
      window_or_date: `${muddaDashaVarsha.varsha_start_iso ?? '?'}..${muddaDashaVarsha.varsha_end_iso ?? '?'}`,
      detail:
        clauses.length > 0
          ? clauses.join('; ')
          : 'Varsha window resolved, but neither year-lord nor Muntha nor an active Mudda ' +
            'period was available this call — see coverage for which specific field is missing.',
      fact_ids: [],
    })
  }

  // ── W4 D4: ritual-opportunity rows, SELECTED (never computed here) ──────────────────
  for (const o of ritualOpportunities ?? []) {
    if (!overlapsDigestWindow(o.window.start_utc, o.window.end_utc, asOfDate, digestToDate)) continue
    const present = o.score_vector.factors_present
    items.push({
      kind: 'ritual_opportunity',
      label: `${o.rite.rite_class ?? 'rite'}${o.rite.planet ? ` (${o.rite.planet})` : ''}`,
      window_or_date: `${o.window.start_utc.slice(0, 10)} .. ${o.window.end_utc.slice(0, 10)}`,
      detail:
        `composite ${o.score_vector.composite ?? 'not scored'} over ${present.length} present ` +
        `factor(s) [${present.join(', ') || 'none'}]; ${o.score_vector.factors_absent.length} absent ` +
        `and dropped from the product, never imputed. ` +
        (o.rite.citation ?? 'no resolvable citation — this row is NOT offered as a prescription'),
      fact_ids: [],
    })
  }

  items.sort((a, b) => a.window_or_date.localeCompare(b.window_or_date))

  return {
    as_of_date: asOfDate,
    digest_to_date: digestToDate,
    horizon_days: 90,
    items,
    item_count: items.length,
    ritual_opportunities_note: ritualOpportunitiesNote(ritualOpportunities, asOfDate, digestToDate),
  }
}

// ── The reading (template-over-computed-data — B.10; no generative call) ───────────

function buildAheadReading(params: {
  horizonLabel: string
  windowFamilies: WindowFamily[]
  projectionFamilies: ProjectionFamily[]
  windowsOk: boolean
  projectionsOk: boolean
  /** F-110: the PACT promise gate for this response. Never null — an unchecked gate is an
   *  explicit `not_applicable`/`unreachable` state, not an absent field. */
  promiseGate: PromiseGate
}): ArgumentReading {
  const { horizonLabel, windowFamilies, projectionFamilies, windowsOk, projectionsOk, promiseGate } = params
  const topProjection = projectionFamilies[0]
  const gateContradicts = promiseGate.contradicts_served_projections
  const gatedDomain = promiseGate.domain

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

  // F-110: the thesis is THIS FILE's own sentence (§N.7). It may not narrate "leading:
  // relationship (high probability …)" while the same server holds a horizon-invariant
  // classical denial for that domain. The L3 tier itself is untouched and still reads
  // `tier_1_high` on the projection row two fields away — this states the dispute, it does
  // not resolve it, and it never re-grades.
  if (gateContradicts) {
    thesisParts.push(
      `CONTRADICTED AT PROMISE: this server's own classical promise chain (pact_query) returns ` +
        `${promiseGate.pact_status} for '${gatedDomain}' — the rāśi/varga stage denies what the ` +
        'projection(s) above date. The probability_tier is served verbatim from L3 and measures ' +
        'temporal signal convergence, NOT classical promise; do not read it as a vetted probability ' +
        'of the event. See promise_gate and drill via kala_explain_get.',
    )
  }

  const evidence: ArgumentEvidence[] = projectionFamilies.slice(0, 4).map((p) => {
    // F-110 / §N.7 item 6 (an honest null beats an invented judgment): for a projection in
    // a domain this server classically denies, this file will not author the word 'strong'.
    // `undefined` is NOT an invented lower grade — it is this file's OWN established value
    // for ungraded evidence (the `probability_tier == null` branch of this very expression).
    const contradicted = gateContradicts && p.domain === gatedDomain
    return {
      claim:
        `${p.domain ?? 'unlabeled domain'} projection, window ${p.window_start ?? '?'}..${p.window_end ?? '?'}` +
        (p.probability_tier ? ` (${TIER_LABEL[p.probability_tier]})` : '') +
        (contradicted ? ' — CONTRADICTED by the PACT promise chain; see promise_gate' : ''),
      fact_ids: [...(p.member_signal_ids ?? []), ...(p.member_ids ?? [])],
      strength: contradicted ? undefined : p.probability_tier ? TIER_TO_STRENGTH[p.probability_tier] : undefined,
    }
  })

  const tierCounts = projectionFamilies.reduce(
    (acc, p) => {
      if (p.probability_tier === 'tier_1_high') acc.tier1++
      else if (p.probability_tier === 'tier_2_moderate') acc.tier2++
      else if (p.probability_tier === 'tier_3_speculative') acc.tier3++
      return acc
    },
    { tier1: 0, tier2: 0, tier3: 0 },
  )

  // F-110: the tier COUNT sentence is this file's own, and "1 high" read alone is the
  // launder in its most compact form. The count stays true to L3; the disputed share is
  // stated alongside it rather than folded into it (§N.6 — never flatten differing
  // densities into one undifferentiated claim).
  const contradictedCount = gateContradicts
    ? projectionFamilies.filter((p) => p.domain === gatedDomain).length
    : 0

  const verdict: ArgumentVerdict = {
    statement:
      projectionFamilies.length > 0
        ? `${tierCounts.tier1} high, ${tierCounts.tier2} moderate, ${tierCounts.tier3} speculative forward window(s) identified over the next ${horizonLabel}.` +
          (contradictedCount > 0
            ? ` ${contradictedCount} of these fall in '${gatedDomain}', which this server's own PACT promise chain ` +
              `returns ${promiseGate.pact_status} for — the tier and the promise chain disagree and are BOTH served; ` +
              'this verdict reconciles neither.'
            : promiseGate.state !== 'checked'
              ? ' NOT CHECKED against the classical promise chain this call (see promise_gate) — unchecked is not the same as clear.'
              : '')
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

  // F-110: `dissent: []` was hardcoded — an assertion that NO system on this server
  // disagrees, emitted while pact_query held a denial on 63 cited L1 facts. The dissent
  // array is this file's own composition and is now populated from the real gate.
  const dissent: ArgumentDissent[] = gateContradicts
    ? [{
        source: 'PACT promise chain (pact_query, PROMISE→CONFIRMATION→ACTIVATION→TRIGGER)',
        claim:
          `${promiseGate.join?.promise_verdict ?? 'PACT chain denied.'} The classical chain denies for ` +
          `'${gatedDomain}' what the projection(s) above date and grade. This is a horizon-invariant denial ` +
          '(natal/varga facts, not date-dependent), so it bears on every forward window served here for that domain.',
        fact_ids: promiseGate.join?.shared_fact_ids ?? [],
      }]
    : []

  return {
    thesis: thesisParts.join(' ') || `No forward temporal state could be assembled for the next ${horizonLabel}.`,
    evidence,
    dissent,
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
  field_snapshot_state: FieldSnapshotState
  field_snapshot_reason: string | null
  tri_plane: TriPlanePointers
  coverage: KalaCoverageEntry[]
  freshness: ReturnType<typeof buildKalaFreshness>
  calibration_maturity: CalibrationMaturityResolution
  windows: WindowFamily[]
  projections: ProjectionFamily[]
  gulika_kalam_ahead: GulikaKalamAheadWindow[]
  gulika_kalam_ahead_horizon_days: number
  /** F-110 (CL-15): the classical PACT promise chain's verdict for this response's domain,
   *  served ADJACENT to the L3-verbatim projections rather than folded into them. Never
   *  absent: an unchecked gate is an explicit `not_applicable`/`unreachable` state so a
   *  caller can distinguish "checked and clear" from "never checked" (they were
   *  byte-identical before this field existed). */
  promise_gate: PromiseGate
  // Item 28 (wave W1): currently-running Vimśottarī MD/AD lord's transit condition
  // projected to this call's horizon boundary (date_to) — the forward half of now.ts's
  // dasha_lord_transit_condition (same lord identity, later snapshot date).
  dasha_lord_transit_condition_forward: DashaLordForwardTransitCondition[]
  // Item 30 (wave W1): current varsha (Tājika annual) context joined with the active Mudda
  // daśā chain for the same date.
  mudda_dasha_varsha: MuddaDashaVarshaJoin | null
  // Item 2 (wave W1): recurrence-ladder serving. Read verbatim from `kala_activation`'s own
  // `activation_predicted_dates_jsonb` column (via the SAME query_temporal_activation call
  // above's raw `activations` array) — NOT from the genuinely-NULL `bodha_msr_signals` L2
  // hook of the same name (see the file-header doc-comment for the production-state check).
  recurrence_ladder: RecurrenceLadderEntry[]
  // E6-lite (wave W1): the 90-day forward digest preset — a curated selection over the
  // fields above, bounded to today..+90d. Ritual-free by design (Mode 1 lands at W4).
  digest_90d: AheadDigest90d
  // Item 31 (wave W3): period-echo mining, hypothesis-framed — same-lord Mahādaśā/Antardaśā
  // recurrence in the native's own lived timeline, LEL-corroborated where the log has data,
  // never served as a prediction. One entry per active chain level (Mahadasha, Antardasha).
  period_echo: PeriodEchoEntry[]
  drill_pointers: DrillPointerLike[]
  // G14b AHEAD auto-file (MASTER_PLAN_v1_0.md G14b): summary of prospective entries filed
  // into brahma_prospective_ledger for this serving call. Best-effort — null when the
  // auto-file hook was not invoked (e.g. the result object was constructed without it),
  // an AheadAutofileResult when it ran (even if filed_count = 0).
  predictions_logged: AheadAutofileResult | null
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
    /** Earned-signal counterpart to the boolean above (CLAUDE.md §N.8): how many served rows
     *  actually carry a transit sign. `*_reachable: true` with 0 here would be a contradiction. */
    dasha_lord_transit_condition_forward_rows_with_transit_data: number
    mudda_dasha_varsha_reachable: boolean
    /** Item 30, Root Cause C: whether the Muntha sub-fields inside the mudda/varsha join
     *  actually resolved. Reported separately from `mudda_dasha_varsha_reachable` because the
     *  mudda chain and the Muntha genuinely failed independently of each other. */
    muntha_varsha_position_reachable: boolean
    recurrence_ladder_reachable: boolean
    // Item 31: whether ≥1 period-echo entry actually served a hypothesis (not merely that the
    // active-chain dispatch returned 200) — §N.8 earned-signal discipline.
    period_echo_reachable: boolean
    promise_gate_reachable: boolean
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
  const ayanamshaId = resolveChartFactsAyanamsha(args.ayanamsha_id)
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
  // Item 2 (recurrence ladder): the SAME query_temporal_activation response's raw,
  // per-predicate `activations` array — already fetched above, no new registry call.
  const rawActivations = (windowsResp.content?.['activations'] as RawActivationRow[] | undefined) ?? []

  const projectionsOk = projectionsResp.ok
  const projectionFamilies =
    (projectionsResp.content?.['projection_families'] as ProjectionFamily[] | undefined) ?? []

  // F-110 (CL-15): consult the classical promise chain for the domain this response is
  // about. Kicked off HERE — the moment `projectionFamilies` (its domain fallback input)
  // is available — and awaited just before the reading is composed, so it overlaps every
  // subsequent join instead of adding a serial leg to the call.
  const promiseGatePromise = computePromiseGate(
    chartId, ayanamshaId, dateFrom, args.domain, projectionFamilies, principal, callRegistryCapability,
  )

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

  // Item 30 — joins the current varsha (Tājika annual) context with the active Mudda
  // daśā chain, both as of today (dateFrom) — the "current developing period" reading.
  const muddaDashaVarsha = await computeMuddaDashaVarsha(chartId, ayanamshaId, dateFrom, principal)

  // Item 2 — recurrence-ladder serving, collapsed per signal, forward points only.
  const { entries: recurrenceLadder, anyLadderPresent } = computeRecurrenceLadder(rawActivations, dateFrom, maxItems)

  // Item 31 — period-echo mining (hypothesis-framed), over the SAME active chain item 28
  // already fetched (dashaLordForward.chain — no second query_active_dashas dispatch).
  // Genuinely field-independent (see the item-31 doc-comment above `dualOutput` for the full
  // pre-build investigation this build decision rests on).
  const [birthYearFloor, lelForEcho] = await Promise.all([
    fetchBirthYearFloor(chartId, principal),
    fetchAllChartLelEventsForEcho(chartId, principal),
  ])
  const periodEcho: PeriodEchoEntry[] = await Promise.all(
    dashaLordForward.chain
      .filter((e) => (e.level_n === 1 || e.level_n === 2) && e.lord_graha && e.start_date != null && e.end_date != null)
      .map((e) =>
        computePeriodEchoForLevel(
          chartId, ayanamshaId, e.level_n, e.lord_graha, e.start_date as string, e.end_date as string,
          birthYearFloor, lelForEcho.events, lelForEcho.fetchError, principal,
        ),
      ),
  )

  // E6-lite — the fixed 90-day forward digest, a pure selection over the fields above.
  const digestToDate = new Date(today.getTime() + 90 * 86400000).toISOString().slice(0, 10)

  // ── W4 D4 (Elevation §6): Mode-1 ritual-opportunity rows join the digest. ────────────
  // COMPUTED BY THE RITUAL PATH, JOINED HERE — the digest's own discipline is "SELECTING,
  // never computing", so this calls Lane R's Mode-1 scorer (which itself terminates at the
  // FROZEN lattice engine) and then SELECTS from its output. `null` on any failure means
  // "not searched", which the note distinguishes from "searched and empty" — two different
  // claims that a single empty array would have collapsed into one.
  let ritualOpportunities: AheadRitualOpportunityInput[] | null = null
  try {
    const ritualSubstrate = await fetchLatticeSubstrate(
      {
        start_utc: new Date(`${dateFrom}T00:00:00Z`).toISOString(),
        end_utc: new Date(`${digestToDate}T23:59:59Z`).toISOString(),
      },
      principal,
    )
    if (ritualSubstrate.lattice_available) {
      const windows = ritualSubstrate.lattice_rows
        .filter((r) => r.factor_family === 'combination_yoga')
        .filter((r) => String((r.detail as { strength?: unknown } | null)?.strength ?? '') === 'auspicious')
        .map((r) => ({
          start_utc: r.start_utc,
          end_utc: r.end_utc,
          authority_basis: [`${r.factor_family}/${r.factor_key}@${r.start_utc}`],
          binding_families: [r.factor_family],
        }))
      const scan = await scoreMode1Opportunities(
        {
          chartId,
          activityClass: 'upaya_ritual',
          windows,
          substrate: ritualSubstrate,
          subjectLabel: 'ritual opportunity (AHEAD 90-day digest, Mode 1)',
          limit: 5,
        },
        principal,
      )
      ritualOpportunities = scan.opportunities.map((o) => ({
        window: o.window,
        rite: { rite_class: o.rite.rite_class, planet: o.rite.planet, citation: o.rite.citation },
        score_vector: {
          composite: o.score_vector.composite,
          factors_present: o.score_vector.factors_present,
          factors_absent: o.score_vector.factors_absent,
        },
      }))
    }
  } catch {
    ritualOpportunities = null
  }

  const digest90d = buildAheadDigest90d({
    asOfDate: dateFrom,
    digestToDate,
    windowFamilies,
    projectionFamilies,
    gulikaKalamAhead,
    recurrenceLadder,
    muddaDashaVarsha: muddaDashaVarsha.result,
    ritualOpportunities,
  })

  // F-110: awaited here — the reading's own sentences depend on the gate verdict.
  const promiseGate = await promiseGatePromise

  const reading = buildAheadReading({ horizonLabel, windowFamilies, projectionFamilies, windowsOk, projectionsOk, promiseGate })
  const composed = composeArgument(reading)

  const triPlane: TriPlanePointers = {
    // F-123 (CL-11 dead pointer): kala_explain_get hard-errors without domain/bhava. args.domain
    // is the same optional filter kala_ahead_get itself accepts — when the caller scoped this
    // AHEAD call to a domain, the pointer carries it forward; otherwise it degrades honestly
    // (explainPointerTo's null branch) rather than fabricating one.
    interpretation_ref: explainPointerTo(
      'Why these forward windows fire — drivers and classical grounds behind each projection',
      args.domain ? { domain: args.domain } : null,
    ),
    // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): was a bare `null`. AHEAD genuinely IS
    // the prediction plane, so there is no sibling surface to point at — but "this object is
    // itself that plane" and "no pointer was wired here" are indistinguishable to a caller
    // reading a bare null, and the campaign's OWN CI gate
    // (platform/scripts/census/shad_darshana_gates/tri_plane_no_dead_end_gate.ts) already grades
    // a null slot `WARN — "only legal when this object IS that plane already; not
    // independently verifiable at v0"`. An honest, self-describing `no_lever` states the same
    // fact in the machine-readable shape the contract provides for it (kala_envelope.ts's
    // `KalaNoLever`, as kala_ritual_get already uses), turning that WARN into a PASS.
    prediction_ref: noLeverPointer(
      'kala_ahead_get IS the prediction plane — this response is itself the predictive ' +
        'continuation, so there is no further forward surface to traverse to. Not a missing ' +
        'pointer: a terminal by construction.',
    ),
    intervention_ref: pointerTo('kala_elect_get', 'When exactly to act inside these forward windows'),
  }

  const coverage: KalaCoverageEntry[] = [
    windowsOk
      ? computedCoverage('forward_temporal_windows')
      : honestEmptyCoverage('forward_temporal_windows', 'L3 Kāla registry unreachable this call.'),
    projectionsOk
      ? computedCoverage('probabilistic_projections')
      : honestEmptyCoverage('probabilistic_projections', 'L3 Kāla registry unreachable this call.'),
    // F-110 (CL-15) — this row used to be an UNCONDITIONAL `not_in_corpus` string: a
    // status with no code path that could ever produce a different value, i.e. exactly the
    // §N.8 Earned-Signal defect ("what would have to run, and fail, for this signal to
    // correctly read false?" — nothing could). It now varies with a real detector: the
    // PACT chain is actually consulted (`computePromiseGate`) and this entry reports what
    // that consultation found. `not_in_corpus` survives ONLY for the genuinely-unbuilt
    // case — no domain to consult at all.
    promiseGate.state === 'checked'
      ? computedCoverage('promise_gated_forecasting')
      : promiseGate.state === 'unreachable'
        ? honestEmptyCoverage('promise_gated_forecasting', promiseGate.reason)
        : notInCorpusCoverage('promise_gated_forecasting', promiseGate.reason),
    // Earned-signal detector (CLAUDE.md §N.8), item 28 forward half: `computed` requires at
    // least one served row to actually CARRY a transit sign — not merely that the capability
    // dispatch returned HTTP 200 with an empty body. See now.ts for the full root-cause note.
    natalLagna.ok && dashaLordForward.chainReachable && dashaLordForward.rowsWithTransitData > 0
      ? computedCoverage('dasha_lord_forward_transit_condition')
      : honestEmptyCoverage(
          'dasha_lord_forward_transit_condition',
          !natalLagna.ok
            ? 'L1 natal reference-sign lookup (get_dignity/graha_sign_attributes LAGNA) could not ' +
              'be dispatched this call, so house_from_lagna is not derivable for the active lord(s).'
            : !dashaLordForward.chainReachable
              ? 'L3 active-dasha registry (query_active_dashas) could not be dispatched this call.'
              : dashaLordForward.rows.length === 0
              ? 'No active Vimśottarī MD/AD chain resolved for this chart as of today — honest empty, not fabricated.'
              : dashaLordForward.transitFailure
                ? transitFailureReason(dashaLordForward.transitFailure)
                : `L0 ephemeris answered but returned no transit row for the active lord(s) on ${dateTo} — ` +
                  'genuine empty for that horizon date, not a masked failure.',
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
    muddaDashaVarsha.result
      ? computedCoverage('mudda_dasha_varsha')
      : honestEmptyCoverage(
          'mudda_dasha_varsha',
          !muddaDashaVarsha.tajikReachable
            ? 'L1 Tajaka registry (get_tajik) unreachable this call.'
            : !muddaDashaVarsha.muddaReachable
              ? 'L3 active-dasha registry (query_active_dashas, system=mudda) unreachable this call.'
              : 'No current varsha row or active Mudda daśā chain resolved for this chart/date — honest empty, not fabricated.',
        ),
    // Root Cause C, disclosure half (ṢAḌ-DARŚANA W1 verify-reopen): the Muntha now gets its OWN
    // coverage entry, SEPARATE from `mudda_dasha_varsha`. That separation is the actual fix for
    // the reported gap: the mudda-chain deliverable was genuinely `computed` while the Muntha
    // sub-fields inside it were silently null, so one shared entry could not tell the truth
    // about both — a caller reading `mudda_dasha_varsha: computed` had no way to learn the
    // Muntha was missing (CLAUDE.md §N.6: never flatten differing-density layers into one
    // undifferentiated claim).
    muddaDashaVarsha.result?.muntha_sign
      ? computedCoverage('muntha_varsha_position')
      : honestEmptyCoverage(
          'muntha_varsha_position',
          !muddaDashaVarsha.result
            ? 'No varsha row resolved for this chart/date, so the Muntha has no row to be read from.'
            : 'The varsha row resolved but carried no readable `muntha_position_jsonb.sign` — ' +
              'the Muntha is stored as a JSONB position object on l1_tajik_varsha_year_lords ' +
              '(sign / degree / lord / house_from_natal_lagna / house_from_varsha_lagna), not as ' +
              'flat columns; an empty or malformed object is reported here rather than served as ' +
              'a null inside a "computed" claim.',
        ),
    windowsOk
      ? recurrenceLadder.length > 0
        ? computedCoverage('recurrence_ladder')
        : honestEmptyCoverage(
            'recurrence_ladder',
            anyLadderPresent
              ? 'This chart\'s activation rows carry a predicted-dates ladder (kala_activation.activation_predicted_dates_jsonb), ' +
                'but every point in it already lies in the past relative to today — no forward recurrence to show. ' +
                '(Note: the L2 bodha_msr_signals.activation_predicted_dates_jsonb hook of the same name remains genuinely ' +
                'NULL in production and is never used as a source.)'
              : 'No activation row for this chart/ayanamsha carries a populated activation_predicted_dates_jsonb ladder yet ' +
                '(neither the L3 kala_activation column this join reads, nor the L2 bodha_msr_signals hook of the same name, ' +
                'which is confirmed genuinely NULL in production).',
          )
      : honestEmptyCoverage('recurrence_ladder', 'L3 Kāla registry (query_temporal_activation) unreachable this call.'),
    digest90d.item_count > 0
      ? computedCoverage('ahead_digest_90d')
      : honestEmptyCoverage(
          'ahead_digest_90d',
          'No item from any already-computed AHEAD surface (windows/projections/gulika-kālam/recurrence-ladder/mudda-varsha) ' +
            'falls inside the next 90 days for this chart.',
        ),
    // Item 31: `computed` requires ≥1 entry to actually serve a hypothesis (status ===
    // 'hypothesis_served') — not merely that the active-chain dispatch returned rows. Every
    // level honestly reporting insufficient_data (the structurally-expected Mahādaśā case) is
    // itself a valid, non-fabricated outcome, so it is disclosed via `honestEmptyCoverage`
    // rather than silently upgraded to `computed`.
    periodEcho.length > 0
      ? periodEcho.some((e) => e.status === 'hypothesis_served')
        ? computedCoverage('period_echo_mining')
        : honestEmptyCoverage(
            'period_echo_mining',
            periodEcho.map((e) => `${e.level_name}: ${e.insufficient_data_reason}`).join(' | '),
          )
      : honestEmptyCoverage(
          'period_echo_mining',
          dashaLordForward.chainReachable
            ? 'No active Vimśottarī MD/AD chain resolved for this chart as of today — no lord to mine an echo for.'
            : 'L3 active-dasha registry (query_active_dashas) unreachable this call.',
        ),
  ]

  const drillPointers: DrillPointerLike[] = [triPlane.interpretation_ref, triPlane.intervention_ref].filter(
    (p): p is DrillPointerLike => p != null && !isNoLever(p),
  )

  // W2 (E5): the real field snapshot read — served id, or an honest marker; never a stub.
  const fieldSnapshot = await resolveFieldSnapshot(chartId, principal)

  const envelope = makeKalaEnvelope({
    reading,
    questionFrame: args.question_frame ?? null,
    fieldSnapshot,
    triPlane,
    coverage,
    freshness: buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: fieldSnapshot.field_content_hash }),
    calibrationMaturity: await fetchCalibrationMaturity(chartId, principal),
  })

  // ── G14b AHEAD auto-file (MASTER_PLAN_v1_0.md G14b) ────────────────────────────────
  //
  // Every served prediction becomes a dated claim against the native's future
  // (brahma_prospective_ledger). This is a BEST-EFFORT side effect: the filing result
  // is captured and surfaced in the response, but a filing failure MUST NOT fail this
  // serving call. `autofileAheadWindows` never throws (see its own module doc).
  //
  // Only `windowFamilies` are auto-filed here — see `ahead_autofile.ts` module doc for
  // why projections are intentionally excluded (they lack an event_class).
  let predictionsLogged: AheadAutofileResult | null = null
  try {
    predictionsLogged = await autofileAheadWindows(chartId, windowFamilies, principal)
  } catch {
    // Should never happen (autofileAheadWindows guarantees no throw), but defence in depth.
    predictionsLogged = null
  }

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
    promise_gate: promiseGate,
    dasha_lord_transit_condition_forward: dashaLordForward.rows,
    mudda_dasha_varsha: muddaDashaVarsha.result,
    recurrence_ladder: recurrenceLadder,
    digest_90d: digest90d,
    period_echo: periodEcho,
    drill_pointers: drillPointers,
    predictions_logged: predictionsLogged,
    provenance_envelope: {
      source: 'kala_ahead_get',
      assets: [
        'kala_activation (ka_kalasutra, forward-dated; also the source of activation_predicted_dates_jsonb — item 2 recurrence ladder)',
        'kala_bhavishya (ka_bhavishya_lekha)',
        'call_panchanga_service (panchang.py, engine-direct, mode=range)',
        'get_dignity (graha_sign_attributes)', 'query_planet_transit (L0 ephemeris)',
        'query_active_dashas (L3, EL-33)', 'bg_dignity_reference (L0)',
        'get_tajik (L1, l1_tajik_varsha_year_lords)',
        'get_dashas (L1, chart_dashas, lord_graha+level facets — item 31 period-echo)',
        'query_life_arc (L3, kala_jivana_parva — item 31 birth-year floor)',
        'lel_query (L5, life_events — item 31 LEL corroboration, native-only)',
        'pact_query (L-PACT, the SAME chained-investigation capability kala_explain_get consumes — F-110 promise gate)',
      ],
      chart_id: chartId,
      horizon_years: horizonYears,
      domain: args.domain ?? null,
      computed_at: new Date().toISOString(),
      source_citation: SOURCE_CITATION,
      gulika_kalam_reachable: gulikaOk,
      windows_reachable: windowsOk,
      projections_reachable: projectionsOk,
      // §N.8: asserts what it NAMES — that the join produced transit data — not merely that a
      // dispatch returned 200 with an empty body.
      dasha_lord_transit_condition_forward_reachable:
        natalLagna.ok && dashaLordForward.chainReachable && dashaLordForward.rowsWithTransitData > 0,
      dasha_lord_transit_condition_forward_rows_with_transit_data: dashaLordForward.rowsWithTransitData,
      mudda_dasha_varsha_reachable: muddaDashaVarsha.tajikReachable && muddaDashaVarsha.muddaReachable,
      muntha_varsha_position_reachable: muddaDashaVarsha.result?.muntha_sign != null,
      recurrence_ladder_reachable: windowsOk,
      period_echo_reachable: periodEcho.some((e) => e.status === 'hypothesis_served'),
      // §N.8: asserts what it NAMES — that a PACT chain was actually evaluated and
      // interpreted — not merely that a dispatch returned 200.
      promise_gate_reachable: promiseGate.state === 'checked',
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
projected to this call's horizon boundary; see kala_now_get for the current-date half) and \
mudda_dasha_varsha (item 30 — the current varsha/Tājika-annual context — varsha_year, \
year_lord, Muntha — joined with the active Mudda daśā chain for the same date; both read \
verbatim from already-computed substrate, never re-derived). Honestly discloses (via \
\`coverage\`) which richer AHEAD concepts (Law-3 promise-gated forecasting, the sky-event \
calendar, Tithi-Praveṣa) are not yet joined into this view.

W1 joins (objective, raw data — no favorable/unfavorable grading): gulika_kalam_ahead — the \
daily gulika-kālam window for each of the next ${GULIKA_AHEAD_MAX_DAYS} days (bounded by the \
underlying panchāṅga range service's own 31-day cap, independent of horizon_years).

recurrence_ladder (item 2): per-signal recurrence ladders — future {date, point_kind, \
strength, trigger, graha} points read verbatim from kala_activation's own \
activation_predicted_dates_jsonb column (the SAME already-fetched query_temporal_activation \
response; never re-derived). NOTE: the differently-scoped bodha_msr_signals L2 hook of the \
identical column name is confirmed genuinely NULL in production and is never the source here.

digest_90d (E6-lite): a curated, fixed 90-day-forward digest — a selection over windows / \
projections / gulika_kalam_ahead / recurrence_ladder / mudda_dasha_varsha bounded to \
today..+90d, never new computation. Ritual-opportunity rows are intentionally absent \
(kala_ritual_get Mode 1) — see the digest's own ritual_opportunities_note, which names the exact horizon searched when no row is present.

period_echo (item 31, hypothesis-framed): for the currently-running Mahādaśā and Antardaśā, \
finds every COMPLETED prior occurrence of the SAME lord at the SAME level in the native's own \
lived timeline (birth-year floored — pre-birth dasha rows are never cited) and joins each to \
the native's LEL life-event log by date-range overlap. Served ONLY as an explicit, falsifiable \
hypothesis (never a prediction or verdict) — "the current X period may echo X's prior period \
at <dates> because <N> similar comparisons were found, M of which carry logged life events." \
Honestly insufficient_data when no prior same-lord occurrence exists (the structurally-expected \
outcome at Mahādaśā level — Vimśottarī's 120-year cycle gives each lord one Mahādaśā per \
cycle). LEL is native-only: on charts with no logged life events, candidates are still served \
(structural same-lord recurrence) with lel_event_count: 0 on every row, never fabricated.

Output includes: reading (structured argument) + reading_prose (composed text) + windows + \
projections + gulika_kalam_ahead + dasha_lord_transit_condition_forward + mudda_dasha_varsha \
+ recurrence_ladder + digest_90d + period_echo + tri_plane (→ kala_explain_get for why, → \
kala_elect_get for when to act) + coverage + drill_pointers.

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
