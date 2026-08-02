/**
 * kala_ritual_resonance.test.ts — ṢAḌ-DARŚANA W4 Lane R, items 37 + 6.
 *
 * The two assertions that carry the weight here:
 *   1. THE RENORMALISATION RULE (gate G5) — an absent factor is DROPPED and the
 *      product renormalised over PRESENT factors, never imputed, never zero-filled,
 *      and the served vector always names the split. A test that only checked
 *      "composite is a number" would pass on a zero-filled vector, which is exactly
 *      the defect the rule exists to prevent, so these tests check the ARITHMETIC.
 *   2. THE ITEM-6 ID-PROVENANCE RAIL — the join reads `detail.factor_id` and NOTHING
 *      ELSE. An atom without a usable id must be counted unjoinable, never rescued by
 *      matching on `factor_key`: a name match IS the hand-mapped correspondence
 *      ADJUDICATION-10 refused (B.10).
 */
import { describe, it, expect } from 'vitest'
import {
  ACTIVITY_CLASSES,
  composeScoreVector,
  joinActivityRules,
  pickRite,
  scoreElectionQuality,
  scoreRarity,
  scoreRiteSpecificResonance,
  scoreStructuralResonance,
  scoreTemporalIntensity,
  type ActivityRuleRow,
  type ScoredFactor,
  type StructuralSubstrate,
} from './kala_ritual_resonance.js'
import type { LatticeFactorRow, LatticeSubstrate } from './kala_lattice_query.js'

const computed = (value: number): ScoredFactor => ({ value, state: 'computed', reason: null, source: 'test' })
const absent = (state: 'honest_empty' | 'not_computed'): ScoredFactor => ({
  value: null, state, reason: 'test-absent', source: 'test',
})

const atom = (family: string, key: string, detail: Record<string, unknown>): LatticeFactorRow => ({
  factor_family: family,
  factor_key: key,
  start_utc: '2026-08-06T00:00:00Z',
  end_utc: '2026-08-07T00:00:00Z',
  detail,
  source_citation: 'test',
  corpus_status: 'computed_cited',
})

describe('composeScoreVector — the renormalisation rule (gate G5)', () => {
  it('renormalises over PRESENT factors: 2 present at 0.8 and 0.5 gives their geometric mean, not a 5-way product', () => {
    const v = composeScoreVector({
      structural_resonance: computed(0.8),
      temporal_intensity: absent('not_computed'),
      election_quality: computed(0.5),
      rarity: absent('not_computed'),
      rite_specific_resonance: absent('honest_empty'),
    })
    // Zero-filling would give 0. Treating absent as 1.0 would give 0.4^(1/5).
    // The correct answer is sqrt(0.8*0.5) = 0.6325.
    expect(v.composite).toBeCloseTo(Math.sqrt(0.8 * 0.5), 4)
    expect(v.factors_present).toEqual(['structural_resonance', 'election_quality'])
    expect(v.factors_absent).toEqual(['temporal_intensity', 'rarity', 'rite_specific_resonance'])
  })

  it('an absent factor is NEVER zero-filled — one strong present factor still scores strongly', () => {
    const v = composeScoreVector({
      structural_resonance: computed(0.9),
      temporal_intensity: absent('not_computed'),
      election_quality: absent('honest_empty'),
      rarity: absent('not_computed'),
      rite_specific_resonance: absent('honest_empty'),
    })
    expect(v.composite).toBeCloseTo(0.9, 4)
    expect(v.factors_present).toEqual(['structural_resonance'])
  })

  it('ALL factors absent yields composite null — an honest empty score, not a zero', () => {
    const v = composeScoreVector({
      structural_resonance: absent('honest_empty'),
      temporal_intensity: absent('not_computed'),
      election_quality: absent('honest_empty'),
      rarity: absent('not_computed'),
      rite_specific_resonance: absent('honest_empty'),
    })
    expect(v.composite).toBeNull()
    expect(v.factors_present).toEqual([])
    expect(v.factors_absent).toHaveLength(5)
  })

  it('every vector states the present/absent split, so a 2-factor score can never read as a 5-factor one', () => {
    const v = composeScoreVector({
      structural_resonance: computed(0.5),
      temporal_intensity: absent('not_computed'),
      election_quality: computed(0.5),
      rarity: absent('not_computed'),
      rite_specific_resonance: absent('honest_empty'),
    })
    expect(v.factors_present.length + v.factors_absent.length).toBe(5)
    expect(v.composite_method).toMatch(/renormalised over PRESENT factors/)
    expect(v.composite_method).toMatch(/never imputed and never/)
  })

  it('a factor whose state is `computed` but whose value is null does NOT enter the product', () => {
    // Defensive: the type permits it, and silently treating it as present would be
    // exactly the imputation gate G5 forbids.
    const malformed: ScoredFactor = { value: null, state: 'computed', reason: null, source: 'test' }
    const v = composeScoreVector({
      structural_resonance: malformed,
      temporal_intensity: computed(0.4),
      election_quality: absent('honest_empty'),
      rarity: absent('not_computed'),
      rite_specific_resonance: absent('honest_empty'),
    })
    expect(v.factors_present).toEqual(['temporal_intensity'])
    expect(v.composite).toBeCloseTo(0.4, 4)
  })
})

