/**
 * INF7-S1: bundle_composer unit tests
 * [BUILD-ORCH-J-02]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
vi.mock('server-only', () => ({}))

import { query } from '@/lib/db/client'
import { compose_chart_bundle } from '../bundle_composer'

const mockQuery = query as ReturnType<typeof vi.fn>

const CHART_ID = 'aaaaaaaa-0000-0000-0000-000000000001'
const AYANAMSHAS = ['lahiri', 'true_chitra']

function makeOldPlanetRow(planet: string, sign: string, house: number) {
  return {
    category: 'planet',
    value_text: null,
    value_number: null,
    value_json: { planet, sign, house, longitude: 42.5, nakshatra: 'Rohini', pada: 2, retro: false, dignity: 'own' },
  }
}

function makeOldHouseRow(house: number, sign: string) {
  return {
    category: 'house',
    value_text: null,
    value_number: null,
    value_json: { house, sign, cusp_deg: 12.3, lord: 'Moon' },
  }
}

function makeOldDashaRow(level: string, lord: string, start: string, end: string) {
  return {
    category: 'dasha_vimshottari',
    value_text: null,
    value_number: null,
    value_json: { level, lord, start_date: start, end_date: end },
  }
}

function makeOldYogaRow(yoga_name: string, strength: number) {
  return {
    category: 'yoga',
    value_text: null,
    value_number: null,
    value_json: { yoga_name, status: 'active', strength, planets: 'Sun Moon' },
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  // Default: all queries return empty
  mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
})

describe('compose_chart_bundle', () => {
  it('returns bundle with correct chart_id and requested ayanamshas', async () => {
    const bundle = await compose_chart_bundle(CHART_ID, AYANAMSHAS)
    expect(bundle.chart_id).toBe(CHART_ID)
    expect(bundle.ayanamshas_requested).toEqual(AYANAMSHAS)
    expect(bundle.generated_at).toBeTruthy()
  })

  it('falls back to all 5 canonical when empty ayanamshas array passed', async () => {
    const bundle = await compose_chart_bundle(CHART_ID, [])
    expect(bundle.ayanamshas_requested).toHaveLength(5)
  })

  it('filters unknown ayanamshas from input', async () => {
    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri', 'unknown_aya'])
    expect(bundle.ayanamshas_requested).toEqual(['lahiri'])
  })

  it('populates planet snapshot from old model rows', async () => {
    // old model query (1st call), new model query (2nd), panchanga (3rd), cross-aya (4th)
    mockQuery
      .mockResolvedValueOnce({
        rows: [makeOldPlanetRow('Sun', 'Capricorn', 12), makeOldPlanetRow('Moon', 'Pisces', 2)],
        rowCount: 2,
      })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    const sun = bundle.ayanamsha_slices[0]?.planets.find((p) => p.planet === 'Sun')
    expect(sun).toBeDefined()
    expect(sun?.sign).toBe('Capricorn')
    expect(sun?.house).toBe(12)
    expect(sun?.nakshatra).toBe('Rohini')
    expect(sun?.pada).toBe(2)
    expect(sun?.retro).toBe(false)
    expect(sun?.dignity).toBe('own')
  })

  it('populates house cusps from old model rows', async () => {
    mockQuery
      .mockResolvedValueOnce({
        rows: [makeOldHouseRow(1, 'Aries'), makeOldHouseRow(7, 'Libra')],
        rowCount: 2,
      })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    const h1 = bundle.ayanamsha_slices[0]?.houses.find((h) => h.house === 1)
    expect(h1).toBeDefined()
    expect(h1?.sign).toBe('Aries')
    expect(h1?.lord).toBe('Moon')
  })

  it('extracts current dasha chain from old model', async () => {
    const today = new Date().toISOString().split('T')[0]!
    const past = '2020-01-01'
    const future = '2030-01-01'

    mockQuery
      .mockResolvedValueOnce({
        rows: [makeOldDashaRow('maha', 'Mercury', past, future)],
        rowCount: 1,
      })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    const dasha = bundle.ayanamsha_slices[0]?.dasha_chain[0]
    expect(dasha?.lord).toBe('Mercury')
    expect(dasha?.level).toBe('maha')
  })

  it('excludes dasha rows where today is outside date range', async () => {
    mockQuery
      .mockResolvedValueOnce({
        rows: [makeOldDashaRow('maha', 'Saturn', '2010-01-01', '2015-01-01')],
        rowCount: 1,
      })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.ayanamsha_slices[0]?.dasha_chain).toHaveLength(0)
  })

  it('extracts active yogas sorted by strength', async () => {
    mockQuery
      .mockResolvedValueOnce({
        rows: [makeOldYogaRow('Gajakesari', 0.9), makeOldYogaRow('Raj Yoga', 0.7)],
        rowCount: 2,
      })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.active_yogas[0]?.yoga_name).toBe('Gajakesari')
    expect(bundle.active_yogas[0]?.strength).toBe(0.9)
  })

  it('caps active_yogas at 20', async () => {
    const yogaRows = Array.from({ length: 30 }, (_, i) =>
      makeOldYogaRow(`Yoga${i}`, 0.5 - i * 0.01),
    )
    mockQuery
      .mockResolvedValueOnce({ rows: yogaRows, rowCount: 30 })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.active_yogas.length).toBeLessThanOrEqual(20)
  })

  it('populates birth_panchanga from new model panchanga rows', async () => {
    const panchangaRows = [
      { fact_category: 'panchanga_tithi', fact_subject: 'TITHI', fact_key: 'tithi_name', ayanamsha_id: 'INVARIANT', fact_value_text: 'Shukla Tritiya', fact_value_num: null },
      { fact_category: 'panchanga_vara', fact_subject: 'VARA', fact_key: 'vara_name', ayanamsha_id: 'INVARIANT', fact_value_text: 'Ravivara', fact_value_num: null },
      { fact_category: 'panchanga_nakshatra', fact_subject: 'NAKSHATRA', fact_key: 'moon_nakshatra', ayanamsha_id: 'INVARIANT', fact_value_text: 'Purva Bhadrapada', fact_value_num: null },
    ]
    // 1st call (old model) empty, 2nd (new model) empty, 3rd (panchanga) has rows
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: panchangaRows, rowCount: 3 })
      .mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.birth_panchanga.tithi).toBe('Shukla Tritiya')
    expect(bundle.birth_panchanga.vara).toBe('Ravivara')
    expect(bundle.birth_panchanga.moon_nakshatra).toBe('Purva Bhadrapada')
  })

  it('populates cross_ayanamsha from chart_ayanamsha_reports', async () => {
    const crossRows = [{
      ayanamsha_id_1: 'lahiri',
      ayanamsha_id_2: 'raman',
      divergence_score: 0.23,
      max_position_delta_deg: 1.5,
    }]
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: crossRows, rowCount: 1 })

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.cross_ayanamsha[0]?.ayanamsha_1).toBe('lahiri')
    expect(bundle.cross_ayanamsha[0]?.divergence_score).toBe(0.23)
  })

  it('handles chart_ayanamsha_reports table absence gracefully', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockResolvedValueOnce({ rows: [], rowCount: 0 })
      .mockRejectedValueOnce(new Error('relation "chart_ayanamsha_reports" does not exist'))

    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.cross_ayanamsha).toEqual([])
  })

  it('includes token_estimate > 0', async () => {
    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.token_estimate).toBeGreaterThan(0)
  })

  it('returns ayanamshas_found empty when no data in DB', async () => {
    const bundle = await compose_chart_bundle(CHART_ID, ['lahiri'])
    expect(bundle.ayanamshas_found).toEqual([])
  })
})
