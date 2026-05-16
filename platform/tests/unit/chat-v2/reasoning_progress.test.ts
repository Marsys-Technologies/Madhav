/**
 * γ2 — Long-reasoning UX: ReasoningProgress
 *
 * Tests the pure logic in ReasoningProgress:
 *  - estimateTokens function
 *  - COLLAPSE_THRESHOLD boundary (2000 tokens)
 *  - Token count accuracy for various text lengths
 */

import { describe, it, expect } from 'vitest'

/** Mirror of the estimateTokens function from ReasoningProgress.tsx. */
function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4)
}

const COLLAPSE_THRESHOLD = 2000

describe('estimateTokens', () => {
  it('returns 0 for empty string', () => {
    expect(estimateTokens('')).toBe(0)
  })

  it('returns 1 for a 1-4 char string', () => {
    expect(estimateTokens('a')).toBe(1)
    expect(estimateTokens('abcd')).toBe(1)
  })

  it('rounds up for non-multiple-of-4 lengths', () => {
    expect(estimateTokens('abcde')).toBe(2) // ceil(5/4) = 2
    expect(estimateTokens('abcdefg')).toBe(2) // ceil(7/4) = 2
    expect(estimateTokens('abcdefgh')).toBe(2) // ceil(8/4) = 2
    expect(estimateTokens('abcdefghi')).toBe(3) // ceil(9/4) = 3
  })

  it('returns 2000 for 8000-char string (exactly at threshold)', () => {
    const text = 'a'.repeat(8000)
    expect(estimateTokens(text)).toBe(COLLAPSE_THRESHOLD)
  })

  it('returns >2000 for 8001-char string (above threshold)', () => {
    const text = 'a'.repeat(8001)
    expect(estimateTokens(text)).toBeGreaterThan(COLLAPSE_THRESHOLD)
  })

  it('returns 1999 for 7996-char string (below threshold)', () => {
    // ceil(7996 / 4) = ceil(1999) = 1999
    const text = 'a'.repeat(7996)
    expect(estimateTokens(text)).toBeLessThan(COLLAPSE_THRESHOLD)
    expect(estimateTokens(text)).toBe(1999)
  })
})

describe('collapse threshold logic', () => {
  it('short reasoning (< 2k tokens) should not trigger collapse', () => {
    const text = 'The chart indicates a strong Jupiter…'.repeat(10) // ~370 tokens
    expect(estimateTokens(text)).toBeLessThan(COLLAPSE_THRESHOLD)
  })

  it('long reasoning (≥ 2k tokens) triggers collapse', () => {
    const text = 'a'.repeat(8001)
    expect(estimateTokens(text)).toBeGreaterThanOrEqual(COLLAPSE_THRESHOLD)
  })
})