describe('the honest-absent factors name their reason (never a bare null)', () => {
  it('temporal_intensity names the N_e blocker and the renormalisation consequence', () => {
    const f = scoreTemporalIntensity()
    expect(f.state).toBe('not_computed')
    expect(f.value).toBeNull()
    expect(f.reason).toMatch(/ka_kshetra/)
    expect(f.reason).toMatch(/never zero-filled/)
  })

  it('rarity names bg_cohort and refuses to invent a scarcity score from the candidate count', () => {
    const f = scoreRarity()
    expect(f.state).toBe('not_computed')
    expect(f.reason).toMatch(/bg_cohort/)
    expect(f.reason).toMatch(/fabricated comparison/)
  })
})

describe('item 6 — joinActivityRules: the ID-PROVENANCE RAIL', () => {
  const rules: ActivityRuleRow[] = [
    { activity_class: 'upaya_ritual', factor_type: 'vara', factor_id: 5, quality_score: 0.9, source_citation: 'MC Upaya ch.' },
    { activity_class: 'upaya_ritual', factor_type: 'nakshatra', factor_id: 2, quality_score: 0.5, source_citation: 'MC Upaya ch.' },
    { activity_class: 'vivah', factor_type: 'vara', factor_id: 5, quality_score: 0.1, source_citation: 'MC 3.2' },
  ]

  it('joins on detail.factor_id and averages the matched rules', () => {
    const atoms = [
      atom('vara', 'guruvara', { factor_id: 5 }),
      atom('nakshatra', 'bharani', { factor_id: 2 }),
    ]
    const out = joinActivityRules(atoms, rules, 'upaya_ritual')
    expect(out.score).toBeCloseTo((0.9 + 0.5) / 2, 4)
    expect(out.matched).toHaveLength(2)
    expect(out.unjoinable_atoms).toBe(0)
    expect(out.matched.every((m) => m.source_citation.length > 0)).toBe(true)
  })

  it('respects activity_class — a vivah rule never scores an upaya_ritual query', () => {
    const out = joinActivityRules([atom('vara', 'guruvara', { factor_id: 5 })], rules, 'vivah')
    expect(out.score).toBeCloseTo(0.1, 4)
  })

  it('THE RAIL: an atom with no usable factor_id is counted UNJOINABLE, never matched by name', () => {
    // `guruvara` is the very name a hand-written map would resolve to id 5. The join
    // must refuse — that map is the B.10 fabrication ADJUDICATION-10 rejected.
    const atoms = [atom('vara', 'guruvara', { name: 'Guruvara' })]
    const out = joinActivityRules(atoms, rules, 'upaya_ritual')
    expect(out.score).toBeNull()
    expect(out.matched).toHaveLength(0)
    expect(out.unjoinable_atoms).toBe(1)
    expect(out.reason).toMatch(/detail\.factor_id/)
    expect(out.reason).toMatch(/B\.10/)
  })

  it('a non-numeric factor_id is unjoinable too (no coercion rescue)', () => {
    const out = joinActivityRules([atom('vara', 'guruvara', { factor_id: 'five' })], rules, 'upaya_ritual')
    expect(out.unjoinable_atoms).toBe(1)
    expect(out.score).toBeNull()
  })

  it('non-joinable families (hora, kalam, lagna) are ignored, not counted as unjoinable', () => {
    const out = joinActivityRules(
      [atom('hora', 'hora_jupiter', { lord: 'Jupiter' }), atom('vara', 'guruvara', { factor_id: 5 })],
      rules,
      'upaya_ritual',
    )
    expect(out.unjoinable_atoms).toBe(0)
    expect(out.matched).toHaveLength(1)
  })

  it('an honest empty join (no rule for these ids) is distinguished from a broken rail', () => {
    const out = joinActivityRules([atom('tithi', 'krishna_ashtami', { factor_id: 23 })], rules, 'upaya_ritual')
    expect(out.score).toBeNull()
    expect(out.unjoinable_atoms).toBe(0)
    expect(out.reason).toMatch(/sparse by construction/)
    expect(out.reason).not.toMatch(/B\.10/)
  })

  it('de-duplicates repeated atoms of the same (family, id) so a long horizon cannot skew the mean', () => {
    const atoms = [atom('vara', 'guruvara', { factor_id: 5 }), atom('vara', 'guruvara', { factor_id: 5 })]
    const out = joinActivityRules(atoms, rules, 'upaya_ritual')
    expect(out.matched).toHaveLength(1)
    expect(out.score).toBeCloseTo(0.9, 4)
  })

  it('scoreRiteSpecificResonance carries the join reason through as an honest_empty', () => {
    const empty = joinActivityRules([], rules, 'upaya_ritual')
    const f = scoreRiteSpecificResonance(empty, 'upaya_ritual')
    expect(f.state).toBe('honest_empty')
    expect(f.value).toBeNull()
    expect(f.source).toMatch(/panchang_engine/)
  })

  it('the eight activity classes match bg_muhurta_activity_rules\' own CHECK vocabulary', () => {
    expect([...ACTIVITY_CLASSES].sort()).toEqual([
      'griha_pravesh', 'mantra_initiation', 'property_purchase', 'sadhana_initiation',
      'upaya_ritual', 'vivah', 'vyapara', 'yatra',
    ])
  })
})

