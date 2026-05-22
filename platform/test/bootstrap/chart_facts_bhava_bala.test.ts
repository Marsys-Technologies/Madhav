/**
 * chart_facts_bhava_bala.test.ts — Unit tests for bootstrap_chart_facts_bhava_bala (v3.3-S1)
 * Tests pure row-building logic; no DB or network required.
 */

import { describe, it, expect } from 'vitest'
import { buildRows, BHAVA_BALA_DATA } from '../../scripts/bootstrap/bootstrap_chart_facts_bhava_bala'

describe('bootstrap_chart_facts_bhava_bala — buildRows()', () => {
  const rows = buildRows()

  it('produces exactly 12 rows', () => {
    expect(rows).toHaveLength(12)
  })

  it('all rows have category="bhava_bala"', () => {
    expect(rows.every(r => r.category === 'bhava_bala')).toBe(true)
  })

  it('all fact_ids are unique', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(12)
  })

  it('FORENSIC §6.4 — House 10 is rank 1 (strongest bhava)', () => {
    const h10 = BHAVA_BALA_DATA.find(d => d.house === 10)
    expect(h10).toBeDefined()
    expect(h10!.rank).toBe(1)
    expect(h10!.virupa).toBeCloseTo(494.53, 2)
  })

  it('FORENSIC §6.4 — House 8 is rank 12 (weakest bhava)', () => {
    const h8 = BHAVA_BALA_DATA.find(d => d.house === 8)
    expect(h8).toBeDefined()
    expect(h8!.rank).toBe(12)
    expect(h8!.virupa).toBeCloseTo(228.37, 2)
  })

  it('fact_id pattern: BVB.FORENSIC.H01 through BVB.FORENSIC.H12', () => {
    for (let i = 1; i <= 12; i++) {
      const id = `BVB.FORENSIC.H${String(i).padStart(2, '0')}`
      expect(rows.some(r => r.fact_id === id)).toBe(true)
    }
  })
})
