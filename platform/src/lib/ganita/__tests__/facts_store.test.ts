/**
 * facts_store.test.ts — Unit tests for ganita/facts_store.ts
 *
 * Tests:
 *   1. query_chart_facts returns a fully structured GanitaFactStore
 *   2. groupByCategory correctly partitions rows
 *   3. All domain sections are non-null (metadata, planets, houses, dashas,
 *      strengths, sensitive_points, panchanga, yogas, aspects)
 *   4. coverage_score is 0–1
 *   5. Handles empty DB result gracefully
 *   6. Handles batched category query (categories param)
 *   7. ayanamsha INVARIANT rows are always included
 *
 * [BRAHMA-GA-1-8]
 */

import { describe, it, expect, vi } from 'vitest'
import { query_chart_facts, groupByCategory } from '../facts_store'
import type { DbClient } from '../facts_store'
import type { ChartFactRow } from '../types'

// ─── Fixtures ─────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = 'test-native-chart-001'
const BUILD_ID = 'test-build-001'
const AYANAMSHA = 'lahiri'

/** Minimal valid raw row as returned by Postgres */
function makeRaw(overrides: Partial<{
  id: string
  fact_id: string
  chart_id: string | null
  ayanamsha_id: string | null
  category: string
  divisional_chart: string
  fact_category: string | null
  fact_key: string | null
  fact_subject: string | null
  value_text: string | null
  value_number: string | null
  value_json: unknown
  source_section: string
  build_id: string
  provenance: unknown
  is_stale: boolean
  created_at: string
  engine_version: string | null
  verification_pass_status: string | null
  citation_ref: string | null
  citation_human: string | null
  unit: string | null
}> = {}) {
  return {
    id: 'row-001',
    fact_id: 'MET.BIRTH.DATE',
    chart_id: NATIVE_CHART_ID,
    ayanamsha_id: AYANAMSHA,
    category: 'metadata',
    divisional_chart: 'D1',
    fact_category: null,
    fact_key: null,
    fact_subject: null,
    value_text: '1984-02-05',
    value_number: null,
    value_json: null,
    source_section: '§1.1',
    build_id: BUILD_ID,
    provenance: {
      source_uri: 'gs://madhav-marsys-sources/99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md',
      source_version: '8.0',
      source_canonical_id: 'FORENSIC',
      extracted_at: '2026-05-01T00:00:00Z',
      extraction_method: 'pyjhora_v3',
    },
    is_stale: false,
    created_at: '2026-05-01T00:00:00Z',
    engine_version: 'pyjhora_v3',
    verification_pass_status: null,
    citation_ref: null,
    citation_human: null,
    unit: null,
    ...overrides,
  }
}

