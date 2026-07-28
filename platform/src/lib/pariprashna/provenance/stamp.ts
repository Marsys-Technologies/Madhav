/**
 * Paripraśna Build — PB-2 (SMṚTI), Lane M-6: per-turn provenance stamp.
 * ============================================================================
 * D-16 (binding architectural decision): provenance — `build_id`,
 * `priors_version`, `formula_versions`, `ranking_config`, `now_context_date` —
 * is data that comes OUT of an answer as a record of what produced it. It must
 * NEVER be an INPUT the engine reasons from, and it must NEVER be shown
 * anywhere ambient in the UI (not header, not dock footer — audit-drawer-only,
 * PB-1 design plan ruling 8c). D-16(d): a later PB-3 ledger row COPIES this
 * stamp at confirmation time, never references/joins it live — this module's
 * job is to make the stamp exist, be written per-turn, and be readable via a
 * clean read API. It stores NOTHING a second time itself.
 *
 * Storage: the stamp is an immutable sub-object written into
 * `conversation_messages.metadata_json.provenance_stamp` on every persisted
 * assistant turn (no schema change — the existing free-form jsonb column).
 * Each turn's stamp is a frozen snapshot; it is never mutated in place, unlike
 * the mutable `mcp_sessions.state_json`-keyed session pin below.
 *
 * REUSE, NOT REINVENTION: `src/lib/retrieval/provenance_stamp.ts` (R5 W4,
 * renamed from `session_pin.ts` per this same D-16 ruling — RC-13) already
 * defines and LIVE-COMPUTES all five stamp fields for the MCP session-pin
 * surface: `build_id` from `build_runs` (the chart-level build-orchestration
 * table, migration 171 — NOT an app-deploy/git-SHA identifier; a chart
 * "rebuild" in this codebase means a `build_runs` row, per CLAUDE.md's L0–L5
 * build arc), `priors_version` from `ranking/priors_config.ts`'s live
 * `PRIORS_VERSION` constant, `ranking_config` as `{mode: 'composite_v1'}`
 * (the live composite ranker), and `formula_versions.salience_formula_ver` as
 * an honest `null` (no such column exists on `build_runs` yet — B.10, never
 * fabricated). This module WRAPS that existing computation
 * (`computeCurrentPinValues`) into an immutable per-turn shape and adds the
 * per-turn (not per-session) drift comparison this lane requires. It does
 * NOT modify `provenance_stamp.ts` — that module's own mutable
 * `mcp_sessions.state_json` storage path is a separate, already-shipped
 * surface and stays untouched.
 */

import 'server-only'
import { query } from '@/lib/db/client'
import { computeCurrentPinValues } from '@/lib/retrieval/provenance_stamp'
import { EDGE_STATE_LABELS } from '@/lib/pariprashna/lexicon'

// ── Types ────────────────────────────────────────────────────────────────────

/** Mirrors `ProvenanceStampFormulaVersions` (provenance_stamp.ts) — see that
 *  module's doc comment for why `salience_formula_ver` is honestly null today. */
export interface TurnProvenanceFormulaVersions {
  salience_formula_ver: string | null
}

/** Mirrors `ProvenanceStampRankingConfig` (provenance_stamp.ts). */
export interface TurnProvenanceRankingConfig {
  mode: string
}

/**
 * The immutable per-turn provenance stamp. Exactly the five D-16 fields plus
 * `computed_at` (call-time metadata — when THIS turn's stamp was captured;
 * mirrors `pinned_at` in provenance_stamp.ts). Two of the five are LIVE,
 * code-tracked values (`build_id`, `priors_version`), one is a live constant
 * object (`ranking_config`), one is a genuine wall-clock read
 * (`now_context_date`), and one is an honest documented placeholder
 * (`formula_versions.salience_formula_ver` — see module doc above).
 */
export interface TurnProvenanceStamp {
  build_id: string | null
  priors_version: string
  formula_versions: TurnProvenanceFormulaVersions
  ranking_config: TurnProvenanceRankingConfig
  /** Genuine wall-clock date the turn ran (ISO yyyy-mm-dd), never a stub. */
  now_context_date: string
  /** ISO timestamp of when this stamp was computed — audit metadata, not one
   *  of the five D-16 fields itself. */
  computed_at: string
}

const STAMP_METADATA_KEY = 'provenance_stamp' as const

// ── Compute (write path) ────────────────────────────────────────────────────

/**
 * Compute the provenance stamp for the CURRENT turn, from live sources only
 * (never re-derives an L1/L2+ value — B.10/N.5; this is metadata ABOUT the
 * serving process, not a chart fact). Safe to call once per persisted turn.
 */
