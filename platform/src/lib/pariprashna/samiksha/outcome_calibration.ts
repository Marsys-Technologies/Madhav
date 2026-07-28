/**
 * SAMĪKṢĀ outcome calibration — PB-3 (SAMĪKṢĀ) lane L-5.
 *
 * The PURE, isomorphic half of L-5's outcome-recording deliverable: the deterministic Brier
 * computation and the calibration-write *intent* builder. NO `server-only`, NO `pg`, NO
 * `@/lib/db` — so it is unit-testable in isolation exactly like schema.ts (the PB-2
 * false-confidence lesson: the thing you assert on must be the thing that ships, not a
 * test-local reimplementation). The DB-touching orchestration lives in outcome_recorder.ts.
 *
 * ── Why this module does NOT write `mimamsa_calibration` ──────────────────────────────────
 * BRIEF_PB-3 §F1 Lane L-5 specifies "upsert into mimamsa_calibration, with source_citation =
 * the ledger row id". That instruction describes the RETIRED MI-5-3 prototype calibration
 * schema (id, technique, ayanamsha_id, brier_score, sample_size, source_citation, computed_at
 * — 0001_brahma_baseline.sql), which was superseded WITHOUT a tracked migration by migration
 * 348's mi_pramana per-match scoring schema and then confirmed dead + dropped by PR #725 /
 * migration 464 (CR-115/CR-128). The LIVE `mimamsa_calibration` table has PRIMARY KEY
 * (chart_id, match_id) and carries NONE of `source_citation`, `brier_score`, or a scalar
 * `confidence` column (verified against the deployed DB, PB-3 L-5 BIND). Writing an INSERT
 * against those columns would RECREATE the exact `outcome.py` phantom-column defect this lane
 * was chartered to diagnose. So this module computes the Brier and assembles the fully-formed
 * `CalibrationWriteIntent` (source_citation = ledger row id — "the ledger is the citation",
 * §14.5) but does NOT persist it; the persistence seam is PARKED pending a Pratinidhi MEMO on
 * the calibration schema. See PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md.
 */

import type { ConfidenceBand, LedgerRow, Outcome } from './schema'

// ---------------------------------------------------------------------------
// Outcome → Brier numeric value.
// ---------------------------------------------------------------------------

/** The default numeric Brier value for each qualitative outcome.
 *  'unverifiable' → null (Brier-EXCLUDED, per §14.4 / migration 470's exclusion CHECK).
 *  'partial' has no single canonical value; DEFAULT_PARTIAL_VALUE is the neutral default the
 *  Resolve surface may override with an operator-supplied fraction. */
export const DEFAULT_PARTIAL_VALUE = 0.5

export function outcomeToValue(
  outcome: Outcome,
  partialValue: number = DEFAULT_PARTIAL_VALUE,
): number | null {
  switch (outcome) {
    case 'happened':
      return 1.0
    case 'did_not_happen':
      return 0.0
    case 'partial':
      return partialValue
    case 'unverifiable':
      return null // Brier-excluded
  }
}

// ---------------------------------------------------------------------------
// Numrange literal → ConfidenceBand. (The DAL returns confidence as the raw Postgres
// numrange literal string, e.g. "[0.55,0.7)"; this parses it back to {low, high}.)
// ---------------------------------------------------------------------------

const NUMRANGE_RE = /^([[(])\s*(-?\d*\.?\d+)?\s*,\s*(-?\d*\.?\d+)?\s*([\])])$/

/**
 * Parse a Postgres numrange literal (`[0.55,0.7)`, `(0.5,0.8]`, `empty`, or null) to a
 * `{low, high}` band. Returns null for an absent / empty / unbounded range — an honest null,
 * never a fabricated default confidence. The point estimate downstream is the band midpoint;
 * bounds are treated as their numeric values regardless of inclusive/exclusive brackets (a
 * [0,1] probability band is dense — the bracket does not move the mean).
 */
