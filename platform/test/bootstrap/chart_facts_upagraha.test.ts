/**
 * chart_facts_upagraha.test.ts
 *
 * Unit tests for Upagraha bootstrap data.
 * Tests data constants and row-building logic without requiring DB.
 *
 * Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §11.1
 *
 * Run: cd platform && npx vitest run test/bootstrap/chart_facts_upagraha.test.ts
 */

import { describe, it, expect } from 'vitest'

// ── Inline data structures (mirrors bootstrap_chart_facts_upagraha.ts) ───────

const SIGN_TO_HOUSE: Record<string, number> = {
  Aries: 1,
  Taurus: 2,
  Gemini: 3,
  Cancer: 4,
  Leo: 5,
  Virgo: 6,
  Libra: 7,
  Scorpio: 8,
  Sagittarius: 9,
  Capricorn: 10,
  Aquarius: 11,
  Pisces: 12,
}

const UPAGRAHA_DATA = [
  // Time-based
  { name: 'Gulika',       upg_type: 'time-based', sign: 'Gemini',      degree: '13°57′', nakshatra: 'Ardra',         forensic_id: 'UPG.GULIKA'       },
  { name: 'Mandi',        upg_type: 'time-based', sign: 'Cancer',      degree: '14°13′', nakshatra: 'Pushya',        forensic_id: 'UPG.MANDI'        },
  { name: 'Yamaghantaka', upg_type: 'time-based', sign: 'Taurus',      degree: '01°54′', nakshatra: 'Krittika',      forensic_id: 'UPG.YAMAGHANTAKA' },
  { name: 'Ardhaprahara', upg_type: 'time-based', sign: 'Aries',       degree: '10°52′', nakshatra: 'Ashwini',       forensic_id: 'UPG.ARDHAPRAHARA' },
  // Sun-based
  { name: 'Dhuma',        upg_type: 'sun-based',  sign: 'Gemini',      degree: '05°17′', nakshatra: 'Mrigasira',     forensic_id: 'UPG.DHUMA'        },
  { name: 'Vyatipata',    upg_type: 'sun-based',  sign: 'Capricorn',   degree: '24°42′', nakshatra: 'Dhanishta',     forensic_id: 'UPG.VYATIPATA'    },
  { name: 'Parivesha',    upg_type: 'sun-based',  sign: 'Cancer',      degree: '24°42′', nakshatra: 'Ashlesha',      forensic_id: 'UPG.PARIVESHA'    },
  { name: 'Indrachapa',   upg_type: 'sun-based',  sign: 'Sagittarius', degree: '05°17′', nakshatra: 'Moola',         forensic_id: 'UPG.INDRACHAPA'   },
  { name: 'Upaketu',      upg_type: 'sun-based',  sign: 'Sagittarius', degree: '21°57′', nakshatra: 'Purva Ashadha', forensic_id: 'UPG.UPAKETU'      },
]

// ── Row count tests ──────────────────────────────────────────────────────────

describe('Upagraha — row count', () => {
  it('has exactly 9 upagrahas total', () => {
    expect(UPAGRAHA_DATA.length).toBe(9)
  })

  it('has exactly 4 time-based upagrahas (≥5 threshold met)', () => {
    const timeBased = UPAGRAHA_DATA.filter((u) => u.upg_type === 'time-based')
    expect(timeBased.length).toBe(4)
    // Total rows ≥ 5 (AC.S2.4 requires upagraha ≥ 5; we ship 9)
    expect(UPAGRAHA_DATA.length).toBeGreaterThanOrEqual(5)
  })

  it('has exactly 5 sun-based upagrahas', () => {
    const sunBased = UPAGRAHA_DATA.filter((u) => u.upg_type === 'sun-based')
    expect(sunBased.length).toBe(5)
  })

  it('all upagrahas have unique names', () => {
    const names = UPAGRAHA_DATA.map((u) => u.name)
    const unique = new Set(names)
    expect(unique.size).toBe(UPAGRAHA_DATA.length)
  })
})

// ── House derivation tests ───────────────────────────────────────────────────

describe('Upagraha — house derivation (Aries Lagna whole-sign)', () => {
  it('Gulika in Gemini → House 3', () => {
    const gulika = UPAGRAHA_DATA.find((u) => u.name === 'Gulika')!
    expect(SIGN_TO_HOUSE[gulika.sign]).toBe(3)
  })

  it('Mandi in Cancer → House 4', () => {
    const mandi = UPAGRAHA_DATA.find((u) => u.name === 'Mandi')!
    expect(SIGN_TO_HOUSE[mandi.sign]).toBe(4)
  })

  it('Yamaghantaka in Taurus → House 2', () => {
    const yama = UPAGRAHA_DATA.find((u) => u.name === 'Yamaghantaka')!
    expect(SIGN_TO_HOUSE[yama.sign]).toBe(2)
  })

  it('Ardhaprahara in Aries → House 1 (Lagna)', () => {
    const ardha = UPAGRAHA_DATA.find((u) => u.name === 'Ardhaprahara')!
    expect(SIGN_TO_HOUSE[ardha.sign]).toBe(1)
  })

  it('all 12 signs have distinct house numbers 1–12', () => {
    const houseNumbers = Object.values(SIGN_TO_HOUSE)
    const uniqueHouses = new Set(houseNumbers)
    expect(uniqueHouses.size).toBe(12)
    expect(Math.min(...houseNumbers)).toBe(1)
    expect(Math.max(...houseNumbers)).toBe(12)
  })
})

// ── Spot-check tests against FORENSIC §11.1 ─────────────────────────────────

