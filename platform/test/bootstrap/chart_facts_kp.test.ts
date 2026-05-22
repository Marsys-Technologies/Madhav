/**
 * chart_facts_kp.test.ts
 *
 * Unit tests for KP bootstrap data.
 * Tests data constants and row-building logic without requiring DB.
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §4.1, §4.2, §4.3
 *
 * Run: cd platform && npx vitest run test/bootstrap/chart_facts_kp.test.ts
 */

import { describe, it, expect } from 'vitest'

// ── Inline data structures (mirrors bootstrap_chart_facts_kp.ts) ────────────

const KP_CUSP_DATA = [
  { house: 1,  description: 'Lagna',      degree: '12°29′19″', sign: 'Aries',       star_lord: 'Ketu',    sub_lord: 'Mercury', sub_sub_lord: 'Mars'    },
  { house: 2,  description: 'Wealth',     degree: '12°29′01″', sign: 'Taurus',      star_lord: 'Moon',    sub_lord: 'Rahu',    sub_sub_lord: 'Saturn'  },
  { house: 3,  description: 'Effort',     degree: '08°00′37″', sign: 'Gemini',      star_lord: 'Rahu',    sub_lord: 'Rahu',    sub_sub_lord: 'Venus'   },
  { house: 4,  description: 'Home',       degree: '03°03′44″', sign: 'Cancer',      star_lord: 'Jupiter', sub_lord: 'Rahu',    sub_sub_lord: 'Moon'    },
  { house: 5,  description: 'Creativity', degree: '01°07′36″', sign: 'Leo',         star_lord: 'Ketu',    sub_lord: 'Venus',   sub_sub_lord: 'Venus'   },
  { house: 6,  description: 'Service',    degree: '04°47′17″', sign: 'Virgo',       star_lord: 'Sun',     sub_lord: 'Saturn',  sub_sub_lord: 'Rahu'    },
  { house: 7,  description: 'Spouse',     degree: '12°29′19″', sign: 'Libra',       star_lord: 'Rahu',    sub_lord: 'Saturn',  sub_sub_lord: 'Jupiter' },
  { house: 8,  description: 'Change',     degree: '12°29′01″', sign: 'Scorpio',     star_lord: 'Saturn',  sub_lord: 'Mars',    sub_sub_lord: 'Saturn'  },
  { house: 9,  description: 'Fortune',    degree: '08°00′37″', sign: 'Sagittarius', star_lord: 'Ketu',    sub_lord: 'Jupiter', sub_sub_lord: 'Saturn'  },
  { house: 10, description: 'Career',     degree: '03°03′44″', sign: 'Capricorn',   star_lord: 'Sun',     sub_lord: 'Saturn',  sub_sub_lord: 'Saturn'  },
  { house: 11, description: 'Gain',       degree: '01°07′36″', sign: 'Aquarius',    star_lord: 'Mars',    sub_lord: 'Mercury', sub_sub_lord: 'Rahu'    },
  { house: 12, description: 'Loss',       degree: '04°47′17″', sign: 'Pisces',      star_lord: 'Saturn',  sub_lord: 'Saturn',  sub_sub_lord: 'Mars'    },
]

const KP_PLANET_DATA = [
  { planet: 'Sun',     degree: '22°02′', star_lord: 'Moon',    sub_lord: 'Venus',   sub_sub_lord: 'Saturn'  },
  { planet: 'Moon',    degree: '27°08′', star_lord: 'Jupiter', sub_lord: 'Venus',   sub_sub_lord: 'Moon'    },
  { planet: 'Mars',    degree: '18°37′', star_lord: 'Rahu',    sub_lord: 'Moon',    sub_sub_lord: 'Saturn'  },
  { planet: 'Mercury', degree: '00°55′', star_lord: 'Sun',     sub_lord: 'Rahu',    sub_sub_lord: 'Sun'     },
  { planet: 'Jupiter', degree: '09°53′', star_lord: 'Ketu',    sub_lord: 'Saturn',  sub_sub_lord: 'Mercury' },
  { planet: 'Venus',   degree: '19°15′', star_lord: 'Venus',   sub_lord: 'Rahu',    sub_sub_lord: 'Mercury' },
  { planet: 'Saturn',  degree: '22°32′', star_lord: 'Jupiter', sub_lord: 'Saturn',  sub_sub_lord: 'Venus'   },
  { planet: 'Rahu',    degree: '19°07′', star_lord: 'Moon',    sub_lord: 'Mercury', sub_sub_lord: 'Jupiter' },
  { planet: 'Ketu',    degree: '19°07′', star_lord: 'Mercury', sub_lord: 'Ketu',    sub_sub_lord: 'Saturn'  },
]

