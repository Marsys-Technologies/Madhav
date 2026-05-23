/**
 * tier_catalog.ts — MCPT v3.2 Phase 6b: Tier-aware tool catalog filtering.
 *
 * getCatalogForTier returns a tier-filtered + annotated slice of the full
 * tool catalog. It is a pure function: it never mutates the input array and
 * never touches any handler references.
 *
 * Tier rules (per MCPT v3.2 Phase 6 spec):
 *
 *   client      — ops tools hidden (data_coverage, tool_health, log_prediction,
 *                 record_outcome, flag_disagreement). Synthesis tools present unchanged.
 *
 *   acharya     — full catalog; holistic_bundle + multi_school_bundle descriptions
 *                 annotated with " [Acharya-review-grade synthesis. Use to verify the fact layer.]"
 *
 *   super_admin — full catalog, default ordering; holistic_bundle + multi_school_bundle
 *                 descriptions annotated with " Server-side synthesized — prefer
 *                 chart_summary + your own synthesis unless you specifically want a
 *                 pre-baked render."
 *
 * Ordering contract (non-client tiers):
 *   1. chart_summary (Tier 1 super-endpoint)
 *   2. Surgical primitives: query_chart_facts, query_signals, query_dasha_periods,
 *      query_panchanga, query_ephemeris, query_transit_event, lel_query,
 *      vector_search, get_cgm_subgraph, cross_school_lookup, read_asset, read_classical_text
 *   3. Synthesis bundles: holistic_bundle, multi_school_bundle
 *   4. Observability: get_trace, list_recent_queries
 *   5. Ops tools: data_coverage, tool_health, log_prediction, record_outcome, flag_disagreement
 *
 * For client tier the ordering is the same minus ops tools.
 *
 * Handler references are NEVER modified — descriptions only. holistic_bundle and
 * multi_school_bundle output is byte-equal across tiers for the same tool call.
 */

import type { ToolCatalogEntry } from './catalog.js'

// ── Constants ─────────────────────────────────────────────────────────────────

/** Tools hidden from client tier. */
export const OPS_TOOLS: ReadonlySet<string> = new Set([
  'data_coverage',
  'tool_health',
  'log_prediction',
  'record_outcome',
  'flag_disagreement',
])

/** Synthesis tools that receive tier-specific description annotations. */
export const SYNTHESIS_TOOLS: ReadonlySet<string> = new Set([
  'holistic_bundle',
  'multi_school_bundle',
])

/** Canonical tool ordering. Tools absent from allTools are silently skipped. */
const CANONICAL_ORDER: readonly string[] = [
  // Tier 1: super-endpoint
  'chart_summary',
  // Tier 2 surgical (ordered by call frequency / specificity)
  'query_chart_facts',
  'query_signals',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  'vector_search',
  'get_cgm_subgraph',
  'cross_school_lookup',
  'read_asset',
  'read_classical_text',
  // Tier 3 synthesis bundles
  'holistic_bundle',
  'multi_school_bundle',
  // Tier 4 observability
  'get_trace',
  'list_recent_queries',
  // Tier 5 ops
  'data_coverage',
  'tool_health',
  'log_prediction',
  'record_outcome',
  'flag_disagreement',
]

const ACHARYA_SYNTHESIS_SUFFIX =
  ' [Acharya-review-grade synthesis. Use to verify the fact layer.]'

const SUPER_ADMIN_SYNTHESIS_SUFFIX =
  ' Server-side synthesized — prefer chart_summary + your own synthesis unless you specifically want a pre-baked render.'

// ── Core function ─────────────────────────────────────────────────────────────

/**
 * Returns the tier-filtered, tier-annotated catalog slice.
 *
 * @param tier           The resolved audience_tier from the Principal.
 * @param allTools       The full flat catalog (ToolCatalogEntry[]). Not mutated.
 * @returns              A new array — same ToolCatalogEntry shape, safe to iterate.
 */
export function getCatalogForTier(
  tier: string,
  allTools: ToolCatalogEntry[],
): ToolCatalogEntry[] {
  // Step 1: Build a lookup map from the input array.
  const byName = new Map<string, ToolCatalogEntry>(allTools.map(t => [t.name, t]))

  // Step 2: Walk canonical order; skip unknowns + tier-gated ops tools for client.
  const result: ToolCatalogEntry[] = []

  for (const name of CANONICAL_ORDER) {
    const entry = byName.get(name)
    if (!entry) continue // tool not in allTools (future-proofing)

    // Client tier: hide ops tools entirely.
    if (tier === 'client' && OPS_TOOLS.has(name)) continue

    // Annotate synthesis tools for acharya tier.
    if (tier === 'acharya' && SYNTHESIS_TOOLS.has(name)) {
      result.push({ ...entry, description: entry.description + ACHARYA_SYNTHESIS_SUFFIX })
      continue
    }

    // Annotate synthesis tools for super_admin tier.
    if (tier === 'super_admin' && SYNTHESIS_TOOLS.has(name)) {
      result.push({ ...entry, description: entry.description + SUPER_ADMIN_SYNTHESIS_SUFFIX })
      continue
    }

    // Default: pass through as-is.
    result.push(entry)
  }

  // Step 3: Append any tools not in CANONICAL_ORDER (future additions) in input order.
  const canonicalSet = new Set(CANONICAL_ORDER)
  for (const entry of allTools) {
    if (!canonicalSet.has(entry.name)) {
      if (tier === 'client' && OPS_TOOLS.has(entry.name)) continue
      result.push(entry)
    }
  }

  return result
}
