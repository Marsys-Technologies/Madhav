/**
 * chart_facts_shadbala.test.ts — Unit tests for bootstrap_chart_facts_shadbala (v3.3-S1)
 * Tests pure row-building logic; no DB or network required.
 */

import { describe, it, expect } from 'vitest'
import { buildRows } from '../../scripts/bootstrap/bootstrap_chart_facts_shadbala'

describe('bootstrap_chart_facts_shadbala — buildRows()', () => {
  const rows = buildRows()

  it('produces exactly 63 rows (9 per planet × 7 planets)', () => {
    expect(rows).toHaveLength(63)
  })

  it('all rows have category="shadbala"', () => {
    expect(rows.every(r => r.category === 'shadbala')).toBe(true)
  })

  it('all rows have divisional_chart="D1"', () => {
    expect(rows.every(r => r.divisional_chart === 'D1')).toBe(true)
  })

  it('all fact_ids are unique', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(63)
  })

  it('FORENSIC §6.1 — Saturn Uccha Bala = 59.18 virupa', () => {
    const row = rows.find(r => r.fact_id === 'SBL.FORENSIC.SATURN.UCCHA')
    expect(row).toBeDefined()
    expect(row!.value_number).toBeCloseTo(59.18, 2)
  })

  it('FORENSIC §6.2 — Sun Total = 510.85 virupa', () => {
    const row = rows.find(r => r.fact_id === 'SBL.FORENSIC.SUN.TOTAL_VP')
    expect(row).toBeDefined()
    expect(row!.value_number).toBeCloseTo(510.85, 2)
  })

  it('FORENSIC §6.2 — Jupiter Total = 7.73 rupa', () => {
    const row = rows.find(r => r.fact_id === 'SBL.FORENSIC.JUPITER.TOTAL_RP')
    expect(row).toBeDefined()
    expect(row!.value_number).toBeCloseTo(7.73, 2)
  })

  it('FORENSIC §6.1 — Drik Bala values can be negative', () => {
    const sun_drik = rows.find(r => r.fact_id === 'SBL.FORENSIC.SUN.DRIK')
    expect(sun_drik).toBeDefined()
    expect(sun_drik!.value_number).toBeCloseTo(-35.08, 2)
  })

  it('all rows have source_section', () => {
    expect(rows.every(r => r.source_section?.length > 0)).toBe(true)
  })

  it('all rows have provenance.source = FORENSIC_ASTROLOGICAL_DATA_v8_0', () => {
    expect(rows.every(r => (r.provenance as { source: string }).source === 'FORENSIC_ASTROLOGICAL_DATA_v8_0')).toBe(true)
  })
})
