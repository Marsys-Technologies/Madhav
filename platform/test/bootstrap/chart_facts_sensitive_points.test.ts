/**
 * chart_facts_sensitive_points.test.ts
 *
 * BRAHMA GA-1-6 — Unit tests for bootstrap_chart_facts_sensitive_points
 *
 * Tests pure row-building logic (buildRows + sub-builders).
 * No DB or network required.
 *
 * Acceptance criteria:
 *   - Gulika present (upagraha)
 *   - Upapada (UL) present (arudha)
 *   - FORENSIC benchmark: Gulika in Gemini 13°57′
 *   - All categories produce correct counts
 *   - All fact_ids are unique
 *
 * Run: cd platform && npx vitest run test/bootstrap/chart_facts_sensitive_points.test.ts
 */

import { describe, it, expect } from 'vitest'
import {
  buildRows,
  buildUpagrahaRows,
  buildSpecialLagnaRows,
  buildSahamRows,
  buildArudhaRows,
} from '../../scripts/bootstrap/bootstrap_chart_facts_sensitive_points'

// ── Aggregate row tests ───────────────────────────────────────────────────────

describe('buildRows() — aggregate', () => {
  const rows = buildRows()

  it('produces exactly 63 rows total (9+9+36+9)', () => {
    expect(rows).toHaveLength(63)
  })

  it('all fact_ids are unique (no duplicates)', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(63)
  })

  it('all rows have a non-empty build_id', () => {
    expect(rows.every(r => typeof r.build_id === 'string' && r.build_id.length > 0)).toBe(true)
  })

  it('all rows have provenance with source_uri', () => {
    for (const r of rows) {
      expect(r.provenance).toBeDefined()
      expect((r.provenance as Record<string, unknown>).source_uri).toContain('FORENSIC')
    }
  })

  it('all rows have a source_section referencing FORENSIC_v8_0', () => {
    expect(rows.every(r => r.source_section.startsWith('FORENSIC_v8_0_§'))).toBe(true)
  })

  it('category distribution: 9+9+36+9', () => {
    const byCat: Record<string, number> = {}
    for (const r of rows) {
      byCat[r.category] = (byCat[r.category] ?? 0) + 1
    }
    expect(byCat['upagraha']).toBe(9)
    expect(byCat['special_lagna']).toBe(9)
    expect(byCat['saham']).toBe(36)
    expect(byCat['arudha']).toBe(9)
  })
})

// ── Upagraha tests ────────────────────────────────────────────────────────────

describe('buildUpagrahaRows() — FORENSIC §11.1', () => {
  const rows = buildUpagrahaRows()

  it('produces exactly 9 upagraha rows', () => {
    expect(rows).toHaveLength(9)
  })

  it('has 4 time-based upagrahas', () => {
    const tb = rows.filter(r => (r.value_json as Record<string, unknown>)?.type === 'time-based')
    expect(tb).toHaveLength(4)
  })

  it('has 5 sun-based upagrahas', () => {
    const sb = rows.filter(r => (r.value_json as Record<string, unknown>)?.type === 'sun-based')
    expect(sb).toHaveLength(5)
  })

  // FORENSIC benchmark: Gulika must be present and in Gemini 13°57′
  it('FORENSIC AC: Gulika present — UPG.GULIKA row exists', () => {
    const gulika = rows.find(r => r.fact_id === 'UPG.GULIKA')
    expect(gulika).toBeDefined()
  })

  it('FORENSIC AC: Gulika in Gemini 13°57′ (FORENSIC §11.1 row 1)', () => {
    const gulika = rows.find(r => r.fact_id === 'UPG.GULIKA')!
    const json = gulika.value_json as Record<string, unknown>
    expect(json.sign).toBe('Gemini')
    expect(json.degree).toBe('13°57′')
    expect(json.nakshatra).toBe('Ardra')
  })

  it('FORENSIC: Gulika → House 3 (Aries Lagna, whole-sign)', () => {
    const gulika = rows.find(r => r.fact_id === 'UPG.GULIKA')!
    const json = gulika.value_json as Record<string, unknown>
    expect(json.house).toBe(3)
  })

  it('FORENSIC: Mandi in Cancer 14°13′, nakshatra Pushya', () => {
    const mandi = rows.find(r => r.fact_id === 'UPG.MANDI')!
    const json = mandi.value_json as Record<string, unknown>
    expect(json.sign).toBe('Cancer')
    expect(json.degree).toBe('14°13′')
    expect(json.nakshatra).toBe('Pushya')
    expect(json.house).toBe(4)
  })

  it('FORENSIC: Dhuma in Gemini 05°17′ (sun-based)', () => {
    const dhuma = rows.find(r => r.fact_id === 'UPG.DHUMA')!
    const json = dhuma.value_json as Record<string, unknown>
    expect(json.sign).toBe('Gemini')
    expect(json.type).toBe('sun-based')
  })

  it('all upagraha rows have category=upagraha', () => {
    expect(rows.every(r => r.category === 'upagraha')).toBe(true)
  })

  it('all upagraha rows have divisional_chart=D1', () => {
    expect(rows.every(r => r.divisional_chart === 'D1')).toBe(true)
  })

  it('all upagraha fact_ids start with UPG.', () => {
    expect(rows.every(r => r.fact_id.startsWith('UPG.'))).toBe(true)
  })
})

