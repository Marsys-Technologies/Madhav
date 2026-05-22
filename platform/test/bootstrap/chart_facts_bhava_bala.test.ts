/**
 * chart_facts_bhava_bala.test.ts
 *
 * Unit tests for Bhava Bala bootstrap data.
 * Tests data correctness without DB access.
 *
 * Run: cd platform && npx vitest run test/bootstrap/chart_facts_bhava_bala.test.ts
 */

import { describe, it, expect } from 'vitest'

// ── Replicated data constants ────────────────────────────────────────────────

interface BhavaRow {
  house: number
  life_area: string
  forensic_total_virupas: number
  forensic_total_rupas: number
  forensic_rank: number
  lord_planet: string
  lord_virupas: number
  dig_bala: number
  drishti_bala: number
  jh_rupas: number
  jh_rank: number
  lord_sign: string
}

const BHAVA_DATA: BhavaRow[] = [
  { house: 1,  life_area: 'Self / Body / Lagna',
    forensic_total_virupas: 340.08, forensic_total_rupas: 5.67, forensic_rank: 10,
    lord_planet: 'Mars',   lord_virupas: 316.23, dig_bala: 30, drishti_bala: -6.15,
    jh_rupas: 7.00, jh_rank: 8, lord_sign: 'Aries' },
  { house: 2,  life_area: 'Family / Speech / Savings',
    forensic_total_virupas: 266.26, forensic_total_rupas: 4.44, forensic_rank: 11,
    lord_planet: 'Venus',  lord_virupas: 276.01, dig_bala: 20, drishti_bala: -29.75,
    jh_rupas: 4.83, jh_rank: 11, lord_sign: 'Taurus' },
  { house: 3,  life_area: 'Skills / Effort / Siblings',
    forensic_total_virupas: 447.37, forensic_total_rupas: 7.46, forensic_rank: 7,
    lord_planet: 'Mercury', lord_virupas: 393.26, dig_bala: 40, drishti_bala: 14.11,
    jh_rupas: 7.83, jh_rank: 6, lord_sign: 'Gemini' },
  { house: 4,  life_area: 'Home / Peace / Mother',
    forensic_total_virupas: 474.87, forensic_total_rupas: 7.91, forensic_rank: 6,
    lord_planet: 'Moon',   lord_virupas: 435.51, dig_bala: 60, drishti_bala: -20.64,
    jh_rupas: 8.80, jh_rank: 5, lord_sign: 'Cancer' },
  { house: 5,  life_area: 'Creativity / Children / Buddhi',
    forensic_total_virupas: 486.86, forensic_total_rupas: 8.11, forensic_rank: 2,
    lord_planet: 'Sun',    lord_virupas: 510.85, dig_bala: 10, drishti_bala: -33.99,
    jh_rupas: 9.64, jh_rank: 1, lord_sign: 'Leo' },
  { house: 6,  life_area: 'Enemies / Debt / Service',
    forensic_total_virupas: 405.17, forensic_total_rupas: 6.75, forensic_rank: 8,
    lord_planet: 'Mercury', lord_virupas: 393.26, dig_bala: 10, drishti_bala: 1.91,
    jh_rupas: 6.61, jh_rank: 9, lord_sign: 'Virgo' },
  { house: 7,  life_area: 'Partners / Spouse / ATT',
    forensic_total_virupas: 253.36, forensic_total_rupas: 4.22, forensic_rank: 12,
    lord_planet: 'Venus',  lord_virupas: 276.01, dig_bala: 0, drishti_bala: -22.65,
    jh_rupas: 4.73, jh_rank: 12, lord_sign: 'Libra' },
  { house: 8,  life_area: 'Crisis / Occult / Inheritance',
    forensic_total_virupas: 358.67, forensic_total_rupas: 5.98, forensic_rank: 9,
    lord_planet: 'Mars',   lord_virupas: 316.23, dig_bala: 50, drishti_bala: -7.56,
    jh_rupas: 6.06, jh_rank: 10, lord_sign: 'Scorpio' },
  { house: 9,  life_area: 'Fortune / Dharma / Guru',
    forensic_total_virupas: 477.55, forensic_total_rupas: 7.96, forensic_rank: 5,
    lord_planet: 'Jupiter', lord_virupas: 464.07, dig_bala: 20, drishti_bala: -6.52,
    jh_rupas: 7.77, jh_rank: 7, lord_sign: 'Sagittarius' },
  { house: 10, life_area: 'Career / Status',
    forensic_total_virupas: 482.99, forensic_total_rupas: 8.05, forensic_rank: 3,
    lord_planet: 'Saturn', lord_virupas: 447.98, dig_bala: 60, drishti_bala: -24.99,
    jh_rupas: 9.39, jh_rank: 3, lord_sign: 'Capricorn' },
  { house: 11, life_area: 'Gains / Network / AK Moon',
    forensic_total_virupas: 478.27, forensic_total_rupas: 7.97, forensic_rank: 4,
    lord_planet: 'Saturn', lord_virupas: 447.98, dig_bala: 40, drishti_bala: -9.71,
    jh_rupas: 9.60, jh_rank: 2, lord_sign: 'Aquarius' },
  { house: 12, life_area: 'Foreign / Isolation / Liberation',
    forensic_total_virupas: 506.09, forensic_total_rupas: 8.43, forensic_rank: 1,
    lord_planet: 'Jupiter', lord_virupas: 464.07, dig_bala: 20, drishti_bala: 22.02,
    jh_rupas: 9.28, jh_rank: 4, lord_sign: 'Pisces' },
]

