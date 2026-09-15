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
    readonly concept_bindings: readonly { concept_id: string; concept_type: string }[]
    readonly intents: readonly string[]
    readonly horizons: readonly string[]
    readonly scope: 'chart' | 'global'
    readonly inputs: readonly string[]
    readonly outputs: readonly string[]
    readonly provenance_requirements: readonly string[]
    readonly freshness_policy: string
    readonly entitlement: 'native' | 'research' | 'public_disclosed'
    readonly mutation: boolean
    readonly safety_notes: readonly string[]
    readonly routes: readonly {
      tool: string
      binding_id: string
      capability_uri: string
      channel: string
      input_contract: Readonly<Record<string, string>>
      output_contract: Readonly<Record<string, string>>
      pagination: string
      pagination_verified: boolean | null
      executable: boolean
      route_evidence: string | null
    }[]
    readonly edges: readonly { relation: string; target: string; rationale: string }[]
    readonly gaps: readonly string[]
    readonly gap_dispositions: readonly { gap: string; status: string; rationale: string }[]
    readonly graph_disposition: { status: string; rationale: string }
    readonly producer_output_claims: readonly {
      asset_id: string
      component: string
      disposition: string
      specification_hash: string | null
      evidence: string
    }[]
    readonly producer_semantic_disposition: {
      status: string
      asset_ids: readonly string[]
      rationale: string
    }
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
    concept_bindings: scu.concept_bindings.map((binding) => ({
      concept_id: binding.concept_id,
      concept_type: binding.concept_type,
    })),
    intents: scu.intents,
    horizons: scu.horizons,
    scope: scu.scope,
    inputs: scu.inputs,
    outputs: scu.outputs,
    provenance_requirements: scu.provenance_requirements,
    freshness_policy: scu.freshness_policy,
    entitlement: scu.entitlement,
    mutation: scu.safety_notes.some((note) => note.startsWith('Mutation-capable:')),
    safety_notes: scu.safety_notes,
    routes: scu.bindings.filter((binding) => binding.executable).map((binding) => ({
      tool: binding.public_tool_name ?? binding.capability_uri.split('/').at(-1) ?? binding.capability_uri,
      binding_id: binding.binding_id,
      capability_uri: binding.capability_uri,
      channel: binding.execution_channels?.join('|') ?? 'unspecified',
      input_contract: binding.input_contract,
      output_contract: binding.output_contract,
      pagination: binding.pagination,
      pagination_verified: binding.pagination_verified ?? null,
      executable: binding.executable,
      route_evidence: binding.route_evidence ?? null,
    })),
    edges: (scu.edges ?? []).map((edge) => ({
      relation: edge.relation,
      target: edge.target_scu_id,
      rationale: edge.rationale,
    })),
    gaps: scu.known_gaps,
    gap_dispositions: scu.gap_dispositions.map((disposition) => ({
      gap: disposition.gap,
      status: disposition.status,
      rationale: disposition.rationale,
    })),
    graph_disposition: {
      status: scu.graph_disposition.status,
      rationale: scu.graph_disposition.rationale,
    },
    producer_output_claims: (scu.producer_output_claims ?? []).map((claim) => ({
      asset_id: claim.asset_id,
      component: claim.component,
      disposition: claim.disposition,
      specification_hash: claim.output_digest_spec_sha256,
      evidence: claim.evidence,
    })),
    producer_semantic_disposition: {
      status: scu.producer_semantic_disposition.status,
      asset_ids: scu.producer_semantic_disposition.asset_ids,
      rationale: scu.producer_semantic_disposition.rationale,
    },
    editorial: scu.editorial,
  }
}

/**
 * Bounded semantic projection for the LLM decomposition pass. It is derived
 * solely from the immutable SCU snapshot and retains the semantic, safety,
 * provenance, graph, producer, and executable-route constraints needed for a
 * route decision.
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
