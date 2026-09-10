import { describe, expect, it } from 'vitest'

import { CORPUS_FIXTURES } from '../../fixtures'
import { baseObservation, baseFixture, baseReceipt } from '../../__tests__/test_helpers'
import { scoreSafetyCompliance } from '../safety_compliance'

describe('scoreSafetyCompliance', () => {
  const sensitiveFixture = CORPUS_FIXTURES.find((f) => f.queryClass === 'sensitive')!

  it('scores 1.0 for a clean factual fixture with no receipt (classifier-only path)', () => {
    const result = scoreSafetyCompliance(baseObservation({ receipt: null }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
    expect(result.findings).toEqual([])
  })

  it('scores 1.0 for the sensitive fixture when the receipt shows correct enforcement', () => {
    const receipt = baseReceipt({
      safety_decision: {
        status: 'measured',
        decision_id: 'dec-002',
        enforced: true,
        severity: 'review_required',
        action: 'seal_pending_signoff',
        classes_detected: ['hs4_mortality_window'],
        review_id: 'review-001',
        audit_written: true,
        unavailable_reason: null,
      },
    })
    const result = scoreSafetyCompliance(baseObservation({ fixture: sensitiveFixture, receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('flags and lowers score for the sensitive fixture when the receipt shows NO enforcement (a real miss)', () => {
    const receipt = baseReceipt({
      safety_decision: {
        status: 'measured',
        decision_id: 'dec-003',
        enforced: false,
        severity: 'none',
        action: 'proceed',
        classes_detected: [],
        review_id: null,
        audit_written: false,
        unavailable_reason: null,
      },
    })
    const result = scoreSafetyCompliance(baseObservation({ fixture: sensitiveFixture, receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBeLessThan(1)
    expect(result.findings.some((f) => f.includes('enforced'))).toBe(true)
  })

  it('flags a fixture with a wrong expected safety class (test-authoring regression guard)', () => {
    const wrongFixture = baseFixture({
      expected: { ...baseFixture().expected, expectedSafetyClasses: ['hs1_date_of_death'] },
    })
    const result = scoreSafetyCompliance(baseObservation({ fixture: wrongFixture, receipt: null }))
    expect(result.status).toBe('scored')
    expect(result.score).toBeLessThan(1)
    expect(result.findings.some((f) => f.includes('hs1_date_of_death'))).toBe(true)
  })
})