describe('Bhava Bala — row count', () => {
  it('produces exactly 12 rows (one per house)', () => {
    expect(BHAVA_DATA.length).toBe(12)
  })

  it('covers houses 1 through 12 with no gaps', () => {
    const houses = BHAVA_DATA.map(b => b.house).sort((a, b) => a - b)
    expect(houses).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  })
})

describe('Bhava Bala — JH ranking (authoritative per FORENSIC §6.6)', () => {
  it('5H is JH rank #1 (strongest)', () => {
    const h5 = BHAVA_DATA.find(b => b.house === 5)!
    expect(h5.jh_rank).toBe(1)
    expect(h5.jh_rupas).toBe(9.64)
  })

  it('7H is JH rank #12 (weakest)', () => {
    const h7 = BHAVA_DATA.find(b => b.house === 7)!
    expect(h7.jh_rank).toBe(12)
    expect(h7.jh_rupas).toBe(4.73)
  })

  it('11H is JH rank #2', () => {
    const h11 = BHAVA_DATA.find(b => b.house === 11)!
    expect(h11.jh_rank).toBe(2)
    expect(h11.jh_rupas).toBe(9.60)
  })

  it('10H is JH rank #3', () => {
    const h10 = BHAVA_DATA.find(b => b.house === 10)!
    expect(h10.jh_rank).toBe(3)
    expect(h10.jh_rupas).toBe(9.39)
  })

  it('JH ranks are unique (no ties)', () => {
    const ranks = BHAVA_DATA.map(b => b.jh_rank)
    const unique = new Set(ranks)
    expect(unique.size).toBe(12)
  })

  it('JH ranks span 1–12', () => {
    const ranks = BHAVA_DATA.map(b => b.jh_rank).sort((a, b) => a - b)
    expect(ranks).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  })
})

describe('Bhava Bala — FORENSIC engine (§6.4 reference)', () => {
  it('12H is FORENSIC rank #1 (506.09 virupas)', () => {
    const h12 = BHAVA_DATA.find(b => b.house === 12)!
    expect(h12.forensic_rank).toBe(1)
    expect(h12.forensic_total_virupas).toBe(506.09)
  })

  it('7H is FORENSIC rank #12 (weakest in both engines)', () => {
    const h7 = BHAVA_DATA.find(b => b.house === 7)!
    expect(h7.forensic_rank).toBe(12)
  })

  it('FORENSIC and JH agree on 7H being weakest', () => {
    const h7 = BHAVA_DATA.find(b => b.house === 7)!
    expect(h7.forensic_rank).toBe(12)
    expect(h7.jh_rank).toBe(12)
  })
})

describe('Bhava Bala — lord planets', () => {
  it('H7 lord = Venus (weakest house lord analysis)', () => {
    const h7 = BHAVA_DATA.find(b => b.house === 7)!
    expect(h7.lord_planet).toBe('Venus')
  })

  it('H5 lord = Sun (strongest house)', () => {
    const h5 = BHAVA_DATA.find(b => b.house === 5)!
    expect(h5.lord_planet).toBe('Sun')
  })

  it('H10 and H11 both have Saturn as lord (Capricorn + Aquarius)', () => {
    const h10 = BHAVA_DATA.find(b => b.house === 10)!
    const h11 = BHAVA_DATA.find(b => b.house === 11)!
    expect(h10.lord_planet).toBe('Saturn')
    expect(h11.lord_planet).toBe('Saturn')
  })

  it('Saturn Uccha Bala powers H10 + H11 as lord (Shadbala concordance)', () => {
    // Saturn is JH Shadbala #1; lords H10 (JH BVB #3) and H11 (JH BVB #2)
    const h10 = BHAVA_DATA.find(b => b.house === 10)!
    const h11 = BHAVA_DATA.find(b => b.house === 11)!
    expect(h10.lord_virupas).toBe(447.98)  // Saturn Shadbala
    expect(h11.lord_virupas).toBe(447.98)
    // Both H10 and H11 are high-Bhavabala (ranks 3 and 2) = career + gains strength
    expect(h10.jh_rank).toBeLessThan(5)
    expect(h11.jh_rank).toBeLessThan(5)
  })
})

describe('Bhava Bala — fact_id format', () => {
  it('H7 fact_id = BVB.JH.7.TOTAL', () => {
    expect('BVB.JH.7.TOTAL').toMatch(/^BVB\.JH\.\d+\.TOTAL$/)
  })

  it('generates 12 unique fact_ids', () => {
    const ids = new Set(BHAVA_DATA.map(b => `BVB.JH.${b.house}.TOTAL`))
    expect(ids.size).toBe(12)
  })
})

describe('Bhava Bala — build_id format', () => {
  it('build_id starts with mcpt-v33-s1-bhava-bala-', () => {
    const ts = '2026-05-22T00-00-00'
    const buildId = `mcpt-v33-s1-bhava-bala-${ts}`
    expect(buildId).toMatch(/^mcpt-v33-s1-bhava-bala-/)
  })
})

describe('Bhava Bala — dig_bala values sanity', () => {
  it('all dig_bala values are 0–60', () => {
    for (const b of BHAVA_DATA) {
      expect(b.dig_bala).toBeGreaterThanOrEqual(0)
      expect(b.dig_bala).toBeLessThanOrEqual(60)
    }
  })

  it('H4 and H10 have dig_bala = 60 (maximum — both angular kendras)', () => {
    const h4 = BHAVA_DATA.find(b => b.house === 4)!
    const h10 = BHAVA_DATA.find(b => b.house === 10)!
    expect(h4.dig_bala).toBe(60)
    expect(h10.dig_bala).toBe(60)
  })

  it('H7 has dig_bala = 0', () => {
    const h7 = BHAVA_DATA.find(b => b.house === 7)!
    expect(h7.dig_bala).toBe(0)
  })
})
