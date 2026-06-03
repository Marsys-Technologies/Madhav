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
  buildChartSensitivePointRows,
} from '../../scripts/bootstrap/bootstrap_chart_facts_sensitive_points'

// ── Aggregate row tests ───────────────────────────────────────────────────────

describe('buildRows() — aggregate', () => {
  const rows = buildRows()

  // 9 upagrahas + 9 special_lagnas + 36 sahams + 15 arudhas (AL+A2-A12+UL+A12+D9+D10)
  it('produces exactly 69 rows total (9+9+36+15)', () => {
    expect(rows).toHaveLength(69)
  })

  it('all fact_ids are unique (no duplicates)', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(69)
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

  it('category distribution: 9+9+36+15', () => {
    const byCat: Record<string, number> = {}
    for (const r of rows) {
      byCat[r.category] = (byCat[r.category] ?? 0) + 1
    }
    expect(byCat['upagraha']).toBe(9)
    expect(byCat['special_lagna']).toBe(9)
    expect(byCat['saham']).toBe(36)
    expect(byCat['arudha']).toBe(15)
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

describe('buildArudhaRows() — FORENSIC §13.1 + §13.2', () => {
  const rows = buildArudhaRows()

  // 15 = AL(A1), A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, UL, A12, AL.D9, AL.D10
  it('produces exactly 15 arudha rows (full A1-A12 + UL + A12 + D9 + D10)', () => {
    expect(rows).toHaveLength(15)
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

  it('all ARD.* fact_ids present — complete A1-A12 + UL + divisionals', () => {
    const expected = [
      'ARD.AL', 'ARD.A2', 'ARD.A3', 'ARD.A4', 'ARD.A5',
      'ARD.A6', 'ARD.A7', 'ARD.A8', 'ARD.A9', 'ARD.A10',
      'ARD.A11', 'ARD.UL', 'ARD.A12', 'ARD.AL.D9', 'ARD.AL.D10',
    ]
    for (const id of expected) {
      expect(rows.some(r => r.fact_id === id), `Missing arudha ${id}`).toBe(true)
    }
  })

  it('FORENSIC §13.2: A3 in Leo H5', () => {
    const a3 = rows.find(r => r.fact_id === 'ARD.A3')!
    const json = a3.value_json as Record<string, unknown>
    expect(json.sign).toBe('Leo')
    expect(json.house).toBe(5)
  })

  it('FORENSIC §13.2: A8 in Virgo H6 (Darapada alt)', () => {
    const a8 = rows.find(r => r.fact_id === 'ARD.A8')!
    const json = a8.value_json as Record<string, unknown>
    expect(json.sign).toBe('Virgo')
    expect(json.house).toBe(6)
  })

  it('FORENSIC §13.2: A5 in Gemini H3', () => {
    const a5 = rows.find(r => r.fact_id === 'ARD.A5')!
    const json = a5.value_json as Record<string, unknown>
    expect(json.sign).toBe('Gemini')
    expect(json.house).toBe(3)
  })
})

// ── Gate-1: chart_sensitive_points rows ──────────────────────────────────────

describe('buildChartSensitivePointRows() — Gate-1 compliance', () => {
  const rows = buildChartSensitivePointRows()

  it('produces rows (non-empty)', () => {
    expect(rows.length).toBeGreaterThan(0)
  })

  it('all rows have chart_id = FORENSIC native UUID', () => {
    expect(rows.every(r => r.chart_id === '362f9f17-95a5-490b-a5a7-027d3e0efda0')).toBe(true)
  })

  it('all rows have non-null source_citation (Gate-1 check)', () => {
    for (const r of rows) {
      expect(r.source_citation, `source_citation null in ${r.fact_id}`).toBeTruthy()
    }
  })

  it('all fact_ids are unique (no duplicates in chart_sensitive_points)', () => {
    const ids = rows.map(r => r.fact_id)
    expect(new Set(ids).size).toBe(rows.length)
  })

  it('Gate-1: Gulika present with non-null longitude', () => {
    const gulika = rows.find(r => r.fact_id === 'UPG.GULIKA')
    expect(gulika).toBeDefined()
    expect(gulika!.longitude).not.toBeNull()
    expect(gulika!.longitude).toContain('Gemini')
    expect(gulika!.sign).toBe('Gemini')
  })

  it('Gate-1: Mandi present with non-null longitude', () => {
    const mandi = rows.find(r => r.fact_id === 'UPG.MANDI')
    expect(mandi).toBeDefined()
    expect(mandi!.longitude).not.toBeNull()
    expect(mandi!.sign).toBe('Cancer')
  })

  it('Gate-1: 7 core upagrahas present (Gulika, Mandi, Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu)', () => {
    const required = ['UPG.GULIKA', 'UPG.MANDI', 'UPG.DHUMA', 'UPG.VYATIPATA', 'UPG.PARIVESHA', 'UPG.INDRACHAPA', 'UPG.UPAKETU']
    for (const id of required) {
      expect(rows.some(r => r.fact_id === id), `Missing Gate-1 upagraha ${id}`).toBe(true)
    }
  })

  it('Gate-1: Hora Lagna present (special_lagna)', () => {
    const hora = rows.find(r => r.fact_id === 'LAG.HORA')
    expect(hora).toBeDefined()
    expect(hora!.sign).toBe('Gemini')
    expect(hora!.house).toBe(3)
    expect(hora!.source_citation).toBeTruthy()
  })

  it('Gate-1: Ghati Lagna present (special_lagna)', () => {
    const ghati = rows.find(r => r.fact_id === 'LAG.GHATI')
    expect(ghati).toBeDefined()
    expect(ghati!.sign).toBe('Sagittarius')
    expect(ghati!.source_citation).toBeTruthy()
  })

  it('Gate-1: Bhava Lagna present (special_lagna)', () => {
    const bhava = rows.find(r => r.fact_id === 'LAG.BHAVA')
    expect(bhava).toBeDefined()
    expect(bhava!.sign).toBe('Pisces')
    expect(bhava!.source_citation).toBeTruthy()
  })

  it('Gate-1: Upapada (UL) present — ARD.UL', () => {
    const ul = rows.find(r => r.fact_id === 'ARD.UL')
    expect(ul).toBeDefined()
    expect(ul!.sign).toBe('Gemini')
    expect(ul!.source_citation).toBeTruthy()
  })

  it('Gate-1: Darapada (A7) present — ARD.A7', () => {
    const a7 = rows.find(r => r.fact_id === 'ARD.A7')
    expect(a7).toBeDefined()
    expect(a7!.sign).toBe('Aquarius')
    expect(a7!.source_citation).toBeTruthy()
  })

  it('Gate-1: Darapada alt (A8) present — ARD.A8', () => {
    const a8 = rows.find(r => r.fact_id === 'ARD.A8')
    expect(a8).toBeDefined()
    expect(a8!.sign).toBe('Virgo')
    expect(a8!.source_citation).toBeTruthy()
  })

  it('Gate-1: complete A1-A12 arudha coverage', () => {
    const requiredArudhas = [
      'ARD.AL', 'ARD.A2', 'ARD.A3', 'ARD.A4', 'ARD.A5',
      'ARD.A6', 'ARD.A7', 'ARD.A8', 'ARD.A9', 'ARD.A10',
      'ARD.A11', 'ARD.UL', 'ARD.A12',
    ]
    for (const id of requiredArudhas) {
      expect(rows.some(r => r.fact_id === id), `Missing Gate-1 arudha ${id}`).toBe(true)
    }
  })

  it('all ayanamsha_ids are INVARIANT', () => {
    expect(rows.every(r => r.ayanamsha_id === 'INVARIANT')).toBe(true)
  })

  it('all source_citations reference FORENSIC_v8_0', () => {
    for (const r of rows) {
      expect(r.source_citation, `source_citation in ${r.fact_id} must reference FORENSIC_v8_0`).toContain('FORENSIC_v8_0')
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
