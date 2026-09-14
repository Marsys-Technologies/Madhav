import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { InquiryContract } from './types'

function normalizeGapReason(reason: string): string {
  return reason.trim().toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_|_$/g, '')
}

function semanticGapClasses(
  disposition: InquiryContract['obligations'][number]['disposition'],
  gapReason: string | null,
): string[] {
  if (disposition !== 'dark' && disposition !== 'failed') return []
  const reasons = gapReason?.split(';').map((reason) => reason.trim()).filter(Boolean) ?? []
  if (reasons.length === 0) return [`${disposition.toUpperCase()}_REASON_MISSING`]
  return [...new Set(reasons.map((rawReason) => {
    const reason = normalizeGapReason(rawReason)
    if (reason.includes('OVERLAY_CHANGED')) return 'OVERLAY_CHANGED'
    if (reason === 'DISPATCH_ERROR' || reason === 'TOOL_DISPATCH_FAILED') return 'DISPATCH_FAILED'
    if (reason === 'TOOL_FAILURE_ENVELOPE') return 'TOOL_FAILURE_ENVELOPE'
    if (reason === 'RESULT_LIMIT_EXCEEDED') return 'RESULT_LIMIT_EXCEEDED'
    if (reason === 'REGISTRY_UNRESOLVABLE' || reason === 'INQUIRY_BINDING_UNAVAILABLE') {
      return 'BINDING_UNAVAILABLE'
    }
    if (/^NO_EXECUTABLE_(?:PLATFORM_INTERNAL|MCP_FULL)_BINDING_IS_DECLARED$/.test(reason)) {
      return 'CHANNEL_BINDING_UNAVAILABLE'
    }
    if (reason.startsWith('REQUIRED_BINDING_ARGUMENTS_ARE_UNRESOLVED')) {
      const missingArgs = reason.slice('REQUIRED_BINDING_ARGUMENTS_ARE_UNRESOLVED'.length).replace(/^_/, '')
      return `BINDING_ARGS_UNRESOLVED:${stableFingerprint(missingArgs)}`
    }
    if (reason === 'THE_CHART_BUILD_OVERLAY_DOES_NOT_PROVE_THIS_BINDING_AVAILABLE') {
      return 'OVERLAY_EVIDENCE_MISSING'
    }
    if (disposition === 'dark' && reason.includes('NO_EXECUTABLE_PLAN_ITEM')) {
      return 'CAPABILITY_UNAVAILABLE'
    }
    return `${disposition.toUpperCase()}_UNCLASSIFIED:${stableFingerprint(reason)}`
  }))].sort()
}

function canonicalEvidenceIdentity(reference: string): string {
  const digest = reference.match(/sha256:[0-9a-f]{64}$/i)?.[0]
  return digest?.toLowerCase() ?? `unparsed:${stableFingerprint(reference)}`
}

/**
 * Channel-neutral closure projection for Portal, managed MCP and raw MCP.
 *
 * Execution-plan hashes and contract ids are deliberately excluded because
 * they identify transport/dispatch envelopes. Door-specific evidence prefixes
 * are stripped only when a canonical SHA-256 payload identity is present; an
 * unparseable reference remains distinct and therefore fails closed.
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
      evidence_hashes: [...new Set(obligation.evidence_refs.map(canonicalEvidenceIdentity))].sort(),
      gap_classes: semanticGapClasses(obligation.disposition, obligation.gap_reason),
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
