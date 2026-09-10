/**
 * Pacing-policy helper tests — lane G3-D / P2-L (PPR-04, roadmap line 104).
 */

import { describe, it, expect } from 'vitest'
import { isDifficultFindingActive, shouldForceDifficultBlockBreak, DIFFICULT_BLOCK_MAX_CHARS } from '../pacing'

describe('isDifficultFindingActive', () => {
  it('is false when safetyDecision is omitted (flag-off / older callers)', () => {
    expect(isDifficultFindingActive(undefined)).toBe(false)
  })

  it('is false when enforced is false, even with classes detected (the honest "not enforced" reading)', () => {
    expect(isDifficultFindingActive({ enforced: false, classes_detected: ['hs3_health_crisis'] })).toBe(false)
  })

  it('is false when enforced is true but nothing fired', () => {
    expect(isDifficultFindingActive({ enforced: true, classes_detected: [] })).toBe(false)
  })

  it('is true when enforced is true AND at least one HS-class fired', () => {
    expect(isDifficultFindingActive({ enforced: true, classes_detected: ['hs4_mortality_window'] })).toBe(true)
  })
})

describe('shouldForceDifficultBlockBreak', () => {
  it('is false below the length floor', () => {
    expect(shouldForceDifficultBlockBreak('Short block.')).toBe(false)
  })

  it('is false at/above the floor if not at a sentence boundary', () => {
    const long = 'a'.repeat(DIFFICULT_BLOCK_MAX_CHARS) // no trailing punctuation
    expect(shouldForceDifficultBlockBreak(long)).toBe(false)
  })

  it('is true at/above the floor AND at a sentence boundary', () => {
    const long = 'a'.repeat(DIFFICULT_BLOCK_MAX_CHARS - 1) + '.'
    expect(shouldForceDifficultBlockBreak(long)).toBe(true)
  })

  it('accepts a sentence boundary followed by a closing quote', () => {
    const long = 'a'.repeat(DIFFICULT_BLOCK_MAX_CHARS - 2) + '."'
    expect(shouldForceDifficultBlockBreak(long)).toBe(true)
  })
})
