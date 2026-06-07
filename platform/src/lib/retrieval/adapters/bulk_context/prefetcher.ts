/**
 * Bulk Context Adapter — Prefetcher
 * ===================================
 * For tagged intent, pre-fetch resources by priority.
 */

import { listCapabilities, getCapability } from '@/lib/retrieval/registry'
import type { CapabilityUri, CapabilityContext } from '@/lib/retrieval/registry/types'
import type { IntentTag } from './intent_classifier'

export interface PrefetchResult {
  uri: CapabilityUri
  content: unknown
  tokens_estimate: number
}

export interface PrefetchPlan {
  resources: CapabilityUri[]
  tools: CapabilityUri[]
  estimated_tokens: number
}

/** Intent → resource URIs to pre-fetch */
const INTENT_PREFETCH_MAP: Record<IntentTag, CapabilityUri[]> = {
  entity_lookup: [
    'marsys://resource/asset-registry/L0',
    'marsys://tool/L0/resolve_entity',
  ],
  rule_query: [
    'marsys://resource/asset-registry/L0',
    'marsys://tool/L0/list_entities',
  ],
  remedy_query: [
    'marsys://resource/asset-registry/L0',
  ],
  temporal_query: [
    'marsys://resource/asset-registry/L0',
  ],
  chart_analysis: [
    'marsys://resource/asset-registry/all',
  ],
  text_reference: [
    'marsys://resource/asset-registry/L0',
  ],
  calculation: [
    'marsys://resource/asset-registry/L0',
  ],
  general: [
    'marsys://resource/asset-registry/L0',
  ],
}

/**
 * Build a prefetch plan based on intent tags.
 * Sorted by pre_fetch_priority (highest first).
 */
export function buildPrefetchPlan(intent_tags: IntentTag[]): PrefetchPlan {
  const all_uris = new Set<CapabilityUri>()

  // Add URIs for each intent tag
  for (const tag of intent_tags) {
    const uris = INTENT_PREFETCH_MAP[tag] || []
    uris.forEach((uri) => all_uris.add(uri))
  }

  // Sort by pre_fetch_priority (from llm_hints)
  const sorted_uris = Array.from(all_uris).sort((a, b) => {
    const cap_a = getCapability(a)
    const cap_b = getCapability(b)
    const pri_a = cap_a?.llm_hints?.bulk_context?.pre_fetch_priority ?? 50
    const pri_b = cap_b?.llm_hints?.bulk_context?.pre_fetch_priority ?? 50
    return pri_b - pri_a  // highest priority first
  })

  const resources = sorted_uris.filter((uri) => uri.startsWith('marsys://resource/'))
  const tools = sorted_uris.filter((uri) => uri.startsWith('marsys://tool/'))

  // Estimate tokens: 500 per resource + 200 per tool
  const estimated_tokens = resources.length * 500 + tools.length * 200

  return { resources, tools, estimated_tokens }
}

/**
 * Execute the prefetch plan and return results.
 */
export async function executePrefetch(
  plan: PrefetchPlan,
  context?: CapabilityContext,
  args?: Record<string, unknown>
): Promise<PrefetchResult[]> {
  const results: PrefetchResult[] = []

  // Pre-fetch resources first (static, cheap)
  for (const uri of plan.resources) {
    const cap = getCapability(uri)
    if (!cap) continue

    try {
      const result = await cap.handler(args || {}, context)
      if (!result.is_error) {
        const content_str = typeof result.content === 'string'
          ? result.content
          : JSON.stringify(result.content)
        results.push({
          uri,
          content: result.content,
          tokens_estimate: Math.ceil(content_str.length / 4),
        })
      }
    } catch {
      // Non-fatal: skip failed pre-fetch
    }
  }

  // Then fetch high-priority tools
  for (const uri of plan.tools) {
    const cap = getCapability(uri)
    if (!cap) continue

    const priority = cap.llm_hints?.bulk_context?.pre_fetch_priority ?? 50
    if (priority < 70) continue  // Only pre-fetch high-priority tools

    try {
      const result = await cap.handler(args || {}, context)
      if (!result.is_error) {
        const content_str = typeof result.content === 'string'
          ? result.content
          : JSON.stringify(result.content)
        results.push({
          uri,
          content: result.content,
          tokens_estimate: Math.ceil(content_str.length / 4),
        })
      }
    } catch {
      // Non-fatal
    }
  }

  return results
}