describe('structural resonance — three legs, one missing, stated not imputed', () => {
  const substrate = (over: Partial<StructuralSubstrate> = {}): StructuralSubstrate => ({
    remedy_rows: [], resonance_rows: [],
    remedy_available: true, resonance_available: true,
    activity_ontology_available: false,
    missing_legs: ['brahma_activity_ontology (no retrieval capability)'],
    ...over,
  })

  it('scores from the two available legs and NAMES the third in its reason', () => {
    const f = scoreStructuralResonance(
      { planet: 'Jupiter', deity: 'Brihaspati', remedy_type: 'mantra' },
      substrate({ resonance_rows: [{ graha: 'Jupiter', resonance_score: 0.75 }] }),
    )
    expect(f.state).toBe('computed')
    expect(f.value).toBeCloseTo(0.75, 4)
    expect(f.reason).toMatch(/TWO of three legs/)
    expect(f.reason).toMatch(/brahma_activity_ontology/)
    expect(f.reason).toMatch(/NOT imputed/)
  })

  it('honest_empty (never a default) when this chart has no resonance row for the rite\'s graha', () => {
    const f = scoreStructuralResonance(
      { planet: 'Saturn' },
      substrate({ resonance_rows: [{ graha: 'Jupiter', resonance_score: 0.75 }] }),
    )
    expect(f.state).toBe('honest_empty')
    expect(f.value).toBeNull()
    expect(f.reason).toMatch(/Saturn/)
  })

  it('honest_empty naming WHICH leg failed when a substrate read failed', () => {
    const f = scoreStructuralResonance({ planet: 'Jupiter' }, substrate({ resonance_available: false }))
    expect(f.state).toBe('honest_empty')
    expect(f.reason).toMatch(/brahma_activity_ontology/)
  })
})

