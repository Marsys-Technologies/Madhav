/**
 * retrieval/register_gochara_windows.ts — D-5 Lane G-4 serving surface.
 *
 * Three views over the ONE signed field `kala_gochara_windows` (G-4's standing
 * table, migration 460 — populated by the `ka_gochara_sweep` writer from G-3's
 * lambda_e(t|chart) engine):
 *
 *   gochara_activation_get         — "is this event_class configuration ACTIVE
 *                                     right now (or on a given date)?"
 *   gochara_forecast_get           — "what windows lie ahead in this date range?"
 *   gochara_election_avoidance_get — adverse (is_adverse=true) windows in a date
 *                                     range, served with the full DR-16 five-
 *                                     property payload (BRIEF_D5 §4, hard
 *                                     acceptance item): honest clarity,
 *                                     probabilistic framing, a falsifier,
 *                                     a paired BPHS-cited mitigation (never
 *                                     bare), and confidence-honest disclosure.
 *
 * SCOPE NOTE (must_not_touch discipline): this file is NEW — G-4's declared
 * `may_touch` is `platform-mcp/src/tools/retrieval/register_*gochara*.ts` (new
 * files only). Wiring these tools into `platform-mcp/src/server.ts`'s
 * registration list (`import ...; register...(server, principal)`, the same
 * one-line pattern every sibling tool in this directory uses — see
 * `kala_temporal.ts`/`phala_outlook.ts`) is OUTSIDE that declared scope
 * (server.ts is an existing shared file, not a new file under this glob) —
 * left as an explicit, documented deferral for the Binder/conductor to wire at
 * merge time, exactly one import + one registration call, no logic to review.
 * Every exported `register*Tool` function below is otherwise complete and
 * independently live-tested against the real `kala_gochara_windows` table
 * (see this lane's close report for the direct-call verification transcript).
 *
 * DB ACCESS NOTE (SARVA-SIDDHI W-1 T-1, 2026-07-24 — root-cause fix, replaces
 * the original self-contained-pg.Pool approach): the D-5 G-4 lane originally
 * opened a self-contained `pg.Pool` here reading `process.env['DATABASE_URL']`,
 * to stay inside a `may_touch` glob that named only new files. That was the
 * defect: the deployed `amjis-mcp` Cloud Run service has NO direct DB path by
 * design — `deploy.yml`'s `deploy-mcp` job sets only PLATFORM_URL /
 * PYTHON_SIDECAR_URL / MCP_BASE_URL, never DATABASE_URL and no Cloud SQL
 * attachment — so `getPool()` threw "DATABASE_URL not set" and all three tools
 * served `backing_data_reachable:false` in production (register CR-131). Every
 * OTHER MCP tool honors the invariant "the MCP server does not hold a direct DB
 * connection" and proxies reads through the platform, which does hold the
 * connection. This file now does the same: it routes its (already-parameterized,
 * server-authored, SELECT-only) SQL through `POST ${PLATFORM_URL}/api/mcp/db/query`
 * via the exact `platformQuery(sql, params, principal)` pattern
 * `register_p1_synthesis.ts` uses — two-layer auth (X-MCP-Internal-Token +
 * X-MCP-User/X-MCP-Key-Id) and table-level whitelisting on the platform side.
 * `kala_gochara_windows` and `brahma_remedy_corpus` were added to that route's
 * ALLOWED_TABLES read-only whitelist. No `pg` dependency, no DATABASE_URL, no
 * infra change to amjis-mcp — the fix conforms the tool to the platform's
 * established DB-access contract rather than bolting DB creds onto a publicly-
 * invokable serving process.
 *
 * §N.6 density_contract (CLAUDE.md, BRIEF_D5 §5 — required from day one, not
 * deferred): each tool's `DENSITY_CONTRACT` const below matches the shape
 * `platform/src/lib/retrieval/registry/types.ts`'s `CapabilityDescriptor.
 * density_contract` declares (paginated / facets / empty_reason discipline).
 * It is surfaced on every response's `provenance_envelope.density_contract`
 * so a served payload is self-describing even before a future census/CI
 * harness (§N.6 Part 2) can read it off a registered `CapabilityDescriptor` —
 * registering these AS CapabilityDescriptors in the shared registry is the
 * same out-of-scope wiring step named above, deferred alongside it.
 *
 * ṢAḌ-DARŚANA item 9 (2026-08-02 — DP-4, the DATA root of the same veto):
 * the sweep grammar now DOES have health classes. `illness_acute`,
 * `chronic_onset` and `surgery` (the `brahma_event_ontology` health domain in
 * full) were added to the single shared sweep scope,
 * `services/gochara_grammar/event_class_scope.py::SWEEP_EVENT_CLASSES`, so
 * `gochara_resonance_map` gains health targets and `ka_gochara_sweep` gains a
 * health substep column. `computeGocharaCoverage` was hardened in the same
 * change: a class counts as covered only when it has BOTH resonance targets
 * AND at least one committed sweep substep for that chart — otherwise the
 * freshly-extended grammar would drop 'health' out of `domains_not_covered`
 * on charts whose health sweep has not run yet, which is the S4-05 shape
 * again one build cycle later. See `event_classes_targeted_not_swept` below
 * and `src/__tests__/s4_05_health_coverage.test.ts`.
 *
 * SATYA-ŚEṢA W2/W3 (2026-07-25 — S4-05 fix, UAT-DARPANA worst veto): at that
 * time this sweep had NO health event class (only career_advancement/marriage/
 * major_gain were populated for the canonical chart — the gap item 9 above
 * later closed at the data root). Before that change, a
 * health-filtered/health-adjacent query against these three tools got a bare
 * "clean" empty that read identically to a genuinely-swept, genuinely-clear
 * result — "I didn't look" served as "there is nothing" (the exact failure
 * mode SATYA_SHESHA_BRIEF_v1_0.md §0 names). Two additions close it:
 *   W2 — every response now carries `coverage` (mechanically derived every
 *        call from gochara_resonance_map ∩ brahma_event_ontology — see
 *        `computeGocharaCoverage` below — never hand-maintained), and a
 *        `domain` filter that, when it names a domain outside the covered
 *        set, short-circuits to a `not_covered` refusal (cross-pointing to
 *        `kala_windows_get`, the domain-capable instrument) INSTEAD of
 *        running a scan that can only look empty.
 *   W3 — `active_sentences` (the true size driver — up to 11.5KB/row observed
 *        live, dwarfing every other field) is capped at construction time
 *        (`capActiveSentences`, disclosed via `active_sentences_total_count`),
 *        and the full response (windows + coverage + provenance_envelope +
 *        drill_pointers) is now measured and trimmed as ONE object via
 *        `finalizeMcpBudget` — the previous `applyResponseBudget` call only
 *        ever measured `{windows}` in isolation, so a response could report
 *        "trimmed to budget" while the actually-served envelope (windows +
 *        trim_report + provenance_envelope stapled on afterward, unmeasured)
 *        was still far over it (114KB observed live for a 10-row "floored"
 *        forecast response against a nominal 40KB ceiling).
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../../types.js'
import { remoteAuthorize } from '../../lib/authz.js'
import { finalizeMcpBudget, type TrimmableSection } from '../../lib/response_budget.js'

// ── Platform DB proxy (see module DB ACCESS NOTE) ────────────────────────────
// The MCP server holds no direct DB connection; it proxies SELECT-only,
// server-authored SQL through the platform's whitelisted /api/mcp/db/query
// route, which owns the live PG connection. Same helper shape as
// register_p1_synthesis.ts's `platformQuery`.

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function platformQuery(
  sql: string,
  params: unknown[],
  principal: Principal
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[gochara_windows] platform DB query failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

// ── Shared row shape ──────────────────────────────────────────────────────────

export interface GocharaContinuityState {
  raw_start: string
  raw_end: string
  left_active: boolean
  right_active: boolean
}

export interface GocharaWindowRow {
  id: number
  chart_id: string
  event_class: string
  temporal_shape: 'point' | 'interval' | 'chain'
  window_start: string
  window_end: string
  peak_date: string
  milestone_id: string | null
  is_irreversibility_milestone: boolean
  signed_intensity: number
  raw_intensity: number
  valence: 'gain' | 'loss' | 'neutral' | 'mixed'
  is_adverse: boolean
  active_sentences: unknown[]
  contributing_systems: Array<{ system_id: string; active: boolean; weight: number; detail?: unknown }>
  suppression_state: Record<string, unknown>
  peak_basis: string
  calibration_state: string
  source: 'live' | 'fixture'
  computed_at: string
  continuity_state: GocharaContinuityState | null
  plateau_disclosure: {
    window_start_open: boolean
    window_end_open: boolean
    note: string
  } | null
  // W3: present once `capActiveSentences` has run; absent (undefined) means
  // the row's active_sentences array is already whole (never fabricated).
  active_sentences_total_count?: number
  // W5.1 (GOCHARA-UTKARSA): pass-through columns from kala_gochara_windows.
  // All three are nullable: v1 rows written before migration 556/559 carry NULL.
  /** Generation-tier discriminator. 'v1' for legacy sweep rows; 'g3_utkarsha'
   * for GOCHARA-UTKARSA W3.4 century-materialize rows. NULL on rows predating
   * migration 527's generation column. */
  generation?: string | null
  /** Era-slice key identifying the decade band this window belongs to.
   * Format: 'g3_{year_start}_{year_end}' for v3 rows (e.g. 'g3_1984_1994').
   * NULL for v1 rows (predates migration 556). */
  era_slice_key?: string | null
  /** Per-mechanism λ_v3 decomposition (W1.5). Structure:
   * {promise, permission, activity, quality_gates, lambda_v3,
   *  activity_terms: [{primitive, target_ref, orb_decay, target_weight, p_i}]}.
   * NULL on v1-parity rows (v1_parity_mode=True path never populates this). */
  term_breakdown?: Record<string, unknown> | null
  // PARIṢKĀRA MR-11(b) (migration 567): hierarchy tier + parent linkage.
  // Both nullable: NULL on every row written before migration 567 (the v1
  // sweep corpus and every pre-MR-11(b) W3.4/W5.4 flat-interval v3 row).
  /** Hierarchy tier this row was produced at -- 'era'|'month'|'day'
   * (services/gochara_v3/resolution_hierarchy.py RESOLUTION_TIERS, muhurta
   * tier not yet built). NULL for pre-migration-567 rows -- see
   * `deriveResolutionDisclosure` for the honest serve-time handling of that
   * NULL per PK-R-1 (a decade-era row must never be presented as a timing
   * claim, stored or implied). */
  resolution?: string | null
  /** DB-assigned bigint `id` (in this SAME table) of this row's widest
   * containing coarser-tier hierarchy window -- e.g. a month row's era
   * parent. NULL for era-tier rows (no coarser parent) and for every row
   * written before migration 567. */
  parent_window_id?: number | null
  // PARIṢKĀRA MR-47 (ADJUDICATOR ruling PK-R-10, migration 570): the
  // earned, explicit marker proving this row's temporal_shape was checked
  // against brahma_event_ontology at WRITE time. 'ontology_match' -- the
  // stored temporal_shape genuinely equals the ontology's declared shape.
  // 'point_class_context_envelope' -- the R8.12 flat-production branch for a
  // point-canonical class: this row is honestly an envelope
  // (temporal_shape='interval', resolution=NULL), never a genuine interval
  // production. NULL for every row written before migration 570 (an honest
  // gap, not backfilled/unclassifiable per that migration's own CASE logic).
  /** See `deriveResolutionDisclosure`'s point-class-envelope branch for the
   * honest, class-specific `timing_window_blocked_reason` this field earns. */
  shape_conformance?: 'ontology_match' | 'point_class_context_envelope' | null
}

// D-5 native disposition (2026-07-20, gate_run_2 finding 1): "the cap never
// fabricates a closed window from a truncated anchor." `window_start`/
// `window_end` on an interval-shaped row can be a structural cap
// (ka_gochara_sweep's duration_prior.max_days ceiling, migration 461's
// `continuity_state`), not a genuine signal-cessation boundary. A caller
// reading only window_start/window_end cannot tell "the signal really
// ended here" from "we simply haven't merged the next adjacent
// already-committed segment yet, or the plateau is structurally capped
// mid-signal" -- `left_active`/`right_active` are the writer's own honest
// record of which. This derives a disclosure object from the SAME
// `continuity_state` the writer persists, so the served bound is never
// presented as more definitive than the instrument actually knows.
export function derivePlateauDisclosure(row: GocharaWindowRow): GocharaWindowRow['plateau_disclosure'] {
  const cs = row.continuity_state
  if (row.temporal_shape !== 'interval' || !cs) return null
  const windowStartOpen = cs.left_active
  const windowEndOpen = cs.right_active
  if (!windowStartOpen && !windowEndOpen) return null
  const parts: string[] = []
  if (windowStartOpen) parts.push(`elevated since ≤${row.window_start} (true onset unresolved -- earlier adjacent history not yet merged)`)
  if (windowEndOpen) parts.push(`still elevated past ${row.window_end} (served end is a structural cap or not-yet-merged boundary, not a confirmed signal cessation)`)
  return {
    window_start_open: windowStartOpen,
    window_end_open: windowEndOpen,
    note: parts.join('; '),
  }
}

