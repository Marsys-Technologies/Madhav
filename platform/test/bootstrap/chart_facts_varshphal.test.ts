/**
 * chart_facts_varshphal.test.ts — Unit tests for bootstrap_chart_facts_varshphal (v3.3-S3)
 *
 * Tests pure row-building logic and Tajaka muntha computation.
 * No DB or network required — all assertions run offline.
 *
 * Coverage:
 *   - Row count ≥ 1500 (AC.S3.1)
 *   - All 87 years represented (1984–2070)
 *   - 18 distinct subkeys per year
 *   - Muntha sign correctness (deterministic Tajaka rule)
 *   - 12-year cycle verification (Cancer → Cancer)
 *   - Muntha house correctness
 *   - Varsha number sequence
 *   - [EXTERNAL_COMPUTATION_REQUIRED] placeholder discipline (B.10)
 *   - fact_id format validation
 *   - No duplicate fact_ids
 *   - category and divisional_chart correctness
 *   - Provenance structure completeness
 */

import { describe, it, expect } from 'vitest'
import {
  buildAllRows,
  getMunthaSign,
  getMunthaHouse,
  getVarshaNumber,
  SIGNS,
  BIRTH_YEAR,
  NATAL_LAGNA_INDEX,
  YEAR_START,
  YEAR_END,
} from '../../scripts/bootstrap/bootstrap_chart_facts_varshphal'