describe('pickRite — selection, never composition (B.10)', () => {
  const substrate: StructuralSubstrate = {
    remedy_rows: [], resonance_rows: [
      { graha: 'Jupiter', resonance_score: 0.9 },
      { graha: 'Saturn', resonance_score: 0.3 },
    ],
    remedy_available: true, resonance_available: true,
    activity_ontology_available: false, missing_legs: [],
  }

  it('picks the cited rite whose graha this chart ranks highest', () => {
    const rite = pickRite(
      [
        { remedy_id: 'r1', planet: 'Saturn', citation: 'BPHS' },
        { remedy_id: 'r2', planet: 'Jupiter', citation: 'BPHS' },
      ],
      substrate,
    )
    expect(rite?.remedy_id).toBe('r2')
  })

  it('returns null when no cited rite\'s graha has a resonance row — no rite is composed to fill the gap', () => {
    expect(pickRite([{ remedy_id: 'r3', planet: 'Ketu', citation: 'BPHS' }], substrate)).toBeNull()
  })

  it('returns null on an empty cited set', () => {
    expect(pickRite([], substrate)).toBeNull()
  })

  it('is deterministic on a tie (total order, so repeated calls return the same rite)', () => {
    const tied = [
      { remedy_id: 'b', planet: 'Jupiter', citation: 'x' },
      { remedy_id: 'a', planet: 'Jupiter', citation: 'x' },
    ]
    expect(pickRite(tied, substrate)?.remedy_id).toBe('a')
    expect(pickRite([...tied].reverse(), substrate)?.remedy_id).toBe('a')
  })
})

describe('election quality — reads the FROZEN engine\'s ledger, introduces no second grader', () => {
  const substrate: LatticeSubstrate = {
    lattice_rows: [
      { ...atom('kalam', 'rahu_kalam', { category: 'inauspicious' }) },
      { ...atom('combination_yoga', 'sarvartha_siddhi', { strength: 'auspicious' }) },
    ],
    parihara_rules: [],
    census_rows: [],
    lattice_available: true,
    parihara_available: true,
    census_available: true,
    unavailable_reason: null,
  }

  it('a window with cited support and an uncancelled doṣa scores between 0 and 1 and cites the ledger counts', () => {
    const { factor, ledger } = scoreElectionQuality(
      { id: 'c0', start: '2026-08-06T01:00:00Z', end: '2026-08-06T02:00:00Z', score: 0, disqualified: false },
      substrate,
      'test',
    )
    expect(ledger).not.toBeNull()
    expect(factor.state).toBe('computed')
    expect(factor.value).toBeGreaterThan(0)
    expect(factor.value).toBeLessThanOrEqual(1)
    expect(factor.reason).toMatch(/residual doṣa/)
    expect(factor.source).toMatch(/FROZEN/)
  })

  it('honest_empty (not a clean verdict) when the lattice payload is unavailable', () => {
    const { factor } = scoreElectionQuality(
      { id: 'c0', start: '2026-08-06T01:00:00Z', end: '2026-08-06T02:00:00Z', score: 0, disqualified: false },
      { ...substrate, lattice_available: false, lattice_rows: [], unavailable_reason: 'payload unreadable' },
      'test',
    )
    expect(factor.state).toBe('honest_empty')
    expect(factor.value).toBeNull()
  })
})
