import { describe, expect, it } from 'vitest'

import { baseObservation, baseReceipt } from '../../__tests__/test_helpers'
import { scoreB11Coverage } from '../b11_coverage'

describe('scoreB11Coverage', () => {
  it('scores high when coverage is measured with good ratio and cross_domain has 2+ domains', () => {
    const result = scoreB11Coverage(baseObservation())
    expect(result.status).toBe('scored')
    expect(result.score).toBe((8 / 10 + 1) / 2)
    expect(result.findings).toEqual([])
  })

  it('scores 0 and flags when coverage and cross_domain are both unavailable', () => {
    const receipt = baseReceipt({
      coverage: {
        status: 'unavailable',
        served: null,
        empty: null,
        dark: null,
        floor_item_total: null,
        channel: null,
        channel_note: null,
        unavailable_reason: 'registry compile fault',
      },
      cross_domain: { status: 'unavailable', domains: null, unavailable_reason: 'plan.domains not populated' },
    })
    const result = scoreB11Coverage(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0)
    expect(result.findings.length).toBe(2)
  })

  it('returns not_yet_measurable when no receipt was supplied', () => {
    const result = scoreB11Coverage(baseObservation({ receipt: null }))
    expect(result.status).toBe('not_yet_measurable')
    expect(result.score).toBeNull()
  })
})
