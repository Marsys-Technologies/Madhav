import { describe, it, expect } from 'vitest'
import { domainForCategory, significatorsForCategory, DOMAIN_LORDS, LOSS_SIGNIFICATORS, WINDFALL_SIGNIFICATORS } from '../mechanisms'

describe('domainForCategory', () => {
  it('maps finance and loss to wealth', () => {
    expect(domainForCategory('finance')).toBe('wealth')
    expect(domainForCategory('loss')).toBe('wealth')
  })

  it('maps relationship and family to marriage', () => {
    expect(domainForCategory('relationship')).toBe('marriage')
    expect(domainForCategory('family')).toBe('marriage')
  })

  it('falls back to general for an unrecognized category', () => {
    expect(domainForCategory('some_unknown_category')).toBe('general')
  })
})

describe('significatorsForCategory', () => {
  it('returns the DOMAIN_LORDS entry for a mapped category', () => {
    expect(significatorsForCategory('finance')).toEqual(DOMAIN_LORDS.wealth)
  })

  it('falls back to general lords for unmapped categories', () => {
    expect(significatorsForCategory('travel')).toEqual(DOMAIN_LORDS.general)
  })
})

describe('anchor mechanism constants', () => {
  it('LOSS significators are Mars only (8L-Mars->2H)', () => {
    expect(Object.keys(LOSS_SIGNIFICATORS)).toEqual(['Mars'])
  })

  it('WINDFALL significators are Venus + Jupiter (dhana_yoga_2_5_9_11)', () => {
    expect(Object.keys(WINDFALL_SIGNIFICATORS).sort()).toEqual(['Jupiter', 'Venus'])
  })
})
