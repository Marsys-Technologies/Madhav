import { describe, expect, it } from 'vitest'

import { CORPUS_FIXTURES } from '../../fixtures'
import { baseObservation, baseFixture, baseReceipt } from '../../__tests__/test_helpers'
import { scoreCitationRecall } from '../citation_recall'

describe('scoreCitationRecall', () => {
  const crossDomainFixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'cross_domain_contradiction')!

  it('scores 1.0 when every expected ref was cited', () => {
    const result = scoreCitationRecall(baseObservation({ fixture: crossDomainFixture }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('scores 0 and flags when the expected ref was never cited', () => {
    const receipt = baseReceipt({ facts_consumed: [{ ref: 'SIG.MSR.001', layer: 'L2.5', index: 1 }] })
    const result = scoreCitationRecall(baseObservation({ fixture: crossDomainFixture, receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0)
    expect(result.findings.some((f) => f.includes('SIG.MSR.413'))).toBe(true)
  })

  it('returns not_yet_measurable for a fixture with no expectedSignalRefs ground truth', () => {
    const noRefsFixture = baseFixture({ expected: { ...baseFixture().expected, expectedSignalRefs: undefined } })
    const result = scoreCitationRecall(baseObservation({ fixture: noRefsFixture }))
    expect(result.status).toBe('not_yet_measurable')
    expect(result.score).toBeNull()
    expect(result.reason).toContain('expectedSignalRefs')
  })

  it('returns not_yet_measurable when no receipt was supplied, for a fixture that DOES carry ground truth', () => {
    const result = scoreCitationRecall(baseObservation({ fixture: crossDomainFixture, receipt: null }))
    expect(result.status).toBe('not_yet_measurable')
  })
})