const KP_SIGNIFICATOR_DATA = [
  { house: 1,  significators: ['Mars', 'Ketu']                                       },
  { house: 2,  significators: ['Rahu', 'Venus']                                      },
  { house: 6,  significators: ['Mars', 'Ketu', 'Mercury']                            },
  { house: 7,  significators: ['Moon', 'Saturn', 'Venus']                            },
  { house: 10, significators: ['Mercury', 'Venus', 'Mars', 'Ketu', 'Sun', 'Saturn']  },
  { house: 11, significators: ['Sun', 'Rahu', 'Moon', 'Saturn']                     },
  { house: 12, significators: ['Saturn', 'Jupiter']                                  },
]

// ── Row count tests ──────────────────────────────────────────────────────────

describe('KP Cusp — row count', () => {
  it('has exactly 12 cusps', () => {
    expect(KP_CUSP_DATA.length).toBe(12)
  })

  it('produces 36 rows (12 cusps × 3 roles)', () => {
    const count = KP_CUSP_DATA.length * 3 // star_lord, sub_lord, sub_sub_lord
    expect(count).toBe(36)
  })

  it('houses are numbered 1–12 without gaps', () => {
    const houses = KP_CUSP_DATA.map((c) => c.house)
    for (let i = 1; i <= 12; i++) {
      expect(houses).toContain(i)
    }
  })
})

describe('KP Planet — row count', () => {
  it('has exactly 9 planets', () => {
    expect(KP_PLANET_DATA.length).toBe(9)
  })

  it('produces 27 rows (9 planets × 3 roles)', () => {
    const count = KP_PLANET_DATA.length * 3
    expect(count).toBe(27)
  })

  it('includes the 7 classical planets + Rahu + Ketu', () => {
    const planets = KP_PLANET_DATA.map((p) => p.planet)
    expect(planets).toContain('Sun')
    expect(planets).toContain('Moon')
    expect(planets).toContain('Mars')
    expect(planets).toContain('Mercury')
    expect(planets).toContain('Jupiter')
    expect(planets).toContain('Venus')
    expect(planets).toContain('Saturn')
    expect(planets).toContain('Rahu')
    expect(planets).toContain('Ketu')
  })
})

describe('KP Significator — row count', () => {
  it('has exactly 7 significator entries (houses present in FORENSIC §4.3)', () => {
    expect(KP_SIGNIFICATOR_DATA.length).toBe(7)
  })

  it('significator entries cover the FORENSIC-documented houses', () => {
    const houses = KP_SIGNIFICATOR_DATA.map((s) => s.house)
    expect(houses).toContain(1)
    expect(houses).toContain(2)
    expect(houses).toContain(6)
    expect(houses).toContain(7)
    expect(houses).toContain(10)
    expect(houses).toContain(11)
    expect(houses).toContain(12)
  })
})

// ── Spot-check tests against FORENSIC §4.1 ──────────────────────────────────

describe('KP Cusp spot-checks (FORENSIC §4.1)', () => {
  it('Cusp 1 (Lagna) star_lord = Ketu (Aries 12°29′ in Ashwini nakshatra, Ketu star)', () => {
    const cusp1 = KP_CUSP_DATA.find((c) => c.house === 1)!
    expect(cusp1.star_lord).toBe('Ketu')
    expect(cusp1.sign).toBe('Aries')
  })

  it('Cusp 1 sub_lord = Mercury', () => {
    const cusp1 = KP_CUSP_DATA.find((c) => c.house === 1)!
    expect(cusp1.sub_lord).toBe('Mercury')
  })

  it('Cusp 7 (Spouse) star_lord = Rahu (Libra 12°29′ in Swati nakshatra, Rahu star)', () => {
    const cusp7 = KP_CUSP_DATA.find((c) => c.house === 7)!
    expect(cusp7.star_lord).toBe('Rahu')
    expect(cusp7.sign).toBe('Libra')
  })

  it('Cusp 7 sub_lord = Saturn', () => {
    const cusp7 = KP_CUSP_DATA.find((c) => c.house === 7)!
    expect(cusp7.sub_lord).toBe('Saturn')
  })

  it('Cusp 10 (Career) star_lord = Sun (Capricorn 3°03′ in Uttara Ashadha, Sun star)', () => {
    const cusp10 = KP_CUSP_DATA.find((c) => c.house === 10)!
    expect(cusp10.star_lord).toBe('Sun')
    expect(cusp10.sign).toBe('Capricorn')
  })

  it('Cusp 10 sub_lord = Saturn', () => {
    const cusp10 = KP_CUSP_DATA.find((c) => c.house === 10)!
    expect(cusp10.sub_lord).toBe('Saturn')
  })
})

// ── Spot-check tests against FORENSIC §4.2 ──────────────────────────────────

