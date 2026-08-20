import { describe, expect, it } from 'vitest'

import { baseObservation, baseReceipt } from '../../__tests__/test_helpers'
import { scoreCitationPrecision } from '../citation_precision'

describe('scoreCitationPrecision', () => {
  it('scores 1.0 when hallucination_count is 0', () => {
    const result = scoreCitationPrecision(baseObservation())
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('scores low and flags when hallucinations outnumber resolved citations', () => {
    const receipt = baseReceipt({
      evidence_grades: {
        status: 'measured',
        grade_counts: { primary: 1, supporting: 1, contextual: 0, unverified: 0, prior_reading: 0 },
        hallucination_count: 3,
        unavailable_reason: null,
      },
    })
    const result = scoreCitationPrecision(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBeCloseTo(2 / 5)
    expect(result.findings.length).toBeGreaterThan(0)
  })

  it('returns not_yet_measurable when evidence_grades is unavailable (regex fallback path)', () => {
    const receipt = baseReceipt({
      evidence_grades: {
        status: 'unavailable',
        grade_counts: null,
        hallucination_count: null,
        unavailable_reason: 'PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED was off this turn',
      },
    })
    const result = scoreCitationPrecision(baseObservation({ receipt }))
    expect(result.status).toBe('not_yet_measurable')
    expect(result.score).toBeNull()
    expect(result.reason).toContain('PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED')
  })

  it('returns not_yet_measurable when no receipt was supplied', () => {
    const result = scoreCitationPrecision(baseObservation({ receipt: null }))
    expect(result.status).toBe('not_yet_measurable')
  })
})