function withPlateauDisclosure(rows: GocharaWindowRow[]): GocharaWindowRow[] {
  return rows.map((row) => ({ ...row, plateau_disclosure: derivePlateauDisclosure(row) }))
}

// W3 (SATYA-ŚEṢA, root-cause size fix): `active_sentences` is the dominant
// byte cost of a GocharaWindowRow by a wide margin — a single row's array
// measured 11.5KB serialized (30 entries, each carrying a full classical_
// citation string) against ~1.4KB for every OTHER field on the row combined.
// The prior budget mechanism only ever trimmed the ROW COUNT (`windows`
// array length); with 10 rows hardFloor-protected at that minKeep, 10 ×
// 11.5KB alone (114KB) blew straight through a 40KB ceiling with no lever
// left to pull. This caps the array at construction time — before any
// row-count budget trim runs — to the N most classically-load-bearing
// entries (cited over uncited: `uncited_extension === false` sentences,
// which are the two-pass-verifiable claims per DR-16-family discipline
// elsewhere in this file, are kept first). The true count is disclosed via
// `active_sentences_total_count`, never silently hidden (B.10) — the
// dropped entries are NOT independently recoverable via a drill instrument
// today (this table has no per-sentence lookup surface), which this
// function's caller states honestly rather than promising a recovery path
// that does not exist.
const ACTIVE_SENTENCES_CAP = 4

function capActiveSentences(rows: GocharaWindowRow[]): GocharaWindowRow[] {
  return rows.map((row) => {
    const all = row.active_sentences ?? []
    if (all.length <= ACTIVE_SENTENCES_CAP) return row
    const cited = all.filter((s) => (s as Record<string, unknown>)['uncited_extension'] === false)
    const uncited = all.filter((s) => (s as Record<string, unknown>)['uncited_extension'] !== false)
    const kept = [...cited, ...uncited].slice(0, ACTIVE_SENTENCES_CAP)
    return { ...row, active_sentences: kept, active_sentences_total_count: all.length }
  })
}

// ══════════════════════════════════════════════════════════════════════════
// PARIṢKĀRA MR-11(b) / ADJUDICATOR ruling PK-R-8 — resolution-tier disclosure
// (migration 567) — R8.9/R8.10 EARNED is_timing_window
// ══════════════════════════════════════════════════════════════════════════
//
// GOVERNING RULING — PK-R-1 (native, binding): "a 'window' served for timing
// decisions must be at MINIMUM a month-resolution span carrying a day-
// precision peak, or a dated point row. Decade-era rows alone are CONTEXT,
// not windows — they may serve, but only labeled at their own resolution,
// never presented as the timing claim itself."
//
// PK-R-8 R8.9 SUPERSEDES this file's original duration-based "implied"
// inference for legacy rows: is_timing_window is now EARNED, never guessed
// from a span. A row earns is_timing_window=true iff:
//   temporal_shape === 'point'                              (PK-R-1's second
//                                                              floor — a dated
//                                                              point row —
//                                                              preserves the
//                                                              v1 sweep's own
//                                                              54 'gochara_
//                                                              lambda_e_v1'
//                                                              point rows)
//   OR (resolution IN {'month','day'}
//       AND peak_basis IN GENUINE_PEAK_BASES)                (a day-refined
//                                                              true argmax,
//                                                              R8.5 — the
//                                                              ONLY basis
//                                                              that earns
//                                                              genuine
//                                                              day-precision
//                                                              trust)
// GENUINE_PEAK_BASES mirrors services/gochara_v3/peak_basis_vocab.py's
// GENUINE_PEAK_BASES exactly ({'gochara_lambda_v3_argmax'} today) —
// extensible only by recorded evidence, never by adding a basis here without
// its Python counterpart.
//
// R8.10 DISCLOSED CONSEQUENCE: the pre-existing v1 sweep's 64 INTERVAL rows
// (peak_basis='gochara_lambda_e_v1', split 1c826d5a=33/482012f1=29/
// cb73cd3d=2 -- corrected 2026-08-11, PARĪKṢAKA F-5; NOT "mostly cb73cd3d"
// as an earlier draft of this PR claimed) do NOT satisfy EITHER clause —
// they are temporal_shape='interval' (not 'point') and carry resolution=
// NULL (not 'month'/'day') — so they now serve is_timing_window=false,
// timing_window_blocked_reason='resolution_unavailable'. This is a RULED
// consequence of PK-R-8, not a bug: those 64 rows' peaks were never
// day-refined and the sweep never classified them into the hierarchy.
// Their v1 POINT rows (54 of them) are UNAFFECTED — the
// temporal_shape==='point' clause preserves them regardless of peak_basis.
// The SAME consequence also lands on the 120 currently-SERVED
// generation='3.0' interval rows on the two authoritative charts
// (1c826d5a, 482012f1) — post-merge/pre-rebuild both canonical charts
// serve ZERO interval-shaped timing windows, restored once the R2 rebuild
// runs (ruled-correct interim, see PR #1229's R8.10 section).
// Remedy path (if ever pursued): a future lane could earn v1's own basis
// into GENUINE_PEAK_BASES by demonstrating v1's peak derivation is genuinely
// day-precision — not done here, not assumed here.
//
// PK-R-8a (2026-08-11, ADJUDICATOR ruling, the chain-basis question PK-R-8
// deferred): a chain milestone's date is DECLARED by brahma_event_
// ontology's milestone_template (episode_anchor_jd + typical_offset_days),
// never LOCATED by a peak search — it earns is_timing_window through its
// OWN, THIRD clause (peak_basis===ONTOLOGY_MILESTONE_OFFSET AND a present
// milestone_id), never through the resolution-tier clause above (chain rows
// are stamped resolution=NULL by the writer -- see ka_gochara_v3_century_
// materialize.py's run_substep chain branch). The chain clause is checked
// via an EARLY SHORT-CIRCUIT on temporal_shape==='chain', BEFORE the
// resolution==='month'/'day' branch below -- a chain row's zero-span
// milestone date must never sneak through that door and get evaluated
// against the resolution-tier formula (which was never designed for it and
// could, on a stray legacy 'day' stamp, silently grant true for the wrong
// reason).

export type TimingWindowBlockedReason =
  | 'era_resolution'
  | 'peak_basis_not_argmax'
  | 'resolution_unavailable'
  | 'chain_basis_not_declared'
  | 'chain_milestone_unanchored'
  | 'point_class_context_envelope'
  | null

// Mirrors services/gochara_v3/peak_basis_vocab.py GENUINE_PEAK_BASES exactly
// -- a LOCATED-extremum basis. ONTOLOGY_MILESTONE_OFFSET (PK-R-8a, a
// DECLARED date) is deliberately NOT a member -- see the chain clause below.
const GENUINE_PEAK_BASES: ReadonlySet<string> = new Set(['gochara_lambda_v3_argmax'])
// PK-R-8a: mirrors services/gochara_v3/peak_basis_vocab.py's
// ONTOLOGY_MILESTONE_OFFSET exactly.
const ONTOLOGY_MILESTONE_OFFSET = 'ontology_milestone_offset'

export interface ResolutionDisclosure {
  /** The row's own STORED `resolution` column ('era'|'month'|'day'|null) --
   * R8.9 no longer infers a label from date span; a NULL resolution on a
   * non-point, non-chain row is honestly reported as null, never guessed. */
  resolution: 'era' | 'month' | 'day' | null
  /** 'stored' -- a real resolution value (or a genuine point-shaped row) is
   * present. 'unavailable' -- resolution is NULL and the row is not
   * point-shaped (R8.10's v1-interval-row case). 'not_hierarchy_classified'
   * (PK-R-8a) -- the row is chain-shaped; chain rows are never hierarchy-
   * tier-classified at all (no era/month/day tier applies to a declared
   * milestone date), distinct from 'unavailable' (which means "we don't
   * know" rather than "this classification doesn't apply here"). */
  resolution_source: 'stored' | 'unavailable' | 'not_hierarchy_classified'
  /** EARNED gate (R8.9 + PK-R-8a's third clause) -- see the module section
   * header for the exact three-clause formula. Never inferred from
   * window_start/window_end span. */
  is_timing_window: boolean
  /** Populated (non-null) whenever is_timing_window is false, naming WHY it
   * was blocked -- 'era_resolution' (a decade-era row, PK-R-1
   * context-only), 'peak_basis_not_argmax' (month/day resolution but the
   * peak was never day-refined to a genuine argmax), 'resolution_
   * unavailable' (no stored resolution and not a point/chain row -- R8.10's
   * v1-row case), 'chain_basis_not_declared' (PK-R-8a: a chain row whose
   * peak_basis is anything other than ONTOLOGY_MILESTONE_OFFSET, including
   * a stray LAMBDA_V3_ARGMAX), 'chain_milestone_unanchored' (PK-R-8a: a
   * chain row with the right basis but milestone_id is NULL -- the row
   * cannot be pinned to a specific declared milestone), or (PARIṢKĀRA MR-47,
   * PK-R-10) 'point_class_context_envelope' -- a class-specific refinement
   * of 'resolution_unavailable' for rows whose stored `shape_conformance`
   * (migration 570) is earned-marked as the R8.12 flat envelope for a
   * point-canonical class, rather than the generic "we don't know why"
   * reason. Null when is_timing_window is true. */
  timing_window_blocked_reason: TimingWindowBlockedReason
}

/**
 * Derive the honest, EARNED resolution disclosure for one served row
 * (PK-R-8 R8.9 + PK-R-8a). Real detector: reads the row's OWN stored
 * `resolution`, `peak_basis`, and (for chain rows) `milestone_id` columns
 * -- never infers a tier from window_start/window_end span (R8.9 supersedes
 * the pre-PK-R-8 duration-based inference this function used to perform).
 */
export function deriveResolutionDisclosure(
  row: Pick<GocharaWindowRow, 'resolution' | 'temporal_shape' | 'peak_basis' | 'milestone_id' | 'shape_conformance'>
): ResolutionDisclosure {
  // PK-R-1's second floor: a dated point row is always a genuine timing
  // claim, regardless of resolution/peak_basis -- this is what preserves
  // the v1 sweep's 54 point rows (R8.9/R8.10).
  if (row.temporal_shape === 'point') {
    return {
      resolution: row.resolution === 'era' || row.resolution === 'month' || row.resolution === 'day'
        ? row.resolution
        : null,
      resolution_source: row.resolution ? 'stored' : 'unavailable',
      is_timing_window: true,
      timing_window_blocked_reason: null,
    }
  }

  // PK-R-8a: chain rows short-circuit HERE, before the resolution==='month'/
  // 'day' branch below -- a chain milestone's timing-window status is
  // earned via its OWN clause (declared basis + anchored milestone_id),
  // never via the resolution-tier formula (chain rows carry resolution=NULL
  // unconditionally; see the writer's run_substep chain branch).
  if (row.temporal_shape === 'chain') {
    if (row.peak_basis !== ONTOLOGY_MILESTONE_OFFSET) {
      return {
        resolution: null,
        resolution_source: 'not_hierarchy_classified',
        is_timing_window: false,
        timing_window_blocked_reason: 'chain_basis_not_declared',
      }
    }
    if (row.milestone_id == null) {
      return {
        resolution: null,
        resolution_source: 'not_hierarchy_classified',
        is_timing_window: false,
        timing_window_blocked_reason: 'chain_milestone_unanchored',
      }
    }
    return {
      resolution: null,
      resolution_source: 'not_hierarchy_classified',
      is_timing_window: true,
      timing_window_blocked_reason: null,
    }
  }

  if (row.resolution === 'era') {
    return {
      resolution: 'era',
      resolution_source: 'stored',
      is_timing_window: false,
      timing_window_blocked_reason: 'era_resolution',
    }
  }

  if (row.resolution === 'month' || row.resolution === 'day') {
    const genuineBasis = row.peak_basis != null && GENUINE_PEAK_BASES.has(row.peak_basis)
    return {
      resolution: row.resolution,
      resolution_source: 'stored',
      is_timing_window: genuineBasis,
      timing_window_blocked_reason: genuineBasis ? null : 'peak_basis_not_argmax',
    }
  }

  // resolution is NULL and the row is not point-shaped -- R8.10's v1-
  // interval-row case (and any pre-hierarchy flat v3 row). Honest null,
  // never guessed from date span (R8.9 supersedes the old duration-based
  // inference entirely).
  //
  // PARIṢKĀRA MR-47 (PK-R-10): before this fix, EVERY row landing here fell
  // through to the SAME generic 'resolution_unavailable' reason, whether it
  // was a genuinely unclassified legacy row or the R8.12 flat-production
  // envelope for a point-canonical class -- an accidental gate, not an
  // earned one (see PK-R-10's own finding: "these rows fall through the
  // generic resolution IS NULL fallback branch, which knows nothing about
  // point-canonicity specifically"). A row whose stored `shape_conformance`
  // (migration 570) is earned-marked as the point-class envelope now gets
  // its own, class-specific reason instead of the generic fallback.
  if (row.shape_conformance === 'point_class_context_envelope') {
    return {
      resolution: null,
      resolution_source: 'unavailable',
      is_timing_window: false,
      timing_window_blocked_reason: 'point_class_context_envelope',
    }
  }

  return {
    resolution: null,
    resolution_source: 'unavailable',
    is_timing_window: false,
    timing_window_blocked_reason: 'resolution_unavailable',
  }
}

