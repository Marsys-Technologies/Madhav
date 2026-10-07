import { describe, it, expect } from 'vitest'
import { ordinal } from './ordinal.js'
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
