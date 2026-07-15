import { describe, it, expect } from 'vitest'
import {
  BHAVAT_BHAVAM_MAP,
  ODD_HOUSES,
  EVEN_HOUSES,
  derivedHouses,
  isOddHouse,
} from '../bhavat_bhavam_map'

describe('bhavat_bhavam_map', () => {
  it('has all 12 houses present as keys', () => {
    expect(Object.keys(BHAVAT_BHAVAM_MAP).map(Number).sort((a, b) => a - b)).toEqual(
      Array.from({ length: 12 }, (_, i) => i + 1),
    )
  })

  it.each([
    [1, [1, 7]],
    [3, [2, 8]],
    [5, [3, 9]],
    [7, [4, 10]],
    [9, [5, 11]],
    [11, [6, 12]],
  ])('odd house %i derives %j (brief verbatim map)', (house, expected) => {
    expect(derivedHouses(house)).toEqual(expected)
  })

  it.each([2, 4, 6, 8, 10, 12])('even house %i receives nothing', (house) => {
    expect(derivedHouses(house)).toEqual([])
  })

  it('odd/even partition is exhaustive and disjoint', () => {
    const all = new Set([...ODD_HOUSES, ...EVEN_HOUSES])
    expect(all.size).toBe(12)
    expect(new Set(ODD_HOUSES).size + new Set(EVEN_HOUSES).size).toBe(12)
  })

  it('isOddHouse agrees with the ODD_HOUSES/EVEN_HOUSES partition', () => {
    for (const h of ODD_HOUSES) expect(isOddHouse(h)).toBe(true)
    for (const h of EVEN_HOUSES) expect(isOddHouse(h)).toBe(false)
  })

  it('throws on an invalid house number', () => {
    expect(() => derivedHouses(0)).toThrow()
    expect(() => derivedHouses(13)).toThrow()
  })
})
