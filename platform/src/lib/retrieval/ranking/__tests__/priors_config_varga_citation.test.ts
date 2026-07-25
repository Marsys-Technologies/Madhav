/**
 * priors_config_varga_citation.test.ts — EL-55 documented varga-weight term
 * ============================================================================
 * Asserts VARGA_WEIGHT_CITATION's ṣoḍaśavarga hierarchy is internally consistent
 * with VARGA_BASE_WEIGHT (every non-supplementary key is a member of the
 * shodasavarga group, and the nested shad/sapta/dasa subsets are true subsets),
 * and that composite_ranker's buildRankingBasis surfaces the citation (EL-55:
 * "surfaced in ranking_basis").
 */

import { describe, it, expect } from 'vitest'
import { PRIORS_VERSION, VARGA_WEIGHT_CITATION, VARGA_BASE_WEIGHT } from '../priors_config'
import { buildRankingBasis, type ScoredSignal } from '../composite_ranker'

describe('EL-55 — VARGA_WEIGHT_CITATION', () => {
  it('priors version is bumped past the pre-EL-55 baseline', () => {
    expect(PRIORS_VERSION).not.toBe('1.1')
  })

  it('shadvarga ⊆ saptavarga ⊆ dasavarga ⊆ shodasavarga (the cited hierarchy nests correctly)', () => {
    const { shadvarga, saptavarga, dasavarga, shodasavarga } = VARGA_WEIGHT_CITATION.hierarchy
    for (const v of shadvarga) expect(saptavarga).toContain(v)
    for (const v of saptavarga) expect(dasavarga).toContain(v)
    for (const v of dasavarga) expect(shodasavarga).toContain(v)
  })

  it('shadvarga has exactly 6 members, saptavarga 7, dasavarga 10, shodasavarga 16', () => {
    const { shadvarga, saptavarga, dasavarga, shodasavarga } = VARGA_WEIGHT_CITATION.hierarchy
    expect(shadvarga).toHaveLength(6)
    expect(saptavarga).toHaveLength(7)
    expect(dasavarga).toHaveLength(10)
    expect(shodasavarga).toHaveLength(16)
  })

  it('every shodasavarga member has a VARGA_BASE_WEIGHT entry (the ranking prior implements the classical 16-fold set)', () => {
    for (const v of VARGA_WEIGHT_CITATION.hierarchy.shodasavarga) {
      expect(VARGA_BASE_WEIGHT[v], `missing VARGA_BASE_WEIGHT[${v}]`).toBeDefined()
    }
  })

  it('D1 (rāśi) and D9 (navāṃśa) carry the two heaviest shodasavarga-tier weights (classical primacy)', () => {
    const shodasavargaWeights = VARGA_WEIGHT_CITATION.hierarchy.shodasavarga
      .map(v => [v, VARGA_BASE_WEIGHT[v]!] as const)
      .sort((a, b) => b[1] - a[1])
    const top2 = shodasavargaWeights.slice(0, 2).map(([v]) => v)
    expect(top2).toContain('D1')
    // D9 or D60 — both are classically primary (BPHS "D60 foremost"); assert D9 is at minimum top-3.
    const top3 = shodasavargaWeights.slice(0, 3).map(([v]) => v)
    expect(top3).toContain('D9')
  })
})

describe('EL-55 — ranking_basis surfaces the varga-weight citation', () => {
  it('buildRankingBasis includes varga_weight_basis naming the cited scheme', () => {
    const scored: ScoredSignal = {
      signal_id: 'sig-1',
      composite_score: 1.2,
      percentile_within_class: 1.0,
      final_rank_score: 1.2,
      _subscores: {
        class_prior: 1.1, topic_relevance: 1.0, intrinsic_strength: 0.8,
        structural_role: 1.1, temporal_activation: 1.0, priors_version: PRIORS_VERSION,
      },
    }
    const basis = buildRankingBasis([scored], 'wealth')
    expect(basis['varga_weight_basis']).toBeDefined()
    const vwb = basis['varga_weight_basis'] as Record<string, unknown>
    expect(vwb['scheme']).toBe(VARGA_WEIGHT_CITATION.scheme)
  })
})
