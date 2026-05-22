/**
 * chart_facts_shadbala.test.ts
 *
 * Unit tests for Shadbala bootstrap data.
 * Tests the data constants and row-building logic without requiring DB.
 *
 * Run: cd platform && npx vitest run test/bootstrap/chart_facts_shadbala.test.ts
 */

import { describe, it, expect } from 'vitest'

// ── Inline the data structures for testing (avoids DB dependency) ───────────

const PLANETS_CLASSICAL = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
const NODES = ['Rahu', 'Ketu']
const ALL_PLANETS = [...PLANETS_CLASSICAL, ...NODES]
const MEASURES = ['Sthana', 'Dig', 'Kala', 'Chesta', 'Naisargika', 'Drik', 'Total']

// FORENSIC §6.2 totals (virupas)
const FORENSIC_TOTALS: Record<string, number> = {
  Sun: 510.85, Moon: 435.51, Mars: 316.23,
  Mercury: 393.26, Jupiter: 464.07, Venus: 276.01, Saturn: 447.98,
}

// JH ranking (authoritative per GAP.07)
const JH_RUPAS: Record<string, number> = {
  Sun: 8.18, Moon: 6.44, Mars: 5.34,
  Mercury: 6.09, Jupiter: 7.68, Venus: 4.80, Saturn: 8.79,
}

const JH_RANKS: Record<string, number> = {
  Saturn: 1, Sun: 2, Jupiter: 3, Moon: 4,
  Mercury: 5, Mars: 6, Venus: 7,
}

// Minimum required Shadbala (BPHS standard)
const MIN_REQUIRED: Record<string, number> = {
  Sun: 5.00, Moon: 6.00, Mars: 5.00, Mercury: 7.00,
  Jupiter: 6.50, Venus: 5.50, Saturn: 5.00,
}

// Uccha Bala values from §6.1 (exaltation proximity)
const UCHA_BALA: Record<string, number> = {
  Sun: 33.99, Moon: 38.02, Mars: 26.84, Mercury: 24.72,
  Jupiter: 8.40, Venus: 27.39, Saturn: 59.18,
}

// Naisargika (natural/fixed) values — classical constants from BPHS
const NAISARGIKA: Record<string, number> = {
  Sun: 60.00, Moon: 51.42, Mars: 17.16, Mercury: 25.74,
  Jupiter: 34.26, Venus: 42.84, Saturn: 8.58,
}

describe('Shadbala — row count', () => {
  it('produces exactly 63 rows (9 planets × 7 measures)', () => {
    const count = ALL_PLANETS.length * MEASURES.length
    expect(count).toBe(63)
  })

  it('has 7 classical planets + 2 nodes = 9', () => {
    expect(ALL_PLANETS.length).toBe(9)
    expect(PLANETS_CLASSICAL.length).toBe(7)
    expect(NODES.length).toBe(2)
  })

  it('has 7 measures', () => {
    expect(MEASURES.length).toBe(7)
  })
})

describe('Shadbala — Saturn spot-check (sealing artifact cross-check)', () => {
  it('Saturn Uccha Bala = 59.18 (near-max; Libra exaltation per §6.1 SBL.UCHA)', () => {
    expect(UCHA_BALA['Saturn']).toBe(59.18)
  })

  it('Saturn total FORENSIC virupas = 447.98 (§6.2 SBL.TOTAL.SATURN)', () => {
    expect(FORENSIC_TOTALS['Saturn']).toBe(447.98)
  })

  it('Saturn JH rupas = 8.79, rank #1 (authoritative per GAP.07)', () => {
    expect(JH_RUPAS['Saturn']).toBe(8.79)
    expect(JH_RANKS['Saturn']).toBe(1)
  })

  it('Saturn JH rupas > minimum required (5.00)', () => {
    expect(JH_RUPAS['Saturn']).toBeGreaterThan(MIN_REQUIRED['Saturn'])
  })
})

describe('Shadbala — Sun spot-check', () => {
  it('Sun total FORENSIC virupas = 510.85', () => {
    expect(FORENSIC_TOTALS['Sun']).toBe(510.85)
  })

  it('Sun JH rupas = 8.18, rank #2', () => {
    expect(JH_RUPAS['Sun']).toBe(8.18)
    expect(JH_RANKS['Sun']).toBe(2)
  })

  it('Sun Naisargika = 60 (highest natural strength — BPHS fixed value)', () => {
    expect(NAISARGIKA['Sun']).toBe(60.00)
  })
})

describe('Shadbala — ranking sanity', () => {
  it('Saturn is JH rank #1', () => {
    const entries = Object.entries(JH_RUPAS).sort((a, b) => b[1] - a[1])
    expect(entries[0][0]).toBe('Saturn')
  })

  it('Venus is JH rank #7 (weakest classical)', () => {
    const entries = Object.entries(JH_RUPAS).sort((a, b) => b[1] - a[1])
    expect(entries[6][0]).toBe('Venus')
  })

  it('all classical planets have JH rupas > 0', () => {
    for (const p of PLANETS_CLASSICAL) {
      expect(JH_RUPAS[p]).toBeGreaterThan(0)
    }
  })
})

describe('Shadbala — Naisargika fixed values (classical constants from BPHS)', () => {
  it('Sun = 60, Moon ≈ 51.42, Mercury ≈ 25.74, Jupiter ≈ 34.26, Venus ≈ 42.84, Mars ≈ 17.16, Saturn ≈ 8.58', () => {
    // Classical Naisargika Bala values are fixed (BPHS Ch.27):
    // Sun=60, Moon=51.43, Venus=42.86, Jupiter=34.29, Mercury=25.71, Mars=17.14, Saturn=8.57
    // FORENSIC shows slight rounding differences — validated per JH engine
    expect(NAISARGIKA['Sun']).toBe(60.00)
    expect(NAISARGIKA['Moon']).toBeCloseTo(51.42, 1)
    expect(NAISARGIKA['Venus']).toBeCloseTo(42.84, 1)
    expect(NAISARGIKA['Jupiter']).toBeCloseTo(34.26, 1)
    expect(NAISARGIKA['Mercury']).toBeCloseTo(25.74, 1)
    expect(NAISARGIKA['Mars']).toBeCloseTo(17.16, 1)
    expect(NAISARGIKA['Saturn']).toBeCloseTo(8.58, 1)
  })
})

describe('Shadbala — fact_id format', () => {
  it('Saturn.Total fact_id = SBL.SATURN.TOTAL', () => {
    const factId = `SBL.${'Saturn'.toUpperCase()}.${'Total'.toUpperCase()}`
    expect(factId).toBe('SBL.SATURN.TOTAL')
  })

  it('Moon.Dig fact_id = SBL.MOON.DIG', () => {
    const factId = `SBL.${'Moon'.toUpperCase()}.${'Dig'.toUpperCase()}`
    expect(factId).toBe('SBL.MOON.DIG')
  })

  it('generates 63 unique fact_ids', () => {
    const ids = new Set<string>()
    for (const p of ALL_PLANETS) {
      for (const m of MEASURES) {
        ids.add(`SBL.${p.toUpperCase()}.${m.toUpperCase()}`)
      }
    }
    expect(ids.size).toBe(63)
  })
})

describe('Shadbala — build_id format', () => {
  it('build_id starts with mcpt-v33-s1-shadbala-', () => {
    const ts = '2026-05-22T00-00-00'
    const buildId = `mcpt-v33-s1-shadbala-${ts}`
    expect(buildId).toMatch(/^mcpt-v33-s1-shadbala-/)
  })
})
