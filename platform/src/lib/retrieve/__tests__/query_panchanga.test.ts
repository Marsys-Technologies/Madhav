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
})

// ── PSHIP-S3H: enrichment field tests (migration 069 — 5 new JSONB columns) ──
describe('query_panchanga tool — enrichment fields (PSHIP-S3H / migration 069)', () => {
  const sampleSpecialYogas = [
    { yoga: 'Sarvartha Siddhi', start_utc: '2026-05-20T01:03:00+00:00', end_utc: '2026-05-20T13:22:00+00:00', strength: 'auspicious', stars: 4 },
    { yoga: 'Guru Pushya', start_utc: '2026-05-20T01:03:00+00:00', end_utc: '2026-05-20T13:22:00+00:00', strength: 'auspicious', stars: 5 },
  ]
  const sampleInauspicious = {
    rahu_kalam: { label: 'rahu_kalam', start_utc: '2026-05-20T04:33:00+00:00', end_utc: '2026-05-20T06:08:00+00:00' },
    yamagandam: { label: 'yamagandam', start_utc: '2026-05-20T01:03:00+00:00', end_utc: '2026-05-20T02:38:00+00:00' },
    gulika_kalam: { label: 'gulika_kalam', start_utc: '2026-05-20T09:18:00+00:00', end_utc: '2026-05-20T10:53:00+00:00' },
  }
  const sampleAuspicious = {
    brahma_muhurta: { label: 'brahma_muhurta', start_utc: '2026-05-19T23:27:00+00:00', end_utc: '2026-05-19T23:51:00+00:00' },
    abhijit: { label: 'abhijit', start_utc: '2026-05-20T06:42:00+00:00', end_utc: '2026-05-20T07:29:00+00:00' },
    amrit_kalam: null,
    varjyam: null,
  }
  const sampleChoghadiya = {
    day: Array.from({ length: 8 }, (_, i) => ({
      label: `choghadiya_${i}`, start_utc: `2026-05-20T0${i}:00:00+00:00`, end_utc: `2026-05-20T0${i + 1}:00:00+00:00`,
    })),
    night: Array.from({ length: 8 }, (_, i) => ({
      label: `choghadiya_night_${i}`, start_utc: `2026-05-20T1${i}:00:00+00:00`, end_utc: `2026-05-20T1${i + 1}:00:00+00:00`,
    })),
  }
  const sampleHora = Array.from({ length: 24 }, (_, i) => ({
    label: `hora_planet_${i}`, start_utc: `2026-05-20T${String(i).padStart(2, '0')}:00:00+00:00`, end_utc: `2026-05-20T${String(i + 1).padStart(2, '0')}:00:00+00:00`,
  }))

  const enrichedRow = {
    date: '2026-05-20',
    sunrise_utc: '2026-05-20 01:03:00',
    sunrise_jd: '2461186.54374',
    sunrise_ist: '06:33:00',
    tithi: 23,
    tithi_name: 'Krishna Ashtami',
    paksha: 'krishna',
    tithi_fraction: '22.12345',
    vara: 'Guruvara',
    vara_lord: 'Jupiter',
    vara_index: 4,
    moon_nakshatra: 'Pushya',
    moon_nakshatra_index: 8,
    moon_nakshatra_pada: 2,
    moon_longitude_deg: '103.45678',
    sun_longitude_deg: '36.54321',
    yoga: 'Shiva',
    yoga_index: 20,
    karana: 'Vanija',
    karana_position_in_month: 44,
    ayanamsha: 'lahiri',
    observer_lat: '20.27021',
    observer_lon: '85.82966',
    observer_alt_m: '45.00',
    ephemeris_version: 'pyswisseph-2.10.03.2+4C-panchanga-v1',
    special_yogas: sampleSpecialYogas,
    inauspicious: sampleInauspicious,
    auspicious: sampleAuspicious,
    choghadiya: sampleChoghadiya,
    hora: sampleHora,
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

  it('returns special_yogas when field requested and column populated', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '2026-05-20', fields: ['special_yogas'] })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.special_yogas).toBeDefined()
    expect(Array.isArray(content.special_yogas)).toBe(true)
    expect(content.special_yogas[0].yoga).toBe('Sarvartha Siddhi')
    expect(content.special_yogas[1].yoga).toBe('Guru Pushya')
  })

  it('returns inauspicious when field requested and column populated', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '2026-05-20', fields: ['inauspicious'] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.inauspicious).toBeDefined()
    expect(content.inauspicious.rahu_kalam).toBeDefined()
    expect(content.inauspicious.rahu_kalam.label).toBe('rahu_kalam')
    expect(content.inauspicious.yamagandam).toBeDefined()
    expect(content.inauspicious.gulika_kalam).toBeDefined()
  })

  it('returns auspicious when field requested and column populated', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '2026-05-20', fields: ['auspicious'] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.auspicious).toBeDefined()
    expect(content.auspicious.brahma_muhurta.label).toBe('brahma_muhurta')
    expect(content.auspicious.abhijit.label).toBe('abhijit')
  })

  it('returns choghadiya with day+night arrays when field requested', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '2026-05-20', fields: ['choghadiya'] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.choghadiya).toBeDefined()
    expect(Array.isArray(content.choghadiya.day)).toBe(true)
    expect(content.choghadiya.day).toHaveLength(8)
    expect(Array.isArray(content.choghadiya.night)).toBe(true)
    expect(content.choghadiya.night).toHaveLength(8)
  })

  it('returns hora with 24 entries when field requested', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { date: '2026-05-20', fields: ['hora'] })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.hora).toBeDefined()
    expect(Array.isArray(content.hora)).toBe(true)
    expect(content.hora).toHaveLength(24)
  })

  it('omits enrichment fields when column is NULL (pre-bootstrap state)', async () => {
    const nullEnrichedRow = { ...enrichedRow, special_yogas: null, inauspicious: null, auspicious: null, choghadiya: null, hora: null }
    mockQuery.mockResolvedValue({ rows: [nullEnrichedRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      date: '2026-05-20',
      fields: ['tithi', 'special_yogas', 'inauspicious', 'choghadiya', 'hora'],
    })

    const content = JSON.parse(bundle.results[0].content)
    // Core fields still present
    expect(content.tithi).toBe(23)
    // Enrichment fields omitted when null (graceful degradation)
    expect(content.special_yogas).toBeUndefined()
    expect(content.inauspicious).toBeUndefined()
    expect(content.choghadiya).toBeUndefined()
    expect(content.hora).toBeUndefined()
  })

  it('returns all enrichment fields when ALL_FIELDS (default) requested', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    // Default params = ALL_FIELDS
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-20' })

    const content = JSON.parse(bundle.results[0].content)
    expect(content.special_yogas).toBeDefined()
    expect(content.inauspicious).toBeDefined()
    expect(content.auspicious).toBeDefined()
    expect(content.choghadiya).toBeDefined()
    expect(content.hora).toBeDefined()
    // Core fields also present
    expect(content.tithi_name).toBe('Krishna Ashtami')
  })

  it('SQL SELECT includes 5 enrichment column names', async () => {
    mockQuery.mockResolvedValue({ rows: [enrichedRow], rowCount: 1 })

    await tool.retrieve(basePlan, { date: '2026-05-20' })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('special_yogas')
    expect(sql).toContain('inauspicious')
    expect(sql).toContain('auspicious')
    expect(sql).toContain('choghadiya')
    expect(sql).toContain('hora')
  })
})
