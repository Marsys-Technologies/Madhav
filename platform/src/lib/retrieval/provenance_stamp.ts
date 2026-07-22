/**
 * provenance_stamp.ts — R5 W4 provenance-stamp serving (design §10.6 SESSION STABILITY +
 * §31.3 SESSION-PIN COLLISION + §31.5 BUILD PROVENANCE AT SERVE TIME).
 * ======================================================================================
 * [RC-13 / W-17 naming note: this module was originally named `session_pin.ts`
 * (types/functions `SessionPin*` / `session_pin`). Renamed to `provenance_stamp.ts`
 * (`ProvenanceStamp*` / `provenance_stamp`) per the D-16 ruling on record
 * (PARIPRASHNA_TARGET_ARCHITECTURE §11.4/§161: "the session pin is renamed ... it is
 * a per-turn provenance stamp, not a session pin"). RC-13 is the naming rename ONLY —
 * internal identifiers + the served JSON field — zero behavior/storage/contract change.
 * The broader D-16 restructuring (moving storage to immutable per-turn
 * `conversation_messages.metadata_json`, per-turn drift detection, copying into
 * prediction-ledger rows) is explicitly NOT executed here; this module still serves
 * the mutable `mcp_sessions.state_json`-keyed value described below.]
 *
 * WHAT THE PROVENANCE STAMP MEANS PER THE DESIGN (do not confuse with time-travel to old data):
 *
 *   §10.6 — "Retrieval pins {priors_version, formula_versions, ranking_config,
 *   now_context timestamp} at session open ... every response reports the pin;
 *   drill calls inherit it. Version bumps take effect at the NEXT session."
 *
 *   §31.5 — "Envelope gains build_id (chart-level); ... one response = one build_id;
 *   a mid-session build change surfaces as a judgment_flag ('chart rebuilt mid-session;
 *   pin refreshed')."
 *
 * IMPORTANT SCOPE NOTE (see JL entry for the full ruling): L1+ storage is
 * delete-then-insert per chart (CLAUDE.md §N.3) — a chart rebuild REPLACES rows in
 * place; there is no retained historical snapshot of an older build's data to serve.
 * The provenance stamp therefore CANNOT mean "force this session to keep reading an
 * older build's data" (that data no longer exists after a rebuild). It means: capture
 * the values that were true at session-open, detect when the live chart has moved on
 * (build_id changed), and surface that drift HONESTLY as a judgment_flag + a
 * refreshed stamp — never silently blend an old assumption with new data.
 *
 * D6 (design §12) — "session pin: serving-layer session row {pins…}; no schema change
 * to data assets." Storage: `mcp_sessions.state_json.pins[chart_id]` — this re-keys the
 * stamp to (user, session_key, chart_id) as §31.3 mandates, entirely inside the existing
 * free-form JSONB column (migration 382), with zero schema change.
 *
 * §31.3's full fix (per-conversation session keys) is explicitly out of scope here —
 * "Full fix rides the MCP-elevation workstream (per-conversation keys are a client
 * concern)." This module implements the mitigations that DO ride this wave: chart_id
 * stays an explicit, required key into the stamp (never inferred), and the stamp
 * re-keys by chart_id so two chart contexts sharing one (user, session_key) get
 * independent stamps instead of clobbering one shared stamp.
 */

import 'server-only'
import { query } from '@/lib/db/client'
import { PRIORS_VERSION } from './ranking/priors_config'
import { getLedgerVersion } from './concept_ledger/ledger'

// ── Types ──────────────────────────────────────────────────────────────────────

export interface ProvenanceStampFormulaVersions {
  /** Reserved for a distinct salience/ranking formula version once one is stamped per
   *  build_runs row (no such column exists live today — honest null, never fabricated,
   *  per B.10). priors_version (above) is the one formula-adjacent version that IS
   *  live and code-tracked (`ranking/priors_config.ts`); this field is additive space
   *  for a future, separately-versioned formula if/when one is introduced. */
  salience_formula_ver: string | null
}

