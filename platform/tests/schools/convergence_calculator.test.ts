import { describe, it, expect } from 'vitest'
import {
  computeConvergence,
  detectDivergence,
  buildConvergenceNarrative,
} from '@/lib/schools/convergence_calculator'
import type { SchoolResult, Domain } from '@/lib/schools/types'

function makeResult(school: SchoolResult['school'], score: number, direction: SchoolResult['direction'], domain: Domain = 'CAREER'): SchoolResult {
  return {
    school,
    domain,
    domainScore: score,
    direction,
    topSignals: [],
    schoolVerdict: 'Test verdict',
    signalCoverage: 'primary',
  }
}

const HIGH_CONVERGENCE_RESULTS: SchoolResult[] = [
  makeResult('parashari', 4.2, 'positive'),
  makeResult('jaimini',   4.0, 'positive'),
  makeResult('kp',        3.8, 'positive'),
  makeResult('nadi',      3.5, 'positive'),
  makeResult('bnn',       3.3, 'positive'),
  makeResult('yogini',    3.6, 'positive'),
  makeResult('tajika',    3.1, 'positive'),
]

const MEDIUM_CONVERGENCE_RESULTS: SchoolResult[] = [
  makeResult('parashari', 4.0, 'positive'),
  makeResult('jaimini',   3.8, 'positive'),
  makeResult('kp',        3.5, 'positive'),
  makeResult('nadi',      3.2, 'positive'),
  makeResult('bnn',       2.0, 'negative'),
  makeResult('yogini',    1.8, 'negative'),
  makeResult('tajika',    1.5, 'negative'),   // 4 positive / 3 negative → MEDIUM
]

const LOW_CONVERGENCE_RESULTS: SchoolResult[] = [
  makeResult('parashari', 4.0, 'positive'),
  makeResult('jaimini',   3.8, 'positive'),
  makeResult('kp',        1.5, 'negative'),
  makeResult('nadi',      1.8, 'negative'),
  makeResult('bnn',       2.5, 'neutral'),
  makeResult('yogini',    1.2, 'negative'),
  makeResult('tajika',    4.0, 'positive'),
]

describe('computeConvergence', () => {
  it('7/7 positive → HIGH convergence', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    expect(c.convergenceLevel).toBe('HIGH')
    expect(c.schoolsAgreeing).toBe(7)
    expect(c.schoolsTotal).toBe(7)
  })

  it('4/7 positive → MEDIUM convergence', () => {
    const c = computeConvergence(MEDIUM_CONVERGENCE_RESULTS, 'CAREER')
    expect(c.convergenceLevel).toBe('MEDIUM')
    expect(c.schoolsAgreeing).toBe(4)
  })

  it('3/7 plurality → LOW convergence', () => {
    // 3 negative, 2 positive, 1 neutral + 1 positive with Tajika present
    // Actually: 3 negative, 2+1 positive = 3, 1 neutral → tie → mode picks first → need to check
    const c = computeConvergence(LOW_CONVERGENCE_RESULTS, 'CAREER')
    expect(c.convergenceLevel).toBe('LOW')
  })

  it('Tajika excluded from schoolsTotal when VARSHA_KUNDALI_PENDING', () => {
    const resultsWithPendingTajika: SchoolResult[] = [
      ...HIGH_CONVERGENCE_RESULTS.filter(r => r.school !== 'tajika'),
      {
        ...makeResult('tajika', 3.0, 'positive'),
        pendingFlags: ['[VARSHA_KUNDALI_PENDING]'],
      }
    ]
    const c = computeConvergence(resultsWithPendingTajika, 'CAREER')
    expect(c.schoolsTotal).toBe(6)  // Tajika excluded
    expect(c.schoolsAgreeing).toBe(6)  // All 6 effective schools agree
    expect(c.convergenceLevel).toBe('HIGH')  // 6 >= 5
  })

  it('mean and std are computed correctly', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    const expectedMean = (4.2 + 4.0 + 3.8 + 3.5 + 3.3 + 3.6 + 3.1) / 7
    expect(c.meanDomainScore).toBeCloseTo(expectedMean, 2)
    expect(c.stdDomainScore).toBeGreaterThan(0)
  })

  it('perSchoolScores contains all 7 schools', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    expect(Object.keys(c.perSchoolScores).sort()).toEqual(
      ['bnn', 'jaimini', 'kp', 'nadi', 'parashari', 'tajika', 'yogini']
    )
  })

  it('throws on empty results', () => {
    expect(() => computeConvergence([], 'CAREER')).toThrow()
  })

  it('direction is mixed when schools disagree significantly', () => {
    const c = computeConvergence(LOW_CONVERGENCE_RESULTS, 'CAREER')
    // < 70% threshold for non-mixed
    expect(c.direction).toBe('mixed')
  })

  it('direction is positive when all agree positive', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    expect(c.direction).toBe('positive')
  })

  it('domain is preserved on convergence output', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'HEALTH')
    // domain passed but results have CAREER — that's fine, domain param wins
    expect(c.domain).toBe('HEALTH')
  })
})

describe('detectDivergence', () => {
  it('isDivergent=false when < 2 schools contradict', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    const div = detectDivergence(HIGH_CONVERGENCE_RESULTS, c)
    expect(div.isDivergent).toBe(false)
    expect(div.schoolsContradict.length).toBe(0)
  })

  it('isDivergent=true when ≥ 2 schools contradict', () => {
    const c = computeConvergence(MEDIUM_CONVERGENCE_RESULTS, 'CAREER')
    const div = detectDivergence(MEDIUM_CONVERGENCE_RESULTS, c)
    // bnn=negative + yogini=negative → 2 contradictions to positive plurality → divergent
    expect(div.isDivergent).toBe(true)
    expect(div.schoolsContradict.length).toBeGreaterThanOrEqual(2)
  })

  it('plurality direction agrees with computeConvergence', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    const div = detectDivergence(HIGH_CONVERGENCE_RESULTS, c)
    expect(div.pluralityDirection).toBe('positive')
  })
})

describe('buildConvergenceNarrative', () => {
  it('narrative contains convergence level', () => {
    const c = computeConvergence(HIGH_CONVERGENCE_RESULTS, 'CAREER')
    const div = detectDivergence(HIGH_CONVERGENCE_RESULTS, c)
    const n = buildConvergenceNarrative(c, div)
    expect(n).toContain('CAREER')
    expect(n).toContain('7/7')
  })

  it('divergence narrative appears when isDivergent=true', () => {
    const c = computeConvergence(MEDIUM_CONVERGENCE_RESULTS, 'CAREER')
    const div = detectDivergence(MEDIUM_CONVERGENCE_RESULTS, c)
    const n = buildConvergenceNarrative(c, div)
    expect(n).toContain('DIVERGENCE')
  })

  it('pending note appears when schoolsTotal < 7', () => {
    const resultsWithPendingTajika: SchoolResult[] = [
      ...HIGH_CONVERGENCE_RESULTS.filter(r => r.school !== 'tajika'),
      { ...makeResult('tajika', 3.0, 'positive'), pendingFlags: ['[VARSHA_KUNDALI_PENDING]'] }
    ]
    const c = computeConvergence(resultsWithPendingTajika, 'CAREER')
    const div = detectDivergence(resultsWithPendingTajika, c)
    const n = buildConvergenceNarrative(c, div)
    expect(n).toContain('excluded')
    expect(n).toContain('pending')
  })
})
