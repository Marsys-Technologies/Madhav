import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

// Mock global fetch for sidecar calls
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { getStorageClient } from '@/lib/storage'
import { tool } from '../query_transit_event'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000099',
  query_text: 'transit event test',
  query_class: 'factual',
  domains: [],
  forward_looking: true,
  audience_tier: 'super_admin',
  tools_authorized: ['query_transit_event'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

beforeEach(() => {
  vi.clearAllMocks()
  ;(getStorageClient as ReturnType<typeof vi.fn>).mockReturnValue({ query: mockQuery })
  process.env.PYTHON_SIDECAR_URL = 'http://localhost:8001'
  process.env.PYTHON_SIDECAR_API_KEY = ''
})

// ── Test 1: ingress routes to ephemeris_daily with sign_ingress_today ─────────

describe('query_transit_event ingress', () => {
  it('routes ingress query to ephemeris_daily WHERE sign_ingress_today', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          date: '2027-04-14',
          planet: 'jupiter',
          sign: 'Aries',
          longitude_deg: '0.54321',
          sign_ingress_today: true,
        },
      ],
    })

    const bundle = await tool.retrieve(basePlan, {
      event_type: 'ingress',
      planet: 'Jupiter',
      target_sign: 'Aries',
      start_date: '2026-05-19',
      end_date: '2028-01-01',
    })

    expect(mockQuery).toHaveBeenCalledOnce()
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('sign_ingress_today = true')
    expect(sql).toContain('FROM ephemeris_daily')
    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.event_type).toBe('ingress')
    expect(content.sign).toBe('Aries')
  })
})

// ── Test 2: station routes to retrogrades table ───────────────────────────────

describe('query_transit_event station', () => {
  it('routes station query to retrogrades table', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          planet: 'mercury',
          retrograde_start: '2026-07-18',
          retrograde_end: '2026-08-11',
          longitude_start: '112.34567',
          longitude_end: '98.12345',
        },
      ],
    })

    const bundle = await tool.retrieve(basePlan, {
      event_type: 'station',
      planet: 'Mercury',
      start_date: '2026-01-01',
      end_date: '2026-12-31',
    })

    expect(mockQuery).toHaveBeenCalledOnce()
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('FROM retrogrades')
    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.event_type).toBe('station')
    expect(content.planet).toBe('mercury')
  })
})

// ── Test 3: aspect routes to sidecar POST /transit_search ────────────────────

describe('query_transit_event aspect', () => {
  it('routes aspect query to sidecar POST /transit_search', async () => {
    const sidecarResponse = [
      {
        event_type: 'aspect',
        event_jd: 2461800.5,
        event_datetime_ist: '2027-11-15T10:30:00',
        transit_planet: 'saturn',
        secondary_planet: null,
        exact_longitude_deg: 124.5,
        orb_at_event_deg: 0.9,
        sign: 'Leo',
        nakshatra: 'Purva Phalguni',
        extra: { aspect_deg: 180 },
      },
    ]
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => sidecarResponse,
    })

    const bundle = await tool.retrieve(basePlan, {
      event_type: 'aspect',
      transit_planet: 'Saturn',
      natal_longitude_deg: 304.5,
      aspect_degrees: [180, 90],
      orb_deg: 1.0,
      start_date: '2026-05-19',
      end_date: '2028-05-19',
    })

    expect(mockFetch).toHaveBeenCalledOnce()
    const [url, init] = mockFetch.mock.calls[0]
    expect(url).toContain('/transit_search')
    const body = JSON.parse(init.body)
    expect(body.event_type).toBe('aspect')
    expect(bundle.results).toHaveLength(1)
  })
})

// ── Test 4: natal_planet lookup from chart_facts before sidecar call ──────────

describe('query_transit_event natal lookup', () => {
  it('looks up natal longitude from chart_facts when natal_planet provided', async () => {
    // First call: chart_facts lookup
    mockQuery.mockResolvedValueOnce({ rows: [{ longitude_deg: '304.5678' }] })
    // Sidecar returns one event
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          event_type: 'aspect',
          event_jd: 2461800.5,
          event_datetime_ist: '2027-11-15T10:30:00',
          transit_planet: 'saturn',
          secondary_planet: null,
          exact_longitude_deg: 124.5,
          orb_at_event_deg: 0.8,
          sign: 'Leo',
          nakshatra: 'Purva Phalguni',
          extra: { aspect_deg: 180 },
        },
      ],
    })

    const bundle = await tool.retrieve(basePlan, {
      event_type: 'aspect',
      transit_planet: 'Saturn',
      natal_planet: 'Moon',
      aspect_degrees: [180],
      start_date: '2026-05-19',
      end_date: '2028-05-19',
    })

    // chart_facts query must use 'planet' category
    expect(mockQuery).toHaveBeenCalledOnce()
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('chart_facts')
    expect(sql).toContain("category = 'planet'")

    // Sidecar request must carry the resolved natal longitude
    const body = JSON.parse(mockFetch.mock.calls[0][1].body)
    expect(body.target_planet_natal_longitude_deg).toBeCloseTo(304.5678, 2)
    expect(bundle.results).toHaveLength(1)
  })
})

// ── Test 5: returns diagnostic row when no events match ───────────────────────

describe('query_transit_event no results', () => {
  it('returns diagnostic row when no ingress events match', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })

    const bundle = await tool.retrieve(basePlan, {
      event_type: 'ingress',
      planet: 'Saturn',
      target_sign: 'Scorpio',
      start_date: '2026-05-19',
      end_date: '2027-05-19',
    })

    expect(bundle.results).toHaveLength(1)
    expect(bundle.results[0].confidence).toBe(0)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.note).toContain('No ingress events found')
  })
})
