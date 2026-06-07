/**
 * adapters/bulk_context/prefetcher.ts
 *
 * For a tagged intent, pre-fetch resources by priority.
 * Uses pre_fetch_priority from capability llm_hints to order fetches.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities, getCapability } from '../../registry'
import type { QueryIntent } from './intent_classifier'
import type { CapabilityContext } from '../../registry/types'

export interface PrefetchResult {
  uri: string
  data: unknown
  latency_ms: number
  error?: string
}

/**
 * Map query intent to capability URIs that should be pre-fetched.
 * Resources + high-priority tools are candidates.
 */
function getPreFetchCandidates(intent: QueryIntent): string[] {
  // Always include asset registry
  const base = [
    'marsys://resource/asset-registry/L0',
  ]

  // Intent-specific additions
  const intentMap: Partial<Record<QueryIntent, string[]>> = {
    chart_overview: [
      'marsys://resource/asset-registry/all',
      'marsys://tool/L0/list_entities',
    ],
    dasha_timing: [
      'marsys://tool/L0/list_entities',
    ],
    remedy_lookup: [
      'marsys://tool/L0/list_entities',
    ],
  }

  return [...base, ...(intentMap[intent] ?? [])]
}

/**
 * Pre-fetch all high-priority resources for a given intent.
 * Results are returned in priority order (highest first).
 */
export async function prefetchForIntent(
  intent: QueryIntent,
  ctx: CapabilityContext
): Promise<PrefetchResult[]> {
  // Get all capabilities ordered by pre_fetch_priority
  const allCaps = listCapabilities()
  const prioritized = allCaps
    .filter(c => (c.llm_hints.bulk_context?.pre_fetch_priority ?? 0) > 0)
    .sort((a, b) =>
      (b.llm_hints.bulk_context?.pre_fetch_priority ?? 0) -
      (a.llm_hints.bulk_context?.pre_fetch_priority ?? 0)
    )

  // Add intent-specific candidates
  const candidates = getPreFetchCandidates(intent)
  const toFetch = new Set([
    ...candidates,
    ...prioritized.slice(0, 5).map(c => c.uri),  // top 5 by priority
  ])

  const results: PrefetchResult[] = []

  for (const uri of toFetch) {
    const cap = getCapability(uri)
    if (!cap) continue

    const start = Date.now()
    try {
      let data: unknown

      if (cap.primitive_type === 'resource') {
        data = await cap.loader(ctx)
      } else if (cap.primitive_type === 'tool') {
        data = await cap.handler({}, ctx)
      } else {
        continue
      }

      results.push({ uri, data, latency_ms: Date.now() - start })
    } catch (err) {
      results.push({
        uri,
        data: null,
        latency_ms: Date.now() - start,
        error: String(err),
      })
    }
  }

  return results
}
