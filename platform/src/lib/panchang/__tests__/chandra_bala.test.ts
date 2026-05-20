/**
 * __tests__/chandra_bala.test.ts
 *
 * Tests for computeChandraBala — exhaustive 12×12 coverage + classical spot checks.
 *
 * Classical source: Muhurta Chintamani §4.
 * STRONG:   houses 1, 3, 6, 7, 10, 11 from natal Moon
 * MODERATE: houses 2, 5, 9
 * WEAK:     houses 4, 8, 12 (8 = Chandrashtama)
 *
 * AC.4C5.2: Pure function tested for all 12×12 combinations.
 */
import { describe, it, expect } from 'vitest'
import { computeChandraBala } from '../chandra_bala'

const STRONG_HOUSES   = [1, 3, 6, 7, 10, 11]
const MODERATE_HOUSES = [2, 5, 9]
const WEAK_HOUSES     = [4, 8, 12]

// ── Classical spot checks ─────────────────────────────────────────────────────

describe('computeChandraBala — classical spot checks', () => {
  it('returns STRONG when transit Moon is in same sign as natal Moon (house 1)', () => {
    const result = computeChandraBala(1, 1)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(1)
    expect(result.isChandrashtama).toBe(false)
  })

  it('returns MODERATE for house 2', () => {
    const result = computeChandraBala(1, 2)
    expect(result.strength).toBe('MODERATE')
    expect(result.houseFromMoon).toBe(2)
  })

  it('returns STRONG for house 3', () => {
    const result = computeChandraBala(1, 3)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(3)
  })

  it('returns WEAK for house 4', () => {
    const result = computeChandraBala(1, 4)
    expect(result.strength).toBe('WEAK')
    expect(result.houseFromMoon).toBe(4)
    expect(result.isChandrashtama).toBe(false)
  })

  it('returns MODERATE for house 5', () => {
    const result = computeChandraBala(1, 5)
    expect(result.strength).toBe('MODERATE')
    expect(result.houseFromMoon).toBe(5)
  })

  it('returns STRONG for house 6', () => {
    const result = computeChandraBala(1, 6)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(6)
  })

  it('returns STRONG for house 7', () => {
    const result = computeChandraBala(1, 7)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(7)
  })

  it('returns WEAK + Chandrashtama for house 8', () => {
    const result = computeChandraBala(1, 8)
    expect(result.strength).toBe('WEAK')
    expect(result.houseFromMoon).toBe(8)
    expect(result.isChandrashtama).toBe(true)
  })

  it('returns MODERATE for house 9', () => {
    const result = computeChandraBala(1, 9)
    expect(result.strength).toBe('MODERATE')
    expect(result.houseFromMoon).toBe(9)
  })

  it('returns STRONG for house 10', () => {
    const result = computeChandraBala(1, 10)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(10)
  })

  it('returns STRONG for house 11', () => {
    const result = computeChandraBala(1, 11)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(11)
  })

  it('returns WEAK for house 12', () => {
    const result = computeChandraBala(1, 12)
    expect(result.strength).toBe('WEAK')
    expect(result.houseFromMoon).toBe(12)
    expect(result.isChandrashtama).toBe(false)
  })

  // Native (Abhisek): natal Moon = Aquarius = sign 11 (Kumbha)
  it('Aquarius(11) natal Moon, same transit → STRONG (house 1)', () => {
    const result = computeChandraBala(11, 11)
    expect(result.strength).toBe('STRONG')
    expect(result.houseFromMoon).toBe(1)
  })

  it('Aquarius(11) natal Moon, Virgo(6) transit → STRONG (house 8 from Aries, but from Aquarius = 8th sign = Virgo)', () => {
    // Aquarius=11, Virgo=6. house = (6-11+12)%12+1 = (7)%12+1 = 8 → WEAK (Chandrashtama)
    const result = computeChandraBala(11, 6)
    expect(result.houseFromMoon).toBe(8)
    expect(result.strength).toBe('WEAK')
    expect(result.isChandrashtama).toBe(true)
  })

  it('wraps correctly: Pisces(12) natal Moon, Aries(1) transit → house 2', () => {
    const result = computeChandraBala(12, 1)
    expect(result.houseFromMoon).toBe(2)
    expect(result.strength).toBe('MODERATE')
  })
})

// ── Exhaustive 12×12 property tests ──────────────────────────────────────────

describe('computeChandraBala — exhaustive 12×12 property tests', () => {
  it('all 12×12 combinations produce a valid strength and house', () => {
    for (let natal = 1; natal <= 12; natal++) {
      for (let transit = 1; transit <= 12; transit++) {
        const result = computeChandraBala(natal, transit)

        // houseFromMoon is 1..12
        expect(result.houseFromMoon).toBeGreaterThanOrEqual(1)
        expect(result.houseFromMoon).toBeLessThanOrEqual(12)

        // Same sign = house 1
        if (natal === transit) {
          expect(result.houseFromMoon).toBe(1)
          expect(result.strength).toBe('STRONG')
        }

        // Chandrashtama only when house 8
        expect(result.isChandrashtama).toBe(result.houseFromMoon === 8)

        // Strength classification
        if (STRONG_HOUSES.includes(result.houseFromMoon)) {
          expect(result.strength).toBe('STRONG')
        } else if (MODERATE_HOUSES.includes(result.houseFromMoon)) {
          expect(result.strength).toBe('MODERATE')
        } else {
          expect(WEAK_HOUSES).toContain(result.houseFromMoon)
          expect(result.strength).toBe('WEAK')
        }
      }
    }
  })

  it('house = (transit − natal + 12) % 12 + 1 for all pairs', () => {
    for (let natal = 1; natal <= 12; natal++) {
      for (let transit = 1; transit <= 12; transit++) {
        const result = computeChandraBala(natal, transit)
        const expected = (transit - natal + 12) % 12 + 1
        expect(result.houseFromMoon).toBe(expected)
      }
    }
  })
})

// ── Range validation ──────────────────────────────────────────────────────────

describe('computeChandraBala — range validation', () => {
  it('throws RangeError for natal sign 0', () => {
    expect(() => computeChandraBala(0, 1)).toThrow(RangeError)
  })

  it('throws RangeError for natal sign 13', () => {
    expect(() => computeChandraBala(13, 1)).toThrow(RangeError)
  })

  it('throws RangeError for transit sign 0', () => {
    expect(() => computeChandraBala(1, 0)).toThrow(RangeError)
  })

  it('throws RangeError for transit sign 13', () => {
    expect(() => computeChandraBala(1, 13)).toThrow(RangeError)
  })

  it('accepts boundary values 1 and 12 without throwing', () => {
    expect(() => computeChandraBala(1, 12)).not.toThrow()
    expect(() => computeChandraBala(12, 1)).not.toThrow()
  })
})
