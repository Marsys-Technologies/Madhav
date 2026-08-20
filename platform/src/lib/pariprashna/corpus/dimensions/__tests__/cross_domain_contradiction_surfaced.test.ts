import { describe, expect, it } from 'vitest'

import { CORPUS_FIXTURES } from '../../fixtures'
import { baseObservation } from '../../__tests__/test_helpers'
import { scoreCrossDomainContradictionSurfaced } from '../cross_domain_contradiction_surfaced'

describe('scoreCrossDomainContradictionSurfaced', () => {
  const crossDomainFixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'cross_domain_contradiction')!
  const factualFixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'factual')!

  it('scores 1.0 when 2+ domains are authorized and prose names the tension', () => {
    const result = scoreCrossDomainContradictionSurfaced(
      baseObservation({
        fixture: crossDomainFixture,
        proseText: 'Mercury simultaneously activates career gains and 6th-house obstacles.',
      }),
    )
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
    expect(result.findings).toEqual([])
  })

  it('flags smoothing: no tension language even though domains are authorized', () => {
    const result = scoreCrossDomainContradictionSurfaced(
      baseObservation({ fixture: crossDomainFixture, proseText: 'Mercury is a strong career planet.' }),
    )
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0.5)
    expect(result.findings.some((f) => f.includes('smoothing'))).toBe(true)
  })

  it('returns not_yet_measurable for a non-cross-domain-contradiction fixture', () => {
    const result = scoreCrossDomainContradictionSurfaced(baseObservation({ fixture: factualFixture }))
    expect(result.status).toBe('not_yet_measurable')
  })

  it('returns not_yet_measurable when receipt or prose text is missing', () => {
    const result = scoreCrossDomainContradictionSurfaced(
      baseObservation({ fixture: crossDomainFixture, receipt: null }),
    )
    expect(result.status).toBe('not_yet_measurable')
  })
})
