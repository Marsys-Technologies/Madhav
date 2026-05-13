/**
 * Pure token-cap helpers used by the synthesis orchestrator. Lives in its own
 * module so unit tests can import without pulling in the server-only synthesis
 * orchestrator graph.
 */

/**
 * Per-style synthesis output cap. All styles set to model-max passthrough
 * (65536 exceeds every registered model's maxOutputTokens, so
 * computeEffectiveMaxTokens will always resolve to the model's own ceiling).
 */
export const STYLE_OUTPUT_CAP: Record<string, number> = {
  brief:   65536,
  client:  65536,
  acharya: 65536,
}

/**
 * Per-query-class output cap — restored to model-max passthrough.
 * computeEffectiveMaxTokens resolves to modelMeta.maxOutputTokens.
 */
export const CLASS_TOKEN_CAP: Record<string, number> = {
  factual:       65536,
  signal_recall: 65536,
  temporal:      65536,
  remedial:      65536,
  cross_domain:  65536,
  holistic:      65536,
  discovery:     65536,
  predictive:    65536,
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
