import { describe, it, expect } from 'vitest'
import { ordinal, ordinalOrRaw } from './ordinal.js'
import { readFileSync } from 'node:fs'
import { composeKpClaim } from './kp_school_voice.js'

describe('ordinal (platform-mcp copy)', () => {
  it.each([
    [1, '1st'], [2, '2nd'], [3, '3rd'], [4, '4th'], [11, '11th'], [12, '12th'], [13, '13th'],
    [21, '21st'], [22, '22nd'], [23, '23rd'], [101, '101st'], [111, '111th'],
  ] as Array<[number, string]>)('%i -> %s', (n, s) => expect(ordinal(n)).toBe(s))
})

describe('KP claim house reference', () => {
  it.each([[1, 'the 1st house'], [2, 'the 2nd house'], [3, 'the 3rd house'], [7, 'the 7th house'], [12, 'the 12th house']] as Array<[number, string]>)(
    'bhava %i reads %s', (bhava, phrase) => {
      const claim = composeKpClaim({ bhava, ladder: { ranked: [] } as never, matches: [], strongest_limb: null, kp_stance: 'not_signified', agreement: 'agree' } as never)
      expect(claim).toContain(phrase)
    })
})

describe('ordinalOrRaw never throws', () => {
  it('integers get ordinals, everything else degrades to the plain string', () => {
    expect(ordinalOrRaw(2)).toBe('2nd')
    expect(ordinalOrRaw(5.5)).toBe('5.5')
    expect(ordinalOrRaw(NaN)).toBe('NaN')
    expect(ordinalOrRaw(undefined)).toBe('undefined')
  })
  it.each([5.5, NaN, undefined])('composeKpClaim does not throw on bhava %s', (bhava) => {
    const mk = () => composeKpClaim({ bhava: bhava as never, ladder: { ranked: [] } as never, matches: [], strongest_limb: null, kp_stance: 'not_signified', agreement: 'agree' } as never)
    expect(mk).not.toThrow()
    expect(mk()).toContain(`the ${String(bhava)} house`)
  })
  it('registry_bridge portrait ordinalWord uses the non-throwing form', () => {
    const src = readFileSync(new URL('../tools/registry_bridge.ts', import.meta.url), 'utf8')
    expect(src).toMatch(/const ordinalWord = \(n: number\): string => ordinalOrRaw\(n\)/)
  })
})
