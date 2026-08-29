import { describe, expect, it } from 'vitest'

import { baseObservation, baseReceipt } from '../../__tests__/test_helpers'
import { scoreCitationPrecision } from '../citation_precision'

describe('scoreCitationPrecision', () => {
  it('scores 1.0 when hallucination_count is 0', () => {
    const result = scoreCitationPrecision(baseObservation())
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('scores low and flags when unverified citations outnumber trustworthy ones', () => {
    // rewriter.ts's resolveSentinel: every unresolvable reference gets grade
    // 'unverified' AND increments the hallucination counter in the SAME branch
    // (citations/rewriter.ts:263-278) — grade_counts.unverified and
    // hallucination_count are the SAME event, always equal, never disjoint in
    // production. A trustworthy grade (primary/supporting/contextual/
    // prior_reading) is the ONLY thing that does NOT also increment the
    // counter. This fixture reflects that real invariant.
    const receipt = baseReceipt({
      evidence_grades: {
        status: 'measured',
        grade_counts: { primary: 1, supporting: 1, contextual: 0, unverified: 3, prior_reading: 0 },
        hallucination_count: 3,
        unavailable_reason: null,
      },
    })
    const result = scoreCitationPrecision(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBeCloseTo(2 / 5)
    expect(result.findings.length).toBeGreaterThan(0)
  })

  it('scores 0, not 0.5, when every citation attempt is unverified (the double-counting regression)', () => {
    // The defect this test guards against: an earlier version of this scorer
    // treated grade_counts.unverified as "resolved" (counted toward the
    // numerator) AND separately added hallucination_count to the denominator
    // — double-counting the SAME unresolvable citations twice and forcing the
    // score toward ~0.5 regardless of true quality, even when literally zero
    // citations ever reached a trustworthy grade. Confirmed live 2026-08-28:
    // 10/10 measured S3 corpus live turns against the deployed web door had
    // primary=supporting=contextual=prior_reading=0 and
    // hallucination_count === grade_counts.unverified in every turn (the
    // rewriter's structural invariant) — the old formula reported 0.5 for
    // all ten, masking a true 0.0 citation-precision turn every time.
    const receipt = baseReceipt({
      evidence_grades: {
        status: 'measured',
        grade_counts: { primary: 0, supporting: 0, contextual: 0, unverified: 8, prior_reading: 0 },
        hallucination_count: 8,
        unavailable_reason: null,
      },
    })
    const result = scoreCitationPrecision(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0)
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