function withResolutionDisclosure<T extends GocharaWindowRow>(
  rows: T[]
): Array<T & { resolution_disclosure: ResolutionDisclosure }> {
  return rows.map((row) => ({ ...row, resolution_disclosure: deriveResolutionDisclosure(row) }))
}

/**
 * §N.6-style page-level summary: how many served rows are CONTEXT-only
 * (is_timing_window===false) vs genuine timing windows. Mirrors the
 * catalog_only_rows_in_page/catalog_only_note pattern this file's sibling
 * tools already use for the confirmed-vs-catalog distinction -- the same
 * "never let a caller read the raw row count as N confirmed timing windows"
 * discipline, applied to the era-context-vs-timing-window axis.
 */
function summarizeResolutionDisclosure(
  disclosures: ResolutionDisclosure[]
): { context_only_rows_in_page: number; context_only_note: string | null } {
  const contextOnly = disclosures.filter((d) => !d.is_timing_window).length
  return {
    context_only_rows_in_page: contextOnly,
    context_only_note:
      contextOnly === 0
        ? null
        : `${contextOnly} of ${disclosures.length} served row(s) are era-scale/unresolved CONTEXT, ` +
          'not timing windows (PK-R-1) -- see each row\'s resolution_disclosure.is_timing_window; ' +
          'do not read window_start/window_end/peak_date on these rows as a month/day-precision claim.',
  }
}

/**
 * R8.15: provenance_envelope.resolution_breakdown — a page-level {era,
 * month, day, unclassified} count of the served row set's STORED
 * resolution column, distinct from (and simpler than) `facets.resolution`
 * (which stays in `facets` per R8.15's explicit instruction: "'resolution'
 * stays in facets"). `unclassified` names the same underlying population as
 * facets.resolution.unavailable — a NULL-resolution, non-point row (R8.10).
 */
function computeResolutionBreakdown(
  disclosures: ResolutionDisclosure[]
): { era: number; month: number; day: number; unclassified: number } {
  const breakdown = { era: 0, month: 0, day: 0, unclassified: 0 }
  for (const d of disclosures) {
    if (d.resolution === 'era') breakdown.era++
    else if (d.resolution === 'month') breakdown.month++
    else if (d.resolution === 'day') breakdown.day++
    else breakdown.unclassified++
  }
  return breakdown
}

// W5.1 (GOCHARA-UTKARSA): SOURCE_CITATION is now generation-conditional.
// For v3/g3_* rows the citation names the UTKARSA campaign's own engine;
// for legacy v1 rows it names the original D-5 G-4 sweep. A response that
// mixes both generations (AUTHORITATIVE_GENERATION_FILTER selects one at a
// time, but the citation is set per-tool-call, not per-row) uses the
// per-generation string for whichever generation the filter resolved to.
// The filter guarantees all rows in one response share one generation.
function buildSourceCitation(generation: string | null | undefined): string {
  // MR-03: explicit branch for generation='3.0' (post-cutover W6.4 rows).
  // ka_gochara (renamed from ka_gochara_v2_materialize at migration 563) is the
  // authoritative writer for these rows; ka_gochara_sweep was RETIRED at cutover.
  // Without this branch, '3.0' falls through to the v1 else-branch below and
  // returns false provenance (ka_gochara_sweep / generation=v1).
  if (generation === '3.0') {
    return (
      'kala_gochara_windows (L3 Kāla, W6.4 cutover ka_gochara materializer) — ' +
      'lambda_v3 via services/gochara_v3, consuming gochara_resonance_map (G-1); ' +
      'generation=3.0'
    )
  }
  if (generation != null && (generation === 'g3_utkarsha' || generation.startsWith('g3_'))) {
    return (
      'kala_gochara_windows (L3 Kāla, GOCHARA-UTKARSA W3.4 ka_gochara_v3_century_materialize writer) — ' +
      'lambda_v3 via services/gochara_v3 (bounded λ_v3 ∈ [0,1], W1.1), W4.4 calibrated weights, ' +
      'consuming gochara_resonance_map (G-1); generation=' + generation
    )
  }
  return (
    'kala_gochara_windows (L3 Kāla, D-5 Lane G-4 ka_gochara_sweep writer) — ' +
    'lambda_e via services/gochara_intensity (G-3), consuming gochara_resonance_map ' +
    '(G-1) + gochara_grammar (G-2); generation=v1'
  )
}

// Convenience: SOURCE_CITATION for legacy v1 rows (used as a static
// default in the election_avoidance per-row citation that predates W5.1).
const SOURCE_CITATION_V1 = buildSourceCitation(null)

const ROW_COLUMNS = `
  id, chart_id, event_class, temporal_shape,
  to_char(window_start, 'YYYY-MM-DD') AS window_start,
  to_char(window_end, 'YYYY-MM-DD') AS window_end,
  to_char(peak_date, 'YYYY-MM-DD') AS peak_date,
  milestone_id, is_irreversibility_milestone,
  signed_intensity::float8 AS signed_intensity,
  raw_intensity::float8 AS raw_intensity,
  valence, is_adverse,
  active_sentences, contributing_systems, suppression_state,
  peak_basis, calibration_state, source,
  computed_at, continuity_state,
  generation, era_slice_key, term_breakdown,
  resolution, parent_window_id, shape_conformance
`
// W5.1 (GOCHARA-UTKARSA): generation and era_slice_key are nullable columns
// present on kala_gochara_windows since migrations 527 and 556 respectively.
// term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source,
// threshold_lambda, threshold_percentile, implied_density, and base_rate_cited
// are the 8 v3 output-model columns added to kala_gochara_windows by migration
// 564 (PARIṢKĀRA MR-01). All arrive as NULL for v1 rows written before those
// migrations — the interface declares them optional-nullable and the serving
// code passes them through without requiring them non-null, per §N.3 "honest
// tier over fabricated".

// ADJUDICATION-6 (SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md, migration 527):
// GOCHARA-2.0 writes generation-stamped rows BESIDE v1, never over it — so
// every read that SERVES rows to a caller must resolve which generation is
// currently authoritative for this chart and filter to exactly that one, or
// a 2.0 row and its v1 counterpart for the same (chart_id, event_class,
// window) would both appear in one response. An ABSENT `kala_gochara_authority`
// row means 'v1' authoritative BY DEFINITION (never requires a seeded row —
// see migration 527's COMMENT ON TABLE). Today this is a no-op: every row is
// generation='v1' and the authority table is empty everywhere, so this filter
// is byte-identical to its absence — it only becomes load-bearing once a 2.0
// writer lands a second generation's rows for the same chart.
const AUTHORITATIVE_GENERATION_FILTER =
  " AND kala_gochara_windows.generation = COALESCE(" +
  '(SELECT authoritative_generation FROM kala_gochara_authority ' +
  "WHERE chart_id = kala_gochara_windows.chart_id), 'v1')"

async function queryRows(
  sql: string,
  params: unknown[],
  principal: Principal
): Promise<{ rows: GocharaWindowRow[]; ok: boolean; error?: string }> {
  try {
    const { rows } = await platformQuery(sql, params, principal)
    return { rows: rows as unknown as GocharaWindowRow[], ok: true }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return { rows: [], ok: false, error: message }
  }
}

// ══════════════════════════════════════════════════════════════════════════
// MR-25 — Citation → verse_refs resolution (PARIṢKĀRA campaign)
// ══════════════════════════════════════════════════════════════════════════
//
// Closes the W2.9 gap: citation strings present in active_sentences (sourced
// from gochara_grammar/citations.py constants + primitives.py families) are
// resolved to classical_text_chunks verse_refs via bg_gochara_citation_resolution
// (migration 565, "verified-before-seeded" pattern per migration 528).
//
// Design:
//   1. extractCitationStrings(): walks active_sentences JSONB looking for any
//      'classical_citation' or 'citation' key in sentence objects. Returns
//      the de-duplicated set across all rows.
//   2. fetchVerseRefs(): queries bg_gochara_citation_resolution for the batch
//      of distinct citation strings. Returns a Map<citation_string, VerseRef[]>.
//      Fails SOFT — if the table is unreachable (e.g. migration not yet applied),
//      returns an empty Map (never breaks the serving call; verse_refs is additive).
//   3. enrichWindowsWithVerseRefs(): adds `citation_verse_refs` to each served
//      window — a list of {citation_string, chunk_id, verse_ref, text_id, status}
//      objects for every resolved citation in that window's active_sentences.
//      A window with no recognized citation strings carries an empty array.
//
// Gate (MR-25): at minimum one served window carries a non-empty citation_verse_refs
// array when any resolved row exists in bg_gochara_citation_resolution.
// AT-PAR: B.3 derivation-ledger discipline — served verse_refs trace to the
// classical_text_chunks table via the resolution table's chunk_id FK.

export interface CitationVerseRef {
  citation_string: string
  chunk_id: string
  text_id: string
  verse_ref: string
  /** 'resolved' = confirmed corpus chunk; 'unresolved' = honest corpus gap */
  status: 'resolved' | 'unresolved'
}

/**
 * Walk active_sentences looking for citation strings in any sentence object
 * that carries a 'classical_citation' or 'citation' key.
 * Returns the de-duplicated set of non-empty citation strings found.
 */
export function extractCitationStrings(rows: GocharaWindowRow[]): Set<string> {
  const found = new Set<string>()
  for (const row of rows) {
    const sentences = row.active_sentences ?? []
    for (const sentence of sentences) {
      if (sentence && typeof sentence === 'object') {
        const s = sentence as Record<string, unknown>
        // W2.9 mechanism sentences use 'classical_citation' key.
        const cit = s['classical_citation'] ?? s['citation']
        if (typeof cit === 'string' && cit.trim()) {
          found.add(cit.trim())
        }
      }
    }
  }
  return found
}

/**
 * Query bg_gochara_citation_resolution for the given citation strings.
 * Returns a Map from citation_string → CitationVerseRef[].
 * Fails soft: returns empty Map on any error (verse_refs is additive, never gating).
 */
export async function fetchVerseRefs(
  citationStrings: Set<string>,
  principal: Principal
): Promise<Map<string, CitationVerseRef[]>> {
  if (citationStrings.size === 0) return new Map()

  const strings = Array.from(citationStrings)
  // Build parameterized IN clause: $1, $2, ...
  const placeholders = strings.map((_, i) => `$${i + 1}`).join(', ')
  const sql =
    `SELECT citation_string, chunk_id, text_id, verse_ref, status ` +
    `FROM bg_gochara_citation_resolution ` +
    `WHERE citation_string IN (${placeholders})`

  try {
    const { rows } = await platformQuery(sql, strings, principal)
    const result = new Map<string, CitationVerseRef[]>()
    for (const row of rows) {
      const cs = row['citation_string'] as string
      if (!result.has(cs)) result.set(cs, [])
      result.get(cs)!.push({
        citation_string: cs,
        chunk_id: row['chunk_id'] as string,
        text_id: row['text_id'] as string,
        verse_ref: row['verse_ref'] as string,
        status: (row['status'] as 'resolved' | 'unresolved') ?? 'unresolved',
      })
    }
    return result
  } catch {
    // Soft failure: bg_gochara_citation_resolution unreachable (e.g. migration
    // not yet applied). verse_refs is additive — the serving call succeeds without it.
    return new Map()
  }
}

/**
 * Add `citation_verse_refs` to each served window object.
 * citation_verse_refs is a COMPLETE list of all citation strings found in
 * active_sentences, with each entry carrying its resolution status:
 *   - 'resolved': confirmed corpus chunk (chunk_id is a real FK into
 *     classical_text_chunks, not a CORPUS_GAP stub)
 *   - 'unresolved': honest corpus gap — either the verseRefMap has an
 *     explicit unresolved row from bg_gochara_citation_resolution, OR the
 *     citation string has no entry in the table at all (CORPUS_GAP stub
 *     synthesised on the fly).
 * C1 change: the previous implementation only included resolved entries.
 * Callers that want only confirmed verse refs should filter on status='resolved'.
 */