// ── Special Lagna tests ───────────────────────────────────────────────────────

describe('buildSpecialLagnaRows() — FORENSIC §12.1', () => {
  const rows = buildSpecialLagnaRows()

  it('produces exactly 9 special lagna rows', () => {
    expect(rows).toHaveLength(9)
  })

  it('all rows have category=special_lagna', () => {
    expect(rows.every(r => r.category === 'special_lagna')).toBe(true)
  })

  it('all rows have divisional_chart=D1', () => {
    expect(rows.every(r => r.divisional_chart === 'D1')).toBe(true)
  })

  // v8.0 corrections — JH authoritative
  it('FORENSIC AC: Hora Lagna in Gemini H3 (NOT Libra 7H — v6.0 error corrected)', () => {
    const hora = rows.find(r => r.fact_id === 'LAG.HORA')!
    const json = hora.value_json as Record<string, unknown>
    expect(json.sign).toBe('Gemini')
    expect(json.house).toBe(3)
    expect(json.nakshatra).toBe('Mrigashira')
    expect(hora.value_text).toContain('Gemini')
  })

  it('FORENSIC AC: Ghati Lagna in Sagittarius H9 (NOT Scorpio 8H — v6.0 error corrected)', () => {
    const ghati = rows.find(r => r.fact_id === 'LAG.GHATI')!
    const json = ghati.value_json as Record<string, unknown>
    expect(json.sign).toBe('Sagittarius')
    expect(json.house).toBe(9)
  })

  it('FORENSIC: Bhrigu Bindu in Libra 8°03′34.51″ H7 (LAG.BB)', () => {
    const bb = rows.find(r => r.fact_id === 'LAG.BB')!
    const json = bb.value_json as Record<string, unknown>
    expect(json.sign).toBe('Libra')
    expect(json.house).toBe(7)
    expect(json.nakshatra).toBe('Swati')
  })

  it('all LAG.* fact_ids present', () => {
    const expected = ['LAG.BHAVA', 'LAG.HORA', 'LAG.GHATI', 'LAG.VIGHATI',
      'LAG.VARNADA', 'LAG.SHREE', 'LAG.PRANAPADA', 'LAG.INDU', 'LAG.BB']
    for (const id of expected) {
      expect(rows.some(r => r.fact_id === id)).toBe(true)
    }
  })
})

// ── Saham tests ───────────────────────────────────────────────────────────────

describe('buildSahamRows() — FORENSIC §12.2', () => {
  const rows = buildSahamRows()

  it('produces exactly 36 saham rows', () => {
    expect(rows).toHaveLength(36)
  })

  it('all rows have category=saham', () => {
    expect(rows.every(r => r.category === 'saham')).toBe(true)
  })

  it('all rows have divisional_chart=D1', () => {
    expect(rows.every(r => r.divisional_chart === 'D1')).toBe(true)
  })

  it('all fact_ids start with SAH.', () => {
    expect(rows.every(r => r.fact_id.startsWith('SAH.'))).toBe(true)
  })

  it('FORENSIC: Punya Saham in Gemini H3', () => {
    const punya = rows.find(r => r.fact_id === 'SAH.PUNYA')!
    const json = punya.value_json as Record<string, unknown>
    expect(json.sign).toBe('Gemini')
    expect(json.house).toBe(3)
  })

  it('FORENSIC AC: Roga Saham in Taurus H2 (NOT Libra 7H — v6.0 error corrected)', () => {
    const roga = rows.find(r => r.fact_id === 'SAH.ROGA')!
    const json = roga.value_json as Record<string, unknown>
    expect(json.sign).toBe('Taurus')
    expect(json.house).toBe(2)
    expect(roga.value_text).not.toContain('Libra')
  })

  it('FORENSIC AC: Mahatmya Saham in Sagittarius H9 (NOT Libra 7H — v6.0 error corrected)', () => {
    const mah = rows.find(r => r.fact_id === 'SAH.MAHATMYA')!
    const json = mah.value_json as Record<string, unknown>
    expect(json.sign).toBe('Sagittarius')
    expect(json.house).toBe(9)
  })

  it('FORENSIC: Vivaha Saham in Cancer H4 (NOT Gemini Ardra 3H — v6.0 error corrected)', () => {
    const vivaha = rows.find(r => r.fact_id === 'SAH.VIVAHA')!
    const json = vivaha.value_json as Record<string, unknown>
    expect(json.sign).toBe('Cancer')
    expect(json.house).toBe(4)
  })

  it('all sahams have a meaning field', () => {
    for (const r of rows) {
      const json = r.value_json as Record<string, unknown>
      expect(typeof json.meaning).toBe('string')
      expect((json.meaning as string).length).toBeGreaterThan(0)
    }
  })

  it('all fact_ids are unique', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(36)
  })
})

