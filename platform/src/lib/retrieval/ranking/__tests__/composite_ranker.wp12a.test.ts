/**
 * composite_ranker.wp12a.test.ts — WP-1.2(a) (LCA-14) unit tests for entity attribution,
 * the UNATTRIBUTED-never-top ordering guard, and resolvable-only fact_id surfacing.
 * Pure functions over a hand-built ScoredSignal[] — no DB.
 */
import { describe, it, expect } from 'vitest'
import {
  buildHierarchicalProfiles,
  grahaFromFactSubject,
  deriveSignalEntity,
  type ScoredSignal,
} from '../composite_ranker'

function sig(overrides: Partial<ScoredSignal> & { signal_id: string; final_rank_score: number }): ScoredSignal {
  return {
    signal_type_class: 'composite_state',
    domains_affected_array: [],
    valence: null,
    configuration_jsonb: null,
    constituent_facts_array: null,
    composite_score: overrides.composite_score ?? overrides.final_rank_score,
    percentile_within_class: 1.0,
    _subscores: {
      class_prior: 1, topic_relevance: 1, intrinsic_strength: 1,
      structural_role: 1, temporal_activation: 1, priors_version: 'test',
    },
    ...overrides,
  } as ScoredSignal
}

describe('grahaFromFactSubject — graha token embedded in fact_subject', () => {
  it('parses D<varga>_<GRAHA> and mean-node subjects', () => {
    expect(grahaFromFactSubject('D108_SAT')).toBe('SATURN')
    expect(grahaFromFactSubject('D1_SAT')).toBe('SATURN')
    expect(grahaFromFactSubject('RAH_MEAN')).toBe('RAHU')
    expect(grahaFromFactSubject('SUN')).toBe('SUN')
    expect(grahaFromFactSubject('D9_MO')).toBe('MOON')
  })
  it('returns null when no graha token present', () => {
    expect(grahaFromFactSubject('D1_LAGNA')).toBeNull()
    expect(grahaFromFactSubject(null)).toBeNull()
    expect(grahaFromFactSubject('')).toBeNull()
  })
})

describe('deriveSignalEntity — attribution order', () => {
  it('prefers configuration_jsonb graha over fact_subject', () => {
    const s = sig({ signal_id: 'a', final_rank_score: 1, configuration_jsonb: { graha: 'Venus' },
      constituent_facts_array: ['f1'] })
    expect(deriveSignalEntity(s, new Map([['f1', 'D9_SAT']]))).toBe('VENUS')
  })
  it('falls back to fact_subject graha when config has no graha', () => {
    const s = sig({ signal_id: 'b', final_rank_score: 1, configuration_jsonb: { fact_key: 'dignity_state', varga: 'D108' },
      constituent_facts_array: ['f2'] })
    expect(deriveSignalEntity(s, new Map([['f2', 'D108_SAT']]))).toBe('SATURN')
  })
  it('returns UNATTRIBUTED only when neither source resolves', () => {
    const s = sig({ signal_id: 'c', final_rank_score: 1, constituent_facts_array: ['f3'] })
    expect(deriveSignalEntity(s, new Map([['f3', 'D1_LAGNA']]))).toBe('UNATTRIBUTED')
  })
})

describe('buildHierarchicalProfiles — WP-1.2(a) UNATTRIBUTED never top + resolvable fact_ids', () => {
  it('attributes per-varga signals via fact_subject, draining UNATTRIBUTED', () => {
    const scored = [
      sig({ signal_id: 's1', final_rank_score: 0.9, configuration_jsonb: { fact_key: 'dignity_state', varga: 'D108' }, constituent_facts_array: ['fA'] }),
      sig({ signal_id: 's2', final_rank_score: 0.8, configuration_jsonb: { fact_key: 'dignity_state', varga: 'D9' }, constituent_facts_array: ['fB'] }),
    ]
    const map = new Map([['fA', 'D108_SAT'], ['fB', 'D9_SAT']])
    const profiles = buildHierarchicalProfiles(scored, 10, 3, { factSubjectByFactId: map })
    expect(profiles).toHaveLength(1)
    expect(profiles[0].entity).toBe('SATURN')
    expect(profiles[0].entity_type).toBe('graha')
    expect(profiles[0].fact_ids.sort()).toEqual(['fA', 'fB'])
  })

  it('a real graha ALWAYS outranks the UNATTRIBUTED bucket even when UNATTRIBUTED has a larger summed score', () => {
    // 3 unattributed atoms summing to 1.5 vs one Saturn atom at 0.9 — pre-fix the sum-of-scores
    // would put UNATTRIBUTED on top. The ordering guard forbids it.
    const scored = [
      sig({ signal_id: 'u1', final_rank_score: 0.5 }),
      sig({ signal_id: 'u2', final_rank_score: 0.5 }),
      sig({ signal_id: 'u3', final_rank_score: 0.5 }),
      sig({ signal_id: 'sat', final_rank_score: 0.9, configuration_jsonb: { graha: 'Saturn' } }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 10, 3)
    expect(profiles[0].entity).toBe('SATURN')
    expect(profiles[0].entity_type).toBe('graha')
    const unattr = profiles.find(p => p.entity === 'UNATTRIBUTED')!
    expect(unattr).toBeDefined()
    expect(profiles.indexOf(unattr)).toBeGreaterThan(0) // never index 0
  })

  it('surfaces only resolvable fact_ids when a resolvability map is supplied (§N.5)', () => {
    const scored = [
      sig({ signal_id: 's1', final_rank_score: 0.9, configuration_jsonb: { graha: 'Mars' }, constituent_facts_array: ['good', 'orphan'] }),
    ]
    // only 'good' is present in the map → 'orphan' must not be surfaced
    const map = new Map([['good', 'D1_MAR']])
    const profiles = buildHierarchicalProfiles(scored, 10, 3, { factSubjectByFactId: map })
    expect(profiles[0].fact_ids).toEqual(['good'])
    expect(profiles[0].fact_ids).not.toContain('orphan')
  })
})
