import type { SemanticCapabilityBinding } from '../../retrieval/registry/knowledge/types'
import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'

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

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null
}

function optionalText(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined
  const normalized = value.trim()
  return normalized || undefined
}

function normalizedSignalIds(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return [...new Set(value
    .filter((candidate): candidate is string => typeof candidate === 'string')
    .map((candidate) => candidate.trim())
    .filter(Boolean))].sort()
}

function normalizedTopK(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(parsed)) return 50
  const normalized = Math.floor(parsed)
  return normalized >= 1 ? Math.min(normalized, 500) : 50
}

function normalizedMinimumStrength(value: unknown): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(parsed) ? Math.max(0, parsed) : 0
}

/**
 * The handler may default a date range for ordinary reads, but an inquiry can
 * only accept closure for a window it actually authorized.  An explicit
 * point-in-time or complete range is therefore required here.
 */
function authorizedTemporalFilters(
  args: Readonly<Record<string, unknown>>,
  closureVersion: string,
): { filters: Record<string, unknown>; topK: number } | null {
  const chartId = optionalText(args['chart_id'])
  if (!chartId) return null
  const asOf = optionalText(args['as_of'])
  const dateFrom = optionalText(args['date_from'])
  const dateTo = optionalText(args['date_to'])
  const temporalFilter = asOf
    ? { mode: 'point_in_time', as_of: asOf }
    : dateFrom && dateTo
      ? { mode: 'range', date_from: dateFrom, date_to: dateTo }
      : null
  if (!temporalFilter) return null
  return {
    filters: {
      closure_version: closureVersion,
      chart_id: chartId,
      ayanamsha_id: optionalText(args['ayanamsha_id']) ?? 'lahiri_chitrapaksha',
      temporal_filter: temporalFilter,
      signal_ids: normalizedSignalIds(args['signal_ids']),
      min_activation_strength: normalizedMinimumStrength(args['min_activation_strength']),
      domain: optionalText(args['domain']) ?? null,
    },
    topK: normalizedTopK(args['top_k']),
  }
}

/**
 * A bounded temporal-window receipt is not pagination: it cannot resume from
 * a cursor or offset.  It can only close one explicitly authorized query when
 * every identity and cardinality field agrees with the observed collection.
 */
function boundedWindowExhausted(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
  args: Readonly<Record<string, unknown>>,
): boolean | null {
  const review = binding?.bounded_window_closure
  if (!binding || !review) return null
  const contract = binding.pagination_contract
  if (!contract || binding.pagination !== 'bounded_unverified') return false
  const authorized = authorizedTemporalFilters(args, review.closure_version)
  if (!authorized) return false

  for (const object of nestedValues(raw)) {
    const collection = atPath(object, contract.result_collection_path)
    const receipt = record(atPath(object, review.receipt_path))
    if (!Array.isArray(collection) || !receipt) continue
    const filters = record(receipt['filters'])
    const limit = record(receipt['limit'])
    const continuation = record(receipt['continuation'])
    const stableSort = receipt['stable_sort']
    const totalMatching = atPath(object, contract.total_path)
    const moreAvailable = atPath(object, contract.more_available_path)
    const truncated = atPath(object, 'content.truncated')
    if (!filters || !limit || !continuation || !Array.isArray(stableSort)) return false
    if (receipt['closure_version'] !== review.closure_version
      || receipt['collection'] !== review.collection
      || receipt['state'] !== 'complete_within_stated_window'
      || receipt['exhaustive_within_stated_window'] !== true
      || moreAvailable !== false
      || truncated !== false
      || continuation['supported'] !== false
      || continuation['next'] !== null
      || stableFingerprint(filters) !== stableFingerprint(authorized.filters)
      || stableFingerprint(stableSort) !== stableFingerprint(contract.deterministic_order)
      || receipt['filter_identity'] !== stableFingerprint(authorized.filters)
      || receipt['query_identity'] !== stableFingerprint({
        ...authorized.filters,
        stable_sort: contract.deterministic_order,
        top_k: authorized.topK,
      })
      || limit['effective_top_k'] !== authorized.topK
      || limit['maximum_top_k'] !== review.maximum_top_k
      || limit['returned'] !== collection.length
      || typeof totalMatching !== 'number'
      || !Number.isSafeInteger(totalMatching)
      || totalMatching < 0
      || limit['total_matching'] !== totalMatching
      || totalMatching !== collection.length) return false
    return true
  }
  return false
}

/** Derive exhaustion only from a source-reviewed binding contract plus server-observed output. */
export function deriveInquiryPaginationReceipt(
  binding: SemanticCapabilityBinding | undefined,
  raw: unknown,
  args: Readonly<Record<string, unknown>>,
): InquiryPaginationReceipt {
  if (!binding || binding.pagination === 'none') return { semantics: binding?.pagination ?? 'none', exhausted: true, next: null }
  const boundedClosure = boundedWindowExhausted(binding, raw, args)
  if (boundedClosure === true) return { semantics: binding.pagination, exhausted: true, next: null }
  if (boundedClosure === false) return { semantics: binding.pagination, exhausted: false, next: 'unproven' }
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
