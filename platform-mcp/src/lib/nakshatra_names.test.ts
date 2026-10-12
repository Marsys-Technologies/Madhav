/**
 * nakshatra_names.test.ts -- pins the TS spelling table to the L0 lexicon (SS N-471).
 * The canonical list is NOT hard-coded here: it is read from platform/python-sidecar/brahmagyan/l0_nakshatra.py
 * (`name_en` of nakshatra_id 1..27), so a lexicon change fails this test until the TS table follows.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import {
  CANONICAL_NAKSHATRA_NAMES,
  nakshatraNumberOf,
  canonicalNakshatraName,
  storedNakshatraSpellings,
} from './nakshatra_names.js'

function lexiconNames(): string[] {
  const src = readFileSync(
    fileURLToPath(new URL('../../../platform/python-sidecar/brahmagyan/l0_nakshatra.py', import.meta.url)), 'utf8',
  )
  const byId = new Map<number, string>()
  for (const m of src.matchAll(/nakshatra_id=(\d+),[\s\S]*?name_en="([^"]+)"/g)) byId.set(Number(m[1]), m[2]!)
  return Array.from({ length: 27 }, (_, i) => {
    const nm = byId.get(i + 1)
    if (!nm) throw new Error(`lexicon row ${i + 1} not found in l0_nakshatra.py`)
    return nm
  })
}

describe('nakshatra_names -- pinned to the L0 lexicon', () => {
  it('CANONICAL_NAKSHATRA_NAMES equals l0_nakshatra.py name_en for ids 1..27, in order', () => {
    expect(CANONICAL_NAKSHATRA_NAMES).toEqual(lexiconNames())
    expect(new Set(CANONICAL_NAKSHATRA_NAMES).size).toBe(27)
  })

  it('every canonical name round-trips to its number and canonical spelling', () => {
    CANONICAL_NAKSHATRA_NAMES.forEach((nm, i) => {
      expect(nakshatraNumberOf(nm)).toBe(i + 1)
      expect(canonicalNakshatraName(nm.toUpperCase())).toBe(nm)
    })
  })

  it.each([
    [5, 'Mrigasira', 'Mrigashira'], [19, 'Moola', 'Mula'], [23, 'Dhanishtha', 'Dhanishta'],
  ])('no. %i: canonical "%s" and old-L1 "%s" resolve to the same number and canonical name', (n, canon, old) => {
    expect(nakshatraNumberOf(canon)).toBe(n)
    expect(nakshatraNumberOf(old)).toBe(n)
    expect(canonicalNakshatraName(old)).toBe(canon)
    expect(storedNakshatraSpellings(old)).toEqual([canon, old])
  })

  it('common aliases resolve (incl. ones the old alias table silently missed)', () => {
    expect(nakshatraNumberOf('Poorvaphalguni')).toBe(11)
    expect(nakshatraNumberOf('Satabhisha')).toBe(24)
    expect(nakshatraNumberOf('Aslesha')).toBe(9)
    expect(nakshatraNumberOf('Pushyami')).toBe(8)
    expect(nakshatraNumberOf('Poorva Ashadha')).toBe(20)
    expect(nakshatraNumberOf('Uttarabhadra')).toBe(26)
  })

  it('unknown names are null (no guess); 28th-row Abhijit and ambiguous "Purva" are not among the 27', () => {
    for (const bad of ['', ' ', 'Abhijit', 'Purva', 'Uttara', 'xyz', undefined, null]) {
      expect(nakshatraNumberOf(bad)).toBeNull()
      expect(canonicalNakshatraName(bad)).toBeNull()
      expect(storedNakshatraSpellings(bad)).toBeNull()
    }
  })
})