export interface ProvenanceStampRankingConfig {
  /** Name of the ranking pipeline in effect. Additive — more fields land here as the
   *  composite ranker grows named configs; never removed once shipped (drill calls
   *  inherit the stamp, so this must stay a stable, appendable shape). */
  mode: 'composite_v1'
}

export interface ProvenanceStampValues {
  chart_id: string
  priors_version: string
  formula_versions: ProvenanceStampFormulaVersions
  ranking_config: ProvenanceStampRankingConfig
  /** Chart-level build identifier (design §31.5). Null if the chart has never completed a build
   *  (honest null, never fabricated — B.10). */
  build_id: string | null
  build_status: string | null
  /** W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4, W-26): the concept-ledger staleness
   *  signal — see `concept_ledger/ledger.ts#getLedgerVersion`. Orthogonal to `build_id`:
   *  build_id tracks THIS chart's data; ledger_version tracks the serving catalog itself
   *  (a capability's lifecycle_state can change with no chart ever rebuilding). Null while
   *  concept_ledger is empty (pre-W-25 harvest) — honest null, never fabricated (B.10). */
  ledger_version: string | null
  /** dd-MMM-yyyy-adjacent ISO date, the "now_context timestamp" of §10.6, captured at stamp time. */
  now_context_date: string
  /** CALL-TIME METADATA (W3-L8 cache-safety note, mirrors envelope.ts's TimingBlock.computed_at):
   *  when this stamp value (this exact build_id + ledger_version) was first captured or last
   *  refreshed. Excluded from any cache-safe "stable content" comparison — two resolutions
   *  of the identical (build_id, ledger_version) stamp will legitimately carry different
   *  `pinned_at` values depending on call time. */
  pinned_at: string
}

export interface ProvenanceStampResolution {
  pin: ProvenanceStampValues
  /** True iff this resolution just detected + repaired a mid-session build change. */
  drift: boolean
  judgment_flags: string[]
}

// ── Pure helpers (unit-testable without a DB) ─────────────────────────────────

/**
 * Compare a previously-stamped value against freshly-computed current values.
 * Two independent drift signals matter here (W3-L8 widened this from build_id-only):
 *   - build_id       (§31.5): THIS chart's data has been rebuilt.
 *   - ledger_version (W-26):  the serving catalog (concept_ledger) has changed —
 *     orthogonal to any chart rebuild (e.g. a capability's lifecycle_state flipped
 *     to RETIRED). Both signals are collected (never short-circuited on the first
 *     match) so a caller sees every reason the stamp refreshed, not just one.
 * priors_version and ranking_config are process-wide constants that only change on a
 * deploy (§10.6's "version bumps take effect at the NEXT session" — i.e. a new session
 * naturally picks up the new value; an in-flight session is not expected to react to
 * those), so they are deliberately NOT drift signals here.
 */
export function detectBuildDrift(
  existing: ProvenanceStampValues | null,
  current: Omit<ProvenanceStampValues, 'pinned_at'>,
): { drift: boolean; judgment_flags: string[] } {
  if (!existing) return { drift: false, judgment_flags: [] }

  const judgment_flags: string[] = []
  if (existing.build_id !== current.build_id) {
    judgment_flags.push('chart_rebuilt_mid_provenance_stamp_refreshed')
  }
  if (existing.ledger_version !== current.ledger_version) {
    judgment_flags.push('concept_ledger_updated_mid_provenance_stamp_refreshed')
  }
  return { drift: judgment_flags.length > 0, judgment_flags }
}

/** Read the (chart_id-namespaced) stamp out of a session's state_json blob, if present. */
export function readPinFromState(
  stateJson: Record<string, unknown> | null | undefined,
  chartId: string,
): ProvenanceStampValues | null {
  const pins = (stateJson?.['pins'] as Record<string, unknown> | undefined) ?? undefined
  if (!pins) return null
  const raw = pins[chartId]
  if (!raw || typeof raw !== 'object') return null
  return raw as ProvenanceStampValues
}

