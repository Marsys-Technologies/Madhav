import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))

vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn(),
}))

import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool } from '../cross_varga_dignity_query'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000099',
  query_text: 'cross varga dignity test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['cross_varga_dignity_query'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

function makeCsiRow(planet: string, d1Sign: string, d9Sign: string, d10Sign: string, vargottama = false) {
  return {
    fact_id: `CSI.${planet.toUpperCase()}`,
    divisional_chart: 'D1',
    value_text: null,
    value_json: { d1_sign: d1Sign, d9_sign: d9Sign, d10_sign: d10Sign, d10_house: 2, vargottama },
  }
}

const allCsiRows = [
  makeCsiRow('Sun',     'Aries',      'Gemini',     'Pisces'),
  makeCsiRow('Moon',    'Taurus',     'Cancer',     'Aquarius'),
  makeCsiRow('Mars',    'Capricorn',  'Aries',      'Scorpio'),
  makeCsiRow('Mercury', 'Gemini',     'Virgo',      'Capricorn'),
  makeCsiRow('Jupiter', 'Cancer',     'Sagittarius','Pisces'),
  makeCsiRow('Venus',   'Pisces',     'Taurus',     'Libra'),
  makeCsiRow('Saturn',  'Capricorn',  'Libra',      'Aquarius'),
  makeCsiRow('Rahu',    'Aries',      'Gemini',     'Pisces'),
  makeCsiRow('Ketu',    'Libra',      'Sagittarius','Virgo'),
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
  })
})

describe('cross_varga_dignity_query tool', () => {
  it('returns all 9 planets when no params supplied', async () => {
    mockQuery.mockResolvedValue({ rows: allCsiRows, rowCount: allCsiRows.length })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(9)
    expect(bundle.tool_name).toBe('cross_varga_dignity_query')
    const planets = bundle.results.map(r => JSON.parse(r.content).planet)
    expect(planets).toContain('Saturn')
    expect(planets).toContain('Jupiter')
  })

  it('filters results to requested planet in JS (SQL returns all rows)', async () => {
    mockQuery.mockResolvedValue({ rows: allCsiRows, rowCount: allCsiRows.length })

    const bundle = await tool.retrieve(basePlan, { planets: ['Saturn'] })

    expect(bundle.results).toHaveLength(1)
    const result = JSON.parse(bundle.results[0].content)
    expect(result.planet).toBe('Saturn')
    expect(result.d1_sign).toBe('Capricorn')
    // SQL does not receive planet param — it returns all rows; filtering is in JS
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).not.toContain('$1')
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams).toHaveLength(0)
  })

  it('returns empty results without error when no matching CSI rows', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(0)
    expect(bundle.tool_name).toBe('cross_varga_dignity_query')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
  })

  it('returns valid ToolBundle shape with correct metadata', async () => {
    mockQuery.mockResolvedValue({ rows: [allCsiRows[6]], rowCount: 1 }) // Saturn only

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('cross_varga_dignity_query')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('FORENSIC')
    expect(bundle.results[0].confidence).toBe(1.0)
    expect(bundle.results[0].significance).toBe(0.95)
  })

  it('rejects and logs error when DB query throws', async () => {
    mockQuery.mockRejectedValue(new Error('connection refused'))

    await expect(tool.retrieve(basePlan)).rejects.toThrow('connection refused')
    expect(vi.mocked(writeToolExecutionLog)).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'error' })
    )
  })
})
