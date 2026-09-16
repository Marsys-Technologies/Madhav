import type { SemanticCapabilityBinding } from '../../retrieval/registry/knowledge/types'

export interface InquiryPaginationReceipt {
  readonly semantics: string
  readonly exhausted: boolean
  readonly next: unknown
}

export interface InquirySemanticFindingExtraction {
  readonly mode: 'reviewed_collection' | 'reviewed_collection_missing' | 'opaque_adapter_items'
  readonly result_collection_path: string | null
  readonly rows: readonly unknown[]
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
 * Empty is asserted only when an independently reviewed semantic collection
 * path is observed. Exhaustion proof remains a separate pagination concern.
 */
export function classifyInquiryResult(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
): 'served' | 'empty' | 'failed' {
  for (const object of nestedValues(raw)) {
    if (object['is_error'] === true || object['ok'] === false || object['success'] === false) return 'failed'
    if (typeof object['error'] === 'string' && object['error'].trim()) return 'failed'
  }
  const semanticCount = semanticInquiryResultCount(binding, raw)
  if (semanticCount !== null) return semanticCount > 0 ? 'served' : 'empty'
  const bundleResults = raw && typeof raw === 'object' ? (raw as Record<string, unknown>)['results'] : undefined
  return Array.isArray(bundleResults) && bundleResults.length === 0 ? 'empty' : 'served'
}

/** A semantic row count exists only for an independently reviewed collection path. */
export function semanticInquiryResultCount(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
): number | null {
  const resultPath = binding?.result_collection_verified ? binding.pagination_contract?.result_collection_path : undefined
  if (!resultPath) return null
  for (const object of nestedValues(raw)) {
    const collection = atPath(object, resultPath)
    if (Array.isArray(collection)) return collection.length
  }
  return null
}

/**
 * Extract the semantic findings that a response-accountability receipt may
 * name. A source-reviewed result collection is decomposed at exactly that
 * path. Without an independently reviewed path, adapter items remain opaque:
 * their internal shape is not promoted into an invented semantic contract.
 */
export function extractInquirySemanticFindings(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
): InquirySemanticFindingExtraction {
  const resultPath = binding?.result_collection_verified
    ? binding.pagination_contract?.result_collection_path
    : undefined
  if (resultPath) {
    for (const object of nestedValues(raw)) {
      const collection = atPath(object, resultPath)
      if (Array.isArray(collection)) {
        return { mode: 'reviewed_collection', result_collection_path: resultPath, rows: collection }
      }
    }
    return { mode: 'reviewed_collection_missing', result_collection_path: resultPath, rows: [] }
  }
  const adapterItems = raw && typeof raw === 'object'
    ? (raw as Record<string, unknown>)['results']
    : undefined
  return {
    mode: 'opaque_adapter_items',
    result_collection_path: null,
    rows: Array.isArray(adapterItems) ? adapterItems : [raw],
  }
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
    const nextCursor = atPath(object, contract.next_path)
    if (contract.next_path && nextCursor !== undefined) {
      return { semantics: binding.pagination, exhausted: nextCursor == null, next: nextCursor ?? null }
    }
    const moreAvailable = atPath(object, contract.more_available_path)
    if (typeof moreAvailable === 'boolean') {
      const hasMore = moreAvailable
      const current = Number(atPath(args, contract.request_position_path) ?? 0)
      const limit = Number(atPath(args, contract.request_limit_path) ?? contract.effective_maximum ?? 0)
      return { semantics: binding.pagination, exhausted: !hasMore, next: hasMore && limit > 0 ? current + limit : hasMore ? 'unproven' : null }
    }
  }
  return { semantics: binding.pagination, exhausted: false, next: 'unproven' }
}
