import type { CapabilityKnowledgeSnapshot, ChartCapabilityOverlay, SemanticCapabilityBinding } from '../../src/lib/retrieval/registry/knowledge/types'

export type CoverageBlocker =
  | 'availability_contract_missing'
  | 'deliberately_dark'
  | 'no_executable_binding'
  | 'overlay_not_measured'
  | 'overlay_unavailable'
  | 'ready'

export interface CapabilityCoverageRow {
  readonly scu_id: string
  readonly outputs: readonly string[]
  readonly source_dependencies: readonly string[]
  readonly availability_contract_binding_ids: readonly string[]
  readonly bindings: readonly {
    binding_id: string
    capability_uri: string
    execution_channels: readonly string[]
    executable: boolean
  }[]
  readonly readiness: 'unknown' | 'available' | 'partial' | 'dark' | 'incompatible'
  readonly blocker: CoverageBlocker
}

function dependencies(scu: CapabilityKnowledgeSnapshot['scus'][number]): string[] {
  return [...new Set([
    ...(scu.producer_output_claims ?? []).map((claim) => `producer:${claim.asset_id}`),
    ...(scu.availability_contracts ?? []).flatMap((contract) => contract.requirements.map((requirement) =>
      requirement.kind === 'producer_output' ? `producer:${requirement.asset_id}`
        : requirement.kind === 'service_probe' ? `probe:${requirement.probe_id}`
          : requirement.kind === 'source_query' ? `source_query:${requirement.contract_id}`
            : `derived:${requirement.required_binding_ids.join(',')}`,
    )),
  ])].sort()
}

function bindingProjection(binding: SemanticCapabilityBinding) {
  return {
    binding_id: binding.binding_id,
    capability_uri: binding.capability_uri,
    execution_channels: binding.execution_channels ?? ['platform_internal'],
    executable: binding.executable,
  }
}

/** Total inventory: exactly one row per generated SCU, never a filtered acceptance subset. */
export function buildCapabilityCoverage(
  snapshot: CapabilityKnowledgeSnapshot,
  overlay?: ChartCapabilityOverlay | null,
): CapabilityCoverageRow[] {
  const readiness = new Map(overlay?.availability.map((entry) => [entry.scu_id, entry.state]) ?? [])
  return snapshot.scus.map((scu) => {
    const state = readiness.get(scu.scu_id)
    const executable = scu.bindings.some((binding) => binding.executable)
    const blocker: CoverageBlocker = state === 'available' || state === 'partial'
      ? 'ready'
      : state ? 'overlay_unavailable'
        : (scu.availability_dispositions?.length ?? 0) > 0 ? 'deliberately_dark'
          : !executable ? 'no_executable_binding'
            : (scu.availability_contracts?.length ?? 0) === 0 ? 'availability_contract_missing'
              : 'overlay_not_measured'
    return {
      scu_id: scu.scu_id,
      outputs: scu.outputs,
      source_dependencies: dependencies(scu),
      availability_contract_binding_ids: (scu.availability_contracts ?? []).map((contract) => contract.binding_id),
      bindings: scu.bindings.map(bindingProjection),
      readiness: state ?? 'unknown',
      blocker,
    }
  }).sort((a, b) => a.scu_id.localeCompare(b.scu_id))
}
