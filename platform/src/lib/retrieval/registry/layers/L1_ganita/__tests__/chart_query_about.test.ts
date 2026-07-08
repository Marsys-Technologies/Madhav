/**
 * chart_query_about.test.ts — unit tests for the minimal inline `about` facet resolver.
 * Pure functions, no DB — see register_d7_channel.chart_query.integration.test.ts for the
 * live-DB conformance + payload-size gate.
 */
import { describe, it, expect } from 'vitest'
import { resolveAboutFacet, normalizeGrahaName, houseSignFromLagna } from '../chart_query_about'

describe('normalizeGrahaName', () => {
  it('normalizes common english + sanskrit aliases', () => {
    expect(normalizeGrahaName('Saturn')).toBe('SAT')
    expect(normalizeGrahaName('shani')).toBe('SAT')
    expect(normalizeGrahaName('Rahu')).toBe('RAH_MEAN')
    expect(normalizeGrahaName('ketu')).toBe('KET_MEAN')
    expect(normalizeGrahaName('Moon')).toBe('MOON')
  })
  it('rejects unknown names', () => {
    expect(normalizeGrahaName('Pluto')).toBeNull()
  })
})

describe('houseSignFromLagna', () => {
  it('computes whole-sign houses from an Aries lagna (native chart)', () => {
    expect(houseSignFromLagna('Aries', 1)).toBe('Aries')
    expect(houseSignFromLagna('Aries', 7)).toBe('Libra')
    expect(houseSignFromLagna('Aries', 10)).toBe('Capricorn')
    expect(houseSignFromLagna('Aries', 12)).toBe('Pisces')
  })
  it('wraps around the zodiac for a non-Aries lagna', () => {
    expect(houseSignFromLagna('Scorpio', 10)).toBe('Leo')
  })
  it('returns null for an out-of-range house or unknown sign', () => {
    expect(houseSignFromLagna('Aries', 13)).toBeNull()
    expect(houseSignFromLagna('Nowhere', 1)).toBeNull()
  })
})

describe('resolveAboutFacet', () => {
  it('resolves the "lagna" string alias', () => {
    const r = resolveAboutFacet('lagna', null)
    expect(r.subjects).toEqual(['LAGNA'])
    expect(r.category_hint).toBe('graha_position')
    expect(r.error).toBeUndefined()
  })

  it('resolves {graha: "Saturn"}', () => {
    const r = resolveAboutFacet({ graha: 'Saturn' }, null)
    expect(r.subjects).toEqual(['SAT'])
  })

  it('resolves {bhava: 10} to the bare house subject', () => {
    const r = resolveAboutFacet({ bhava: 10 }, null)
    expect(r.subjects).toEqual(['HOUSE_10'])
  })

  it('resolves {house_lord: 10} for an Aries lagna to Saturn, with a served chain', () => {
    const r = resolveAboutFacet({ house_lord: 10 }, 'Aries')
    expect(r.subjects).toEqual(['SAT'])
    expect(r.chain.length).toBe(3)
    expect(r.chain[1].output).toBe('Capricorn')
    expect(r.chain[2].output).toBe('SAT')
  })

  it('errors on {house_lord: 10} when lagna sign is unavailable', () => {
    const r = resolveAboutFacet({ house_lord: 10 }, null)
    expect(r.error).toMatch(/requires the lagna sign/)
  })

  it('errors on an unrecognized graha name', () => {
    const r = resolveAboutFacet({ graha: 'Pluto' }, null)
    expect(r.error).toMatch(/unrecognized graha/)
  })

  it('errors on an out-of-range bhava', () => {
    const r = resolveAboutFacet({ bhava: 13 }, null)
    expect(r.error).toMatch(/1-12/)
  })

  it('passes through null/undefined as a no-op (no about facet requested)', () => {
    expect(resolveAboutFacet(undefined, null)).toEqual({ subjects: [], chain: [] })
  })
})
