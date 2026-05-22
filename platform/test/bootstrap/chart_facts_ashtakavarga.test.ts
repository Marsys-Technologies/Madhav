/**
 * chart_facts_ashtakavarga.test.ts — Unit tests for bootstrap_chart_facts_ashtakavarga (v3.3-S1)
 * Tests pure row-building logic; no DB or network required.
 */

import { describe, it, expect } from 'vitest'
import { buildSavRows, buildBavRows } from '../../scripts/bootstrap/bootstrap_chart_facts_ashtakavarga'

describe('bootstrap_chart_facts_ashtakavarga — SAV rows', () => {
  const rows = buildSavRows()

  it('produces exactly 12 SAV rows', () => {
    expect(rows).toHaveLength(12)
  })

  it('all rows have category="ashtakavarga_sav"', () => {
    expect(rows.every(r => r.category === 'ashtakavarga_sav')).toBe(true)
  })

  it('FORENSIC §7.2 — Cancer (H4) = 32 bindus', () => {
    const row = rows.find(r => r.fact_id === 'SAV.FORENSIC.H04')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(32)
  })

  it('FORENSIC §7.2 — SAV total = 337 (sum of all 12 houses)', () => {
    const total = rows.reduce((sum, r) => sum + r.value_number, 0)
    expect(total).toBe(337)
  })

  it('all fact_ids are unique', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(12)
  })
})

describe('bootstrap_chart_facts_ashtakavarga — BAV rows', () => {
  const rows = buildBavRows()

  it('produces ≥100 rows (84 bindu + 21 pinda = 105)', () => {
    expect(rows.length).toBeGreaterThanOrEqual(100)
    expect(rows).toHaveLength(105)
  })

  it('all rows have category="ashtakavarga_bav"', () => {
    expect(rows.every(r => r.category === 'ashtakavarga_bav')).toBe(true)
  })

  it('all fact_ids are unique', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(105)
  })

  it('FORENSIC §7.1 — Moon Pisces = 6 bindus', () => {
    const row = rows.find(r => r.fact_id === 'BAV.FORENSIC.MOON.PI')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(6)
  })

  it('FORENSIC §7.1 — Mercury Taurus = 7 bindus (highest in Mercury BAV)', () => {
    const row = rows.find(r => r.fact_id === 'BAV.FORENSIC.MERCURY.TA')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(7)
  })

  it('FORENSIC §7.3 — Mars Shuddha Pinda = 198 (rank 1)', () => {
    const row = rows.find(r => r.fact_id === 'BAV.FORENSIC.MARS.PINDA_SHUDDHA')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(198)
  })

  it('FORENSIC §7.3 — Saturn Shuddha Pinda = 80 (rank 7, weakest)', () => {
    const row = rows.find(r => r.fact_id === 'BAV.FORENSIC.SATURN.PINDA_SHUDDHA')
    expect(row).toBeDefined()
    expect(row!.value_number).toBe(80)
  })

  it('FORENSIC §7.1 — Sun BAV total = 48 bindus', () => {
    const bindus = rows
      .filter(r => r.fact_id.startsWith('BAV.FORENSIC.SUN.') && !r.fact_id.includes('PINDA'))
      .reduce((sum, r) => sum + r.value_number, 0)
    expect(bindus).toBe(48)
  })
})