export function enrichWindowsWithVerseRefs<T extends { active_sentences: unknown[] }>(
  windows: T[],
  rows: GocharaWindowRow[],
  verseRefMap: Map<string, CitationVerseRef[]>
): Array<T & { citation_verse_refs: CitationVerseRef[]; citation_resolution_note: string | null }> {
  return windows.map((window, i) => {
    const row = rows[i]
    if (!row) {
      return { ...window, citation_verse_refs: [], citation_resolution_note: null }
    }

    // Collect all citation strings for this row's active_sentences.
    const citations = extractCitationStrings([row])

    // Build the complete list: resolved entries from verseRefMap, then any
    // unresolved entries (explicit from the map or corpus-gap stubs for
    // strings that have no entry in bg_gochara_citation_resolution at all).
    const allRefs: CitationVerseRef[] = []
    let resolvedCount = 0
    for (const cit of citations) {
      const refs = verseRefMap.get(cit)
      if (refs && refs.length > 0) {
        // Entry exists in bg_gochara_citation_resolution — include all rows
        // (may be resolved, unresolved, or mixed) with their honest status.
        for (const ref of refs) {
          allRefs.push(ref)
          if (ref.status === 'resolved' && !ref.chunk_id.startsWith('CORPUS_GAP:')) {
            resolvedCount++
          }
        }
      } else {
        // No entry in bg_gochara_citation_resolution at all — synthesise an
        // honest corpus-gap stub using the established CORPUS_GAP: prefix
        // pattern so callers can distinguish "not looked up" from "looked up
        // and found nothing" (both are unresolved, but the chunk_id tells
        // which kind of gap this is).
        allRefs.push({
          citation_string: cit,
          chunk_id: `CORPUS_GAP:${cit}`,
          text_id: 'unknown',
          verse_ref: 'unresolved',
          status: 'unresolved',
        })
      }
    }

    const note =
      citations.size === 0
        ? null
        : resolvedCount > 0
          ? `${resolvedCount} citation(s) resolved to verse_refs from bg_gochara_citation_resolution (migration 565)`
          : `${citations.size} citation string(s) found in active_sentences but none resolved to corpus chunks yet — see bg_gochara_citation_resolution for honest gap catalog`

    return { ...window, citation_verse_refs: allRefs, citation_resolution_note: note }
  })
}

/**
 * Build a concise human-readable summary string from a λ_v3 term_breakdown
 * object. Returns null if term_breakdown is null/undefined (honest gap — the
 * row predates migration 564 or was written on the v1-parity path).
 *
 * Format: "λ_v3={lambda_v3:.2f} (promise={promise:.2f} × permission={permission:.2f} × activity={activity:.2f})"
 * Only keys present in the object are included in the product list.
 * If lambda_v3 is absent, the prefix reads "λ_v3=?".
 *
 * C1 addition: exported so callers and tests can use it directly.
 */
export function buildTermBreakdownSummary(
  termBreakdown: Record<string, unknown> | null | undefined
): string | null {
  if (termBreakdown == null) return null

  const lv3 = termBreakdown['lambda_v3']
  const prefix = typeof lv3 === 'number' ? `λ_v3=${lv3.toFixed(2)}` : 'λ_v3=?'

  const FACTOR_KEYS = ['promise', 'permission', 'activity'] as const
  const parts: string[] = []
  for (const key of FACTOR_KEYS) {
    const val = termBreakdown[key]
    if (typeof val === 'number') {
      parts.push(`${key}=${val.toFixed(2)}`)
    }
  }

  if (parts.length === 0) return prefix
  return `${prefix} (${parts.join(' × ')})`
}

// ══════════════════════════════════════════════════════════════════════════
// W2 — Category-coverage attestation (SATYA-ŚEṢA, S4-05 mechanism fix)
// ══════════════════════════════════════════════════════════════════════════
//
// Distinguishes the two axes EL-60b conflated: EXECUTION coverage (how many
// of the sweep's planned substeps have committed — `sweep_completeness`
// below) vs CATEGORY coverage (which domains the sweep's event-class
// universe even includes in the first place — `event_classes_covered` /
// `domains_not_covered`). A tool can be 100% complete on the first axis and
// structurally silent on the second; both used to read as "clean". Every
// value here is a live query result, never a hand-maintained literal —
// re-run this and the answer changes the moment G-1's resonance map (or the
// domain ontology) does, with no code change required.

export interface GocharaCoverage {
  event_classes_covered: string[]
  /** Classes G-1 built resonance targets for whose sweep has committed ZERO substeps for this
   *  chart — the grammar can see them, this chart's data cannot yet. Reported separately and
   *  EXCLUDED from `event_classes_covered`, so their domains stay in `domains_not_covered`
   *  (ṢAḌ-DARŚANA item 9: closing DP-4 must not open a second door to the same false all-clear). */
  event_classes_targeted_not_swept: string[]
  domains_not_covered: string[]
  universe_source: string
  sweep_completeness: {
    substeps_committed: number
    source: string
    note: string
    materialized_through: string | null
  }
  /** C3 (SAMPŪRTI-γ): first-class "thin ≠ rich silence" facet.
   *  Derived from event_classes_covered — thin/moderate/rich signals whether the covered set
   *  is sparse (0–3 classes), mid-range (4–9), or broad (10+).
   *  Never fabricated: always computed from the same `eventClasses` / `coveredDomains` sets
   *  that back the rest of this object; never hand-maintained. */
  coverage_quality: {
    tier: 'thin' | 'moderate' | 'rich'
    covered_class_count: number
    covered_domain_count: number
    reason: string
  }
}

export interface GocharaNotCovered {
  domain: string
  cross_pointer: { instrument: string; hint: string }
}

const COVERAGE_UNIVERSE_SOURCE =
  'event_classes_covered = DISTINCT gochara_resonance_map.event_class for this chart_id (G-1\'s own ' +
  'record of which event classes the D-5 sweep populated targets for, and therefore substepped over — ' +
  'the writer\'s docstring: "one substep per populated gochara_resonance_map event_class x decade" — ' +
  'more precise than kala_gochara_windows itself, which can under-report a class that was swept but ' +
  'produced zero rows) INTERSECTED with the classes whose sweep has actually committed at least one ' +
  'substep for this chart (build_substep_progress.substep_key is "{event_class}:year:{n}"); a class ' +
  'with targets but zero committed substeps is reported in event_classes_targeted_not_swept and is ' +
  'NOT counted as covered. Covered classes are resolved to brahma_event_ontology.domain; ' +
  'domains_not_covered = DISTINCT brahma_event_ontology.domain minus that covered set. Mechanically ' +
  'derived fresh every call from live table state — never hand-maintained.'

/** Chart-scoped: which event classes did THIS chart's sweep actually look at, which domains does
 *  that leave structurally dark, and how much of the sweep's own execution has committed. Never
 *  throws — a query failure degrades to an honestly-empty coverage object with `ok: false` so the
 *  caller can distinguish "we checked and it's genuinely uncovered" from "coverage itself could
 *  not be computed this call" rather than silently presenting the former when it is really the
 *  latter. */
export async function computeGocharaCoverage(
  chartId: string,
  principal: Principal
): Promise<{ coverage: GocharaCoverage; ok: boolean; knownDomains: string[]; knownDomainsOk: boolean }> {
  // MR-02 (PARIṢKĀRA): coverage source is authority-aware.
  // After migration 563 retires ka_gochara_sweep, v3-authority charts never had
  // substeps recorded under 'ka_gochara_sweep' — the v3 materializer (ka_gochara,
  // renamed from ka_gochara_v2_materialize) logs under its own asset_id. Querying
  // build_substep_progress for 'ka_gochara_sweep' on a v3-authority chart would
  // always return 0, misreporting a fully-built chart as uncovered.
  //
  // Resolution:
  //   - No kala_gochara_authority row (or absent table) → v1 authority → use
  //     'ka_gochara_sweep' substep history (unchanged existing behaviour).
  //   - kala_gochara_authority row present with any g3_* or '3.0' generation →
  //     v3 authority → use 'ka_gochara' (the renamed materializer) substep history.
  //     The resonance-map coverage (classesResp) is still the canonical scope source
  //     for WHAT was built; the substep count shifts to the v3 asset_id.
  //
  // The authority lookup is a single SELECT that never throws on a missing table
  // (the IF NOT EXISTS guard produces an empty rows array instead).
  const authorityResp = await platformQuery(
    `SELECT authoritative_generation
       FROM kala_gochara_authority
      WHERE chart_id = $1
      LIMIT 1`,
    [chartId],
    principal
  ).then((r) => ({ rows: r.rows, ok: true as const })).catch(() => ({ rows: [] as Record<string, unknown>[], ok: true as const }))

  const authGen = typeof authorityResp.rows[0]?.['authoritative_generation'] === 'string'
    ? authorityResp.rows[0]['authoritative_generation'] as string
    : 'v1'
  const isV3Authority = authGen === '3.0' || authGen.startsWith('g3_')

  // The substep asset_id and source description differ by authority generation.
  // v1: 'ka_gochara_sweep' (D-5 Lane G-4 sweep writer, now RETIRED but substep
  //     history is preserved in build_substep_progress for existing charts).
  //     Key format: '{event_class}:year:{n}' — split on ':year:' extracts the class.
  // v3: 'ka_gochara_v3_century_materialize' (the century materializer; W6.4 rename
  //     from ka_gochara_v2_materialize; asset_id was previously wrongly set to
  //     'ka_gochara' here — R1 SEV-1 fix).
  //     Key format: '{event_class}::{era_slice_key}' — split on '::' extracts the class.
  //     Using ':year:' split on v3 keys returns NULL for every row → swept_event_classes=[].
  const substepAssetId = isV3Authority ? 'ka_gochara_v3_century_materialize' : 'ka_gochara_sweep'
  const substepSourceLabel = isV3Authority
    ? `build_substep_progress (asset_id=ka_gochara_v3_century_materialize, chart-scoped, century materializer)`
    : `build_substep_progress (asset_id=ka_gochara_sweep, chart-scoped)`

  // R1 SEV-1 fix (Bug 2): the substep SQL query must be authority-aware because the
  // key separator differs between generations.
  //   v1 (ka_gochara_sweep): '{event_class}:year:{n}'   → split_part(key, ':year:', 1)
  //   v3 (ka_gochara_v3_century_materialize): '{event_class}::{era_slice_key}' → split_part(key, '::', 1)
  const substepQuery = isV3Authority
    ? `SELECT COUNT(*)::int AS substeps_committed,
              COALESCE(
                ARRAY_AGG(DISTINCT split_part(substep_key, '::', 1))
                  FILTER (WHERE substep_key LIKE '%::%'),
                ARRAY[]::text[]
              ) AS swept_event_classes
         FROM build_substep_progress
        WHERE chart_id = $1 AND asset_id = $2`
    : `SELECT COUNT(*)::int AS substeps_committed,
              COALESCE(
                ARRAY_AGG(DISTINCT split_part(substep_key, ':year:', 1))
                  FILTER (WHERE substep_key LIKE '%:year:%'),
                ARRAY[]::text[]
              ) AS swept_event_classes
         FROM build_substep_progress
        WHERE chart_id = $1 AND asset_id = $2`

  const [classesResp, universeResp, substepResp, horizonResp] = await Promise.all([
    platformQuery(
      `SELECT DISTINCT rm.event_class AS event_class, eo.domain AS domain
         FROM gochara_resonance_map rm
         LEFT JOIN brahma_event_ontology eo ON eo.event_class_id = rm.event_class
        WHERE rm.chart_id = $1
        ORDER BY 1`,
      [chartId],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const })).catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
    platformQuery(
      `SELECT DISTINCT domain FROM brahma_event_ontology WHERE domain IS NOT NULL ORDER BY 1`,
      [],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const })).catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
    platformQuery(
      substepQuery,
      [chartId, substepAssetId],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const })).catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
    platformQuery(
      `SELECT MAX(window_end)::text AS materialized_through
         FROM kala_gochara_windows
        WHERE chart_id = $1` + AUTHORITATIVE_GENERATION_FILTER,
      [chartId],
      principal
    ).then((r) => ({ rows: r.rows, ok: true as const }))
     .catch((err) => ({ rows: [] as Record<string, unknown>[], ok: false as const, error: String(err) })),
  ])

  const targetedClasses = [...new Set(classesResp.rows.map((r) => r['event_class']).filter((v): v is string => typeof v === 'string'))].sort()
  const substepsCommitted = Number(substepResp.rows[0]?.['substeps_committed'] ?? 0)
  const sweptClasses = new Set(
    (Array.isArray(substepResp.rows[0]?.['swept_event_classes']) ? (substepResp.rows[0]?.['swept_event_classes'] as unknown[]) : [])
      .filter((v): v is string => typeof v === 'string')
  )

  // A class only counts as COVERED when both axes hold for THIS chart: G-1 built its resonance
  // targets AND the sweep has committed at least one substep for it. Targets alone would let a
  // freshly-extended grammar (item 9's health classes, before any chart has been re-swept) drop
  // 'health' out of domains_not_covered while kala_gochara_windows still holds nothing for it —
  // reinstating the exact S4-05 shape the coverage attestation exists to prevent.
  const eventClasses = targetedClasses.filter((ec) => sweptClasses.has(ec))
  const targetedNotSwept = targetedClasses.filter((ec) => !sweptClasses.has(ec))
  const coveredDomains = new Set(
    classesResp.rows
      .filter((r) => typeof r['event_class'] === 'string' && sweptClasses.has(r['event_class'] as string))
      .map((r) => r['domain'])
      .filter((d): d is string => typeof d === 'string')
  )
  const universeDomains = universeResp.rows.map((r) => r['domain']).filter((d): d is string => typeof d === 'string').sort()
  const domainsNotCovered = universeDomains.filter((d) => !coveredDomains.has(d))

  const ok = classesResp.ok && universeResp.ok && substepResp.ok

  // C3 (SAMPŪRTI-γ): compute coverage_quality — tier classification based on covered class count.
  const coveredClassCount = eventClasses.length
  const coveredDomainCount = coveredDomains.size
  const coverageTier: 'thin' | 'moderate' | 'rich' =
    coveredClassCount < 4 ? 'thin' : coveredClassCount < 10 ? 'moderate' : 'rich'
  const coverageReason =
    coveredClassCount === 0
      ? `0 event classes covered — thin coverage: no classes in universe`
      : coverageTier === 'thin'
        ? `${coveredClassCount} event class${coveredClassCount === 1 ? '' : 'es'} covered (${eventClasses.slice(0, 3).join(', ')}) — thin coverage: only ${coveredClassCount} of ${targetedClasses.length} targeted`
        : coverageTier === 'moderate'
          ? `${coveredClassCount} event classes covered across ${coveredDomainCount} domain${coveredDomainCount === 1 ? '' : 's'} — moderate coverage`
          : `${coveredClassCount} event classes covered across ${coveredDomainCount} domain${coveredDomainCount === 1 ? '' : 's'} — rich coverage`

  return {
    ok,
    // Keep vocabulary authority separate from coverage authority.  A domain may be
    // valid in the ontology yet uncovered for this chart; conversely, a failed
    // ontology read must never be laundered into an "invalid domain" verdict.
    knownDomains: universeDomains,
    knownDomainsOk: universeResp.ok,
    coverage: {
      event_classes_covered: eventClasses,
      event_classes_targeted_not_swept: targetedNotSwept,
      domains_not_covered: domainsNotCovered,
      universe_source: COVERAGE_UNIVERSE_SOURCE,
      coverage_quality: {
        tier: coverageTier,
        covered_class_count: coveredClassCount,
        covered_domain_count: coveredDomainCount,
        reason: coverageReason,
      },
      sweep_completeness: {
        substeps_committed: substepsCommitted,
        source: substepSourceLabel,
        note:
          'Execution completeness ONLY — how many substeps have committed for THIS chart ' +
          '(MR-02: asset_id is authority-aware: ka_gochara_sweep for v1-authority charts, ' +
          'ka_gochara_v3_century_materialize for v3-authority charts per kala_gochara_authority.authoritative_generation). ' +
          'NOT the same axis as the category coverage above (which domains the sweep can ever ' +
          'surface at all, per event_classes_covered/domains_not_covered) — a fully-executed sweep ' +
          '(every substep committed) still structurally excludes any domain in domains_not_covered. ' +
          'No total-planned-substep denominator is reported here: that figure is not independently ' +
          'queryable post-build without re-deriving the writer\'s own planning logic, and this field ' +
          'will not fabricate one.',
        materialized_through: horizonResp.ok ? (horizonResp.rows[0]?.['materialized_through'] as string | null ?? null) : null,
      },
    },
  }
}

