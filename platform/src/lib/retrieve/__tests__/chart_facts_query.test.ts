import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock storage and telemetry before importing the module under test
vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))

import { getStorageClient } from '@/lib/storage'
import { tool } from '../chart_facts_query'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000001',
  query_text: 'Rank my planets by Shadbala',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: ['chart_facts_query'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

interface MockChartFactsRow {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
}

const makeShadbalaRow = (planet: string, forensic_rupas: number): MockChartFactsRow => ({
  fact_id: `SBL.TOTAL.${planet.toUpperCase()}`,
  category: 'shadbala',
  divisional_chart: 'D1',
  value_text: null,
  value_number: null,
  value_json: { planet, forensic_rupas, jh_rupas: forensic_rupas - 0.1, forensic_rank: '1', jh_rank: '1', min_required_rupas: '5.00' },
  source_section: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
})

const makeRow = (overrides: Partial<MockChartFactsRow>): MockChartFactsRow => ({
  ...makeShadbalaRow('Sun', 8.5),
  ...overrides,
})

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

describe('chart_facts_query tool', () => {
  // TC.1 — Shadbala ranking query
  it('returns shadbala rows when category=shadbala, rank_by=total_rupas', async () => {
    const rows = [
      makeShadbalaRow('Sun', 8.51),
      makeShadbalaRow('Saturn', 7.47),
      makeShadbalaRow('Jupiter', 7.73),
      makeShadbalaRow('Moon', 7.26),
      makeShadbalaRow('Mars', 5.27),
      makeShadbalaRow('Mercury', 6.55),
      makeShadbalaRow('Venus', 4.6),
    ]
    mockQuery.mockResolvedValue({ rows, rowCount: rows.length })

    const bundle = await tool.retrieve(basePlan, { category: 'shadbala', rank_by: 'total_rupas' })

    expect(bundle.tool_name).toBe('chart_facts_query')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.results).toHaveLength(7)
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
  })

  // TC.2 — BAV bindu lookup with planet + sign filter
  it('filters by planet and sign for ashtakavarga_bav query', async () => {
    const row = makeRow({
      fact_id: 'AVG.BAV.MARS',
      category: 'ashtakavarga_bav',
      value_json: {
        planet: 'Mars',
        by_sign: { Capricorn: 3 },
        total_bindus: 39,
      },
    })
    mockQuery.mockResolvedValue({ rows: [row], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      category: 'ashtakavarga_bav',
      planet: 'Mars',
      sign: 'Capricorn',
    })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.category).toBe('ashtakavarga_bav')
    expect(JSON.stringify(content.data)).toContain('Mars')
  })

  // TC.3 — Saham lookup by keyword
  it('returns Vivaha saham when keyword=Vivaha', async () => {
    const row = makeRow({
      fact_id: 'SAH.VIVAHA',
      category: 'saham',
      value_json: { sign: 'Libra', house: 7, meaning: 'Marriage', longitude: '5°00′00″ Li', nakshatra: 'Chitra' },
      value_text: 'Vivaha Saham',
    })
    mockQuery.mockResolvedValue({ rows: [row], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { category: 'saham', keyword: 'Vivaha' })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.fact_id).toContain('VIVAHA')
  })

  // TC.4 — Yoga register (category only, no other filters)
  it('returns yoga rows when category=yoga', async () => {
    const yogaRows = Array.from({ length: 18 }, (_, i) => makeRow({
      fact_id: `YGA.D1.YOGA${i}`,
      category: 'yoga',
      value_json: { type: `Yoga type ${i}`, source: 'JH confirmed', key_configuration: `Config ${i}` },
    }))
    mockQuery.mockResolvedValue({ rows: yogaRows, rowCount: yogaRows.length })

    const bundle = await tool.retrieve(basePlan, { category: 'yoga' })

    expect(bundle.results).toHaveLength(18)
    bundle.results.forEach(r => {
      expect(JSON.parse(r.content).category).toBe('yoga')
    })
  })

  // TC.5 — House filter (planets/entities in house 7)
  it('returns house 7 entries when house=7', async () => {
    const rows = [
      makeRow({ fact_id: 'HSE.7.SATURN', category: 'house', value_json: { house: 7, planet: 'Saturn', sign: 'Libra' } }),
      makeRow({ fact_id: 'HSE.7.MARS', category: 'house', value_json: { house: 7, planet: 'Mars', sign: 'Libra' } }),
    ]
    mockQuery.mockResolvedValue({ rows, rowCount: rows.length })

    const bundle = await tool.retrieve(basePlan, { category: 'house', house: 7 })

    expect(bundle.results).toHaveLength(2)
    const [first, second] = bundle.results.map(r => JSON.parse(r.content))
    expect(first.data?.house).toBe(7)
    expect(second.data?.house).toBe(7)
  })

  // TC.6 — Multiple categories (array)
  it('accepts an array of categories', async () => {
    const rows = [
      makeShadbalaRow('Sun', 8.5),
      makeRow({ fact_id: 'BVB.JH.10', category: 'bhava_bala', value_json: { house: 10, jh_rupas: 9.39, engine: 'JH', jh_rank: '3', life_area: 'Career' } }),
    ]
    mockQuery.mockResolvedValue({ rows, rowCount: rows.length })

    const bundle = await tool.retrieve(basePlan, {
      category: ['shadbala', 'bhava_bala'],
      rank_by: 'total_rupas',
    })

    expect(bundle.results).toHaveLength(2)
    const categories = bundle.results.map(r => JSON.parse(r.content).category)
    expect(categories).toContain('shadbala')
    expect(categories).toContain('bhava_bala')
  })

  // TC.7 — nakshatra_pada filter is passed in SQL args
  it('includes nakshatra_pada filter in SQL call when provided', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { category: 'planet', nakshatra_pada: 2 })

    const callArgs = mockQuery.mock.calls[0]
    const sql: string = callArgs[0]
    const args: unknown[] = callArgs[1]

    expect(sql).toContain('nakshatra_pada')
    expect(args).toContain(2)
  })

  // TC.8 — limit respected and capped at 100
  it('respects limit param and caps at 100', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { limit: 5 })
    const sql5: string = mockQuery.mock.calls[0][0]
    expect(sql5).toContain('LIMIT 5')

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
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { limit: 200 })
    const sql200: string = mockQuery.mock.calls[0][0]
    expect(sql200).toContain('LIMIT 100')
  })

  // TC.9 — ToolBundle shape
  it('returns a correctly shaped ToolBundle', async () => {
    mockQuery.mockResolvedValue({ rows: [makeShadbalaRow('Sun', 8.51)], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { category: 'shadbala' })

    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.tool_bundle_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    )
    expect(bundle.tool_name).toBe('chart_facts_query')
    expect(bundle.results).toHaveLength(1)
    expect(bundle.results[0].source_canonical_id).toBe('FORENSIC')
    expect(bundle.results[0].source_version).toBe('8.0')
    expect(bundle.results[0].confidence).toBe(1.0)
    expect(typeof bundle.latency_ms).toBe('number')
    expect(bundle.latency_ms).toBeGreaterThanOrEqual(0)
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.schema_version).toBe('1.0')
  })

  // TC.10 — Empty result for impossible filter
  it('returns empty results for impossible filter without error', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, {
      category: 'shadbala',
      planet: 'NonExistentPlanet',
    })

    expect(bundle.results).toHaveLength(0)
    expect(bundle.tool_name).toBe('chart_facts_query')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  // TC.11 — rank_by=total_bindus produces correct ORDER BY
  it('applies total_bindus ordering in SQL for ashtakavarga_bav query', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, {
      category: 'ashtakavarga_bav',
      rank_by: 'total_bindus',
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('total_bindus')
    expect(sql).toContain('DESC')
  })

  // TC.12 — keyword search hits value_text and value_json
  it('includes ILIKE conditions on value_text and value_json for keyword search', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, { keyword: 'Sasha' })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('value_text ILIKE')
    expect(sql).toContain('value_json::text ILIKE')
  })

  // TC.13 — as_of_date emits start_date/end_date bracket (Phase 5A dasha filter)
  it('emits start_date <= as_of_date < end_date condition for dasha date lookup', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, {
      category: 'dasha_vimshottari',
      as_of_date: '2026-05-19',
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("start_date')::date <=")
    expect(sql).toContain("end_date')::date >")
    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args).toContain('2026-05-19')
  })

  // TC.14 — from_date emits end_date >= from_date (range start filter)
  it('emits end_date >= from_date condition for forward range query', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, {
      category: 'dasha_vimshottari',
      from_date: '2027-01-01',
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("end_date')::date >=")
    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args).toContain('2027-01-01')
  })

  // TC.15 — to_date emits start_date <= to_date (range end filter)
  it('emits start_date <= to_date condition for historical range query', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    await tool.retrieve(basePlan, {
      category: 'dasha_vimshottari',
      to_date: '2025-12-31',
    })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain("start_date')::date <=")
    const args: unknown[] = mockQuery.mock.calls[0][1]
    expect(args).toContain('2025-12-31')
  })
})
