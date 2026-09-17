import type { SemanticCapabilityDeclaration } from './types'

/**
 * A reviewed result collection is a concrete route contract, not an authored
 * boolean. Source evidence, a semantic collection path, and deterministic
 * ordering must all survive compilation and census generation.
 */
export function hasReviewedResultCollection(
  details: SemanticCapabilityDeclaration['primary_binding_details'],
): boolean {
  const contract = details?.pagination_contract
  return Boolean(
    details?.route_evidence
    && contract?.result_collection_path
    && contract.deterministic_order.length > 0,
  )
}

/**
 * Exhaustion is reviewable only when a route accepts a bounded position,
 * returns the reviewed collection, and supplies a continuation mechanism.
 * Offset routes may prove continuation through total-plus-more metadata; a
 * bounded no-continuation route remains deliberately unverified.
 */
export function hasReviewedExhaustion(
  details: SemanticCapabilityDeclaration['primary_binding_details'],
): boolean {
  const contract = details?.pagination_contract
  if (!details || !contract || !hasReviewedResultCollection(details)) return false
  if (details.pagination !== 'cursor' && details.pagination !== 'offset') return false
  return Boolean(
    contract.request_position_path
    && contract.request_limit_path
    && typeof contract.effective_maximum === 'number'
    && contract.effective_maximum > 0
    && (contract.next_path
      || (details.pagination === 'offset' && contract.total_path && contract.more_available_path)),
  )
}