const KALA_WINDOWS_CROSS_POINTER_INSTRUMENT = 'kala_windows_get'

type InvalidGocharaDomain = {
  provided_domain: string
  valid_domains: string[]
  reason: 'domain_not_in_gochara_ontology'
}

/** Resolve a supplied domain only when the ontology vocabulary was reachable.
 * This separates an unsupported request from a valid-but-unswept domain, and
 * prevents an unknown filter from being served as a generic honest-empty scan. */
function resolveGocharaDomain(
  domain: string | undefined,
  knownDomains: string[],
  knownDomainsOk: boolean
): { effectiveDomain: string | undefined; invalidDomain: InvalidGocharaDomain | null } {
  if (!domain || !knownDomainsOk) return { effectiveDomain: domain, invalidDomain: null }
  const normalized = domain.trim().toLocaleLowerCase()
  const matched = knownDomains.find((known) => known.toLocaleLowerCase() === normalized)
  if (matched) return { effectiveDomain: matched, invalidDomain: null }
  return {
    effectiveDomain: undefined,
    invalidDomain: {
      provided_domain: domain,
      valid_domains: knownDomains,
      reason: 'domain_not_in_gochara_ontology',
    },
  }
}

/** W2 server-side refusal rule: when a caller's `domain` filter names a domain this sweep's
 *  event-class universe does not cover, return the refusal shape instead of running a scan that
 *  can only ever come back empty for that domain — the response must never present that empty as
 *  a completed, domain-covering scan result (SATYA_SHESHA_BRIEF_v1_0.md §2 W2). Returns null when
 *  no domain filter was supplied, or the requested domain IS covered (normal path proceeds). */
function notCoveredFor(domain: string | undefined, coverage: GocharaCoverage): GocharaNotCovered | null {
  if (!domain) return null
  if (!coverage.domains_not_covered.includes(domain)) return null
  // Two distinct honest reasons, never collapsed into one: the grammar has no class for this
  // domain at all, vs. the grammar has one but THIS chart's sweep has not committed a substep for
  // it yet. Both are refusals; conflating them would misreport a build gap as a doctrine gap.
  const pending = coverage.event_classes_targeted_not_swept.length > 0
  return {
    domain,
    cross_pointer: {
      instrument: KALA_WINDOWS_CROSS_POINTER_INSTRUMENT,
      hint:
        `${KALA_WINDOWS_CROSS_POINTER_INSTRUMENT}(chart_id, domain="${domain}") serves L3 Kāla ` +
        'temporal-activation windows for this domain — the gochara sweep\'s covered event-class set ' +
        '(see coverage.event_classes_covered) does not include it for this chart' +
        (pending
          ? `, though ${coverage.event_classes_targeted_not_swept.join(', ')} ` +
            'have resonance targets awaiting a sweep run (coverage.event_classes_targeted_not_swept) ' +
            '— a build gap for this chart, not an absence of grammar'
          : '') +
        '. This response is a refusal, not a completed scan of that domain: do not read the empty ' +
        '`windows` array below as "no adverse window found" for it.',
    },
  }
}

// ── §N.6 density_contract (documented, see module docstring) ────────────────

const ACTIVATION_DENSITY_CONTRACT = {
  max_digest_bytes: 20_000,
  paginated: false,
  // PARIṢKĀRA MR-11(b): 'resolution' added — see facets.resolution
  // (computeWindowFacets) + the resolution filter param on this tool.
  facets: ['event_class', 'temporal_shape', 'is_adverse', 'calibration_state', 'era_slice_key', 'resolution'],
  empty_reason: true,
  // W5.1: calibration_state layering per §N.6 — empirically_calibrated is the
  // dense layer; structural_prior is the structural layer. Reflected in the
  // `facets` key on every response (computeWindowFacets — real detector).
  density_layering: 'calibration_state:empirically_calibrated>structural_prior',
} as const

const FORECAST_DENSITY_CONTRACT = {
  max_digest_bytes: 40_000,
  paginated: true,
  facets: ['event_class', 'temporal_shape', 'valence', 'is_adverse', 'calibration_state', 'era_slice_key', 'resolution'],
  empty_reason: true,
  density_layering: 'calibration_state:empirically_calibrated>structural_prior',
} as const

const ELECTION_AVOIDANCE_DENSITY_CONTRACT = {
  max_digest_bytes: 50_000,
  paginated: true,
  facets: ['event_class', 'temporal_shape', 'calibration_state', 'era_slice_key', 'resolution'],
  empty_reason: true,
  density_layering: 'calibration_state:empirically_calibrated>structural_prior',
} as const

// ── SATYA-ŚEṢA W3 — declared response-budget ceilings for this family ───────
// Source-text-parsed by platform/scripts/census/elev_gates/_tool_enumeration.ts
// the same way registry_bridge.ts's MCP_RESPONSE_BUDGET_KB ledger is parsed for
// every tool registered there — kept HERE (not in registry_bridge.ts) because
// these three tools are not registered via that file's server.tool() call
// sites; each has its own file-local budget wiring (finalizeMcpBudget calls
// below). This constant is the single declared-ceiling SOURCE OF TRUTH the CI
// gate reads; keep it in sync BY HAND with the `maxKb` literals passed to
// finalizeMcpBudget in each compute* function below — the same discipline the
// MCP_RESPONSE_BUDGET_KB/call-site pairing in registry_bridge.ts already
// requires of every tool registered there.
export const GOCHARA_RESPONSE_BUDGET_KB = {
  gochara_activation_get: 20,
  gochara_forecast_get: 40,
  gochara_election_avoidance_get: 50,
} as const

// ── Response-budget sections (§N.6 hardFloor — see response_budget.ts) ──────
// Every row in `kala_gochara_windows` is a materialized, real-intensity
// computed window (no catalog-only/label-match rows exist in this table's
// design — G-3's PROMISE is an honest 0.0, never served, when a chart/
// event_class has no G-1 targets). The `windows` array is therefore this
// tool's single densest/most-authoritative section and is hardFloor-protected
// so a budget trim never zeroes it — `capActiveSentences` above is what keeps
// per-row detail from dominating the budget instead, run BEFORE this section
// is ever measured.
//
// `coverage` (W2) is deliberately NOT declared as a trimmable section here —
// response_budget.ts's own `IMMUNE_HONESTY_FIELDS` set already names
// `coverage` as a frozen-immune honesty field (never auto-detected as
// trimmable, never string-truncated by the last-resort walk), and this file's
// explicit-sections design means it is simply never handed to the trimmer at
// all — the strongest possible guarantee (nothing to override) rather than a
// declared floor that PASS 2 could in principle still touch.

// Non-generic over Record<string, unknown> (not the narrow {windows: GocharaWindowRow[]}
// shape the original applyResponseBudget-only version used) — the content object each
// compute* function now hands to finalizeMcpBudget also carries coverage/drill_pointers/
// provenance_envelope, so it is typed Record<string, unknown> throughout; this matches
// FinalizeMcpBudgetOptions<T>.sections: TrimmableSection<T>[] for that same T.
function windowsSection(
  toolName: string,
  minKeep: number
): TrimmableSection<Record<string, unknown>>[] {
  return [
    {
      path: 'windows',
      getArray: (c) => (Array.isArray(c['windows']) ? (c['windows'] as unknown[]) : undefined),
      setArray: (c, kept) => {
        c['windows'] = kept
      },
      minKeep,
      hardFloor: true,
      recover: { instrument: toolName, hint: 'narrow date_range or event_class to page through the full result' },
      label: 'kala_gochara_windows rows (materialized, firings-authoritative)',
    },
  ]
}

// ══════════════════════════════════════════════════════════════════════════
// W5.1 — §N.6 density facets: calibration_state layering + term_breakdown
// ══════════════════════════════════════════════════════════════════════════
//
// Per §N.6: calibrated (empirically_calibrated) rows are the dense layer;
// structural_prior rows are the structural layer. The facets key is a
// machine-readable summary served on every response — it carries counts
// by calibration_state and a boolean for term_breakdown presence so a
// consumer can immediately distinguish which density tier the response
// represents without scanning every row.
//
// I3 (W5.1): this is a real detector — it counts from the actual served
// row set, never from a hand-maintained constant. A response with zero
// empirically_calibrated rows will report calibrated_count=0 honestly.

export interface GocharaWindowFacets {
  /** Counts of served rows by calibration_state tier. */
  calibration_state: {
    empirically_calibrated: number
    structural_prior: number
    other: number
  }
  /** True iff at least one served row carries a non-null term_breakdown
   * (W1.5 λ_v3 decomposition). Never true for v1-sweep rows. */
  has_term_breakdown: boolean
  /** Generation label(s) present in the served row set. 'mixed' if both
   * v1 and g3_* rows appear (only possible if AUTHORITATIVE_GENERATION_FILTER
   * somehow yields multiple — documented but structurally prevented by design). */
  generation_tier: string
  /** PARIṢKĀRA MR-11(b) / PK-R-8: resolution-tier breakdown of the served
   * row set, computed via deriveResolutionDisclosure (real detector,
   * per-row — never a hand-maintained count). era/month/day are the row's
   * own STORED resolution (R8.9 no longer infers a tier from date span);
   * unavailable = no stored resolution and not a point-shaped row (R8.10's
   * v1-interval-row case). */
  resolution: {
    era: number
    month: number
    day: number
    unavailable: number
  }
}

