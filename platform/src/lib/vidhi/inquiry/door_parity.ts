import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { InquiryContract } from './types'

function semanticGapClass(
  disposition: InquiryContract['obligations'][number]['disposition'],
  gapReason: string | null,
): string | null {
  if (disposition === 'dark') return 'CAPABILITY_UNAVAILABLE'
  if (disposition !== 'failed') return null
  if (gapReason?.includes('OVERLAY_CHANGED')) return 'OVERLAY_CHANGED'
  return 'EXECUTION_FAILED'
}

/**
 * Channel-neutral closure projection for Portal, managed MCP and raw MCP.
 *
 * Execution-plan hashes, contract ids and evidence-reference strings are
 * deliberately excluded: those identify transport/dispatch envelopes, not the
 * semantic question or its observed disposition. Evidence presence remains in
 * the projection so a door cannot claim parity by silently dropping proof.
 */
export function buildInquiryDoorParityProjection(contract: InquiryContract) {
  const normalized = {
    parity_version: 'inquiry-door-parity-v1' as const,
    semantic_contract_hash: contract.semantic_contract_hash,
    capability_content_hash: contract.capability_content_hash,
    chart_availability_version: contract.chart_availability_version,
    chart_build_id: contract.chart_build_id,
    normalized_scope_hash: contract.scope_normalization?.normalized_scope_hash
      ?? stableFingerprint(contract.scope_tuple),
    status: contract.status,
    status_reasons: [...contract.status_reasons].sort(),
    obligation_coverage: contract.obligations.map((obligation) => ({
      obligation_id: obligation.obligation_id,
      materiality: obligation.materiality,
      disposition: obligation.disposition,
      evidence_present: obligation.evidence_refs.length > 0,
      gap_class: semanticGapClass(obligation.disposition, obligation.gap_reason),
    })).sort((a, b) => a.obligation_id.localeCompare(b.obligation_id)),
    residual_frontier: contract.material_frontier
      .filter((item) => item.disposition === 'open' || item.disposition === 'capped')
      .map((item) => ({
        scu_id: item.scu_id,
        materiality: item.materiality,
        reason: item.reason,
        disposition: item.disposition,
      }))
      .sort((a, b) => `${a.scu_id}:${a.reason}`.localeCompare(`${b.scu_id}:${b.reason}`)),
  }
  return { ...normalized, parity_hash: stableFingerprint(normalized) }
}
