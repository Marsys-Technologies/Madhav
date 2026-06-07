/**
 * adapters/hybrid/adapter.ts
 *
 * Hybrid adapter: pre-fetch top-priority resources + expose remaining tools to Gemini.
 * Combines bulk_context's deterministic pre-fetch with agentic tool access.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { listCapabilities } from '../../registry'
import type { CapabilityContext } from '../../registry/types'
import { buildPrefetchPlan, executePrefetch, type PrefetchResult } from '../bulk_context/prefetcher'
import { buildBundle, formatBundleForPrompt } from '../bulk_context/bundler'
import { classifyIntent } from '../bulk_context/intent_classifier'

export interface HybridContext {
  /** Pre-fetched context as formatted prompt section */
  system_context: string
  /** Remaining tools exposed to Gemini for agentic access */
  available_tools: Array<{
    uri: string
    name: string
    description: string
    layer: string
  }>
  /** Size of pre-fetched context in KB */
  prefetch_size_kb: number
}

/**
 * Prepare hybrid context for a query.
 *
 * 1. Classify query intent
 * 2. Pre-fetch top-priority resources deterministically
 * 3. Return formatted context + remaining tool catalog
 */
export async function prepareHybridContext(
  query: string,
  ctx: CapabilityContext,
  opts?: {
    /** Max tools to expose agentically (default: 20) */
    max_tools?: number
    /** Uris to always include in pre-fetch */
    always_prefetch?: string[]
  }
): Promise<HybridContext> {
  // Step 1: classify intent
  const intent = await classifyIntent(query)

  // Step 2: pre-fetch
  const plan = buildPrefetchPlan([intent.primary_intent])
  const prefetched = await executePrefetch(plan, ctx)

  // Always-prefetch additions
  if (opts?.always_prefetch) {
    const { getCapability } = await import('../../registry')
    for (const uri of opts.always_prefetch) {
      if (prefetched.some(p => p.uri === uri)) continue
      const cap = getCapability(uri)
      if (!cap) continue
      const start = Date.now()
      try {
        let data: unknown
        if (cap.primitive_type === 'resource') data = await cap.loader(ctx)
        else if (cap.primitive_type === 'tool') data = await cap.handler({}, ctx)
        else continue
        prefetched.push({ uri, content: data, tokens_estimate: 0 })
      } catch (err) {
        void err  // skip failed always_prefetch entries — null content filtered in buildBundle
      }
    }
  }

  const bundle = buildBundle(prefetched)
  const systemContext = formatBundleForPrompt(bundle)

  // Step 3: remaining tools (not already pre-fetched as resources)
  const prefetchedUris = new Set(prefetched.map(p => p.uri))
  const maxTools = opts?.max_tools ?? 20

  const remainingTools = listCapabilities({ primitive_type: 'tool' })
    .filter(c => !prefetchedUris.has(c.uri))
    .sort((a, b) =>
      (b.llm_hints.agentic?.cost_class === 'cheap' ? 2 : 0) -
      (a.llm_hints.agentic?.cost_class === 'cheap' ? 2 : 0)
    )
    .slice(0, maxTools)
    .map(c => ({
      uri: c.uri,
      name: c.name,
      description: c.description,
      layer: c.layer,
    }))

  return {
    system_context: systemContext,
    available_tools: remainingTools,
    prefetch_size_kb: bundle.total_size_kb,
  }
}