describe('bootstrap_chart_facts_varshphal', () => {
  // Build all rows once for the describe block
  const allRows = buildAllRows()
  const yearCount = YEAR_END - YEAR_START + 1 // 87

  // ── Row count ──────────────────────────────────────────────────────────────

  it('AC.S3.1 — produces ≥ 1500 rows total', () => {
    expect(allRows.length).toBeGreaterThanOrEqual(1500)
  })

  it('produces exactly 1566 rows (18 × 87 years)', () => {
    expect(allRows).toHaveLength(18 * yearCount)
  })

  it('1984 has exactly 18 distinct subkeys', () => {
    const rows1984 = allRows.filter(r => r.fact_id.startsWith('VPH.1984.'))
    expect(rows1984).toHaveLength(18)
  })

  it('2070 has exactly 18 distinct subkeys', () => {
    const rows2070 = allRows.filter(r => r.fact_id.startsWith('VPH.2070.'))
    expect(rows2070).toHaveLength(18)
  })

  // ── Year coverage ──────────────────────────────────────────────────────────

  it('covers all 87 years from 1984 to 2070', () => {
    for (let year = YEAR_START; year <= YEAR_END; year++) {
      const rows = allRows.filter(r => r.fact_id.startsWith(`VPH.${year}.`))
      expect(rows.length, `year ${year} should have 18 rows`).toBeGreaterThan(0)
    }
  })

  it('does not include years outside 1984–2070', () => {
    const outside = allRows.filter(r => {
      const m = r.fact_id.match(/^VPH\.(\d{4})\./)
      if (!m) return true
      const y = parseInt(m[1])
      return y < YEAR_START || y > YEAR_END
    })
    expect(outside).toHaveLength(0)
  })

  // ── Muntha sign correctness ────────────────────────────────────────────────

  it('muntha for 1984 (Varsha 1) = Cancer (natal lagna)', () => {
    expect(getMunthaSign(1984)).toBe('Cancer')
  })

  it('muntha for 1985 (Varsha 2) = Leo', () => {
    expect(getMunthaSign(1985)).toBe('Leo')
  })

  it('muntha for 1986 (Varsha 3) = Virgo', () => {
    expect(getMunthaSign(1986)).toBe('Virgo')
  })

  it('muntha for 1995 (Varsha 12) = Gemini (last in 12-cycle before reset)', () => {
    // 1984+0=Cancer, 1984+11=Gemini → 1984+11=1995
    expect(getMunthaSign(1995)).toBe('Gemini')
  })

  it('muntha for 1996 (Varsha 13) = Cancer (12-year cycle resets)', () => {
    expect(getMunthaSign(1996)).toBe('Cancer')
  })

  it('NATAL_LAGNA_INDEX points to Cancer in SIGNS array', () => {
    expect(SIGNS[NATAL_LAGNA_INDEX]).toBe('Cancer')
  })

  it('muntha cycles back to Cancer every 12 years', () => {
    for (let offset = 0; offset < 84; offset += 12) {
      const year = BIRTH_YEAR + offset
      expect(getMunthaSign(year), `year ${year} should be Cancer`).toBe('Cancer')
    }
  })

  it('chart_facts row for muntha 1984 has value_text = Cancer', () => {
    const row = allRows.find(r => r.fact_id === 'VPH.1984.MUNTHA')
    expect(row).toBeDefined()
    expect(row!.value_text).toBe('Cancer')
  })

  it('chart_facts row for muntha 1985 has value_text = Leo', () => {
    const row = allRows.find(r => r.fact_id === 'VPH.1985.MUNTHA')
    expect(row).toBeDefined()
    expect(row!.value_text).toBe('Leo')
  })

  it('chart_facts row for muntha 1996 has value_text = Cancer (cycle)', () => {
    const row = allRows.find(r => r.fact_id === 'VPH.1996.MUNTHA')
    expect(row).toBeDefined()
    expect(row!.value_text).toBe('Cancer')
  })

  // ── Muntha house correctness ───────────────────────────────────────────────

  it('muntha_house for 1984 = 1 (Cancer lagna = house 1)', () => {
    expect(getMunthaHouse(1984)).toBe(1)
  })

  it('muntha_house for 1985 = 2 (Leo = house 2 from Cancer)', () => {
    expect(getMunthaHouse(1985)).toBe(2)
  })

  it('muntha_house for 1996 = 1 (Cancer again = H1)', () => {
    expect(getMunthaHouse(1996)).toBe(1)
  })

  it('chart_facts row for muntha_house 1984 has value_number = 1', () => {
    const row = allRows.find(r => r.fact_id === 'VPH.1984.MUNTHA_HOUSE')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(1)
  })

  // ── Varsha number sequence ─────────────────────────────────────────────────

  it('varsha_number for 1984 = 1', () => {
    expect(getVarshaNumber(1984)).toBe(1)
  })

  it('varsha_number for 2070 = 87', () => {
    expect(getVarshaNumber(2070)).toBe(87)
  })

  it('chart_facts varsha_number 1984 row has value_number = 1', () => {
    const row = allRows.find(r => r.fact_id === 'VPH.1984.VARSHA_NUMBER')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(1)
  })

  it('chart_facts varsha_number 2070 row has value_number = 87', () => {
    const row = allRows.find(r => r.fact_id === 'VPH.2070.VARSHA_NUMBER')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(87)
  })

  // ── B.10 [EXTERNAL_COMPUTATION_REQUIRED] discipline ───────────────────────

  it('year_lord rows exist for all 87 years', () => {
    for (let year = YEAR_START; year <= YEAR_END; year++) {
      const row = allRows.find(r => r.fact_id === `VPH.${year}.YEAR_LORD`)
      expect(row, `year_lord row missing for ${year}`).toBeDefined()
    }
  })

  it('year_lord rows have value_text = [EXTERNAL_COMPUTATION_REQUIRED]', () => {
    const yearLordRows = allRows.filter(r => r.fact_id.includes('.YEAR_LORD'))
    expect(yearLordRows).toHaveLength(yearCount)
    expect(yearLordRows.every(r => r.value_text === '[EXTERNAL_COMPUTATION_REQUIRED]')).toBe(true)
  })

  it('saham.punya rows exist for all 87 years', () => {
    const sahamRows = allRows.filter(r => r.fact_id.includes('.SAHAM.PUNYA'))
    expect(sahamRows).toHaveLength(yearCount)
  })

  it('all EXTERNAL_COMPUTATION_REQUIRED rows have that exact marker string', () => {
    const externalRows = allRows.filter(r =>
      r.value_text === '[EXTERNAL_COMPUTATION_REQUIRED]'
    )
    // 15 external subkeys × 87 years = 1305
    expect(externalRows.length).toBe(15 * yearCount)
  })

  it('muntha rows do NOT say EXTERNAL_COMPUTATION_REQUIRED', () => {
    const munthaRows = allRows.filter(r => r.fact_id.match(/\.MUNTHA$/))
    expect(munthaRows).toHaveLength(yearCount)
    expect(munthaRows.every(r => r.value_text !== '[EXTERNAL_COMPUTATION_REQUIRED]')).toBe(true)
  })

  // ── fact_id format validation ──────────────────────────────────────────────

  it('all fact_ids follow VPH.<year>.<SUBKEY> format', () => {
    const pattern = /^VPH\.\d{4}\.[A-Z0-9_.]+$/
    const invalid = allRows.filter(r => !pattern.test(r.fact_id))
    expect(invalid).toHaveLength(0)
  })

  it('no duplicate fact_ids', () => {
    const ids = allRows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(allRows.length)
  })

  // ── category and divisional_chart ─────────────────────────────────────────

  it('all rows have category = varshphal', () => {
    expect(allRows.every(r => r.category === 'varshphal')).toBe(true)
  })

  it('all rows have divisional_chart = D1', () => {
    expect(allRows.every(r => r.divisional_chart === 'D1')).toBe(true)
  })

  // ── Provenance structure ───────────────────────────────────────────────────

  it('all rows have provenance with required fields', () => {
    const missingProvenance = allRows.filter(r => {
      const p = r.provenance
      return !p || !p.source_uri || !p.source_canonical_id || !p.extracted_at || !p.extraction_method
    })
    expect(missingProvenance).toHaveLength(0)
  })

  it('muntha rows reference TAJAKA_NEELAKANTHI as source', () => {
    const munthaRows = allRows.filter(r => r.fact_id.match(/\.MUNTHA$/))
    expect(munthaRows.every(r => r.provenance.source_canonical_id === 'TAJAKA_NEELAKANTHI')).toBe(true)
  })

  it('all rows have non-empty source_section', () => {
    expect(allRows.every(r => r.source_section && r.source_section.length > 0)).toBe(true)
  })

  // ── Subkey completeness spot-check ────────────────────────────────────────

  it('1984 has all 12 saham subkeys', () => {
    const sahamKeys = ['PUNYA', 'VIDYA', 'YASAS', 'MITRA', 'MAHATMYA',
                       'AASHA', 'SAMEERA', 'KARMA', 'KALI', 'BADHAKA', 'KAMA', 'SHREE']
    for (const key of sahamKeys) {
      const row = allRows.find(r => r.fact_id === `VPH.1984.SAHAM.${key}`)
      expect(row, `saham ${key} missing for 1984`).toBeDefined()
    }
  })

  it('all years have PANCHA_VARGIYA_BALA row', () => {
    const pvbRows = allRows.filter(r => r.fact_id.includes('.PANCHA_VARGIYA_BALA'))
    expect(pvbRows).toHaveLength(yearCount)
    expect(pvbRows.every(r => r.value_text === '[EXTERNAL_COMPUTATION_REQUIRED]')).toBe(true)
  })
})
