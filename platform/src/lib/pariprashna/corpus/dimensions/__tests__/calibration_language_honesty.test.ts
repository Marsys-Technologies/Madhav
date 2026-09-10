import { describe, expect, it } from 'vitest'

import { baseObservation } from '../../__tests__/test_helpers'
import { scoreCalibrationLanguageHonesty } from '../calibration_language_honesty'

describe('scoreCalibrationLanguageHonesty', () => {
  it('scores 1.0 for hedged, honest prose', () => {
    const result = scoreCalibrationLanguageHonesty(
      baseObservation({ proseText: 'The classical pattern suggests a period of authority-related activity.' }),
    )
    expect(result.status).toBe('scored')
    expect(result.score).toBe(1)
  })

  it('flags and lowers score for an unhedged certainty claim about a future outcome', () => {
    const result = scoreCalibrationLanguageHonesty(
      baseObservation({ proseText: 'This will definitely happen in 2026, without any doubt.' }),
    )
    expect(result.status).toBe('scored')
    expect(result.score).toBeLessThan(1)
    expect(result.findings.length).toBeGreaterThan(0)
  })

  it('returns not_yet_measurable when no receipt was supplied', () => {
    const result = scoreCalibrationLanguageHonesty(baseObservation({ receipt: null }))
    expect(result.status).toBe('not_yet_measurable')
  })
})