export async function computeTurnProvenanceStamp(chartId: string): Promise<TurnProvenanceStamp> {
  const current = await computeCurrentPinValues(chartId)
  return {
    build_id: current.build_id,
    priors_version: current.priors_version,
    formula_versions: current.formula_versions,
    ranking_config: current.ranking_config,
    now_context_date: current.now_context_date,
    computed_at: new Date().toISOString(),
  }
}

/**
 * Attach the stamp to a `metadata_json` object as an additive sub-object
 * (never replaces existing keys — e.g. the route's `custom` block). This is
 * the ONLY place the stamp is written; it lands in
 * `conversation_messages.metadata_json.provenance_stamp` via whichever
 * write-through persists the assistant row (PB-2 lane M-2's `writeTurn` for
 * the pariprashna route as of this wave) — no new persistence path of its
 * own, no schema change (per M-6 file scope: no migration owned by this lane).
 */
export function withProvenanceStamp(
  metadata: Record<string, unknown>,
  stamp: TurnProvenanceStamp,
): Record<string, unknown> {
  return { ...metadata, [STAMP_METADATA_KEY]: stamp }
}

// ── Read (PB-3 ledger-confirmation surface) ─────────────────────────────────

function isTurnProvenanceStamp(value: unknown): value is TurnProvenanceStamp {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  return (
    'priors_version' in v &&
    typeof v.priors_version === 'string' &&
    'now_context_date' in v &&
    typeof v.now_context_date === 'string' &&
    'ranking_config' in v &&
    typeof v.ranking_config === 'object' &&
    'formula_versions' in v &&
    typeof v.formula_versions === 'object'
  )
}

/**
 * Read the most recently PERSISTED assistant turn's provenance stamp for a
 * conversation — the clean read API PB-3's future ledger-confirmation code
 * calls to COPY the stamp fields onto a ledger row at confirmation time
 * (D-16(d): copy, never a live reference/join). Returns `null` when the
 * conversation has no prior stamped assistant turn (first turn, or a turn
 * persisted before this lane shipped).
 *
 * Also doubles as the "previous turn" side of this lane's own per-turn drift
 * comparison (`detectTurnProvenanceDrift`) — call this BEFORE persisting the
 * current turn's row so it genuinely returns the prior turn, not the one
 * about to be written.
 */
export async function getLastTurnStamp(conversationId: string): Promise<TurnProvenanceStamp | null> {
  const { rows } = await query<{ metadata_json: unknown }>(
    `SELECT metadata_json
       FROM conversation_messages
      WHERE conversation_id = $1 AND role = 'assistant'
      ORDER BY created_at DESC
      LIMIT 1`,
    [conversationId],
  )
  const metadata = rows[0]?.metadata_json as Record<string, unknown> | null | undefined
  const candidate = metadata?.[STAMP_METADATA_KEY]
  return isTurnProvenanceStamp(candidate) ? candidate : null
}

// ── Drift detection (consecutive-turn comparison only) ──────────────────────

export interface TurnProvenanceDriftResult {
  drift: boolean
  /** The exact PB-1 lexicon string (EDGE_STATE_LABELS.chart_rebuilt) — never
   *  invented copy. Null when there is no drift. */
  edge_state_label: string | null
  changed_fields: string[]
}

/**
 * Compare the CURRENT turn's stamp against the conversation's PREVIOUS turn's
 * stamp — consecutive-turn comparison only, no shared session state beyond
 * the single `getLastTurnStamp` read. Only `build_id` is a drift signal here:
 * `priors_version` and `ranking_config` are process-wide constants that only
 * change on a deploy (same reasoning `provenance_stamp.ts#detectBuildDrift`
 * already documents for its own, session-scoped comparison) — an in-flight
 * conversation is not expected to react to those mid-thread. A `build_id`
 * change means the CHART's data was rebuilt since the last turn (a
 * `build_runs` row completed) — the one case PB-1's lexicon already has a
 * reader-facing edge-state string for.
 */
export function detectTurnProvenanceDrift(
  previous: TurnProvenanceStamp | null,
  current: TurnProvenanceStamp,
): TurnProvenanceDriftResult {
  if (!previous) return { drift: false, edge_state_label: null, changed_fields: [] }

  const changed_fields: string[] = []
  if (previous.build_id !== current.build_id) changed_fields.push('build_id')

  if (changed_fields.length === 0) {
    return { drift: false, edge_state_label: null, changed_fields: [] }
  }
  return {
    drift: true,
    // Reused verbatim from the PB-1 closed lexicon — never invented copy.
    edge_state_label: EDGE_STATE_LABELS.chart_rebuilt,
    changed_fields,
  }
}