function computeWindowFacets(rows: GocharaWindowRow[]): GocharaWindowFacets {
  let calibrated = 0
  let structural = 0
  let other = 0
  let hasTermBreakdown = false
  const generationSet = new Set<string>()
  const resolutionFacet = { era: 0, month: 0, day: 0, unavailable: 0 }

  for (const row of rows) {
    if (row.calibration_state === 'empirically_calibrated') {
      calibrated++
    } else if (row.calibration_state === 'structural_prior') {
      structural++
    } else {
      other++
    }
    if (row.term_breakdown != null) hasTermBreakdown = true
    const gen = row.generation ?? 'v1'
    generationSet.add(gen)

    const disclosure = deriveResolutionDisclosure(row)
    if (disclosure.resolution === 'era') resolutionFacet.era++
    else if (disclosure.resolution === 'month') resolutionFacet.month++
    else if (disclosure.resolution === 'day') resolutionFacet.day++
    else resolutionFacet.unavailable++
  }

  const generations = Array.from(generationSet).sort()
  const generationTier =
    generations.length === 0 ? 'none' :
    generations.length === 1 ? generations[0]! :
    'mixed:' + generations.join('+')

  return {
    calibration_state: {
      empirically_calibrated: calibrated,
      structural_prior: structural,
      other,
    },
    has_term_breakdown: hasTermBreakdown,
    generation_tier: generationTier,
    resolution: resolutionFacet,
  }
}

// ══════════════════════════════════════════════════════════════════════════
// 1. gochara_activation_get — "is this configuration active right now?"
// ══════════════════════════════════════════════════════════════════════════

// PARIṢKĀRA MR-11(b): shared resolution-tier facet filter, identical across
// all three tools. Matches ONLY the row's STORED `resolution` column
// (migration 567) — never an implied/inferred label — so a caller who
// filters resolution="month" gets exactly the writer-asserted month-tier
// rows, never a legacy row this serving layer merely guessed was month-length.
const RESOLUTION_FILTER_DESCRIPTION =
  'Filter to one hierarchy resolution tier: "era" | "month" | "day" (PARIṢKĀRA MR-11(b), migration ' +
  '567). Matches ONLY rows the writer itself stamped with this tier — never a row whose resolution ' +
  'this serving layer merely inferred from its date span (see each row\'s resolution_disclosure). ' +
  'Default: all tiers, including legacy rows that predate the hierarchy producer.'
const ResolutionFilterSchema = z.enum(['era', 'month', 'day']).optional().describe(RESOLUTION_FILTER_DESCRIPTION)

const ActivationInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  as_of_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/)
    .optional()
    .describe('Date to check activation on (YYYY-MM-DD). Default: today.'),
  event_class: z.string().optional().describe('Filter to one event_class (e.g. "marriage"). Default: all.'),
  domain: z
    .string()
    .optional()
    .describe(
      'Filter to event classes in this life domain (e.g. "health", "career"). If this sweep does ' +
        'not cover the domain for this chart, the response returns a `not_covered` refusal naming ' +
        'the capable instrument (kala_windows_get) instead of a misleading empty scan.'
    ),
  resolution: ResolutionFilterSchema,
})

