import type { SemanticCapabilityBinding } from '../../retrieval/registry/knowledge/types'

export interface InquiryPaginationReceipt {
  readonly semantics: string
  readonly exhausted: boolean
  readonly next: unknown
}

function nestedValues(raw: unknown): Record<string, unknown>[] {
  const queue: unknown[] = [raw]
  const objects: Record<string, unknown>[] = []
  const seen = new Set<object>()
  while (queue.length) {
    const value = queue.shift()
    if (typeof value === 'string' && /^[\s]*[\[{]/.test(value)) {
      try {
        const parsed = JSON.parse(value) as unknown
        // Registry ToolResult.content objects are JSON-stringified into
        // ToolBundleResult.content by the compatibility adapter. Retain both
        // the parsed object and its original `content` envelope for reviewed
        // paths declared against the handler response.
        queue.push(parsed, { content: parsed })
      } catch { /* non-JSON evidence string */ }
      continue
    }
    if (!value || typeof value !== 'object' || seen.has(value)) continue
    seen.add(value)
    const object = value as Record<string, unknown>
    objects.push(object)
    queue.push(...Object.values(object))
  }
  return objects
}

/**
 * Empty is asserted only when a reviewed collection path is observed. For
 * unreviewed shapes, a successful bundle remains served rather than inventing
 * a semantic empty from adapter/container structure.
 */
export function classifyInquiryResult(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
): 'served' | 'empty' {
  const resultPath = binding?.pagination_verified ? binding.pagination_contract?.result_collection_path : undefined
  if (resultPath) {
    for (const object of nestedValues(raw)) {
      const collection = atPath(object, resultPath)
      if (Array.isArray(collection)) return collection.length > 0 ? 'served' : 'empty'
    }
  }
  const bundleResults = raw && typeof raw === 'object' ? (raw as Record<string, unknown>)['results'] : undefined
  return Array.isArray(bundleResults) && bundleResults.length === 0 ? 'empty' : 'served'
}

function atPath(value: unknown, path: string | undefined): unknown {
  if (!path) return undefined
  return path.split('.').reduce<unknown>((current, key) => current && typeof current === 'object' ? (current as Record<string, unknown>)[key] : undefined, value)
}

/** Derive exhaustion only from a source-reviewed binding contract plus server-observed output. */
export function deriveInquiryPaginationReceipt(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
  args: Readonly<Record<string, unknown>>,
): InquiryPaginationReceipt {
  if (!binding || binding.pagination === 'none') return { semantics: binding?.pagination ?? 'none', exhausted: true, next: null }
  if (!binding.pagination_verified) return { semantics: binding.pagination, exhausted: false, next: 'unproven' }
  if (binding.pagination === 'bounded_complete') return { semantics: binding.pagination, exhausted: true, next: null }
  const contract = binding.pagination_contract
  if (!contract) return { semantics: binding.pagination, exhausted: false, next: 'unproven' }
  for (const object of nestedValues(raw)) {
    if (!Array.isArray(atPath(object, contract.result_collection_path))) continue
    const moreAvailable = atPath(object, contract.more_available_path)
    if (typeof moreAvailable === 'boolean') {
      const hasMore = moreAvailable
      const current = Number(args['offset'] ?? 0)
      const limit = Number(args['limit'] ?? binding.pagination_contract?.effective_maximum ?? 0)
      return { semantics: binding.pagination, exhausted: !hasMore, next: hasMore && limit > 0 ? current + limit : hasMore ? 'unproven' : null }
    }
    const nextCursor = atPath(object, contract.next_path)
    if (contract.next_path && nextCursor !== undefined) return { semantics: binding.pagination, exhausted: nextCursor == null, next: nextCursor ?? null }
  }
  return { semantics: binding.pagination, exhausted: false, next: 'unproven' }
}
