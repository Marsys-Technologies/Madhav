/**
 * spine/constants.ts — shared constants for the "spine bundle" mechanism.
 *
 * See compute_spine_bundle.ts's module doc for the full definition. Short version:
 * a spine bundle is the pre-joined chain
 *   signal (bodha_msr_signals) → activation windows (kala_activation)
 *     → phala anchors (phala_anchors) → calibration (mimamsa_calibration/mimamsa_multipliers)
 * per (chart, ayanamsha, domain), per RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §8 item 11.
 */

/**
 * The domain vocabulary spine bundles materialize over. Matches the free-text
 * `domain` values already used by phala_anchors / bodha_msr_signals.domains_affected_array
 * filters elsewhere in the registry (query_predictive_anchors.ts's own doc comment lists
 * the same 7 values as phala_anchors' domain vocabulary).
 */
export const SPINE_DOMAINS = [
  'career',
  'wealth',
  'relationship',
  'health',
  'character',
  'spirituality',
  'other',
] as const

export type SpineDomain = typeof SPINE_DOMAINS[number]

/** Default number of top-salience signals a spine bundle carries per domain. */
export const DEFAULT_SPINE_TOP_K = 15

/** Ceiling — a caller-requested top_k above this is clamped (mirrors sibling capabilities). */
export const MAX_SPINE_TOP_K = 50

/**
 * The four asset_registry asset_ids whose last_built_at feeds the staleness marker
 * (source_asset_marker column, migration 463). One writer per layer in the chain:
 *   bo_laksana   → bodha_msr_signals   (L2 signal root)
 *   ka_kalasutra → kala_activation      (L3 activation windows)
 *   ph_nimitta   → phala_anchors        (L4 predictive anchors)
 *   mi_pramana   → mimamsa_calibration + mimamsa_reliability (L5 calibration)
 */
export const SPINE_SOURCE_ASSET_IDS = [
  'bo_laksana',
  'ka_kalasutra',
  'ph_nimitta',
  'mi_pramana',
] as const
