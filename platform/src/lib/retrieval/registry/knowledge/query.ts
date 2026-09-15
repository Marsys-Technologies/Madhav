import type { CapabilityKnowledgeSnapshot, SemanticCapabilityEdge, SemanticCapabilityUnit } from './types'

export interface CapabilitySearchHit {
  readonly scu_id: string
  readonly label: string
  readonly score: number
  readonly matched_terms: readonly string[]
}
function tokens(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? []
}

export function summarizeCapabilityKnowledge(snapshot: CapabilityKnowledgeSnapshot) {
  return {
    schema_version: snapshot.schema_version,
    compatibility_version: snapshot.compatibility_version,
    content_hash: snapshot.content_hash,
    census: snapshot.census,
    domains: Array.from(new Set(snapshot.scus.flatMap((scu) => scu.domains))).sort(),
    kinds: Array.from(new Set(snapshot.scus.map((scu) => scu.kind))).sort(),
  }
}

export function searchSemanticCapabilities(
  snapshot: CapabilityKnowledgeSnapshot,
  query: string,
  limit = 20,
): readonly CapabilitySearchHit[] {
  const queryTokens = Array.from(new Set(tokens(query)))
  return snapshot.scus.map((scu) => {
    const name = `${scu.scu_id} ${scu.label}`.toLowerCase()
    const fields = `${scu.description} ${scu.domains.join(' ')} ${scu.concepts.join(' ')} ${scu.intents.join(' ')}`.toLowerCase()
    const matched = queryTokens.filter((term) => name.includes(term) || fields.includes(term))
    const score = matched.reduce((total, term) => total + (name.includes(term) ? 4 : 1), 0)
    return { scu_id: scu.scu_id, label: scu.label, score, matched_terms: matched }
  }).filter((hit) => hit.score > 0).sort((a, b) => b.score - a.score || a.scu_id.localeCompare(b.scu_id)).slice(0, Math.max(1, Math.min(limit, 100)))
}

export function inspectSemanticCapability(
  snapshot: CapabilityKnowledgeSnapshot,
  scuId: string,
  depth = 1,
): { root: SemanticCapabilityUnit | null; nodes: readonly SemanticCapabilityUnit[]; edges: readonly SemanticCapabilityEdge[]; truncated: boolean } {
  const byId = new Map(snapshot.scus.map((scu) => [scu.scu_id, scu]))
  const root = byId.get(scuId) ?? null
  if (!root) return { root: null, nodes: [], edges: [], truncated: false }
  const seen = new Set([scuId])
  let frontier = [scuId]
  const selectedEdges: SemanticCapabilityEdge[] = []
  const cappedDepth = Math.max(0, Math.min(depth, 3))
  for (let hop = 0; hop < cappedDepth && frontier.length > 0; hop++) {
    const next: string[] = []
    for (const edge of snapshot.edges.filter((candidate) => frontier.includes(candidate.from_scu_id))) {
      selectedEdges.push(edge)
      if (!seen.has(edge.to_scu_id) && byId.has(edge.to_scu_id)) {
        seen.add(edge.to_scu_id)
        next.push(edge.to_scu_id)
      }
    }
    frontier = next
  }
  const truncated = cappedDepth === 3 && snapshot.edges.some((edge) => frontier.includes(edge.from_scu_id) && !seen.has(edge.to_scu_id))
  return {
    root,
    nodes: [...seen].map((id) => byId.get(id)).filter((node): node is SemanticCapabilityUnit => Boolean(node)).sort((a, b) => a.scu_id.localeCompare(b.scu_id)),
    edges: selectedEdges,
    truncated,
  }
}
