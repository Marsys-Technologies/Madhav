import { describe, expect, it } from 'vitest'
import { factSubjectForLord } from '@/lib/retrieval/registry/layers/L1_ganita/get_dashas'

// F-A11 (L1_W1_ANALYSIS_BATCH_A.md): 83,740 yogini rows carry a correctly-resolved
// lord_natal_shadbala_total that get_dashas.ts's serve-side re-derivation used to
// overwrite with NULL, because its name -> fact_subject map only knew the 9
// classical graha display names, not the 8 yogini deity names chart_dashas.lord_graha
// actually stores for the yogini system. factSubjectForLord must resolve both.
describe('F-A11 factSubjectForLord — yogini deity lords resolve to their graha subject', () => {
  const CLASSICAL_CASES: ReadonlyArray<readonly [string, string]> = [
    ['Sun', 'SUN'], ['Moon', 'MOON'], ['Mars', 'MAR'], ['Mercury', 'MER'],
    ['Jupiter', 'JUP'], ['Venus', 'VEN'], ['Saturn', 'SAT'], ['Rahu', 'RAH_MEAN'], ['Ketu', 'KET_MEAN'],
  ]

  it.each(CLASSICAL_CASES)('classical graha name %s resolves to its own subject code', (name, expected) => {
    expect(factSubjectForLord(name)).toBe(expected)
  })

  // Same 8 pairs as ga_dashas_writer.py's YOGINI_SEQUENCE / _YOGINI_DEITY_TO_GRAHA.
  const YOGINI_CASES: ReadonlyArray<readonly [string, string]> = [
    ['Mangala', 'MOON'], ['Pingala', 'SUN'], ['Dhanya', 'JUP'], ['Bhramari', 'MAR'],
    ['Bhadrika', 'MER'], ['Ulka', 'SAT'], ['Siddha', 'VEN'], ['Sankata', 'RAH_MEAN'],
  ]

  it.each(YOGINI_CASES)('yogini deity lord %s resolves to its inherited graha subject', (deity, expected) => {
    expect(factSubjectForLord(deity)).toBe(expected)
  })

  it('returns undefined for an unrecognized lord rather than a wrong guess', () => {
    expect(factSubjectForLord('Ketu-deity-that-does-not-exist')).toBeUndefined()
    expect(factSubjectForLord(undefined)).toBeUndefined()
  })
})
