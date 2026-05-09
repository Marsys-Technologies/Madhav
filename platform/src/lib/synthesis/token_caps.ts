/**
 * Pure token-cap helpers used by the synthesis orchestrator. Lives in its own
 * module so unit tests can import without pulling in the server-only synthesis
 * orchestrator graph.
 */

/**
 * Per-style synthesis output cap. brief/client/acharya define increasing
 * verbosity ceilings; the model max can lower further but never raise.
 */
export const STYLE_OUTPUT_CAP: Record<string, number> = {
  brief:   1200,
  client:  3500,
  acharya: 8000,
}

/**
 * P5 D.5.2 — per-query-class output cap. Never raises a cap; only lowers
 * when the class shape is naturally compact (factual lookups, remedial
 * prescriptions). Holistic + discovery stay at 8000.
 */
export const CLASS_TOKEN_CAP: Record<string, number> = {
  factual:       1500,
  signal_recall: 2000,
  temporal:      2500,
  remedial:      3000,
  cross_domain:  4000,
  holistic:      8000,
  discovery:     8000,
  predictive:    4000,
}

/**
 * Returns the effective `maxOutputTokens` to pass to streamText: the minimum
 * of the style cap, query-class cap, and the model's own max-output ceiling
 * (when known). Falls back to the style cap when modelMax is undefined.
 */
export function computeEffectiveMaxTokens(
  styleCap: number,
  classCap: number,
  modelMax: number | undefined,
): number {
  return Math.min(styleCap, classCap, modelMax ?? styleCap)
}
