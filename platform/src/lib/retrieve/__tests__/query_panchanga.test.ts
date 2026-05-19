/**
 * __tests__/query_panchanga.test.ts
 *
 * Unit tests for query_panchanga RetrievalTool with mocked sidecar responses.
 * No live sidecar calls — all fetch calls are mocked.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock the sidecar URL to be set so callSidecar doesn't abort on missing env
process.env['PYTHON_SIDECAR_URL'] = 'http://localhost:8001'

import { tool, RetrievalToolError } from '../query_panchanga'
import type { QueryPlan } from '../types'

// Mock Panchang response from the sidecar (single-day)
const MOCK_PANCHANG_DICT = {
  date: '2026-05-19',
  lat: 20.27,
  lon: 85.84,
  tz_offset_minutes: 330,
  sunrise_utc: '2026-05-19T00:12:34Z',
  sunset_utc: '2026-05-19T13:01:22Z',
  moonrise_utc: '2026-05-19T04:30:00Z',
  moonset_utc: '2026-05-19T17:45:00Z',
  tithi: { id: 12, name: 'Shukla Dvadashi', end_utc: '2026-05-19T18:00:00Z' },
  nakshatra: { id: 17, name: 'Anuradha', end_utc: '2026-05-19T22:00:00Z' },
  yoga: { id: 5, name: 'Shobhana', end_utc: '2026-05-20T01:00:00Z' },
  karana_first: { id: 4, name: 'Bava', end_utc: '2026-05-19T10:00:00Z' },
  karana_second: { id: 5, name: 'Balava', end_utc: '2026-05-19T18:00:00Z' },
  vara: { id: 3, name: 'Mangalavara', end_utc: '2026-05-20T00:12:34Z' },
  paksha: 'shukla',
  inauspicious: [
    { label: 'rahu_kalam', start_utc: '2026-05-19T09:10:00Z', end_utc: '2026-05-19T10:38:00Z' },
  ],
  auspicious: [
    { label: 'brahma_muhurta', start_utc: '2026-05-18T22:44:00Z', end_utc: '2026-05-19T00:12:00Z' },
  ],
  choghadiya: {
    day: [{ label: 'Kaal', start_utc: '2026-05-19T00:12:00Z', end_utc: '2026-05-19T01:53:00Z' }],
    night: [{ label: 'Labh', start_utc: '2026-05-19T13:01:00Z', end_utc: '2026-05-19T14:49:00Z' }],
  },
  hora: [
    { label: 'hora_mars', start_utc: '2026-05-19T00:12:00Z', end_utc: '2026-05-19T01:12:00Z' },
  ],
  special_yogas: [
    { yoga: 'amrit_siddhi', start_utc: '2026-05-19T00:12:34Z', end_utc: '2026-05-19T22:00:00Z', strength: 'high', stars: 5 },
  ],
  planets: {
    sun: { name: 'Sun', longitude_sidereal: 34.5, sign_id: 1, sign_name: 'Mesha', nakshatra_id: 2, nakshatra_name: 'Bharani', nakshatra_pada: 2, retrograde: false, combust: false },
    moon: { name: 'Moon', longitude_sidereal: 220.3, sign_id: 8, sign_name: 'Vrischika', nakshatra_id: 17, nakshatra_name: 'Anuradha', nakshatra_pada: 1, retrograde: false, combust: false },
    mars: { name: 'Mars', longitude_sidereal: 80.0, sign_id: 3, sign_name: 'Mithuna', nakshatra_id: 6, nakshatra_name: 'Ardra', nakshatra_pada: 3, retrograde: true, combust: false },
    mercury: { name: 'Mercury', longitude_sidereal: 18.0, sign_id: 1, sign_name: 'Mesha', nakshatra_id: 1, nakshatra_name: 'Ashwini', nakshatra_pada: 4, retrograde: false, combust: true },
    jupiter: { name: 'Jupiter', longitude_sidereal: 82.0, sign_id: 3, sign_name: 'Mithuna', nakshatra_id: 7, nakshatra_name: 'Punarvasu', nakshatra_pada: 1, retrograde: false, combust: false },
    venus: { name: 'Venus', longitude_sidereal: 62.0, sign_id: 3, sign_name: 'Mithuna', nakshatra_id: 6, nakshatra_name: 'Ardra', nakshatra_pada: 1, retrograde: false, combust: false },
    saturn: { name: 'Saturn', longitude_sidereal: 320.0, sign_id: 11, sign_name: 'Kumbha', nakshatra_id: 24, nakshatra_name: 'Shatabhisha', nakshatra_pada: 4, retrograde: true, combust: false },
    rahu: { name: 'Rahu', longitude_sidereal: 350.0, sign_id: 12, sign_name: 'Meena', nakshatra_id: 27, nakshatra_name: 'Revati', nakshatra_pada: 2, retrograde: true, combust: false },
    ketu: { name: 'Ketu', longitude_sidereal: 170.0, sign_id: 6, sign_name: 'Kanya', nakshatra_id: 13, nakshatra_name: 'Hasta', nakshatra_pada: 2, retrograde: true, combust: false },
  },
  computation_version: '1.0.0-S2',
  ephemeris_version: '2.10.03',
}

const MOCK_SIDECAR_RESPONSE = {
  ok: true,
  panchang: MOCK_PANCHANG_DICT,
  cache_hit: false,
}

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000099',
  query_text: "What is today's tithi?",
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: ['query_panchanga'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      if (url.includes('/api/compute/panchanga/range')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              ok: true,
              panchangs: [MOCK_PANCHANG_DICT],
              count: 1,
            }),
        })
      }
      if (url.includes('/api/compute/panchanga')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(MOCK_SIDECAR_RESPONSE),
        })
      }
      return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
    }),
  )
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('query_panchanga tool identity', () => {
  it('has correct name and version', () => {
    expect(tool.name).toBe('query_panchanga')
    expect(tool.version).toBe('1.0.0')
  })

  it('has a non-empty description', () => {
    expect(tool.description).toBeTruthy()
    expect((tool.description ?? '').length).toBeGreaterThan(50)
  })

  it('description mentions key Panchang terms', () => {
    const desc = tool.description ?? ''
    expect(desc).toContain('tithi')
    expect(desc).toContain('nakshatra')
    expect(desc).toContain('Rahu Kalam')
    expect(desc).toContain('auspicious')
  })
})

describe('retrieve() — single-day query', () => {
  it('returns a ToolBundle with non-empty results', async () => {
    const bundle = await tool.retrieve(basePlan, {
      date: '2026-05-19',
      lat: 20.27,
      lon: 85.84,
      tz_offset_minutes: 330,
    })
    expect(bundle).toBeDefined()
    expect(bundle.tool_name).toBe('query_panchanga')
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('returns results including tithi, nakshatra, vara (five_angas section)', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-19' })
    const angaResult = bundle.results.find(r => r.content.includes('five_angas'))
    expect(angaResult).toBeDefined()
    const parsed = JSON.parse(angaResult!.content)
    expect(parsed.tithi).toBeDefined()
    expect(parsed.nakshatra).toBeDefined()
    expect(parsed.vara).toBeDefined()
  })

  it('returns results including special_yogas section', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-19' })
    const yogaResult = bundle.results.find(r => r.content.includes('special_yogas'))
    expect(yogaResult).toBeDefined()
    const parsed = JSON.parse(yogaResult!.content)
    expect(Array.isArray(parsed.special_yogas)).toBe(true)
  })

  it('includes diagnostics: latency_ms is finite', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-19' })
    expect(typeof bundle.latency_ms).toBe('number')
    expect(isFinite(bundle.latency_ms)).toBe(true)
    expect(bundle.latency_ms).toBeGreaterThanOrEqual(0)
  })

  it('result_hash starts with sha256:', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-19' })
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
  })

  it('schema_version is 1.0', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-19' })
    expect(bundle.schema_version).toBe('1.0')
  })

  it('uses default location (Bhubaneswar) when lat/lon not provided', async () => {
    const bundle = await tool.retrieve(basePlan, { date: '2026-05-19' })
    const params = bundle.invocation_params as Record<string, unknown>
    expect(params['lat']).toBe(20.27)
    expect(params['lon']).toBe(85.84)
  })

  it('uses today as default date when date not provided', async () => {
    const bundle = await tool.retrieve(basePlan, {})
    const today = new Date().toISOString().slice(0, 10)
    const params = bundle.invocation_params as Record<string, unknown>
    expect(params['date']).toBe(today)
  })

  it('accepts chart_id param without error (4C-5 scope; ignored this session)', async () => {
    const bundle = await tool.retrieve(basePlan, {
      date: '2026-05-19',
      chart_id: 'abhisek_mohanty',
    })
    expect(bundle).toBeDefined()
    const params = bundle.invocation_params as Record<string, unknown>
    expect(params['chart_id']).toBe('abhisek_mohanty')
  })
})

describe('retrieve() — range query', () => {
  it('calls the range endpoint when range param is provided', async () => {
    const bundle = await tool.retrieve(basePlan, {
      range: { from: '2026-05-19', to: '2026-05-19' },
    })
    expect(bundle).toBeDefined()
    const calls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls
    expect(calls.some((c: unknown[]) => String(c[0]).includes('panchanga/range'))).toBe(true)
  })

  it('returns a results array with panchang_range section', async () => {
    const bundle = await tool.retrieve(basePlan, {
      range: { from: '2026-05-19', to: '2026-05-19' },
    })
    const rangeResult = bundle.results.find(r => r.content.includes('panchang_range'))
    expect(rangeResult).toBeDefined()
  })
})

describe('retrieve() — error handling', () => {
  it('throws RetrievalToolError on sidecar HTTP error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 503,
          json: () => Promise.resolve({ detail: 'Service unavailable' }),
        }),
      ),
    )
    await expect(
      tool.retrieve(basePlan, { date: '2026-05-19' }),
    ).rejects.toThrow(RetrievalToolError)
  })

  it('throws RetrievalToolError when PYTHON_SIDECAR_URL is not set', async () => {
    const origUrl = process.env['PYTHON_SIDECAR_URL']
    delete process.env['PYTHON_SIDECAR_URL']
    try {
      await expect(
        tool.retrieve(basePlan, { date: '2026-05-19' }),
      ).rejects.toThrow(RetrievalToolError)
    } finally {
      process.env['PYTHON_SIDECAR_URL'] = origUrl
    }
  })
})
