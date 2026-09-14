import { stableFingerprint } from '../../retrieval/registry/knowledge/stable'
import type { CapabilityKnowledgeSnapshot, CapabilityRelation, SemanticCapabilityEdge } from '../../retrieval/registry/knowledge/types'
import type { GraphTraversalFrontier, GraphTraversalReceipt, GraphTraversalStep } from './types'

const REQUIRED_RELATIONS = new Set<CapabilityRelation>(['requires', 'contradicts'])

function edgeKey(edge: SemanticCapabilityEdge): string {
  return `${edge.from_scu_id}\u0000${edge.relation}\u0000${edge.to_scu_id}\u0000${edge.source_ref ?? ''}`
}

function reviewedEdges(snapshot: CapabilityKnowledgeSnapshot): SemanticCapabilityEdge[] {
  const ids = new Set(snapshot.scus.map((scu) => scu.scu_id))
  return snapshot.edges.filter((edge) => Boolean(edge.edge_source && edge.source_ref)
    && ids.has(edge.from_scu_id) && ids.has(edge.to_scu_id)).sort((a, b) => edgeKey(a).localeCompare(edgeKey(b)))
}

export function sourceBackedEdge(
  snapshot: CapabilityKnowledgeSnapshot,
  fromScuId: string,
  toScuId: string,
): SemanticCapabilityEdge | null {
  return reviewedEdges(snapshot).find((edge) => edge.from_scu_id === fromScuId && edge.to_scu_id === toScuId) ?? null
}

export function traverseCapabilityGraph(
  snapshot: CapabilityKnowledgeSnapshot,
  seedScuIds: readonly string[],
  budget: { readonly max_hops: number; readonly max_nodes: number },
): GraphTraversalReceipt {
  const ids = new Set(snapshot.scus.map((scu) => scu.scu_id))
  const maxHops = Math.max(0, Math.min(Math.trunc(budget.max_hops), 3))
  const maxNodes = Math.max(1, Math.min(Math.trunc(budget.max_nodes), 48))
  const seeds = [...new Set(seedScuIds)].filter((id) => ids.has(id))
  const selected = new Set(seeds)
  const queue = seeds.map((scuId) => ({ scu_id: scuId, hop: 0 }))
  const steps: GraphTraversalStep[] = []
  const frontier = new Map<string, GraphTraversalFrontier>()
  const outgoing = new Map<string, SemanticCapabilityEdge[]>()
  for (const edge of reviewedEdges(snapshot)) outgoing.set(edge.from_scu_id, [...(outgoing.get(edge.from_scu_id) ?? []), edge])

  while (queue.length > 0) {
    const current = queue.shift()!
    for (const edge of outgoing.get(current.scu_id) ?? []) {
      const materiality = REQUIRED_RELATIONS.has(edge.relation) ? 'required' as const : 'supporting' as const
      const nextHop = current.hop + 1
      const key = edgeKey(edge)
      if (selected.has(edge.to_scu_id) && nextHop > maxHops) continue
      if (nextHop > maxHops || (!selected.has(edge.to_scu_id) && selected.size >= maxNodes)) {
        frontier.set(key, {
          from_scu_id: edge.from_scu_id,
          relation: edge.relation,
          to_scu_id: edge.to_scu_id,
          hop: nextHop,
          materiality,
          reason: nextHop > maxHops ? 'graph_hop_budget_exhausted' : 'graph_node_budget_exhausted',
          edge_source: edge.edge_source!,
          source_ref: edge.source_ref!,
        })
        continue
      }
      steps.push({
        from_scu_id: edge.from_scu_id,
        relation: edge.relation,
        to_scu_id: edge.to_scu_id,
        hop: nextHop,
        materiality,
        edge_source: edge.edge_source!,
        source_ref: edge.source_ref!,
      })
      if (!selected.has(edge.to_scu_id)) {
        selected.add(edge.to_scu_id)
        queue.push({ scu_id: edge.to_scu_id, hop: nextHop })
      }
    }
  }

  const normalized = {
    traversal_version: 'inquiry-graph-traversal-v1' as const,
    seed_scu_ids: seeds,
    selected_scu_ids: [...selected],
    steps,
    frontier: [...frontier.values()],
    max_hops: maxHops,
    max_nodes: maxNodes,
    truncated: frontier.size > 0,
  }
  return { ...normalized, traversal_hash: stableFingerprint(normalized) }
}
