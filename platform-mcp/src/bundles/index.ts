/**
 * bundles/index.ts — Bundle composition rules + public API.
 *
 * One bundle is implemented here:
 *   - holistic_bundle: 8-tool parallel read across MSR/CGM/UCN/RM/CDLM/LEL/Panchang/Dasha
 *   (the multi_school_bundle copy that lived here had no live importer and was removed;
 *    the live multi_school_bundle implementation is platform/src/lib/mcp/bundle_adapters.ts)
 *
 * The bundle:
 *   - Use deterministic parallel fan-out (Promise.allSettled)
 *   - Have per-sub-tool error isolation (timeout or error → errored slot, not bundle failure)
 *   - Cache results for 5 minutes (content-addressable by query + params + tier + chart_id)
 *   - Optionally emit SSE events via onEvent callback
 *   - Make NO LLM calls
 *
 * MCPT v3.1.0-S2
 */

export { executeHolisticBundle } from './holistic_bundle.js'
export { computeCacheKey, cacheLookup, cacheStore } from './cache.js'

export type { HolisticBundleParams, HolisticBundleEnvelope, BundleEvent } from './holistic_bundle.js'

// ── Composition rules ──────────────────────────────────────────────────────────

/**
 * COMPOSITION RULES (non-normative; for documentation):
 *
 * 1. Use holistic_bundle when: you need a broad cross-layer read before asking
 *    a synthesis question; equivalent to calling 8 primitives manually.
 *    Subset filter reduces tool count for targeted reads.
 *
 * 2. Do NOT use bundles for: simple single-domain queries (prefer primitive);
 *    when the LLM already has sufficient context; real-time/streaming synthesis
 *    (bundles only emit when all sub-tools settle).
 *
 * 3. Bundle → primitive fallback: if the bundle is too slow (>8s total),
 *    call the relevant primitives directly with targeted params.
 *
 * 4. Bundle cache: served_from_cache: true means the response is ≤5 min old;
 *    signal_ids_available[] may not reflect real-time changes. For fresh data,
 *    bypass cache by using a different query_text.
 */
