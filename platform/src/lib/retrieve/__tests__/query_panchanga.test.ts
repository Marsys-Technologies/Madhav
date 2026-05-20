import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool } from '../query_panchanga'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000088',
  query_text: 'panchanga test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_panchanga'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const panchangaRow = {
  date: '2026-05-19',
  sunrise_utc: '2026-05-19 01:03:00',
  sunrise_jd: '2461185.54374',
  sunrise_ist: '06:33:00',
  tithi: 22,
  tithi_name: 'Krishna Saptami',
  paksha: 'krishna',
  tithi_fraction: '21.87432',
  vara: 'Mangalavara',
  vara_lord: 'Mars',
  vara_index: 2,
  moon_nakshatra: 'Shatabhisha',
  moon_nakshatra_index: 23,
  moon_nakshatra_pada: 3,
  moon_longitude_deg: '314.27621',
  sun_longitude_deg: '35.12345',
  yoga: 'Vriddhi',
  yoga_index: 11,
  karana: 'Garaja',
  karana_position_in_month: 42,
  ayanamsha: 'lahiri',
  observer_lat: '20.27021',
  observer_lon: '85.82966',
  observer_alt_m: '45.00',
  ephemeris_version: 'pyswisseph-2.10.03.2+4C-panchanga-v1',
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(getStorageClient).mockReturnValue({
    query: mockQuery,
    transaction: vi.fn(),
    readObject: vi.fn(),
    writeObject: vi.fn(),
    objectExists: vi.fn(),
    readFile: vi.fn(),
    fileExists: vi.fn(),
    listFiles: vi.fn(),
  })
})

describe('query_panchanga tool', () => {
  it('default params: SQL uses CURRENT_DATE with no extra filters', async () => {
    mockQuery.mockResolvedValue({ rows: [panchangaRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.tithi_name).toBe('Krishna Saptami')

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('CURRENT_DATE')
    expect(sql).not.toContain('tithi =')
    expect(sql).not.toContain('moon_nakshatra =')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams).toHaveLength(0)
  })

  it('filters by tithi=15 (Purnima): SQL contains tithi = $N', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, {
      start_date: '2026-05-01',
      end_date: '2026-07-31',
      tithi: 15,
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('date >= $1::date')
    expect(sql).toContain('date <= $2::date')
    expect(sql).toContain('tithi = $3')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('2026-05-01')
    expect(sqlParams[1]).toBe('2026-07-31')
    expect(sqlParams[2]).toBe(15)
  })

  it('filters by date range + paksha: both clauses present', async () => {
    mockQuery.mockResolvedValue({ rows: [panchangaRow], rowCount: 1 })

    await tool.retrieve(basePlan, {
      start_date: '2026-01-01',
      end_date: '2026-12-31',
      paksha: 'shukla',
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('paksha = $3')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[2]).toBe('shukla')
  })

  it('filters by moon_nakshatra: SQL contains moon_nakshatra = $N', async () => {
    mockQuery.mockResolvedValue({ rows: [panchangaRow], rowCount: 1 })

    await tool.retrieve(basePlan, {
      start_date: '2026-01-01',
      end_date: '2026-12-31',
      moon_nakshatra: 'Rohini',
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('moon_nakshatra = $3')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[2]).toBe('Rohini')
  })

  it('returns diagnostic row when no rows match (confidence=0, note field)', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, { date: '1800-01-01' })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.note).toContain('panchanga_daily empty or out-of-range')
    expect(bundle.results[0].confidence).toBe(0)
    expect(bundle.results[0].significance).toBe(0)
  })

  it('returns valid ToolBundle shape with tool_name, version, sha256 hash', async () => {
    mockQuery.mockResolvedValue({ rows: [panchangaRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('query_panchanga')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('PANCHANGA_DAILY')
    expect(bundle.results[0].confidence).toBe(1.0)
  })

  it('enrichment fields present: special_yogas + inauspicious parsed from JSON text', async () => {
    const enrichedRow = {
      ...panchangaRow,
      special_yogas: JSON.stringify([{ name: 'Guru Pushya', rating: 'excellent', start_ts: '2026-05-20T06:01:00', end_ts: '2026-05-20T18:30:00' }]),
      choghadiya: null,
      hora: null,
      inauspicious: JSON.stringify({ rahu: { start: '09:00', end: '10:30' }, yama: { start: '12:00', end: '13:30' }, gulika: { start: '07:30', end: '09:00' }, dur_muhurta: [] }),
      auspicious: null,
    }
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      fields: ['special_yogas', 'inauspicious'],
    })

    const content = JSON.parse(bundle.results[0].content)
    expect(Array.isArray(content.special_yogas)).toBe(true)
    expect(content.special_yogas[0].name).toBe('Guru Pushya')
    expect(content.inauspicious.rahu.start).toBe('09:00')
    // choghadiya/hora/auspicious were not requested — must be absent
    expect(content.choghadiya).toBeUndefined()
    expect(content.hora).toBeUndefined()
    expect(content.auspicious).toBeUndefined()
    // 5-limb fields were not requested either
    expect(content.tithi).toBeUndefined()
  })

  it('enrichment fields absent (pre-rebuild rows): fields return null gracefully', async () => {
    const preRebuildRow = {
      ...panchangaRow,
      special_yogas: null,
      choghadiya: null,
      hora: null,
      inauspicious: null,
      auspicious: null,
    }
    mockQuery.mockResolvedValue({ rows: [preRebuildRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      fields: ['special_yogas', 'choghadiya', 'hora', 'inauspicious', 'auspicious'],
    })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.special_yogas).toBeNull()
    expect(content.choghadiya).toBeNull()
    expect(content.hora).toBeNull()
    expect(content.inauspicious).toBeNull()
    expect(content.auspicious).toBeNull()
    // 5-limb fields absent (not requested)
    expect(content.tithi).toBeUndefined()
    // result confidence is still 1.0 — null enrichment is not a tool error
    expect(bundle.results[0].confidence).toBe(1.0)
  })
})
