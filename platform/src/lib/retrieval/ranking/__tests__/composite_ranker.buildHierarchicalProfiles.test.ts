/**
 * composite_ranker.buildHierarchicalProfiles.test.ts — unit tests for the R5 W1
 * (design §E-6) hierarchical-aggregation entity grouping added to the
 * signals/synthesis_query lane (see R5_RUN_LEDGER W1 lane report + JL-009(a)).
 *
 * No DB required — pure function over a hand-built ScoredSignal[] pool.
 * Covers item 3(a) of the Ring-1 reconciliation brief: "buildHierarchicalProfiles
 * groups signals by primary graha correctly" with a few concrete cases.
 */
import { describe, it, expect } from 'vitest'
import { buildHierarchicalProfiles, type ScoredSignal } from '../composite_ranker'

function sig(overrides: Partial<ScoredSignal> & { signal_id: string; final_rank_score: number }): ScoredSignal {
  return {
    signal_type_class: 'yoga',
    domains_affected_array: [],
    valence: null,
    configuration_jsonb: null,
    composite_score: overrides.composite_score ?? overrides.final_rank_score,
    percentile_within_class: 1.0,
    _subscores: {
      class_prior: 1, topic_relevance: 1, intrinsic_strength: 1,
      structural_role: 1, temporal_activation: 1, priors_version: 'test',
    },
    ...overrides,
  } as ScoredSignal
}

describe('buildHierarchicalProfiles — entity grouping by primary graha (JL-009(a))', () => {
  it('groups signals sharing the same configuration_jsonb.graha into one entity profile', () => {
    const scored: ScoredSignal[] = [
      sig({ signal_id: 's1', final_rank_score: 0.9, configuration_jsonb: { graha: 'Saturn' } }),
      sig({ signal_id: 's2', final_rank_score: 0.7, configuration_jsonb: { graha: 'Saturn' } }),
      sig({ signal_id: 's3', final_rank_score: 0.5, configuration_jsonb: { graha: 'Moon' } }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 10, 3)

    expect(profiles).toHaveLength(2)
    const saturn = profiles.find(p => p.entity === 'SATURN')!
    expect(saturn).toBeDefined()
    expect(saturn.entity_type).toBe('graha')
    expect(saturn.signal_count).toBe(2)
    expect(saturn.top_signal_ids).toEqual(['s1', 's2']) // sorted by final_rank_score desc
    expect(saturn.peak_score).toBeCloseTo(0.9)
    expect(saturn.aggregate_score).toBeCloseTo(1.6) // 0.9 + 0.7

    const moon = profiles.find(p => p.entity === 'MOON')!
    expect(moon.signal_count).toBe(1)
  })

  it('recognizes primary_graha, lord_graha, planet, graha_key, karaka_graha as equivalent keys (extractPrimaryGraha fallback chain)', () => {
    const scored: ScoredSignal[] = [
      sig({ signal_id: 'a', final_rank_score: 0.5, configuration_jsonb: { primary_graha: 'Mars' } }),
      sig({ signal_id: 'b', final_rank_score: 0.5, configuration_jsonb: { lord_graha: 'Mars' } }),
      sig({ signal_id: 'c', final_rank_score: 0.5, configuration_jsonb: { planet: 'Mars' } }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 10, 3)
    expect(profiles).toHaveLength(1)
    expect(profiles[0].entity).toBe('MARS')
    expect(profiles[0].signal_count).toBe(3)
  })

  it('buckets signals with no resolvable graha into a single "unattributed" entity, never dropped', () => {
    const scored: ScoredSignal[] = [
      sig({ signal_id: 'x', final_rank_score: 0.6, configuration_jsonb: null }),
      sig({ signal_id: 'y', final_rank_score: 0.4, configuration_jsonb: {} }),
      sig({ signal_id: 'z', final_rank_score: 0.9, configuration_jsonb: { graha: 'Venus' } }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 10, 3)
    const unattributed = profiles.find(p => p.entity === 'UNATTRIBUTED')!
    expect(unattributed).toBeDefined()
    expect(unattributed.entity_type).toBe('unattributed')
    expect(unattributed.signal_count).toBe(2)
    const venus = profiles.find(p => p.entity === 'VENUS')!
    expect(venus.signal_count).toBe(1)
  })

  it('sorts profiles by aggregate_score descending and caps at top_k_entities', () => {
    const scored: ScoredSignal[] = [
      sig({ signal_id: 's1', final_rank_score: 0.9, configuration_jsonb: { graha: 'Saturn' } }),
      sig({ signal_id: 's2', final_rank_score: 0.85, configuration_jsonb: { graha: 'Sun' } }),
      sig({ signal_id: 's3', final_rank_score: 0.1, configuration_jsonb: { graha: 'Mercury' } }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 2, 3)
    expect(profiles).toHaveLength(2)
    expect(profiles[0].entity).toBe('SATURN')
    expect(profiles[1].entity).toBe('SUN')
  })

  it('never recomputes a score — aggregate/peak are pure sums/max of already-computed final_rank_score (B.10)', () => {
    const scored: ScoredSignal[] = [
      sig({ signal_id: 's1', final_rank_score: 0.3, configuration_jsonb: { graha: 'Jupiter' } }),
      sig({ signal_id: 's2', final_rank_score: 0.2, configuration_jsonb: { graha: 'Jupiter' } }),
      sig({ signal_id: 's3', final_rank_score: 0.4, configuration_jsonb: { graha: 'Jupiter' } }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 10, 3)
    expect(profiles[0].aggregate_score).toBeCloseTo(0.9)
    expect(profiles[0].peak_score).toBeCloseTo(0.4)
  })

  it('tracks dominant_domains and dominant_valence by frequency across the group', () => {
    const scored: ScoredSignal[] = [
      sig({ signal_id: 's1', final_rank_score: 0.5, configuration_jsonb: { graha: 'Saturn' }, domains_affected_array: ['career'], valence: 'malefic' }),
      sig({ signal_id: 's2', final_rank_score: 0.4, configuration_jsonb: { graha: 'Saturn' }, domains_affected_array: ['career', 'health'], valence: 'malefic' }),
      sig({ signal_id: 's3', final_rank_score: 0.3, configuration_jsonb: { graha: 'Saturn' }, domains_affected_array: ['wealth'], valence: 'benefic' }),
    ]
    const profiles = buildHierarchicalProfiles(scored, 10, 3)
    expect(profiles[0].dominant_domains[0]).toBe('career')
    expect(profiles[0].dominant_valence).toBe('malefic')
  })
})