export function parseNumrangeLiteral(literal: string | null | undefined): ConfidenceBand | null {
  if (!literal) return null
  const s = literal.trim()
  if (s === '' || s.toLowerCase() === 'empty') return null
  const m = NUMRANGE_RE.exec(s)
  if (!m) return null
  const lo = m[2]
  const hi = m[3]
  if (lo === undefined || hi === undefined) return null // unbounded on a side → no point estimate
  const low = Number(lo)
  const high = Number(hi)
  if (!Number.isFinite(low) || !Number.isFinite(high)) return null
  return { low, high }
}

/** Point estimate of a confidence band = its midpoint, clamped to [0,1]. */
export function confidencePoint(band: ConfidenceBand | null): number | null {
  if (!band) return null
  const mid = (band.low + band.high) / 2
  if (!Number.isFinite(mid)) return null
  return Math.min(1, Math.max(0, mid))
}

// ---------------------------------------------------------------------------
// Brier score.
// ---------------------------------------------------------------------------

export interface BrierResult {
  /** Point estimate of the stated confidence (band midpoint), or null if no band. */
  confidence_point: number | null
  /** Numeric outcome value in [0,1], or null when Brier-excluded ('unverifiable'). */
  outcome_value: number | null
  /** Brier score (confidence_point − outcome_value)² in [0,1], or null when either input is null. */
  brier: number | null
}

/**
 * Compute the Brier score for a resolved prediction: `(confidence − outcome)²`, the exact
 * formula the retired sidecar `compute_brier_score()` used and the ledger schema documents.
 *
 * Honest-null discipline: when the confidence band is absent or the outcome is Brier-excluded
 * ('unverifiable'), `brier` is null — never a plausible-looking substitute.
 */
export function computeBrier(
  band: ConfidenceBand | null,
  outcome: Outcome,
  partialValue: number = DEFAULT_PARTIAL_VALUE,
): BrierResult {
  const point = confidencePoint(band)
  const value = outcomeToValue(outcome, partialValue)
  const brier = point === null || value === null ? null : (point - value) ** 2
  return { confidence_point: point, outcome_value: value, brier }
}

// ---------------------------------------------------------------------------
// Calibration-write intent — the payload the PARKED mimamsa_calibration persistence consumes.
// ---------------------------------------------------------------------------

/**
 * The fully-formed calibration record a conversational outcome produces. Its provenance
 * (`source_citation`) is the ledger row id itself — "the ledger IS the citation" (§14.5): the
 * calibration point traces back to `brahma_mimamsa_prediction_ledger`, NOT to
 * `mimamsa_predictions` or `phala_anchors`. This object is RETURNED, not persisted; see the
 * module header + PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md for why persistence is parked.
 */
export interface CalibrationWriteIntent {
  chart_id: string
  /** The ledger row id. §14.5 "the ledger is the citation." */
  source_citation: string
  /** Same value, explicitly named for the parked writer's clarity. */
  prediction_ledger_row_id: string
  domain: string | null
  confidence_point: number | null
  outcome: Outcome
  outcome_value: number | null
  brier: number | null
  /** True when this row is Brier-excluded (outcome 'unverifiable'); it counts as coverage, not skill. */
  brier_excluded: boolean
  technique_refs: string[]
  grounding_fact_ids: string[]
  scored_at: string
}

/** Assemble the calibration-write intent from a resolved ledger row + its computed Brier. */
export function buildCalibrationIntent(
  row: Pick<
    LedgerRow,
    'id' | 'chart_id' | 'domain' | 'outcome' | 'technique_refs' | 'grounding_fact_ids'
  >,
  brier: BrierResult,
  scoredAt: string = new Date().toISOString(),
): CalibrationWriteIntent {
  const outcome = (row.outcome ?? 'unverifiable') as Outcome
  return {
    chart_id: row.chart_id,
    source_citation: row.id,
    prediction_ledger_row_id: row.id,
    domain: row.domain,
    confidence_point: brier.confidence_point,
    outcome,
    outcome_value: brier.outcome_value,
    brier: brier.brier,
    brier_excluded: brier.brier === null,
    technique_refs: row.technique_refs ?? [],
    grounding_fact_ids: row.grounding_fact_ids ?? [],
    scored_at: scoredAt,
  }
}