/** Build a minimal "native chart" row set covering all required domains */
function buildNativeRows(): object[] {
  return [
    // ── metadata ──
    makeRaw({ fact_id: 'MET.BIRTH.DATE', category: 'metadata', value_text: '1984-02-05', fact_key: 'BIRTH.DATE' }),
    makeRaw({ id: 'r2', fact_id: 'MET.BIRTH.TIME', category: 'metadata', value_text: '10:43:00 IST', fact_key: 'BIRTH.TIME' }),
    makeRaw({ id: 'r3', fact_id: 'MET.BIRTH.PLACE', category: 'metadata', value_text: 'Bhubaneswar, Odisha, India', fact_key: 'BIRTH.PLACE' }),
    makeRaw({ id: 'r4', fact_id: 'MET.LAGNA.SIGN', category: 'metadata', value_text: 'Aries', fact_key: 'LAGNA.SIGN' }),
    makeRaw({ id: 'r5', fact_id: 'MET.AYANAMSHA.NAME', category: 'metadata', value_text: 'Lahiri', fact_key: 'AYANAMSHA.NAME' }),

    // ── planet (SUN) ──
    makeRaw({ id: 'p1', fact_id: 'PLN.SUN.SIGN', category: 'planet', value_text: 'Capricorn', fact_subject: 'SUN' }),
    makeRaw({ id: 'p2', fact_id: 'PLN.SUN.HOUSE_RASHI', category: 'planet', value_number: '10', fact_subject: 'SUN' }),
    makeRaw({ id: 'p3', fact_id: 'PLN.SUN.LON_DMS', category: 'planet', value_text: '21°57′35″', fact_subject: 'SUN' }),
    makeRaw({ id: 'p4', fact_id: 'PLN.SUN.NAK', category: 'planet', value_text: 'Shravana', fact_subject: 'SUN' }),
    makeRaw({ id: 'p5', fact_id: 'PLN.SUN.LON_DEG', category: 'planet', value_number: '291.96', fact_subject: 'SUN' }),

    // ── house ──
    makeRaw({ id: 'h1', fact_id: 'HSE.1.SIGN', category: 'house', value_text: 'Aries' }),
    makeRaw({ id: 'h2', fact_id: 'HSE.7.SIGN', category: 'house', value_text: 'Libra' }),

    // ── divisional ──
    makeRaw({ id: 'd1', fact_id: 'D9.SUN.SIGN', category: 'divisional', divisional_chart: 'D9', value_text: 'Leo', fact_subject: 'SUN' }),

    // ── dasha_vimshottari ──
    makeRaw({
      id: 'dv1',
      fact_id: 'DSH.V.MD.MERCURY',
      category: 'dasha_vimshottari',
      value_text: 'Mercury',
      fact_subject: 'Mercury',
      value_json: { start: '2010-03-14', end: '2027-03-14', duration_days: 6210 },
    }),

    // ── shadbala ──
    makeRaw({ id: 's1', fact_id: 'SBL.SUN.TOTAL', category: 'shadbala', value_number: '7.32', fact_subject: 'Sun', unit: 'rupas' }),

    // ── ashtakavarga ──
    makeRaw({ id: 'a1', fact_id: 'AVG.SAV.ARIES', category: 'ashtakavarga', value_number: '28', fact_subject: 'Aries', unit: 'bindus' }),

    // ── upagraha ──
    makeRaw({ id: 'u1', fact_id: 'UPG.GULIKA', category: 'upagraha', value_text: 'Capricorn', fact_subject: 'Gulika',
      value_json: { house: 10, degree: '15°00′' } }),

    // ── saham ──
    makeRaw({ id: 'sa1', fact_id: 'SAH.PUNYA', category: 'saham', value_text: 'Leo', fact_subject: 'Punya Saham',
      value_json: { house: 5, degree: '12°' } }),

    // ── special_lagna ──
    makeRaw({ id: 'sl1', fact_id: 'LAG.HORA', category: 'special_lagna', value_text: 'Cancer', fact_subject: 'Hora Lagna' }),

    // ── arudha ──
    makeRaw({ id: 'ar1', fact_id: 'ARD.AL', category: 'arudha', value_text: 'Capricorn', fact_subject: 'Arudha Lagna' }),

    // ── karaka ──
    makeRaw({ id: 'kr1', fact_id: 'KRK.ATMA', category: 'karaka', value_text: 'Saturn', fact_subject: 'Atmakaraka' }),

    // ── yoga ──
    makeRaw({ id: 'y1', fact_id: 'YGA.D1.KALPADRUMA', category: 'yoga', value_text: 'Kalpadruma', fact_subject: 'Kalpadruma',
      fact_key: 'rajayoga', value_json: { planets: ['Jupiter', 'Venus'], houses: [9], strength: 'strong', rule: 'BPHS Ch.35' } }),

    // ── aspect ──
    makeRaw({ id: 'asp1', fact_id: 'ASP.SATURN.MOON', category: 'aspect', value_number: '2.5', fact_key: 'full',
      value_json: { strength: 'full', type: 'full' } }),

    // ── panchanga ──
    makeRaw({ id: 'pc1', fact_id: 'PCG.TITHI', category: 'panchanga', value_text: 'Shukla Tritiya', fact_subject: 'tithi' }),

    // ── sade_sati ──
    makeRaw({ id: 'ss1', fact_id: 'TRS.SADE_SATI.C2.P1', category: 'sade_sati', value_text: '1998-01-01',
      value_json: { phase: 1, start: '1998-01-01', end: '2000-01-01' } }),

    // ── varshphal ──
    makeRaw({ id: 'vp1', fact_id: 'VRS.MUNTHA.SIGN', category: 'varshphal', value_text: 'Libra', fact_subject: 'Muntha' }),

    // ── kp ──
    makeRaw({ id: 'kp1', fact_id: 'KP.CUSP.1', category: 'kp', value_text: 'Aries', fact_subject: 'Cusp 1' }),
  ]
}

