import { describe, expect, it } from 'vitest'

import { DIMENSION_IDS } from '../../types'
import {
  DIMENSION_REGISTRY,
  REAL_DETECTOR_DIMENSIONS,
  UNSCORED_STUB_DIMENSIONS,
  scoreAllDimensions,
} from '../index'
import { baseObservation } from '../../__tests__/test_helpers'

describe('dimension registry', () => {
  it('registers exactly the 13 dimensions named in types.ts', () => {
    expect(DIMENSION_REGISTRY.size).toBe(13)
    for (const id of DIMENSION_IDS) {
      expect(DIMENSION_REGISTRY.has(id)).toBe(true)
    }
  })

  it('REAL_DETECTOR_DIMENSIONS + UNSCORED_STUB_DIMENSIONS exactly partition all 13, no overlap', () => {
    expect(REAL_DETECTOR_DIMENSIONS.length + UNSCORED_STUB_DIMENSIONS.length).toBe(13)
    const union = new Set([...REAL_DETECTOR_DIMENSIONS, ...UNSCORED_STUB_DIMENSIONS])
    expect(union.size).toBe(13)
    const overlap = REAL_DETECTOR_DIMENSIONS.filter((d) => (UNSCORED_STUB_DIMENSIONS as readonly string[]).includes(d))
    expect(overlap).toEqual([])
  })

  it('scoreAllDimensions runs all 13 scorers and every unscored-stub dimension reports not_yet_measurable', () => {
    const results = scoreAllDimensions(baseObservation())
    expect(results).toHaveLength(13)
    for (const dim of UNSCORED_STUB_DIMENSIONS) {
      const r = results.find((x) => x.dimension === dim)
      expect(r?.status).toBe('not_yet_measurable')
      expect(r?.score).toBeNull()
    }
  })
})