export async function computeGocharaActivation(
  chartId: string,
  asOfDate: string,
  principal: Principal,
  eventClass?: string,
  domain?: string,
  resolution?: string
): Promise<Record<string, unknown>> {
  const { coverage, ok: coverageOk, knownDomains, knownDomainsOk } = await computeGocharaCoverage(chartId, principal)
  const { effectiveDomain, invalidDomain } = resolveGocharaDomain(domain, knownDomains, knownDomainsOk)
  const notCovered = notCoveredFor(effectiveDomain, coverage)

  // W5.1: source_citation is generation-conditional. Build with SOURCE_CITATION_V1
  // as default; updated after query when first row's generation is known.
  const baseEnvelope = {
    source: 'gochara_activation_get',
    source_citation: SOURCE_CITATION_V1,
    chart_id: chartId,
    as_of_date: asOfDate,
    event_class_filter: eventClass ?? null,
    domain_filter: domain ?? null,
    resolution_filter: resolution ?? null,
    computed_at: new Date().toISOString(),
    density_contract: ACTIVATION_DENSITY_CONTRACT,
  }

  if (invalidDomain) {
    return {
      windows: [],
      invalid_domain: invalidDomain,
      coverage,
      drill_pointers: [],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  if (notCovered) {
    return {
      windows: [],
      not_covered: notCovered,
      coverage,
      drill_pointers: [notCovered.cross_pointer],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  const params: unknown[] = [chartId, asOfDate]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND window_start <= $2 AND window_end >= $2` +
    AUTHORITATIVE_GENERATION_FILTER
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  if (effectiveDomain) {
    params.push(effectiveDomain)
    sql += ` AND EXISTS (SELECT 1 FROM brahma_event_ontology eo WHERE eo.event_class_id = kala_gochara_windows.event_class AND eo.domain = $${params.length})`
  }
  if (resolution) {
    params.push(resolution)
    sql += ` AND resolution = $${params.length}`
  }
  sql += ' ORDER BY signed_intensity DESC'

  const { rows: rawRows, ok, error } = await queryRows(sql, params, principal)
  const rows = capActiveSentences(withPlateauDisclosure(rawRows))

  // W5.1: compute facets (real detector per I3) and resolve generation-conditional citation.
  const facets = computeWindowFacets(rows)
  const resolvedCitation = buildSourceCitation(rawRows[0]?.generation ?? null)

  // MR-25: resolve citation strings from active_sentences to verse_refs.
  // Soft failure: verseRefMap is empty Map on any error (additive, never gating).
  const citationStrings = extractCitationStrings(rows)
  const verseRefMap = await fetchVerseRefs(citationStrings, principal)
  const enrichedWindows = enrichWindowsWithVerseRefs(rows as unknown as Array<{ active_sentences: unknown[] }>, rows, verseRefMap)
  // PARIṢKĀRA MR-11(b): attach resolution_disclosure to every served window
  // (PK-R-1 — a decade-era row must be labeled as CONTEXT, never presented
  // as a timing claim, stored or implied).
  const disclosures = rows.map((row) => deriveResolutionDisclosure(row))
  const windowsWithDisclosure = enrichedWindows.map((window, i) => ({
    ...window,
    resolution_disclosure: disclosures[i] ?? null,
  }))
  const { context_only_rows_in_page, context_only_note } = summarizeResolutionDisclosure(disclosures)
  const resolution_breakdown = computeResolutionBreakdown(disclosures)

  const content: Record<string, unknown> = {
    windows: windowsWithDisclosure,
    facets,
    coverage,
    drill_pointers: [] as unknown[],
    provenance_envelope: {
      ...baseEnvelope,
      source_citation: resolvedCitation,
      window_count: rows.length,
      backing_data_reachable: ok && coverageOk,
      citation_verse_refs_available: verseRefMap.size > 0,
      context_only_rows_in_page,
      context_only_note,
      resolution_breakdown,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no kala_gochara_windows row spans this date for this chart/event_class/domain filter — an honest zero-activation result, not a fabricated one'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
    },
  }

  return finalizeMcpBudget(content, {
    maxKb: GOCHARA_RESPONSE_BUDGET_KB.gochara_activation_get,
    sections: windowsSection('gochara_activation_get', 5),
  })
}

export function registerGocharaActivationTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_activation_get',
    'What it does: Returns kala_gochara_windows rows ACTIVE on a given date (default today) ' +
      'for a chart — "is this event_class configuration firing right now?" One of three views ' +
      '(activation / forecast / election_avoidance) over the D-5 G-4 signed intensity field. ' +
      'Shape-aware: point rows are single-day matches, interval rows match when the date falls ' +
      'inside the span, chain rows are per-milestone (each its own single-day match).\n\n' +
      'Output: { windows: [...], coverage: {...}, provenance_envelope: {...} }. Every response ' +
      'carries `coverage` (event_classes_covered / domains_not_covered / sweep_completeness), ' +
      'mechanically derived per call — this sweep does NOT cover every life domain (e.g. it may ' +
      'have no health event class for this chart); a `domain` filter naming an uncovered domain ' +
      'returns a `not_covered` refusal (with a cross_pointer to kala_windows_get) instead of a ' +
      'misleading empty. An honest empty `windows` array is distinguished from an unreachable ' +
      'table via provenance_envelope.empty_reason — never silently substituted.\n\n' +
      'RESOLUTION (PARIṢKĀRA MR-11(b)): every window carries `resolution_disclosure` — ' +
      '{resolution, resolution_source, is_timing_window}. Per PK-R-1 (native ruling), a decade-era ' +
      'row (is_timing_window=false) is CONTEXT, never a genuine timing claim, no matter how precise ' +
      'its peak_date looks — check is_timing_window before treating a row as a scheduling signal. ' +
      'Filter with `resolution` ("era"|"month"|"day") to select only writer-asserted tiers.\n\n' +
      'Requires: chart_id (UUID).',
    ActivationInputSchema.shape,
    async (params) => {
      const input = ActivationInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      const asOf = input.as_of_date ?? new Date().toISOString().slice(0, 10)
      try {
        const result = await computeGocharaActivation(
          input.chart_id, asOf, principal, input.event_class, input.domain, input.resolution
        )
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_activation_get' }) }],
          isError: true,
        }
      }
    }
  )
}

// ══════════════════════════════════════════════════════════════════════════
// 2. gochara_forecast_get — forward-looking windows in a date range
// ══════════════════════════════════════════════════════════════════════════

const ForecastInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    })
    .describe('Date range to forecast over (YYYY-MM-DD each). Overlap semantics: window_end >= start AND window_start <= end.'),
  event_class: z.string().optional().describe('Filter to one event_class. Default: all.'),
  valence: z.enum(['gain', 'loss', 'neutral', 'mixed']).optional().describe('Filter to one valence. Default: all.'),
  domain: z
    .string()
    .optional()
    .describe(
      'Filter to event classes in this life domain (e.g. "health", "career"). If this sweep does ' +
        'not cover the domain for this chart, the response returns a `not_covered` refusal naming ' +
        'the capable instrument (kala_windows_get) instead of a misleading empty scan — this is the ' +
        'S4-05 fix: "is there a rough patch coming for my health?" must never read this tool\'s ' +
        'silence on health as an all-clear.'
    ),
  limit: z.number().int().min(1).max(500).default(100),
  resolution: ResolutionFilterSchema,
})

// ── C2: nested era⊃month⊃day hierarchy (SAMPŪRTI-γ C2) ──────────────────────

/** Enriched window type: GocharaWindowRow with resolution_disclosure attached
 * (produced by the `withResolutionDisclosure` helper above). */
export type ServedWindow = GocharaWindowRow & { resolution_disclosure: unknown }

/** A node in the era⊃month⊃day hierarchy tree. */
export interface HierarchyNode {
  /** 'era', 'month', 'day', or null for legacy rows. */
  resolution: string | null
  /** The enriched window this node represents. */
  window: ServedWindow
  /** Sub-windows: month children of an era node, day children of a month node. */
  children: HierarchyNode[]
}

/** Nested hierarchy result returned inside `computeGocharaForecast`'s response. */
export interface NestedHierarchyResult {
  roots: HierarchyNode[]
  legacy_flat: ServedWindow[]
  coverage_note: string
}

/**
 * Build an era⊃month⊃day hierarchy from a flat array of ServedWindows.
 *
 * Rules (per SAMPŪRTI-γ C2 spec):
 * - resolution='era' (or parent_window_id=null with non-null resolution): era roots.
 * - resolution='month': child of the era identified by parent_window_id.
 * - resolution='day': child of the month identified by parent_window_id.
 * - resolution=null: legacy (pre-migration-567) — goes into legacy_flat, not the tree.
 * - A window whose parent_window_id points to a non-present id: defensive fallback
 *   to legacy_flat (never silently dropped, never incorrectly promoted to root).
 */
export function buildNestedHierarchy(windows: ServedWindow[]): NestedHierarchyResult {
  // Build id→window map for O(1) parent lookup.
  const byId = new Map<number, ServedWindow>()
  for (const w of windows) {
    byId.set(w.id, w)
  }

  // Build id→HierarchyNode map so we can attach children.
  const nodeById = new Map<number, HierarchyNode>()
  for (const w of windows) {
    nodeById.set(w.id, { resolution: w.resolution ?? null, window: w, children: [] })
  }

  const roots: HierarchyNode[] = []
  const legacy_flat: ServedWindow[] = []

  for (const w of windows) {
    const res = w.resolution ?? null

    // Legacy: resolution is null → flat list, not in tree.
    if (res === null) {
      legacy_flat.push(w)
      continue
    }

    const node = nodeById.get(w.id) as HierarchyNode

    // Era roots: resolution='era' or no parent.
    if (res === 'era' || w.parent_window_id == null) {
      roots.push(node)
      continue
    }

    // Month/day: must attach to their parent node.
    const parentNode = nodeById.get(w.parent_window_id)
    if (!parentNode) {
      // Defensive: parent not present in this page → legacy_flat.
      legacy_flat.push(w)
      // Remove from roots in case it was accidentally added; remove from nodeById
      // so no child can attach to it either.
      nodeById.delete(w.id)
      continue
    }
    parentNode.children.push(node)
  }

  const nestedCount = windows.length - legacy_flat.length
  const coverage_note =
    `${nestedCount} window${nestedCount === 1 ? '' : 's'} organized in era⊃month⊃day hierarchy; ` +
    `${legacy_flat.length} legacy row${legacy_flat.length === 1 ? '' : 's'} (resolution=null, pre-migration-567) ` +
    `served flat — hierarchy requires resolution column (migration 567)`

  return { roots, legacy_flat, coverage_note }
}

export async function computeGocharaForecast(
  chartId: string,
  dateRange: { start: string; end: string },
  eventClass: string | undefined,
  valence: string | undefined,
  limit: number,
  principal: Principal,
  domain?: string,
  resolution?: string
): Promise<Record<string, unknown>> {
  const { coverage, ok: coverageOk, knownDomains, knownDomainsOk } = await computeGocharaCoverage(chartId, principal)
  const { effectiveDomain, invalidDomain } = resolveGocharaDomain(domain, knownDomains, knownDomainsOk)
  const notCovered = notCoveredFor(effectiveDomain, coverage)

  // W5.1: source_citation is generation-conditional; default to v1 for not_covered path.
  const baseEnvelope = {
    source: 'gochara_forecast_get',
    source_citation: SOURCE_CITATION_V1,
    chart_id: chartId,
    date_range: dateRange,
    event_class_filter: eventClass ?? null,
    valence_filter: valence ?? null,
    domain_filter: domain ?? null,
    resolution_filter: resolution ?? null,
    computed_at: new Date().toISOString(),
    density_contract: FORECAST_DENSITY_CONTRACT,
  }

  if (invalidDomain) {
    return {
      windows: [],
      invalid_domain: invalidDomain,
      coverage,
      drill_pointers: [],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        shape_breakdown: {},
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  if (notCovered) {
    return {
      windows: [],
      not_covered: notCovered,
      coverage,
      drill_pointers: [notCovered.cross_pointer],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        shape_breakdown: {},
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  const params: unknown[] = [chartId, dateRange.end, dateRange.start]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND window_start <= $2 AND window_end >= $3` +
    AUTHORITATIVE_GENERATION_FILTER
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  if (valence) {
    params.push(valence)
    sql += ` AND valence = $${params.length}`
  }
  if (effectiveDomain) {
    params.push(effectiveDomain)
    sql += ` AND EXISTS (SELECT 1 FROM brahma_event_ontology eo WHERE eo.event_class_id = kala_gochara_windows.event_class AND eo.domain = $${params.length})`
  }
  if (resolution) {
    params.push(resolution)
    sql += ` AND resolution = $${params.length}`
  }
  params.push(limit)
  sql += ` ORDER BY window_start ASC, signed_intensity DESC LIMIT $${params.length}`

  const { rows: rawRows, ok, error } = await queryRows(sql, params, principal)
  const rows = capActiveSentences(withPlateauDisclosure(rawRows))

  const byShape = { point: 0, interval: 0, chain: 0 } as Record<string, number>
  for (const r of rawRows) byShape[r.temporal_shape] = (byShape[r.temporal_shape] ?? 0) + 1

  // W5.1: compute facets (real detector per I3) and resolve generation-conditional citation.
  const facets = computeWindowFacets(rows)
  const resolvedCitation = buildSourceCitation(rawRows[0]?.generation ?? null)

  // MR-25: resolve citation strings from active_sentences to verse_refs.
  // Soft failure: verseRefMap is empty Map on any error (additive, never gating).
  const citationStrings = extractCitationStrings(rows)
  const verseRefMap = await fetchVerseRefs(citationStrings, principal)
  const enrichedWindows = enrichWindowsWithVerseRefs(rows as unknown as Array<{ active_sentences: unknown[] }>, rows, verseRefMap)
  // PARIṢKĀRA MR-11(b): resolution_disclosure per served window (PK-R-1).
  const disclosures = rows.map((row) => deriveResolutionDisclosure(row))
  // C1: attach term_breakdown_summary (human-readable λ_v3 decomposition) and
  // resolution_disclosure to every served window before budget assembly.
  const windowsWithDisclosure = enrichedWindows.map((window, i) => ({
    ...window,
    resolution_disclosure: disclosures[i] ?? null,
    term_breakdown_summary: buildTermBreakdownSummary(rows[i]?.term_breakdown ?? null),
  }))
  const { context_only_rows_in_page, context_only_note } = summarizeResolutionDisclosure(disclosures)
  const resolution_breakdown = computeResolutionBreakdown(disclosures)

  // C2: build era⊃month⊃day hierarchy from the enriched windows.
  const nested_hierarchy = buildNestedHierarchy(windowsWithDisclosure as unknown as ServedWindow[])

  const materializedThrough = coverage.sweep_completeness.materialized_through
  const partialTruncation = materializedThrough !== null && materializedThrough < dateRange.end

  const content: Record<string, unknown> = {
    windows: windowsWithDisclosure,
    nested_hierarchy,
    facets,
    coverage,
    drill_pointers: [] as unknown[],
    provenance_envelope: {
      ...baseEnvelope,
      source_citation: resolvedCitation,
      window_count: rawRows.length,
      shape_breakdown: byShape,
      backing_data_reachable: ok && coverageOk,
      citation_verse_refs_available: verseRefMap.size > 0,
      context_only_rows_in_page,
      context_only_note,
      resolution_breakdown,
      empty_reason: rawRows.length === 0
        ? (ok
            ? 'no kala_gochara_windows rows overlap this date_range/filter combination — honest zero result. ' +
              'Note: G-4 has only materialized rows for chart-relative decades that have actually been swept ' +
              '(see coverage.sweep_completeness) — an empty result for an unswept decade is a coverage gap, not ' +
              'a negative signal; check kala_gochara_windows build coverage before reading this as "nothing happens".'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
      coverage_disclosure: {
        requested_range: dateRange,
        materialized_through: materializedThrough,
        partial_truncation: partialTruncation,
        truncation_note: partialTruncation
          ? `Requested range extends to ${dateRange.end}; this chart's kala_gochara_windows ` +
            `materialization (all event classes, all generations) currently reaches only through ` +
            `${materializedThrough}. Windows beyond that date have not been swept -- this is a ` +
            `coverage gap, not a signal that nothing happens after ${materializedThrough}. See ` +
            `coverage.sweep_completeness / coverage.event_classes_targeted_not_swept for what has ` +
            `and has not been swept for this chart.`
          : null,
      },
    },
  }

  return finalizeMcpBudget(content, {
    maxKb: GOCHARA_RESPONSE_BUDGET_KB.gochara_forecast_get,
    sections: windowsSection('gochara_forecast_get', 10),
  })
}

export function registerGocharaForecastTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_forecast_get',
    'What it does: Returns kala_gochara_windows rows overlapping a forward-looking date range ' +
      'for a chart — the FORECAST view over the D-5 G-4 signed lambda_e intensity field. ' +
      'Shape-aware (point/interval/chain, per brahma_event_ontology — BRIEF_D5 §3): an ' +
      'interval-shaped row is a real elevated-hazard SPAN (never a lone asserted day); a ' +
      'chain-shaped row is one of several per-milestone sub-windows, each independently scored, ' +
      'with is_irreversibility_milestone flagging the class\'s primary claim where declared.\n\n' +
      'CATEGORY COVERAGE (S4-05 fix): this sweep does not necessarily cover every life domain — ' +
      'every response carries `coverage.event_classes_covered` / `coverage.domains_not_covered`, ' +
      'mechanically derived per call. A silent/empty result for a domain NOT in event_classes_covered ' +
      'is NOT a clearance for that domain (e.g. "no adverse window" here says nothing about health if ' +
      'health is absent from coverage) — pass `domain` to get an explicit `not_covered` refusal with a ' +
      'cross_pointer to the capable instrument (kala_windows_get) instead of relying on silence.\n\n' +
      'Output: { windows: [...], coverage: {...}, provenance_envelope: { shape_breakdown, empty_reason, ... } }.\n\n' +
      'RESOLUTION (PARIṢKĀRA MR-11(b)): every window carries `resolution_disclosure` — ' +
      '{resolution, resolution_source, is_timing_window}. Per PK-R-1 (native ruling), a decade-era ' +
      'row (is_timing_window=false) is CONTEXT, never a genuine timing claim — check ' +
      'is_timing_window before treating a forecast row as an actionable date. Filter with ' +
      '`resolution` ("era"|"month"|"day") to select only writer-asserted tiers.\n\n' +
      'Requires: chart_id (UUID), date_range {start, end}.',
    ForecastInputSchema.shape,
    async (params) => {
      const input = ForecastInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      try {
        const result = await computeGocharaForecast(
          input.chart_id,
          input.date_range,
          input.event_class,
          input.valence,
          input.limit,
          principal,
          input.domain,
          input.resolution
        )
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_forecast_get' }) }],
          isError: true,
        }
      }
    }
  )
}

// ══════════════════════════════════════════════════════════════════════════
// 3. gochara_election_avoidance_get — adverse windows, full DR-16 payload
// ══════════════════════════════════════════════════════════════════════════
//
// BRIEF_D5 §4 (DR-16 honest-clarity gate, hard acceptance item, NOT a
// diagnostic): every adverse window served here carries, in ONE payload:
//   1. honest clarity      — plain valence/magnitude language, no euphemism
//   2. probabilistic       — `framing` field states this explicitly; NEVER a
//                             fatalistic/point death-or-ruin claim (the
//                             uniform birth->birth+100y horizon itself exists
//                             so this table never encodes a longevity opinion)
//   3. falsifier-bearing    — `falsifier` names what would disconfirm the claim
//   4. mitigation-paired    — `mitigation` (BPHS-cited brahma_remedy_corpus
//                             row, matched by the window's dominant
//                             contributing graha) ships in the SAME payload,
//                             never bare; `suppression_state` (G-2's own
//                             vedha/kartari damping) is also surfaced
//   5. confidence-honest    — `calibration_state`/`n_observations`/
//                             `control_delta` disclosed per row (D-5 ships
//                             `structural_prior` only; empirical calibration
//                             is D-4b's job, not claimed here)

const ElectionAvoidanceInputSchema = z.object({
  chart_id: z.string().uuid().describe('UUID of the chart. Required — no default chart.'),
  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    })
    .describe('Date range to check for adverse windows to avoid (YYYY-MM-DD each).'),
  event_class: z.string().optional().describe('Filter to one event_class. Default: all adverse classes.'),
  domain: z
    .string()
    .optional()
    .describe(
      'Filter to event classes in this life domain (e.g. "health", "career"). If this sweep does ' +
        'not cover the domain for this chart, the response returns a `not_covered` refusal naming ' +
        'the capable instrument (kala_windows_get) instead of a misleading empty scan.'
    ),
  limit: z.number().int().min(1).max(200).default(50),
  resolution: ResolutionFilterSchema,
})

export function dominantGraha(row: GocharaWindowRow): string | null {
  const active = (row.contributing_systems ?? []).filter((s) => s.active)
  // Prefer a graha-double-transit system's own detail (guru_shani_double_transit
  // names a real graha pair); otherwise fall back to the highest-weight active
  // dasha lord if the detail carries one (best-effort, never fabricated).
  for (const s of active) {
    const detail = s.detail as Record<string, unknown> | undefined
    const lord = detail?.['lord_graha'] ?? detail?.['natural_planet'] ?? detail?.['natal_planet']
    if (typeof lord === 'string') return lord.toLowerCase()
  }
  return null
}

async function fetchMitigation(planet: string | null, principal: Principal): Promise<Record<string, unknown> | null> {
  if (!planet) return null
  const { rows } = await queryRows(
    `SELECT remedy_id, planet, domain, remedy_type, prescription_text, mantra_text, gemstone,
            charity_action, source_citation, classical_ref, confidence
       FROM brahma_remedy_corpus WHERE planet = $1 ORDER BY confidence DESC LIMIT 1`,
    [planet],
    principal
  ) as unknown as { rows: Record<string, unknown>[] }
  return rows[0] ?? null
}

