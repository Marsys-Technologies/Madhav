import { describe, expect, it } from 'vitest'
import { getCatalog } from '../../retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../retrieval/registry/knowledge/compiler'
import { traverseCapabilityGraph } from './graph_traversal'

describe('source-backed inquiry graph traversal', () => {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-14T00:00:00.000Z')

  it('deterministically follows reviewed required and contradictory neighbors', () => {
    const first = traverseCapabilityGraph(snapshot, ['scu.finance.prosperity_assessment'], {
      max_hops: 1,
      max_nodes: 8,
    })
    const second = traverseCapabilityGraph(snapshot, ['scu.finance.prosperity_assessment'], {
      max_hops: 1,
      max_nodes: 8,
    })

    expect(second).toEqual(first)
    expect(first.selected_scu_ids).toEqual(expect.arrayContaining([
      'scu.finance.prosperity_assessment',
      'scu.bodha.mechanism.network',
      'scu.catalog.get_divisionals',
      'scu.kala.temporal_activation',
      'scu.yoga.firing_and_cancellation',
    ]))
    expect(first.steps.every((step) => step.edge_source.length > 0 && step.source_ref.length > 0)).toBe(true)
    expect(first.steps.filter((step) => step.materiality === 'required').length).toBeGreaterThan(0)
  })

  it('reports material frontier instead of silently dropping a bounded traversal', () => {
    const result = traverseCapabilityGraph(snapshot, ['scu.finance.prosperity_assessment'], {
      max_hops: 1,
      max_nodes: 2,
    })

    expect(result.truncated).toBe(true)
    expect(result.frontier.some((item) => item.materiality === 'required')).toBe(true)
    expect(result.selected_scu_ids).toHaveLength(2)
  })

  it('ignores an edge that lacks reviewed source provenance', () => {
    const forged = {
      ...snapshot,
      edges: [...snapshot.edges, {
        from_scu_id: 'scu.finance.prosperity_assessment',
        relation: 'requires' as const,
        to_scu_id: 'scu.catalog.asset_registry_all',
        rationale: 'forged',
      }],
    }
    const result = traverseCapabilityGraph(forged, ['scu.finance.prosperity_assessment'], {
      max_hops: 1,
      max_nodes: 16,
    })
    expect(result.steps.some((step) => step.to_scu_id === 'scu.catalog.asset_registry_all')).toBe(false)
  })
})
