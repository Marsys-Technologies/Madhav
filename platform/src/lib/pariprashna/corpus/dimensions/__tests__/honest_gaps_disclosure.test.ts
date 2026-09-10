import { describe, expect, it } from 'vitest'

import { baseObservation, baseReceipt } from '../../__tests__/test_helpers'
import { scoreHonestGapsDisclosure } from '../honest_gaps_disclosure'

describe('scoreHonestGapsDisclosure', () => {
  it('scores 1.0 when honest_gaps.gaps.length matches coverage.empty + coverage.dark', () => {
    // baseReceipt: coverage.empty=1, coverage.dark=1 -> expected 2, but honest_gaps has 1 entry.
    // Build a coherent receipt explicitly instead of relying on the base default.
    const receipt = baseReceipt({
      coverage: {
        status: 'measured',
        served: 8,
        empty: 1,
        dark: 0,
        floor_item_total: 9,
        channel: 'web',
        channel_note: null,
        unavailable_reason: null,
      },
      honest_gaps: {
        status: 'measured',
        gaps: [{ floor_item_id: 'floor-1', kind: 'empty', reason: 'no data' }],
        unavailable_reason: null,
      },
    })
    const result = scoreHonestGapsDisclosure(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
    expect(result.findings).toEqual([])
  })

  it('flags and lowers score when coverage reports gaps but honest_gaps is unavailable (hidden gap)', () => {
    const receipt = baseReceipt({
      honest_gaps: { status: 'unavailable', gaps: null, unavailable_reason: 'registry compile fault' },
    })
    const result = scoreHonestGapsDisclosure(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBe(0)
    expect(result.findings.length).toBeGreaterThan(0)
  })

  it('flags a count mismatch between coverage and honest_gaps', () => {
    const receipt = baseReceipt({
      coverage: {
        status: 'measured',
        served: 5,
        empty: 3,
        dark: 2,
        floor_item_total: 10,
        channel: 'web',
        channel_note: null,
        unavailable_reason: null,
      },
      honest_gaps: {
        status: 'measured',
        gaps: [{ floor_item_id: 'floor-1', kind: 'empty', reason: 'no data' }],
        unavailable_reason: null,
      },
    })
    const result = scoreHonestGapsDisclosure(baseObservation({ receipt }))
    expect(result.status).toBe('scored')
    expect(result.score).toBeLessThan(1)
    expect(result.findings[0]).toContain('5 empty+dark')
  })

  it('returns not_yet_measurable when no receipt was supplied', () => {
    const result = scoreHonestGapsDisclosure(baseObservation({ receipt: null }))
    expect(result.status).toBe('not_yet_measurable')
  })
})
