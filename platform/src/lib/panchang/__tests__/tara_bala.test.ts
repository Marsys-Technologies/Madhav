/**
 * __tests__/tara_bala.test.ts
 *
 * Tests for computeTaraBala — exhaustive 27×27 coverage + classical spot checks.
 *
 * Classical source: Muhurta Chintamani §2 — 9 Taras cycling from Janma nakshatra.
 * Auspicious: Sampat(2), Kshema(4), Sadhaka(6), Mitra(8), Ati Mitra(9)
 * Inauspicious: Vipat(3), Pratyari(5), Vadha(7)
 * Mixed: Janma(1)
 *
 * AC.4C5.1: Pure function tested for all 27×27 combinations; matches classical table.
 */
import { describe, it, expect } from 'vitest'
import { computeTaraBala } from '../tara_bala'

const TARA_NAMES = [
  'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyari',
  'Sadhaka', 'Vadha', 'Mitra', 'Ati Mitra',
] as const

const AUSPICIOUS_TARAS = new Set(['Sampat', 'Kshema', 'Sadhaka', 'Mitra', 'Ati Mitra'])
const INAUSPICIOUS_TARAS = new Set(['Vipat', 'Pratyari', 'Vadha'])
const MIXED_TARAS = new Set(['Janma'])

// ── Classical spot checks ─────────────────────────────────────────────────────

describe('computeTaraBala — classical spot checks', () => {
  it('returns Janma when birth === current (own star)', () => {
    const result = computeTaraBala(1, 1)
    expect(result.tara).toBe('Janma')
    expect(result.count).toBe(1)
    expect(result.classification).toBe('mixed')
  })

  it('Ashwini birth, Bharani current → Sampat (count 2)', () => {
    const result = computeTaraBala(1, 2)
    expect(result.tara).toBe('Sampat')
    expect(result.count).toBe(2)
    expect(result.classification).toBe('auspicious')
  })

  it('Ashwini birth, Krittika current → Vipat (count 3)', () => {
    const result = computeTaraBala(1, 3)
    expect(result.tara).toBe('Vipat')
    expect(result.classification).toBe('inauspicious')
  })

  it('Ashwini birth, Rohini current → Kshema (count 4)', () => {
    const result = computeTaraBala(1, 4)
    expect(result.tara).toBe('Kshema')
    expect(result.classification).toBe('auspicious')
  })

  it('Ashwini birth, Mrigashira current → Pratyari (count 5)', () => {
    const result = computeTaraBala(1, 5)
    expect(result.tara).toBe('Pratyari')
    expect(result.classification).toBe('inauspicious')
  })

  it('Ashwini birth, Ardra current → Sadhaka (count 6)', () => {
    const result = computeTaraBala(1, 6)
    expect(result.tara).toBe('Sadhaka')
    expect(result.classification).toBe('auspicious')
  })

  it('Ashwini birth, Punarvasu current → Vadha (count 7)', () => {
    const result = computeTaraBala(1, 7)
    expect(result.tara).toBe('Vadha')
    expect(result.classification).toBe('inauspicious')
  })

  it('Ashwini birth, Pushya current → Mitra (count 8)', () => {
    const result = computeTaraBala(1, 8)
    expect(result.tara).toBe('Mitra')
    expect(result.classification).toBe('auspicious')
  })

  it('Ashwini birth, Ashlesha current → Ati Mitra (count 9)', () => {
    const result = computeTaraBala(1, 9)
    expect(result.tara).toBe('Ati Mitra')
    expect(result.classification).toBe('auspicious')
  })

  it('Ashwini birth, Magha current → Janma again (count 10 → cycle wraps)', () => {
    // Magha = 10, distance = 9, count = 10, taraIdx = 9 % 9 = 0 → Janma
    const result = computeTaraBala(1, 10)
    expect(result.tara).toBe('Janma')
    expect(result.count).toBe(10)
  })

  // Native (Abhisek): birth nakshatra = Purva Bhadrapada = 25
  it('Purva Bhadrapada(25) birth, Purva Bhadrapada(25) current → Janma', () => {
    const result = computeTaraBala(25, 25)
    expect(result.tara).toBe('Janma')
    expect(result.count).toBe(1)
  })

  it('Purva Bhadrapada(25) birth, Uttara Bhadrapada(26) current → Sampat (count 2)', () => {
    const result = computeTaraBala(25, 26)
    expect(result.tara).toBe('Sampat')
    expect(result.count).toBe(2)
  })

  it('wraps correctly: Revati(27) birth, Ashwini(1) current → Sampat (count 2)', () => {
    const result = computeTaraBala(27, 1)
    expect(result.tara).toBe('Sampat')
    expect(result.count).toBe(2)
  })

  it('last nakshatra cycle: Revati(27) birth, Revati(27) current → Janma', () => {
    const result = computeTaraBala(27, 27)
    expect(result.tara).toBe('Janma')
  })
})

// ── Exhaustive 27×27 property tests ──────────────────────────────────────────

describe('computeTaraBala — exhaustive 27×27 property tests', () => {
  it('all 27×27 combinations produce a valid Tara name and classification', () => {
    for (let birth = 1; birth <= 27; birth++) {
      for (let current = 1; current <= 27; current++) {
        const result = computeTaraBala(birth, current)

        // Tara name must be from the 9-Tara table
        expect(TARA_NAMES).toContain(result.tara)

        // count is 1..27
        expect(result.count).toBeGreaterThanOrEqual(1)
        expect(result.count).toBeLessThanOrEqual(27)

        // count 1 ↔ Janma (same nakshatra)
        if (birth === current) {
          expect(result.tara).toBe('Janma')
          expect(result.count).toBe(1)
        }

        // Classification matches table
        if (AUSPICIOUS_TARAS.has(result.tara as string)) {
          expect(result.classification).toBe('auspicious')
        } else if (INAUSPICIOUS_TARAS.has(result.tara as string)) {
          expect(result.classification).toBe('inauspicious')
        } else {
          expect(result.classification).toBe('mixed')
        }
      }
    }
  })

  it('count = (current − birth + 27) % 27 + 1 for all pairs', () => {
    for (let birth = 1; birth <= 27; birth++) {
      for (let current = 1; current <= 27; current++) {
        const result = computeTaraBala(birth, current)
        const expected = (current - birth + 27) % 27 + 1
        expect(result.count).toBe(expected)
      }
    }
  })
})

// ── Range validation ──────────────────────────────────────────────────────────

describe('computeTaraBala — range validation', () => {
  it('throws RangeError for birth nakshatra 0', () => {
    expect(() => computeTaraBala(0, 1)).toThrow(RangeError)
  })

  it('throws RangeError for birth nakshatra 28', () => {
    expect(() => computeTaraBala(28, 1)).toThrow(RangeError)
  })

  it('throws RangeError for current nakshatra 0', () => {
    expect(() => computeTaraBala(1, 0)).toThrow(RangeError)
  })

  it('throws RangeError for current nakshatra 28', () => {
    expect(() => computeTaraBala(1, 28)).toThrow(RangeError)
  })

  it('accepts boundary values 1 and 27 without throwing', () => {
    expect(() => computeTaraBala(1, 27)).not.toThrow()
    expect(() => computeTaraBala(27, 1)).not.toThrow()
  })
})
