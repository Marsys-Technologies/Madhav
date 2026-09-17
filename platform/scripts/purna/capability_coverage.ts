import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay } from '../../src/lib/retrieval/registry/knowledge/types'

export type CoverageBlocker =
  | 'availability_contract_missing'
  | 'deliberately_dark'
  | 'overlay_not_measured'
  | 'overlay_unavailable'
  | 'ready'

export interface CapabilityCoverageRow {
  /** Stable occurrence key; binding_id alone is not globally unique in the generated estate. */
  readonly coverage_id: string
  readonly scu_id: string
  readonly binding_id: string
  readonly capability_uri: string
  readonly execution_channels: readonly string[]
  readonly outputs: readonly string[]
  readonly source_dependencies: readonly string[]
  readonly availability_contract: 'authored' | 'deliberately_dark' | 'missing'
  readonly readiness: 'unknown' | 'available' | 'partial' | 'dark' | 'incompatible'
  readonly blocker: CoverageBlocker
}

function dependencies(scu: CapabilityKnowledgeSnapshot['scus'][number], bindingId: string): string[] {
  const contract = scu.availability_contracts?.find((candidate) => candidate.binding_id === bindingId)
  return [...new Set([
    ...(contract?.requirements ?? []).map((requirement) =>
      requirement.kind === 'producer_output' ? `producer:${requirement.asset_id}`
        : requirement.kind === 'service_probe' ? `probe:${requirement.probe_id}`
          : requirement.kind === 'source_query' ? `source_query:${requirement.contract_id}`
            : `derived:${requirement.required_binding_ids.join(',')}`),
  ])].sort()
}

/** Total inventory: exactly one row per executable binding occurrence. */
export function buildCapabilityCoverage(
  snapshot: CapabilityKnowledgeSnapshot,
  overlay?: ChartCapabilityOverlay | null,
): CapabilityCoverageRow[] {
  const readiness = new Map(overlay?.availability.map((entry) => [entry.scu_id, entry]) ?? [])
  return snapshot.scus.flatMap((scu) => scu.bindings.filter((binding) => binding.executable).map((binding) => {
    const overlayEntry = readiness.get(scu.scu_id)
    const bindingAvailable = overlayEntry?.available_binding_ids.includes(binding.binding_id) ?? false
    const contract = scu.availability_contracts?.find((candidate) => candidate.binding_id === binding.binding_id)
    const disposition = scu.availability_dispositions?.find((candidate) => candidate.binding_id === binding.binding_id)
    const contractState = contract ? 'authored' : disposition ? 'deliberately_dark' : 'missing'
    const blocker: CoverageBlocker = bindingAvailable
      ? 'ready'
      : overlayEntry ? 'overlay_unavailable'
        : disposition ? 'deliberately_dark'
          : !contract ? 'availability_contract_missing'
            : 'overlay_not_measured'
    return {
      coverage_id: `${scu.scu_id}::${binding.binding_id}`,
      scu_id: scu.scu_id,
      binding_id: binding.binding_id,
      capability_uri: binding.capability_uri,
      execution_channels: binding.execution_channels ?? ['platform_internal'],
      outputs: scu.outputs,
      source_dependencies: dependencies(scu, binding.binding_id),
      availability_contract: contractState,
      readiness: bindingAvailable
        ? 'available'
        : overlayEntry?.state === 'incompatible' ? 'incompatible'
          : overlayEntry ? 'dark'
            : 'unknown',
      blocker,
    }
  })).sort((a, b) => a.coverage_id.localeCompare(b.coverage_id))
}