/** Create a mock DbClient that returns the given rows */
function mockDb(rows: object[]): DbClient {
  return {
    query: vi.fn().mockResolvedValue({ rows }),
  }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('groupByCategory', () => {
  it('partitions rows correctly', () => {
    const rows: ChartFactRow[] = [
      { fact_id: 'A', category: 'planet', divisional_chart: 'D1', value_text: null, value_number: null, value_json: null, source_section: '', build_id: '', provenance: { source_uri: '', source_version: '', source_canonical_id: '', extracted_at: '', extraction_method: '' } },
      { fact_id: 'B', category: 'planet', divisional_chart: 'D1', value_text: null, value_number: null, value_json: null, source_section: '', build_id: '', provenance: { source_uri: '', source_version: '', source_canonical_id: '', extracted_at: '', extraction_method: '' } },
      { fact_id: 'C', category: 'house', divisional_chart: 'D1', value_text: null, value_number: null, value_json: null, source_section: '', build_id: '', provenance: { source_uri: '', source_version: '', source_canonical_id: '', extracted_at: '', extraction_method: '' } },
    ]
    const grouped = groupByCategory(rows)
    expect(grouped['planet']).toHaveLength(2)
    expect(grouped['house']).toHaveLength(1)
    expect(grouped['metadata']).toBeUndefined()
  })

  it('returns empty object for empty input', () => {
    expect(groupByCategory([])).toEqual({})
  })
})

describe('query_chart_facts', () => {
  it('returns a GanitaFactStore with correct chart_id and build_id', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.chart_id).toBe(NATIVE_CHART_ID)
    expect(store.build_id).toBe(BUILD_ID)
    expect(store.ayanamsha_id).toBe(AYANAMSHA)
  })

  it('metadata section is non-null and populated', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.metadata.birth_date).toBe('1984-02-05')
    expect(store.metadata.lagna_sign).toBe('Aries')
  })

  it('planets section is non-empty and contains Sun', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.planets.length).toBeGreaterThan(0)
    const sun = store.planets.find(p => p.planet === 'Sun')
    expect(sun).toBeDefined()
    expect(sun?.sign).toBe('Capricorn')
    expect(sun?.house_rashi).toBe(10)
  })

  it('houses section contains house 1', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.houses.length).toBeGreaterThan(0)
    const h1 = store.houses.find(h => h.house === 1)
    expect(h1?.sign).toBe('Aries')
  })

  it('divisionals section contains D9 data', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.divisionals.length).toBeGreaterThan(0)
    const d9Sun = store.divisionals.find(d => d.varga === 'D9' && d.planet === 'SUN')
    expect(d9Sun?.sign).toBe('Leo')
  })

  it('dashas section contains Mercury MD', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.dashas.length).toBeGreaterThan(0)
    const md = store.dashas.find(d => d.lord === 'Mercury')
    expect(md).toBeDefined()
    expect(md?.system).toBe('vimshottari')
  })

  it('strengths section is non-empty', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.strengths.length).toBeGreaterThan(0)
    const sunShad = store.strengths.find(s => s.planet === 'Sun' && s.system === 'shadbala')
    expect(sunShad?.value).toBeCloseTo(7.32)
  })

  it('sensitive_points section includes Gulika (upagraha)', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.sensitive_points.length).toBeGreaterThan(0)
    const gulika = store.sensitive_points.find(p => p.name === 'Gulika')
    expect(gulika?.sign).toBe('Capricorn')
    expect(gulika?.type).toBe('upagraha')
  })

  it('sensitive_points includes Hora Lagna (special_lagna)', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    const hl = store.sensitive_points.find(p => p.name === 'Hora Lagna')
    expect(hl?.type).toBe('special_lagna')
  })

  it('sensitive_points includes Punya Saham (saham)', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    const ps = store.sensitive_points.find(p => p.name === 'Punya Saham')
    expect(ps?.type).toBe('saham')
  })

  it('sensitive_points includes Arudha Lagna (arudha)', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    const al = store.sensitive_points.find(p => p.name === 'Arudha Lagna')
    expect(al?.type).toBe('arudha')
  })

  it('sensitive_points includes Atmakaraka (karaka)', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    const atma = store.sensitive_points.find(p => p.name === 'Atmakaraka')
    expect(atma?.type).toBe('karaka')
  })

  it('panchanga section includes tithi', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.panchanga.length).toBeGreaterThan(0)
    const tithi = store.panchanga.find(p => p.component === 'tithi')
    expect(tithi?.value).toBe('Shukla Tritiya')
  })

  it('yogas section includes Kalpadruma', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.yogas.length).toBeGreaterThan(0)
    const yd = store.yogas.find(y => y.yoga_name === 'Kalpadruma')
    expect(yd?.planets_involved).toContain('Jupiter')
  })

  it('aspects section includes Saturn-Moon aspect', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.aspects.length).toBeGreaterThan(0)
    const asp = store.aspects.find(a => a.aspector === 'SATURN' && a.aspected_body === 'MOON')
    expect(asp?.aspect_type).toBe('full')
  })

  it('sade_sati section is non-empty', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.sade_sati.length).toBeGreaterThan(0)
  })

  it('varshphal section is non-empty', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.varshphal.length).toBeGreaterThan(0)
  })

  it('coverage_score is between 0 and 1', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.coverage_score).toBeGreaterThan(0)
    expect(store.coverage_score).toBeLessThanOrEqual(1)
  })

  it('domains_present is non-empty', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.domains_present.length).toBeGreaterThan(0)
    // At minimum metadata, planet, house, dasha_vimshottari should be present
    expect(store.domains_present).toContain('metadata')
    expect(store.domains_present).toContain('planet')
  })

  it('handles empty DB result gracefully', async () => {
    const db = mockDb([])
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    // chart_id falls back to the input when no rows — that's fine
    expect(store.chart_id === null || store.chart_id === NATIVE_CHART_ID).toBe(true)
    expect(store.planets).toEqual([])
    expect(store.houses).toEqual([])
    expect(store.dashas).toEqual([])
    expect(store.coverage_score).toBe(0)
    expect(store.domains_present).toEqual([])
  })

  it('handles batched categories query', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts(
      { chart_id: NATIVE_CHART_ID, categories: ['metadata', 'planet'] },
      db,
    )
    // Should still build the store correctly
    expect(store.metadata.birth_date).toBe('1984-02-05')
    // Verify the SQL called with categories param (mock was called)
    expect((db.query as ReturnType<typeof vi.fn>).mock.calls[0][0]).toContain('ANY(')
  })

  it('INVARIANT ayanamsha rows included regardless of ayanamsha_id filter', async () => {
    const invariantRow = makeRaw({
      id: 'inv1',
      fact_id: 'INVARIANT.PUNYA',
      category: 'saham',
      ayanamsha_id: 'INVARIANT',
      value_text: 'Leo',
      fact_subject: 'Punya Saham',
    })
    const db = mockDb([invariantRow])
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID, ayanamsha_id: 'lahiri' }, db)
    // The SQL should include INVARIANT rows — verify via mock call
    const sql: string = (db.query as ReturnType<typeof vi.fn>).mock.calls[0][0]
    expect(sql).toContain("'INVARIANT'")
  })

  it('rows_by_category index is populated', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    expect(store.rows_by_category['metadata']).toBeDefined()
    expect(store.rows_by_category['metadata'].length).toBeGreaterThan(0)
    expect(store.rows_by_category['planet']).toBeDefined()
  })

  it('value_number is parsed as number not string', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    const sun = store.planets.find(p => p.planet === 'Sun')
    expect(typeof sun?.degree_decimal).toBe('number')
    expect(sun?.degree_decimal).toBeCloseTo(291.96)
  })

  it('retrograde defaults to false when absent', async () => {
    const db = mockDb(buildNativeRows())
    const store = await query_chart_facts({ chart_id: NATIVE_CHART_ID }, db)
    const sun = store.planets.find(p => p.planet === 'Sun')
    // Sun has no RETROGRADE row in the fixture → defaults to false
    expect(sun?.retrograde).toBe(false)
  })
})
