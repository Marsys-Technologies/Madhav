import type { InquiryScopeTuple } from '@/lib/vidhi/inquiry/types'
import { searchSemanticCapabilities } from './query'
import type { CapabilityKnowledgeSnapshot, SemanticCapabilityUnit } from './types'

export interface PlannerCapabilityKnowledgeProjection {
  readonly content_hash: string
  readonly compatibility_version: string
  readonly authority: 'compiled_registry_scu_snapshot'
  readonly caveat: string
  readonly capabilities: readonly {
    readonly id: string
    readonly kind: string
    readonly description: string
    readonly domains: readonly string[]
    readonly concepts: readonly string[]
    readonly routes: readonly { tool: string; binding_id: string; channel: string }[]
    readonly edges: readonly { relation: string; target: string }[]
    readonly gaps: readonly string[]
    readonly editorial: boolean
  }[]
}

function project(scu: SemanticCapabilityUnit) {
  return {
    id: scu.scu_id,
    kind: scu.kind,
    description: scu.description,
    domains: scu.domains,
    concepts: scu.concepts,
    routes: scu.bindings.filter((binding) => binding.executable).map((binding) => ({
      tool: binding.public_tool_name ?? binding.capability_uri.split('/').at(-1) ?? binding.capability_uri,
      binding_id: binding.binding_id,
      channel: binding.execution_channels?.join('|') ?? 'unspecified',
    })),
    edges: (scu.edges ?? []).map((edge) => ({ relation: edge.relation, target: edge.target_scu_id })),
    gaps: scu.known_gaps,
    editorial: scu.editorial,
  }
}

/**
 * Bounded semantic projection for the LLM decomposition pass. It is derived
 * from the immutable SCU snapshot; the legacy manifest remains only an
 * execution-name compatibility projection during cutover.
 */
export function buildPlannerCapabilityKnowledgeProjection(
  snapshot: CapabilityKnowledgeSnapshot,
  query: string,
  scope: InquiryScopeTuple,
  limit = 32,
): PlannerCapabilityKnowledgeProjection {
  const boundedLimit = Math.max(1, Math.min(limit, 48))
  const search = searchSemanticCapabilities(snapshot, `${query} ${scope.intent} ${scope.domains.join(' ')}`, boundedLimit)
  const selected = new Map(search.map((hit) => [hit.scu_id, snapshot.scus.find((scu) => scu.scu_id === hit.scu_id)]))
  const protectedSeeds = new Set([...selected.keys()].slice(0, Math.min(8, selected.size)))
  const expansionTargets = new Set<string>()
  const evictionCandidates = [...selected.keys()].reverse()
  // Expand only the strongest seeds. If text search filled the bound, replace
  // the weakest seed so source-backed adjacency is not silently unreachable.
  for (const scu of [...selected.values()].slice(0, Math.min(8, selected.size))) {
    if (!scu) continue
    for (const edge of scu.edges ?? []) {
      if (selected.has(edge.target_scu_id)) continue
      if (selected.size >= boundedLimit) {
        const weakest = evictionCandidates.find((candidate) => selected.has(candidate) && !protectedSeeds.has(candidate) && !expansionTargets.has(candidate))
        if (weakest) selected.delete(weakest)
      }
      selected.set(edge.target_scu_id, snapshot.scus.find((candidate) => candidate.scu_id === edge.target_scu_id))
      expansionTargets.add(edge.target_scu_id)
    }
  }
  return {
    content_hash: snapshot.content_hash,
    compatibility_version: snapshot.compatibility_version,
    authority: 'compiled_registry_scu_snapshot',
    caveat: 'editorial=false entries are conservative registry-derived routing stubs, not reviewed output-semantic coverage',
    capabilities: [...selected.values()].filter((value): value is SemanticCapabilityUnit => Boolean(value)).slice(0, boundedLimit).map(project),
  }
}
