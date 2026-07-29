/**
 * SAMĪKṢĀ Brier eligibility — PB-3 (SAMĪKṢĀ) lane L-3.
 *
 * The single, named predicate that decides whether a resolved ledger row participates in
 * Brier scoring. BRIEF_PB-3 §F1/§G-6: "can't-tell → `unverifiable`, Brier-EXCLUDED, counted
 * separately as an honesty metric." The exclusion is enforced in THREE independent places,
 * by design (defence in depth), and this module is the read/query-layer one:
 *
 *   1. DB CHECK `bmpl_unverifiable_has_no_value` (migration 470): an `unverifiable` outcome
 *      can never carry an `outcome_value` — so an excluded row structurally has NULL value.
 *   2. DAL `recordOutcome` (writer.ts): forces `outcome_value = null` for the unverifiable
 *      path before the write.
 *   3. THIS predicate: a row is Brier-eligible iff its outcome is a scorable resolution AND it
 *      carries a numeric value. `unverifiable` (and any not-yet-resolved row) is excluded.
 *
 * L-3 owns (3) because the brief says: "if unclear, treat this as your job to make correct at
 * the query/read layer even if L-1's schema doesn't enforce it structurally." L-1's schema
 * DOES enforce it structurally (the CHECK), so (3) is a belt-and-braces query-layer guarantee
 * that any Brier consumer reaches through the SAME named predicate rather than open-coding a
 * `WHERE outcome IS NOT 'unverifiable'` that could drift.
 *
 * Isomorphic (no server-only) so it is unit-testable with zero DB dependency and reusable by
 * L-5's calibration path.
 */

import type { LedgerRow, Outcome } from './schema'

/** The outcomes that CONTRIBUTE a Brier data point (a numeric value scored against confidence). */
export const BRIER_SCORABLE_OUTCOMES: readonly Outcome[] = ['happened', 'did_not_happen', 'partial'] as const

/**
 * The Brier-EXCLUDED outcome. `unverifiable` (can't-tell) is recorded as an honesty metric but
 * never scored — it carries no `outcome_value` and must never enter a Brier average.
 */
export const BRIER_EXCLUDED_OUTCOME: Outcome = 'unverifiable'

/**
 * True iff this row's outcome is the Brier-excluded marker. A row with no recorded outcome yet
 * is NOT "excluded" (it is simply unresolved) — `isBrierExcluded` is specifically the
 * can't-tell exclusion, so it returns false for a null outcome and true only for
 * `unverifiable`.
 */
export function isBrierExcluded(row: Pick<LedgerRow, 'outcome'>): boolean {
  return row.outcome === BRIER_EXCLUDED_OUTCOME
}

/**
 * True iff this row contributes a Brier data point: it has a scorable outcome AND a numeric
 * value in [0,1]. This is the positive predicate a calibration pass filters on; an
 * `unverifiable` row fails it on BOTH counts (not a scorable outcome, and value is null).
 */
export function isBrierEligible(row: Pick<LedgerRow, 'outcome' | 'outcome_value'>): boolean {
  if (row.outcome == null) return false
  if (!BRIER_SCORABLE_OUTCOMES.includes(row.outcome)) return false
  return row.outcome_value != null && row.outcome_value >= 0 && row.outcome_value <= 1
}

/** Split resolved rows into the Brier-scored set and the (separately counted) excluded set. */
export function partitionForBrier<T extends Pick<LedgerRow, 'outcome' | 'outcome_value'>>(
  rows: T[],
): { eligible: T[]; excluded: T[] } {
  const eligible: T[] = []
  const excluded: T[] = []
  for (const r of rows) {
    if (isBrierEligible(r)) eligible.push(r)
    else if (isBrierExcluded(r)) excluded.push(r)
  }
  return { eligible, excluded }
}

/**
 * The SQL predicate fragment a Brier query uses to select ONLY eligible rows — the query-layer
 * twin of `isBrierEligible`. Kept as a constant so a consumer cannot open-code a subtly-wrong
 * variant. Parameterless (references columns directly): `WHERE ${BRIER_ELIGIBLE_SQL}`.
 */
export const BRIER_ELIGIBLE_SQL =
  `outcome IN ('happened','did_not_happen','partial') AND outcome_value IS NOT NULL` as const