export async function computeGocharaElectionAvoidance(
  chartId: string,
  dateRange: { start: string; end: string },
  eventClass: string | undefined,
  limit: number,
  principal: Principal,
  domain?: string,
  resolution?: string
): Promise<Record<string, unknown>> {
  const { coverage, ok: coverageOk, knownDomains, knownDomainsOk } = await computeGocharaCoverage(chartId, principal)
  const { effectiveDomain, invalidDomain } = resolveGocharaDomain(domain, knownDomains, knownDomainsOk)
  const notCovered = notCoveredFor(effectiveDomain, coverage)

  // W5.1: source_citation is generation-conditional; default to v1 for not_covered path.
  const baseEnvelope = {
    source: 'gochara_election_avoidance_get',
    source_citation: SOURCE_CITATION_V1,
    chart_id: chartId,
    date_range: dateRange,
    event_class_filter: eventClass ?? null,
    domain_filter: domain ?? null,
    resolution_filter: resolution ?? null,
    computed_at: new Date().toISOString(),
    dr16_properties: ['honest_clarity', 'probabilistic_never_fatalistic', 'falsifier_bearing', 'mitigation_paired', 'confidence_honest'],
    density_contract: ELECTION_AVOIDANCE_DENSITY_CONTRACT,
  }

  if (invalidDomain) {
    return {
      windows: [],
      invalid_domain: invalidDomain,
      coverage,
      drill_pointers: [],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  if (notCovered) {
    return {
      windows: [],
      not_covered: notCovered,
      coverage,
      drill_pointers: [notCovered.cross_pointer],
      provenance_envelope: {
        ...baseEnvelope,
        window_count: 0,
        backing_data_reachable: coverageOk,
        empty_reason: null,
      },
    }
  }

  const params: unknown[] = [chartId, dateRange.end, dateRange.start]
  let sql = `SELECT ${ROW_COLUMNS} FROM kala_gochara_windows
             WHERE chart_id = $1 AND is_adverse = true AND window_start <= $2 AND window_end >= $3` +
    AUTHORITATIVE_GENERATION_FILTER
  if (eventClass) {
    params.push(eventClass)
    sql += ` AND event_class = $${params.length}`
  }
  if (effectiveDomain) {
    params.push(effectiveDomain)
    sql += ` AND EXISTS (SELECT 1 FROM brahma_event_ontology eo WHERE eo.event_class_id = kala_gochara_windows.event_class AND eo.domain = $${params.length})`
  }
  if (resolution) {
    params.push(resolution)
    sql += ` AND resolution = $${params.length}`
  }
  params.push(limit)
  sql += ` ORDER BY signed_intensity ASC LIMIT $${params.length}`  // most-negative first

  const { rows, ok, error } = await queryRows(sql, params, principal)

  // W5.1: resolve generation-conditional citation once, applied to envelope + per-row.
  const resolvedCitation = buildSourceCitation(rows[0]?.generation ?? null)

  const avoidWindows = await Promise.all(
    rows.map(async (row) => {
      const planet = dominantGraha(row)
      const mitigation = await fetchMitigation(planet, principal)
      const plateauDisclosure = derivePlateauDisclosure(row)
      // PARIṢKĀRA MR-11(b): PK-R-1 gate — a decade-era adverse row must be
      // disclosed as CONTEXT, never presented as an election date to avoid.
      const resolutionDisclosure = deriveResolutionDisclosure(row)
      return {
        event_class: row.event_class,
        temporal_shape: row.temporal_shape,
        window_start: row.window_start,
        window_end: row.window_end,
        peak_date: row.peak_date,
        milestone_id: row.milestone_id,
        // MR-12 (PARIṢKĀRA): is_irreversibility_milestone was selected in
        // ROW_COLUMNS but dropped when this object was reconstructed
        // field-by-field (unlike gochara_forecast_get's windows, which spread
        // the full row and so already served it). Additive fix — chain-shaped
        // adverse windows (a future chain-canonical adverse class) now carry
        // the same milestone_id + is_irreversibility_milestone pair here that
        // gochara_forecast_get already serves.
        is_irreversibility_milestone: row.is_irreversibility_milestone,
        // W5.1: pass-through density facet columns from kala_gochara_windows.
        // All nullable — NULL for v1 rows predating migration 556/559.
        era_slice_key: row.era_slice_key ?? null,
        generation: row.generation ?? null,
        term_breakdown: row.term_breakdown ?? null,
        // PARIṢKĀRA MR-11(b) (migration 567).
        resolution: row.resolution ?? null,
        parent_window_id: row.parent_window_id ?? null,
        resolution_disclosure: resolutionDisclosure,
        signed_intensity: row.signed_intensity,
        raw_intensity: row.raw_intensity,
        valence: row.valence,
        plateau_disclosure: plateauDisclosure,
        // 1. honest clarity (D-5 native disposition, 2026-07-20: never state a
        // capped/truncated bound as if it were a confirmed closure — see
        // `derivePlateauDisclosure`)
        clarity_statement:
          `Elevated adverse-valence configuration for '${row.event_class}' ` +
          `(${row.temporal_shape}-shaped) over ${row.window_start}..${row.window_end}, ` +
          `raw magnitude ${row.raw_intensity.toFixed(4)}. This is a probabilistic signal from a ` +
          `structural-prior model, not a certainty and not a fatalistic prediction.` +
          (plateauDisclosure ? ` PLATEAU NOTICE: ${plateauDisclosure.note}.` : '') +
          // PARIṢKĀRA MR-11(b), PK-R-1 (native ruling): a decade-era span
          // must never read as an election-avoidance date recommendation.
          (!resolutionDisclosure.is_timing_window
            ? ` CONTEXT ONLY (PK-R-1): this is a ${resolutionDisclosure.resolution ?? 'coarse'}-scale ` +
              `span, not a month/day-resolution timing window — do not treat ${row.window_start}..` +
              `${row.window_end} as specific dates to avoid; see resolution_disclosure.`
            : ''),
        // 2. probabilistic, never fatalistic
        framing: {
          probabilistic: true,
          fatalistic_claim: false,
          note:
            'Never a death/ruin point-claim. The birth->birth+100y sweep horizon is uniform for ' +
            'every chart and is NOT tied to computed longevity/ayurdaya (Ethical Framework — using ' +
            'it to bound the sweep would itself encode a lifespan opinion).',
        },
        // 3. falsifier-bearing
        falsifier: {
          statement:
            `This claim is falsified if no LEL-loggable adverse '${row.event_class}' outcome is ` +
            `recorded for chart ${chartId} overlapping ${row.window_start}..${row.window_end}.`,
          checked_via: 'G-5 prospective-ledger outcome matching (brahma_prospective_ledger, ' +
            'once this window is filed as a claim) — not yet filed by this read-only view.',
        },
        // 4. mitigation-paired (never bare)
        suppression_state: row.suppression_state,
        mitigation: mitigation ?? {
          available: false,
          reason: planet
            ? `no brahma_remedy_corpus row found for planet='${planet}'`
            : 'no dominant contributing graha could be resolved from contributing_systems for this window ' +
              '-- honest gap, not a fabricated remedy',
        },
        // 5. confidence-honest
        confidence_disclosure: {
          calibration_state: row.calibration_state,
          // W5.1: generation-tier carried in confidence disclosure so consumers
          // can distinguish structural-prior v1 rows from potentially empirically-
          // calibrated g3_* rows (the g3 calibration cycle — W4.4+W4.5 — can
          // promote rows to 'empirically_calibrated').
          generation_tier: row.generation ?? 'v1',
          era_slice_key: row.era_slice_key ?? null,
          n_observations: null,
          control_delta: null,
          note:
            'D-5 ships structural_prior weights only (beta_e, PERMISSION system weights, suppression ' +
            'damping) -- empirical calibration (n_observations, control_delta) is D-4b\'s job, not yet ' +
            'available. This is disclosed, not silently omitted.',
        },
        contributing_systems_active: (row.contributing_systems ?? []).filter((s) => s.active).map((s) => s.system_id),
        active_sentences_count: row.active_sentences.length,
        peak_basis: row.peak_basis,
        // W5.1: generation-conditional per-row citation.
        source_citation: buildSourceCitation(row.generation ?? null),
      }
    })
  )

  // W5.1: compute facets (real detector per I3).
  const facets = computeWindowFacets(rows)
  // PARIṢKĀRA MR-11(b): page-level context-only summary (PK-R-1).
  const electionAvoidanceDisclosures = rows.map((row) => deriveResolutionDisclosure(row))
  const { context_only_rows_in_page, context_only_note } = summarizeResolutionDisclosure(
    electionAvoidanceDisclosures
  )
  const resolution_breakdown = computeResolutionBreakdown(electionAvoidanceDisclosures)

  const materializedThrough = coverage.sweep_completeness.materialized_through
  const partialTruncation = materializedThrough !== null && materializedThrough < dateRange.end

  const content: Record<string, unknown> = {
    windows: avoidWindows,
    facets,
    coverage,
    drill_pointers: [] as unknown[],
    provenance_envelope: {
      ...baseEnvelope,
      source_citation: resolvedCitation,
      window_count: rows.length,
      backing_data_reachable: ok && coverageOk,
      context_only_rows_in_page,
      context_only_note,
      resolution_breakdown,
      empty_reason: rows.length === 0
        ? (ok
            ? 'no adverse (is_adverse=true) kala_gochara_windows rows overlap this date_range/filter -- ' +
              'an honestly clean window, not a fabricated all-clear (verify coverage.sweep_completeness ' +
              'for this range)'
            : `kala_gochara_windows unreachable this call: ${error ?? 'unknown error'}`)
        : null,
      coverage_disclosure: {
        requested_range: dateRange,
        materialized_through: materializedThrough,
        partial_truncation: partialTruncation,
        truncation_note: partialTruncation
          ? `Requested range extends to ${dateRange.end}; this chart's kala_gochara_windows ` +
            `materialization (all event classes, all generations) currently reaches only through ` +
            `${materializedThrough}. Windows beyond that date have not been swept -- this is a ` +
            `coverage gap, not a signal that nothing happens after ${materializedThrough}. See ` +
            `coverage.sweep_completeness / coverage.event_classes_targeted_not_swept for what has ` +
            `and has not been swept for this chart.`
          : null,
      },
    },
  }

  return finalizeMcpBudget(content, {
    maxKb: GOCHARA_RESPONSE_BUDGET_KB.gochara_election_avoidance_get,
    sections: windowsSection('gochara_election_avoidance_get', 5),
  })
}

export function registerGocharaElectionAvoidanceTool(server: McpServer, principal: Principal): void {
  server.tool(
    'gochara_election_avoidance_get',
    'What it does: Returns ADVERSE (is_adverse=true) kala_gochara_windows rows overlapping a date ' +
      'range — the ELECTION-AVOIDANCE view over the D-5 G-4 signed lambda_e field ("which dates in ' +
      'this range should an election/muhurta avoid?"). Every returned window carries the full DR-16 ' +
      'honest-clarity payload in one object (BRIEF_D5 §4, binding): clarity_statement (plain language, ' +
      'no euphemism), framing (probabilistic, never fatalistic), falsifier, suppression_state + ' +
      'mitigation (BPHS-cited remedy from brahma_remedy_corpus, paired in the SAME payload — honestly ' +
      'flagged unavailable when no remedy row resolves, never fabricated), and confidence_disclosure ' +
      '(calibration_state — D-5 ships structural_prior only).\n\n' +
      'CATEGORY COVERAGE (S4-05 fix): every response carries `coverage` (mechanically derived); a ' +
      '`domain` filter naming a domain outside coverage.event_classes_covered/domains returns a ' +
      '`not_covered` refusal (cross-pointing to kala_windows_get) instead of a misleading empty.\n\n' +
      'DEFERRED (documented, not silently dropped): the existing muhurta_finder tool is NOT ' +
      're-pointed to this table by this lane (see register_gochara_windows.ts module docstring / ' +
      'this lane\'s close report for the full reasoning) — use this tool directly for the signed-field ' +
      'election-avoidance view in the interim.\n\n' +
      'RESOLUTION (PARIṢKĀRA MR-11(b), PK-R-1 native ruling): a decade-era adverse row is CONTEXT, ' +
      'never a genuine date-to-avoid — every window carries `resolution_disclosure.is_timing_window` ' +
      '(false for era-scale rows) and clarity_statement appends an explicit CONTEXT ONLY caveat for ' +
      'them; do not surface an is_timing_window=false row as a specific election date to avoid. ' +
      'Filter with `resolution` ("era"|"month"|"day") to select only writer-asserted tiers.\n\n' +
      'Requires: chart_id (UUID), date_range {start, end}.',
    ElectionAvoidanceInputSchema.shape,
    async (params) => {
      const input = ElectionAvoidanceInputSchema.parse(params)
      const authorized = await remoteAuthorize(principal, input.chart_id)
      if (!authorized) {
        return { content: [{ type: 'text' as const, text: 'AUTHZ_DENIED: not authorized to access this chart' }], isError: true }
      }
      try {
        const result = await computeGocharaElectionAvoidance(
          input.chart_id,
          input.date_range,
          input.event_class,
          input.limit,
          principal,
          input.domain,
          input.resolution
        )
        return { content: [{ type: 'text' as const, text: JSON.stringify(result) }] }
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ ok: false, error: message, tool: 'gochara_election_avoidance_get' }) }],
          isError: true,
        }
      }
    }
  )
}

// ── Combined registration convenience (server.ts wires this ONE call) ───────

export function registerGocharaWindowsTools(server: McpServer, principal: Principal): void {
  registerGocharaActivationTool(server, principal)
  registerGocharaForecastTool(server, principal)
  registerGocharaElectionAvoidanceTool(server, principal)
}
