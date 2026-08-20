/**
 * pariprashna/confidence/engine_tier.ts — "new engine layers surface at
 * their earned tier" (lane G3-C, PPR-03 / roadmap G3-C line 103).
 *
 * Grounded in the one REAL, checkable generation-authority mechanism this
 * codebase already has for exactly this problem — `kala_gochara_windows`'s
 * `generation` column plus `kala_gochara_authority.authoritative_generation`
 * (migration 527, read live by
 * `registry/layers/reading_checklist.ts#fetchGocharaSweep`):
 *
 *   SELECT ... FROM kala_gochara_windows w ...
 *   WHERE w.generation = COALESCE(
 *     (SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = w.chart_id),
 *     'v1')
 *
 * An absent authority row means the chart's authoritative generation is
 * `'v1'` BY DEFINITION. A newer engine generation (`'v2'`, `'v3'`,
 * `'g3_utkarsha'` — real literal values seen in
 * `src/lib/lel/prospective_ledger_w51_lel_sig.test.ts` and
 * `src/lib/components/cockpit/v2/__tests__/AssetRow_CockpitPolishR2.test.tsx`)
 * has landed rows but has NOT been promoted to authoritative for a given
 * chart until that flip happens. The SAME shape generalizes to any other
 * versioned engine layer the roadmap names (the `bo_pratijna v4.1` mention in
 * `registry/layers/L2_bodha/query_pratijna.ts` — a version string on a
 * derivation, not (yet) a DB-tracked authority split) — this module's
 * `capConfidenceTypeForEngineGeneration` takes the comparison generically
 * rather than hardcoding `kala_gochara_*` names, so it applies to any future
 * generation-tracked engine layer without modification.
 *
 * WHAT THIS ENFORCES: a claim sourced from a NON-authoritative generation
 * (one that exists in the data but has not been promoted) can never be typed
 * `deterministic_fact` or `empirically_calibrated`, regardless of how
 * confident that engine's own internal score reads — it is capped to
 * `structural_prior` at most (a structurally-present-in-the-chart claim, not
 * yet an authoritative fact or a calibrated posterior).
 *
 * NOT WIRED into `receipt/assemble.ts` in this lane: the pipeline does not
 * currently thread per-citation generation metadata (which `generation` a
 * cited signal came from) through to receipt-assembly scope, and inventing
 * that plumbing is a larger, separate change than "type this turn's already-
 * resolved citations" — adding a live DB read for it here would also violate
 * `assemble.ts`'s own "PURE with respect to I/O, no new DB read" discipline
 * (see that module's header comment). This function is built and
 * independently tested against the REAL generation semantics above so a
 * future lane that threads generation metadata through can call it directly
 * — see the report for this lane's honest disclosure of this residual.
 */

import type { ConfidenceType } from './types'

/**
 * The confidence types an unpromoted/experimental engine generation may
 * never receive, in cap-target order (first entry is the cap ceiling).
 * `structural_prior` and below remain reachable — an experimental engine
 * generation's output is still honestly "structurally present," just not
 * yet an authoritative fact or a calibrated posterior.
 */
const ENGINE_TIER_CAPPED_TYPES: readonly ConfidenceType[] = ['deterministic_fact', 'empirically_calibrated']

const ENGINE_TIER_CEILING: ConfidenceType = 'structural_prior'

export interface EngineGenerationInput {
  /** The generation tag the cited claim's row actually carries (e.g. `'v3'`, `'g3_utkarsha'`). */
  sourceGeneration: string | null
  /**
   * The chart's currently-PROMOTED/authoritative generation for this engine
   * layer (e.g. `kala_gochara_authority.authoritative_generation`, or
   * `'v1'` when that row is absent — the same COALESCE default
   * `fetchGocharaSweep` uses). `null` when authority tracking does not apply
   * to this engine layer (nothing to cap against).
   */
  authoritativeGeneration: string | null
}

/**
 * True iff the claim's source generation is a real, non-authoritative
 * (not-yet-promoted) engine generation for this chart. `false` (never caps)
 * when either generation is unknown — an honest "cannot determine" must
 * never silently suppress a legitimately-earned type either.
 */
export function isNonAuthoritativeEngineGeneration(input: EngineGenerationInput): boolean {
  if (input.sourceGeneration === null || input.authoritativeGeneration === null) return false
  return input.sourceGeneration !== input.authoritativeGeneration
}

/**
 * Cap a proposed confidence type down when its source is a non-authoritative
 * engine generation. Never raises a type, only lowers `deterministic_fact`
 * or `empirically_calibrated` to `structural_prior`; every other proposed
 * type (`structural_prior`, `classical_prior`, `unresolved`) passes through
 * unchanged, since none of those claim a tier an unpromoted generation could
 * fail to earn.
 */
export function capConfidenceTypeForEngineGeneration(
  proposed: ConfidenceType,
  generation: EngineGenerationInput,
): ConfidenceType {
  if (!ENGINE_TIER_CAPPED_TYPES.includes(proposed)) return proposed
  if (!isNonAuthoritativeEngineGeneration(generation)) return proposed
  return ENGINE_TIER_CEILING
}