/** Produce the new state_json blob with this chart's stamp set/replaced — additive to any
 *  other chart's stamp already present (the re-keying that satisfies §31.3). */
export function buildPinPatch(
  stateJson: Record<string, unknown> | null | undefined,
  chartId: string,
  pin: ProvenanceStampValues,
): Record<string, unknown> {
  const base = stateJson ?? {}
  const pins = { ...((base['pins'] as Record<string, unknown> | undefined) ?? {}) }
  pins[chartId] = pin
  return { ...base, pins }
}

// ── DB-backed lookups ──────────────────────────────────────────────────────────

/**
 * The chart's current build identity, per §31.5. `build_runs` is the LIVE per-chart
 * build-orchestration table (migration 171: id, chart_id, scope, state, ended_at) —
 * read-only here; this module never writes to it (build plane is sealed/frozen, per
 * scope; the orchestrator itself is FROZEN — CLAUDE.md §N.2). Only a 'completed' run
 * counts as having actually replaced served data (a planned/running/paused/stopped/
 * failed run has not); this covers BOTH full-chart builds and single-asset rebuilds
 * (scope='global'|'layer'|'asset') — a partial rebuild still changes the chart's
 * served data and must still be detected as drift.
 *
 * (Earlier design drafts referenced a `builds` table with a `salience_formula_ver`
 * column — that table does not exist on the live schema; `0001_brahma_baseline.sql`'s
 * `builds`/`build_notifications`/etc. are dead legacy-schema artifacts from an
 * unrelated prior product baseline, never provisioned in this environment. Verified
 * live against Cloud SQL before wiring this query — see the JL entry.)
 */
export async function getLatestChartBuild(chartId: string): Promise<{
  build_id: string | null
  status: string | null
  salience_formula_ver: string | null
}> {
  const { rows } = await query<{
    build_id: string
    status: string
  }>(
    `SELECT id::text AS build_id, state AS status
     FROM build_runs
     WHERE chart_id = $1 AND state = 'completed'
     ORDER BY ended_at DESC NULLS LAST
     LIMIT 1`,
    [chartId],
  )
  const row = rows[0]
  return {
    build_id: row?.build_id ?? null,
    status: row?.status ?? null,
    // No distinct formula-version column exists on build_runs — see ProvenanceStampFormulaVersions doc.
    salience_formula_ver: null,
  }
}

/** Compute what the stamp WOULD be right now for this chart (no session/state involved). */
export async function computeCurrentPinValues(
  chartId: string,
): Promise<Omit<ProvenanceStampValues, 'pinned_at'>> {
  const [build, ledger_version] = await Promise.all([
    getLatestChartBuild(chartId),
    getLedgerVersion(),
  ])
  return {
    chart_id: chartId,
    priors_version: PRIORS_VERSION,
    formula_versions: { salience_formula_ver: build.salience_formula_ver },
    ranking_config: { mode: 'composite_v1' },
    build_id: build.build_id,
    build_status: build.status,
    ledger_version,
    now_context_date: new Date().toISOString().slice(0, 10),
  }
}

/**
 * Resolve the effective stamp for (session state_json, chart_id): reuse the existing
 * stamp if the chart's build hasn't moved; otherwise (first stamp, or build drift)
 * compute+return a fresh one. Does NOT persist — callers own the write-back
 * (mirrors the mcp_sessions lookup-mutate-writeback discipline already established
 * in `lib/mcp/sessions.ts`).
 */
export async function resolveProvenanceStamp(
  stateJson: Record<string, unknown> | null | undefined,
  chartId: string,
): Promise<ProvenanceStampResolution> {
  const existing = readPinFromState(stateJson, chartId)
  const current = await computeCurrentPinValues(chartId)
  const { drift, judgment_flags } = detectBuildDrift(existing, current)

  if (existing && !drift) {
    return { pin: existing, drift: false, judgment_flags: [] }
  }

  const pin: ProvenanceStampValues = { ...current, pinned_at: new Date().toISOString() }
  return { pin, drift, judgment_flags }
}
