/**
 * composite_ranker_cr84_graph.test.ts — D-2 Lane V-3 bonus (CR-84 serving leg).
 *
 * Asserts the composite ranker now CONSUMES graph_node_strength_contribution_jsonb (CGM centrality)
 * in its structural_role term, and falls back cleanly to the class constant when the column is
 * absent (un-re-ranked chart) — closing the "pagerank 100% NULL" dead link without destabilizing
 * the class-constant floor.
 */
import { describe, it, expect } from 'vitest'
import { applyCompositeRanking, extractGraphCentrality, type MsrSignalRow, type L1ChartContext } from '../composite_ranker.js'

const CTX: L1ChartContext = {
  graha_map: {}, current_md_lord: null, current_ad_lord: null, as_of_date: '2026-07-17',
}

function row(id: string, extra: Partial<MsrSignalRow> = {}): MsrSignalRow {
  return {
    signal_id: id,
    signal_type_class: 'position',
    computed_salience: 0.5,
    domains_affected_array: ['wealth'],
    constituent_facts_array: [`f_${id}`],
    ...extra,
  }
}

describe('extractGraphCentrality', () => {
  it('reads pagerank/eigenvector/normalized keys', () => {
    expect(extractGraphCentrality({ pagerank: 0.7 })).toBe(0.7)
    expect(extractGraphCentrality({ normalized: 0.9, pagerank: 0.1 })).toBe(0.9) // normalized preferred
    expect(extractGraphCentrality({ eigenvector: 0.4 })).toBe(0.4)
  })
  it('clamps out-of-range values defensively', () => {
    expect(extractGraphCentrality({ pagerank: 5 })).toBe(1)
    expect(extractGraphCentrality({ pagerank: -2 })).toBe(0)
  })
  it('returns null for absent/unusable jsonb', () => {
    expect(extractGraphCentrality(null)).toBeNull()
    expect(extractGraphCentrality({})).toBeNull()
    expect(extractGraphCentrality({ pagerank: 'x' as unknown as number })).toBeNull()
  })
})

describe('CR-84 — structural_role consumes CGM centrality', () => {
  it('a high-centrality signal outranks its identical low-centrality twin', () => {
    const high = row('high', { graph_node_strength_contribution_jsonb: { pagerank: 0.95 } })
    const low = row('low', { graph_node_strength_contribution_jsonb: { pagerank: 0.05 } })
    const scored = applyCompositeRanking([low, high], CTX, 'wealth')
    const hi = scored.find((s) => s.signal_id === 'high')!
    const lo = scored.find((s) => s.signal_id === 'low')!
    expect(hi._subscores.structural_role).toBeGreaterThan(lo._subscores.structural_role)
    expect(hi.final_rank_score).toBeGreaterThan(lo.final_rank_score)
  })

  it('falls back to the class constant when the graph column is absent (no regression)', () => {
    const withGraph = row('g', { graph_node_strength_contribution_jsonb: { pagerank: 0.5 } })
    const noGraph = row('n')
    const scored = applyCompositeRanking([withGraph, noGraph], CTX, 'wealth')
    const n = scored.find((s) => s.signal_id === 'n')!
    // class 'position' constant = 1.00; absent graph → structural_role stays exactly 1.00
    expect(n._subscores.structural_role).toBeCloseTo(1.0, 5)
  })

  it('blended score stays within a sane bound (not runaway)', () => {
    const g = row('g', { signal_type_class: 'yoga', graph_node_strength_contribution_jsonb: { pagerank: 1 } })
    const scored = applyCompositeRanking([g], CTX, 'wealth')
    // 0.4*1.30 + 0.6*(0.80+0.55*1) = 0.52 + 0.6*1.35 = 0.52 + 0.81 = 1.33
    expect(scored[0]._subscores.structural_role).toBeLessThanOrEqual(1.4)
    expect(scored[0]._subscores.structural_role).toBeGreaterThan(0.8)
  })
})
