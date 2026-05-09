import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

import { getStorageClient } from '@/lib/storage'
import { tool } from '../cross_varga_dignity_query'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000d8a',
  query_text: 'cross-varga dignity test',
  query_class: 'interpretive',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['cross_varga_dignity_query'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'three_interpretation',
  manifest_fingerprint: 'd8',
  schema_version: '1.0',
}

// Fixture mirroring the v1.1 YAML §3.15 CSI rows + a few D9.* / D10.* per-planet rows.
const fixtureRows = [
  // CSI ledger — all 9 planets
  {
    fact_id: 'CSI.SUN',
    divisional_chart: 'D1',
    value_text: 'D1 Capricorn → D9 Cancer → D10 9th (Aries)',
    value_json: { planet: 'Sun', vargottama: false, d1_sign: 'Capricorn', d9_sign: 'Cancer', d10_sign: 'Aries', d10_house: 9, d10_dignity: 'trine' },
  },
  {
    fact_id: 'CSI.MOON',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Moon', vargottama: false, d1_sign: 'Aquarius', d9_sign: 'Gemini', d10_sign: 'Scorpio', d10_house: 4, d10_dignity: 'debilitated' },
  },
  {
    fact_id: 'CSI.MARS',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Mars', vargottama: false, d1_sign: 'Libra', d9_sign: 'Pisces', d10_sign: 'Aries', d10_house: 9, d10_dignity: 'own_sign' },
  },
  {
    fact_id: 'CSI.MERCURY',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Mercury', vargottama: true, d1_sign: 'Capricorn', d9_sign: 'Capricorn', d10_sign: 'Virgo', d10_house: 2, d10_dignity: 'own_sign' },
  },
  {
    fact_id: 'CSI.JUPITER',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Jupiter', vargottama: false, d1_sign: 'Sagittarius', d1_dignity: 'own_sign', d9_sign: 'Gemini', d10_sign: 'Pisces', d10_house: 8, d10_dignity: 'own_sign_dusthana' },
  },
  {
    fact_id: 'CSI.VENUS',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Venus', vargottama: false, d1_sign: 'Sagittarius', d9_sign: 'Virgo', d9_dignity: 'debilitated', d10_sign: 'Gemini', d10_house: 11, d10_dignity: 'neutral' },
  },
  {
    fact_id: 'CSI.SATURN',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Saturn', vargottama: false, d1_sign: 'Libra', d1_dignity: 'exalted', d9_sign: 'Aries', d9_dignity: 'debilitated', d10_sign: 'Taurus', d10_house: 10, d10_dignity: 'angular' },
  },
  {
    fact_id: 'CSI.RAHU',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Rahu', vargottama: false, d1_sign: 'Taurus', d9_sign: 'Gemini', d10_sign: 'Cancer', d10_house: 12 },
  },
  {
    fact_id: 'CSI.KETU',
    divisional_chart: 'D1',
    value_text: '',
    value_json: { planet: 'Ketu', vargottama: false, d1_sign: 'Scorpio', d9_sign: 'Sagittarius', d10_sign: 'Capricorn', d10_house: 6 },
  },
  // A few D9.* / D10.* rows — used for fact_ids provenance only.
  { fact_id: 'D9.SATURN', divisional_chart: 'D9', value_text: 'Aries', value_json: { sign: 'Aries' } },
  { fact_id: 'D10.SATURN', divisional_chart: 'D10', value_text: 'Taurus', value_json: { sign: 'Taurus' } },
]

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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any)
  mockQuery.mockResolvedValue({ rows: fixtureRows, rowCount: fixtureRows.length })
})

describe('cross_varga_dignity_query tool', () => {
  it('returns 9 rows for empty input (all planets)', async () => {
    const bundle = await tool.retrieve(basePlan, {})
    expect(bundle.results).toHaveLength(9)
    expect(bundle.tool_name).toBe('cross_varga_dignity_query')
  })

  it('filters correctly by planet (Saturn only)', async () => {
    const bundle = await tool.retrieve(basePlan, { planets: ['Saturn'] })
    expect(bundle.results).toHaveLength(1)
    const saturn = JSON.parse(bundle.results[0].content)
    expect(saturn.planet).toBe('Saturn')
    expect(saturn.d1_sign).toBe('Libra')
    expect(saturn.d1_dignity).toBe('exalted')
    expect(saturn.d9_sign).toBe('Aries')
    expect(saturn.d9_dignity).toBe('debilitated')
    expect(saturn.d10_sign).toBe('Taurus')
    expect(saturn.d10_house).toBe(10)
    expect(saturn.vargottama).toBe(false)
    expect(saturn.fact_ids).toContain('CSI.SATURN')
    expect(saturn.fact_ids).toContain('D9.SATURN')
    expect(saturn.fact_ids).toContain('D10.SATURN')
  })

  it('vargottama=true for Mercury (the only vargottama planet in the chart)', async () => {
    const bundle = await tool.retrieve(basePlan, {})
    const mercury = bundle.results
      .map((r) => JSON.parse(r.content))
      .find((r) => r.planet === 'Mercury')
    expect(mercury).toBeDefined()
    expect(mercury.vargottama).toBe(true)
    expect(mercury.d1_sign).toBe('Capricorn')
    expect(mercury.d9_sign).toBe('Capricorn')
    // No other planet should report vargottama=true.
    const others = bundle.results
      .map((r) => JSON.parse(r.content))
      .filter((r) => r.planet !== 'Mercury' && r.vargottama === true)
    expect(others).toHaveLength(0)
  })

  it('derives Saturn D9 dignity even when CSI value_json field is absent (fallback to lookup table)', async () => {
    // Replace the CSI.SATURN value_json so d9_dignity is missing — ensures the lookup-table path fires.
    const rowsNoSatD9Dignity = fixtureRows.map((r) =>
      r.fact_id === 'CSI.SATURN'
        ? {
            ...r,
            value_json: { ...r.value_json, d9_dignity: undefined },
          }
        : r,
    )
    mockQuery.mockResolvedValueOnce({ rows: rowsNoSatD9Dignity, rowCount: rowsNoSatD9Dignity.length })

    const bundle = await tool.retrieve(basePlan, { planets: ['Saturn'] })
    const saturn = JSON.parse(bundle.results[0].content)
    // Saturn in Aries → debilitated by classical lookup
    expect(saturn.d9_dignity).toBe('debilitated')
  })
})
