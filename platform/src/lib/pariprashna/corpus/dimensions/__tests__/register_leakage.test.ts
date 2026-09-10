import { describe, expect, it } from 'vitest'

import { baseObservation, baseTurnMetrics } from '../../__tests__/test_helpers'
import { scoreRegisterLeakage } from '../register_leakage'

describe('scoreRegisterLeakage', () => {
  it('scores 1.0 when the register-leak lint never fired', () => {
    const result = scoreRegisterLeakage(baseObservation())
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('scores low and flags a high fire rate', () => {
    const turnMetrics = baseTurnMetrics({ register_lint: { delta_calls: 10, fires: 4, leaks_total: 9 } })
    const result = scoreRegisterLeakage(baseObservation({ turnMetrics }))
    expect(result.status).toBe('scored')
    expect(result.score).toBeCloseTo(0.6)
    expect(result.findings.some((f) => f.includes('4/10'))).toBe(true)
  })

  it('returns not_yet_measurable when no TurnMetricsSnapshot was supplied', () => {
    const result = scoreRegisterLeakage(baseObservation({ turnMetrics: null }))
    expect(result.status).toBe('not_yet_measurable')
    expect(result.score).toBeNull()
  })
})