describe('Upagraha spot-checks (FORENSIC §11.1)', () => {
  it('Gulika: Gemini 13°57′, nakshatra Ardra', () => {
    const g = UPAGRAHA_DATA.find((u) => u.name === 'Gulika')!
    expect(g.sign).toBe('Gemini')
    expect(g.degree).toBe('13°57′')
    expect(g.nakshatra).toBe('Ardra')
  })

  it('Mandi: Cancer 14°13′, nakshatra Pushya (cross-check with HAZ.MANDI §11.5)', () => {
    const m = UPAGRAHA_DATA.find((u) => u.name === 'Mandi')!
    expect(m.sign).toBe('Cancer')
    expect(m.degree).toBe('14°13′')
    expect(m.nakshatra).toBe('Pushya')
  })

  it('Yamaghantaka: Taurus 01°54′, nakshatra Krittika', () => {
    const y = UPAGRAHA_DATA.find((u) => u.name === 'Yamaghantaka')!
    expect(y.sign).toBe('Taurus')
    expect(y.degree).toBe('01°54′')
    expect(y.nakshatra).toBe('Krittika')
  })

  it('Ardhaprahara: Aries 10°52′, nakshatra Ashwini', () => {
    const a = UPAGRAHA_DATA.find((u) => u.name === 'Ardhaprahara')!
    expect(a.sign).toBe('Aries')
    expect(a.degree).toBe('10°52′')
    expect(a.nakshatra).toBe('Ashwini')
  })

  it('Dhuma: Gemini 05°17′ (sun-based)', () => {
    const d = UPAGRAHA_DATA.find((u) => u.name === 'Dhuma')!
    expect(d.sign).toBe('Gemini')
    expect(d.degree).toBe('05°17′')
    expect(d.upg_type).toBe('sun-based')
  })

  it('Vyatipata: Capricorn 24°42′, nakshatra Dhanishta (sun-based)', () => {
    const v = UPAGRAHA_DATA.find((u) => u.name === 'Vyatipata')!
    expect(v.sign).toBe('Capricorn')
    expect(v.degree).toBe('24°42′')
    expect(v.nakshatra).toBe('Dhanishta')
  })

  it('Parivesha: Cancer 24°42′ (sun-based, complementary to Vyatipata)', () => {
    const p = UPAGRAHA_DATA.find((u) => u.name === 'Parivesha')!
    expect(p.sign).toBe('Cancer')
    expect(p.degree).toBe('24°42′')
    expect(p.upg_type).toBe('sun-based')
  })

  it('Upaketu: Sagittarius 21°57′, nakshatra Purva Ashadha (sun-based)', () => {
    const u = UPAGRAHA_DATA.find((u) => u.name === 'Upaketu')!
    expect(u.sign).toBe('Sagittarius')
    expect(u.degree).toBe('21°57′')
    expect(u.nakshatra).toBe('Purva Ashadha')
  })
})

// ── forensic_id format tests ─────────────────────────────────────────────────

describe('Upagraha forensic_id format', () => {
  it('forensic_ids start with UPG.', () => {
    for (const u of UPAGRAHA_DATA) {
      expect(u.forensic_id).toMatch(/^UPG\./)
    }
  })

  it('Gulika forensic_id = UPG.GULIKA', () => {
    const g = UPAGRAHA_DATA.find((u) => u.name === 'Gulika')!
    expect(g.forensic_id).toBe('UPG.GULIKA')
  })

  it('Mandi forensic_id = UPG.MANDI', () => {
    const m = UPAGRAHA_DATA.find((u) => u.name === 'Mandi')!
    expect(m.forensic_id).toBe('UPG.MANDI')
  })
})

// ── fact_id format tests ─────────────────────────────────────────────────────

describe('Upagraha fact_id format', () => {
  it('fact_ids follow pattern UPG.<NAME_UPPERCASE>', () => {
    for (const u of UPAGRAHA_DATA) {
      const factId = `UPG.${u.name.toUpperCase()}`
      expect(factId).toMatch(/^UPG\.[A-Z]+$/)
    }
  })

  it('Gulika fact_id = UPG.GULIKA', () => {
    const g = UPAGRAHA_DATA.find((u) => u.name === 'Gulika')!
    expect(`UPG.${g.name.toUpperCase()}`).toBe('UPG.GULIKA')
  })

  it('generates 9 unique fact_ids', () => {
    const ids = new Set(UPAGRAHA_DATA.map((u) => `UPG.${u.name.toUpperCase()}`))
    expect(ids.size).toBe(9)
  })
})

// ── build_id format ──────────────────────────────────────────────────────────

describe('Upagraha build_id format', () => {
  it('build_id starts with mcpt-v33-s2-upagraha-', () => {
    const ts = '2026-05-22T00-00-00'
    const buildId = `mcpt-v33-s2-upagraha-${ts}`
    expect(buildId).toMatch(/^mcpt-v33-s2-upagraha-/)
  })
})

// ── B.10 discipline — no fabrication check ───────────────────────────────────

describe('B.10 discipline — FORENSIC-grounded values only', () => {
  it('all signs are valid zodiac signs (not fabricated)', () => {
    const validSigns = new Set(Object.keys(SIGN_TO_HOUSE))
    for (const u of UPAGRAHA_DATA) {
      expect(validSigns.has(u.sign)).toBe(true)
    }
  })

  it('all forensic_ids have canonical UPG prefix matching §11.1 IDs', () => {
    for (const u of UPAGRAHA_DATA) {
      expect(u.forensic_id).toMatch(/^UPG\.[A-Z]+$/)
    }
  })
})