// ── Arudha tests ──────────────────────────────────────────────────────────────

describe('buildArudhaRows() — FORENSIC §13.1', () => {
  const rows = buildArudhaRows()

  it('produces exactly 9 arudha rows', () => {
    expect(rows).toHaveLength(9)
  })

  it('all rows have category=arudha', () => {
    expect(rows.every(r => r.category === 'arudha')).toBe(true)
  })

  // FORENSIC benchmark: Upapada (UL) must be present
  it('FORENSIC AC: Upapada Lagna (UL) present — ARD.UL exists', () => {
    const ul = rows.find(r => r.fact_id === 'ARD.UL')
    expect(ul).toBeDefined()
  })

  it('FORENSIC AC: UL in Gemini H3 (spouse-image significator)', () => {
    const ul = rows.find(r => r.fact_id === 'ARD.UL')!
    const json = ul.value_json as Record<string, unknown>
    expect(json.sign).toBe('Gemini')
    expect(json.house).toBe(3)
  })

  it('FORENSIC: AL (Lagna Arudha) in Capricorn H10', () => {
    const al = rows.find(r => r.fact_id === 'ARD.AL')!
    const json = al.value_json as Record<string, unknown>
    expect(json.sign).toBe('Capricorn')
    expect(json.house).toBe(10)
    expect(al.divisional_chart).toBe('D1')
  })

  it('FORENSIC: A7 (Darapada) in Aquarius H11', () => {
    const a7 = rows.find(r => r.fact_id === 'ARD.A7')!
    const json = a7.value_json as Record<string, unknown>
    expect(json.sign).toBe('Aquarius')
    expect(json.house).toBe(11)
  })

  it('D9 arudha (ARD.AL.D9) has divisional_chart=D9', () => {
    const d9 = rows.find(r => r.fact_id === 'ARD.AL.D9')!
    expect(d9.divisional_chart).toBe('D9')
    const json = d9.value_json as Record<string, unknown>
    expect(json.sign).toBe('Taurus')
  })

  it('D10 arudha (ARD.AL.D10) has divisional_chart=D10', () => {
    const d10 = rows.find(r => r.fact_id === 'ARD.AL.D10')!
    expect(d10.divisional_chart).toBe('D10')
    const json = d10.value_json as Record<string, unknown>
    expect(json.sign).toBe('Sagittarius')
  })

  it('all ARD.* fact_ids present', () => {
    const expected = ['ARD.AL', 'ARD.A2', 'ARD.A6', 'ARD.A7', 'ARD.A10',
      'ARD.A11', 'ARD.UL', 'ARD.AL.D9', 'ARD.AL.D10']
    for (const id of expected) {
      expect(rows.some(r => r.fact_id === id)).toBe(true)
    }
  })
})

// ── B.10 discipline ───────────────────────────────────────────────────────────

describe('B.10 discipline — FORENSIC-grounded values only', () => {
  const rows = buildRows()

  it('all signs are valid zodiac signs', () => {
    const VALID_SIGNS = new Set([
      'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
    ])
    for (const r of rows) {
      const sign = (r.value_json as Record<string, unknown>)?.sign as string
      if (sign) {
        expect(VALID_SIGNS.has(sign), `Invalid sign '${sign}' in ${r.fact_id}`).toBe(true)
      }
    }
  })

  it('no rows have null value_json (all are structured)', () => {
    expect(rows.every(r => r.value_json !== null)).toBe(true)
  })

  it('upagraha rows carry forensic_id field', () => {
    const upgRows = rows.filter(r => r.category === 'upagraha')
    for (const r of upgRows) {
      const json = r.value_json as Record<string, unknown>
      expect(typeof json.forensic_id).toBe('string')
    }
  })
})
