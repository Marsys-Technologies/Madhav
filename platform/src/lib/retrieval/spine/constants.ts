/**
 * spine/constants.ts — shared constants for the "spine bundle" mechanism.
 *
 * See compute_spine_bundle.ts's module doc for the full definition. Short version:
 * a spine bundle is the pre-joined chain
 *   signal (bodha_msr_signals) → activation windows (kala_activation)
 *     → phala anchors (phala_anchors) → calibration (mimamsa_calibration/mimamsa_multipliers)
 * per (chart, ayanamsha, domain), per RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §8 item 11.
 */

import { CANONICAL_DOMAINS } from '@/lib/domain_vocabulary'
import type { CanonicalDomain } from '@/lib/domain_vocabulary'

/**
 * The domain vocabulary spine bundles materialize over. Matches the free-text
 * `domain` values already used by phala_anchors / bodha_msr_signals.domains_affected_array
 * filters elsewhere in the registry.
 *
 * ADHIṢṬHĀNA Lane A7: previously a local literal (6 members + 'other'), one of 4 divergent
 * TS domain vocabularies. Now sourced from the canonical 13-domain SSoT
 * (`brahmagyan/domain_vocabulary.py` / `@/lib/domain_vocabulary`) rather than a stale
 * 7-value subset — phala_anchors' own DB CHECK constraint (migration 386) already governs
 * all 13 domains, so `materializeAllDomainsForChart` now correctly materializes a bundle per
 * canonical domain instead of silently skipping the 6 domains this file's old literal never
 * covered (progeny/education/family/residence/travel/transition/general). No CHECK constraint
 * on `bodha_spine_bundles.domain` and no caller validates against a fixed 7-value set (verified
 * before this change), so widening is behavior-additive, not behavior-breaking.
 */
export const SPINE_DOMAINS = CANONICAL_DOMAINS

export type SpineDomain = CanonicalDomain

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