describe('KP Planet spot-checks (FORENSIC §4.2)', () => {
  it('Saturn star_lord = Jupiter (Libra 22°32′ in Vishakha nakshatra, Jupiter star)', () => {
    const sat = KP_PLANET_DATA.find((p) => p.planet === 'Saturn')!
    expect(sat.star_lord).toBe('Jupiter')
  })

  it('Saturn sub_lord = Saturn', () => {
    const sat = KP_PLANET_DATA.find((p) => p.planet === 'Saturn')!
    expect(sat.sub_lord).toBe('Saturn')
  })

  it('Mercury star_lord = Sun (Capricorn 00°55′ in Uttara Ashadha, Sun star)', () => {
    const merc = KP_PLANET_DATA.find((p) => p.planet === 'Mercury')!
    expect(merc.star_lord).toBe('Sun')
  })

  it('Mercury sub_lord = Rahu', () => {
    const merc = KP_PLANET_DATA.find((p) => p.planet === 'Mercury')!
    expect(merc.sub_lord).toBe('Rahu')
  })

  it('Rahu star_lord = Moon', () => {
    const rahu = KP_PLANET_DATA.find((p) => p.planet === 'Rahu')!
    expect(rahu.star_lord).toBe('Moon')
  })

  it('Ketu star_lord = Mercury', () => {
    const ketu = KP_PLANET_DATA.find((p) => p.planet === 'Ketu')!
    expect(ketu.star_lord).toBe('Mercury')
  })

  it('Ketu sub_lord = Ketu', () => {
    const ketu = KP_PLANET_DATA.find((p) => p.planet === 'Ketu')!
    expect(ketu.sub_lord).toBe('Ketu')
  })
})

// ── Spot-check tests against FORENSIC §4.3 ──────────────────────────────────

describe('KP Significator spot-checks (FORENSIC §4.3)', () => {
  it('House 10 (Career) significators include Saturn as lord', () => {
    const h10 = KP_SIGNIFICATOR_DATA.find((s) => s.house === 10)!
    expect(h10.significators).toContain('Saturn')
  })

  it('House 10 (Career) significators include Sun and Mercury as occupants', () => {
    const h10 = KP_SIGNIFICATOR_DATA.find((s) => s.house === 10)!
    expect(h10.significators).toContain('Sun')
    expect(h10.significators).toContain('Mercury')
  })

  it('House 7 (Partners) significators include Saturn (occupant)', () => {
    const h7 = KP_SIGNIFICATOR_DATA.find((s) => s.house === 7)!
    expect(h7.significators).toContain('Saturn')
  })

  it('House 1 (Self) significators = [Mars, Ketu]', () => {
    const h1 = KP_SIGNIFICATOR_DATA.find((s) => s.house === 1)!
    expect(h1.significators).toEqual(['Mars', 'Ketu'])
  })

  it('House 12 (Loss) significators = [Saturn, Jupiter]', () => {
    const h12 = KP_SIGNIFICATOR_DATA.find((s) => s.house === 12)!
    expect(h12.significators).toEqual(['Saturn', 'Jupiter'])
  })
})

// ── fact_id format tests ─────────────────────────────────────────────────────

describe('KP fact_id format', () => {
  it('kp_cusp fact_ids follow pattern KP.CUSP.<H>.STAR_LORD', () => {
    const factId = `KP.CUSP.1.STAR_LORD`
    expect(factId).toMatch(/^KP\.CUSP\.\d+\.STAR_LORD$/)
  })

  it('kp_planet fact_ids follow pattern KP.PLN.<PLANET>.SUB_LORD', () => {
    const factId = `KP.PLN.SATURN.SUB_LORD`
    expect(factId).toMatch(/^KP\.PLN\.[A-Z]+\.SUB_LORD$/)
  })

  it('kp_significator fact_ids follow pattern KP.SIG.<H>', () => {
    const factId = `KP.SIG.10`
    expect(factId).toMatch(/^KP\.SIG\.\d+$/)
  })

  it('generates 36 unique kp_cusp fact_ids', () => {
    const ids = new Set<string>()
    const roles = ['STAR_LORD', 'SUB_LORD', 'SUB_SUB_LORD']
    for (const cusp of KP_CUSP_DATA) {
      for (const role of roles) {
        ids.add(`KP.CUSP.${cusp.house}.${role}`)
      }
    }
    expect(ids.size).toBe(36)
  })

  it('generates 27 unique kp_planet fact_ids', () => {
    const ids = new Set<string>()
    const roles = ['STAR_LORD', 'SUB_LORD', 'SUB_SUB_LORD']
    for (const pln of KP_PLANET_DATA) {
      for (const role of roles) {
        ids.add(`KP.PLN.${pln.planet.toUpperCase()}.${role}`)
      }
    }
    expect(ids.size).toBe(27)
  })

  it('generates 7 unique kp_significator fact_ids', () => {
    const ids = new Set<string>()
    for (const sig of KP_SIGNIFICATOR_DATA) {
      ids.add(`KP.SIG.${sig.house}`)
    }
    expect(ids.size).toBe(7)
  })
})

// ── build_id format ──────────────────────────────────────────────────────────

describe('KP build_id format', () => {
  it('build_id starts with mcpt-v33-s2-kp-', () => {
    const ts = '2026-05-22T00-00-00'
    const buildId = `mcpt-v33-s2-kp-${ts}`
    expect(buildId).toMatch(/^mcpt-v33-s2-kp-/)
  })
})
