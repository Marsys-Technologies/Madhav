/**
 * bundles/index.ts — Bundle composition rules + public API.
 *
 * Two bundles are available:
 *   - holistic_bundle: 8-tool parallel read across MSR/CGM/UCN/RM/CDLM/LEL/Panchang/Dasha
 *   - multi_school_bundle: cross-school convergence check + per-school evidence
 *
 * Both bundles:
 *   - Use deterministic parallel fan-out (Promise.allSettled)
 *   - Have per-sub-tool error isolation (timeout or error → errored slot, not bundle failure)
 *   - Cache results for 5 minutes (content-addressable by query + params + tier + chart_id)
 *   - Optionally emit SSE events via onEvent callback
 *   - Make NO LLM calls
 *
 * MCPT v3.1.0-S2
 */

export { executeHolisticBundle } from './holistic_bundle.js'
export { executeMultiSchoolBundle } from './multi_school_bundle.js'
export { computeCacheKey, cacheLookup, cacheStore } from './cache.js'

export type { HolisticBundleParams, HolisticBundleEnvelope, BundleEvent } from './holistic_bundle.js'
export type {
  MultiSchoolBundleParams,
  MultiSchoolBundleEnvelope,
  MultiSchoolBundleEvent,
  SchoolName,
} from './multi_school_bundle.js'

// ── Composition rules ──────────────────────────────────────────────────────────

/**
 * COMPOSITION RULES (non-normative; for documentation):
 *
 * 1. Use holistic_bundle when: you need a broad cross-layer read before asking
 *    a synthesis question; equivalent to calling 8 primitives manually.
 *    Subset filter reduces tool count for targeted reads.
 *
 * 2. Use multi_school_bundle when: the question explicitly concerns multi-school
 *    convergence or divergence on a specific astrological claim.
 *
 * 3. Do NOT use bundles for: simple single-domain queries (prefer primitive);
 *    when the LLM already has sufficient context; real-time/streaming synthesis
 *    (bundles only emit when all sub-tools settle).
 *
 * 4. Bundle → primitive fallback: if the bundle is too slow (>8s total),
 *    call the relevant primitives directly with targeted params.
 *
 * 5. Bundle cache: served_from_cache: true means the response is ≤5 min old;
 *    signal_ids_available[] may not reflect real-time changes. For fresh data,
 *    bypass cache by using a different query_text.
 */
