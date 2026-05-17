import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))
vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))
vi.mock('@/lib/schemas', () => ({
  validate: vi.fn().mockReturnValue({ valid: true, errors: [] }),
}))

import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import { tool } from '../query_kp_ruling_planets'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000012',
  query_text: 'kp ruling planets test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_kp_ruling_planets'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const sunRow = {
  chart_id: 'abhisek_mohanty_primary',
  planet: 'Sun',
  sidereal_lon: 322.45,
  sign: 'Aquarius',
  nakshatra: 'Shatabhisha',
  nakshatra_lord: 'Rahu',
  sub_lord: 'Venus',
  sub_sub_lord: 'Mercury',
  ayanamsha: 'lahiri',
  computed_by: 'compute_kp_v1',
}

function makeNineGrahaRows() {
  const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
  return planets.map((planet, i) => ({
    ...sunRow,
    planet,
    sidereal_lon: i * 40,
  }))
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

describe('query_kp_ruling_planets tool', () => {
  it('returns 9 grahas with default chart_id + lahiri ayanamsha', async () => {
    const rows = makeNineGrahaRows()
    mockQuery.mockResolvedValue({ rows, rowCount: 9 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(9)
    expect(bundle.tool_name).toBe('query_kp_ruling_planets')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('abhisek_mohanty_primary')
    expect(sqlParams[1]).toBe('lahiri')
  })

  it('filters by planet via ILIKE', async () => {
    mockQuery.mockResolvedValue({ rows: [sunRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      chart_id: 'abhisek_mohanty_primary',
      ayanamsha: 'lahiri',
      planet: 'Sun',
    })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.planet).toBe('Sun')
    expect(content.star_lord).toBe('Rahu')
    expect(content.sub_lord).toBe('Venus')

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('planet ILIKE')
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[2]).toBe('Sun')
  })

  it('returns empty results without error when no row matches', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, { planet: 'Pluto' })

    expect(bundle.results).toHaveLength(0)
    expect(bundle.tool_name).toBe('query_kp_ruling_planets')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('returns valid ToolBundle shape', async () => {
    mockQuery.mockResolvedValue({ rows: [sunRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('query_kp_ruling_planets')
    expect(bundle.tool_version).toBe('1.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('KP_SUBLORDS_RAW')
    expect(bundle.results[0].confidence).toBe(0.95)
    expect(bundle.results[0].significance).toBe(0.8)
  })

  it('logs error path on DB failure and rethrows', async () => {
    mockQuery.mockRejectedValueOnce(new Error('kp_explode'))
    await expect(tool.retrieve(basePlan)).rejects.toThrow('kp_explode')
    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({
        tool_name: 'query_kp_ruling_planets',
        status: 'error',
        error_code: 'kp_explode',
      }),
    )
  })
})
