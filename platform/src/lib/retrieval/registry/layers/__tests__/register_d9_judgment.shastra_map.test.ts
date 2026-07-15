/**
 * register_d9_judgment.shastra_map.test.ts — D-1.5b Lane B-4 (CR-97) unit test.
 *
 * Verifies the SHASTRA_MAP extension (Task 2): every domain gets a `derived_bhavas`
 * field sourced from the shared Bhavat-Bhavam registry (bhavat_bhavam_map.ts), never
 * hardcoded per-domain. Pure module-level data check — no DB required.
 */
import { describe, it, expect } from 'vitest'
import { SHASTRA_MAP } from '../register_d9_judgment'
import { derivedHouses } from '@/lib/jyotish/bhavat_bhavam_map'

describe('SHASTRA_MAP Bhavat-Bhavam extension', () => {
  it('every domain has a derived_bhavas field matching the shared registry for its primary bhava', () => {
    for (const [domain, spec] of Object.entries(SHASTRA_MAP)) {
      expect(spec.derived_bhavas, domain).toEqual(derivedHouses(spec.bhava))
    }
  })

  it('marriage/relationship/partnership (bhava 7, odd) derive [4, 10]', () => {
    for (const key of ['marriage', 'relationship', 'partnership']) {
      expect(SHASTRA_MAP[key].bhava).toBe(7)
      expect(SHASTRA_MAP[key].derived_bhavas).toEqual([4, 10])
    }
  })

  it('progeny/children (bhava 5, odd) derive [3, 9]', () => {
    for (const key of ['progeny', 'children']) {
      expect(SHASTRA_MAP[key].bhava).toBe(5)
      expect(SHASTRA_MAP[key].derived_bhavas).toEqual([3, 9])
    }
  })

  it('spirituality (bhava 9, odd) derives [5, 11]', () => {
    expect(SHASTRA_MAP.spirituality.bhava).toBe(9)
    expect(SHASTRA_MAP.spirituality.derived_bhavas).toEqual([5, 11])
  })

  it('health/vitality and character/buddhi (bhava 1, odd) derive [1, 7]', () => {
    for (const key of ['health', 'vitality', 'character', 'buddhi']) {
      expect(SHASTRA_MAP[key].bhava).toBe(1)
      expect(SHASTRA_MAP[key].derived_bhavas).toEqual([1, 7])
    }
  })

  it('career/vocation (bhava 10, even) has NO derived house — intentional, not a gap', () => {
    for (const key of ['career', 'vocation']) {
      expect(SHASTRA_MAP[key].bhava).toBe(10)
      expect(SHASTRA_MAP[key].derived_bhavas).toEqual([])
    }
  })

  it('wealth/finance (bhava 2, even) has NO derived house', () => {
    for (const key of ['wealth', 'finance']) {
      expect(SHASTRA_MAP[key].bhava).toBe(2)
      expect(SHASTRA_MAP[key].derived_bhavas).toEqual([])
    }
  })

  it('every even-primary domain resolves to an empty derived_bhavas array', () => {
    for (const [domain, spec] of Object.entries(SHASTRA_MAP)) {
      if (spec.bhava % 2 === 0) {
        expect(spec.derived_bhavas, domain).toEqual([])
      }
    }
  })

  it('every odd-primary domain resolves to a non-empty derived_bhavas array', () => {
    for (const [domain, spec] of Object.entries(SHASTRA_MAP)) {
      if (spec.bhava % 2 === 1) {
        expect(spec.derived_bhavas!.length, domain).toBeGreaterThan(0)
      }
    }
  })
})
