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
import { tool } from '../query_varshaphala'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000013',
  query_text: 'varshaphala test',
  query_class: 'predictive',
  domains: [],
  forward_looking: true,
  audience_tier: 'super_admin',
  tools_authorized: ['query_varshaphala'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const yearRow = {
  chart_id: 'abhisek_mohanty_primary',
  year: 2026,
  solar_return_utc: '2026-02-05T05:13:00Z',
  ascendant_sidereal: 95.4,
  ascendant_sign: 'Cancer',
  planet_positions: {
    Sun: { sidereal_lon: 320.5, sign: 'Aquarius', nakshatra: 'Shatabhisha' },
  },
  ayanamsha: 'lahiri',
  computed_by: 'compute_varshaphala_v1',
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

describe('query_varshaphala tool', () => {
  it('returns annual chart row for single year param', async () => {
    mockQuery.mockResolvedValue({ rows: [yearRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { year: 2026 })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.year).toBe(2026)
    expect(content.ascendant.sign).toBe('Cancer')
    expect(content.planets.Sun.sign).toBe('Aquarius')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('abhisek_mohanty_primary')
    expect(sqlParams[1]).toBe('lahiri')
    expect(sqlParams[2]).toBe(2026)
    expect(sqlParams[3]).toBe(2026)
  })

  it('falls back to plan.time_window when year params absent', async () => {
    mockQuery.mockResolvedValue({ rows: [yearRow], rowCount: 1 })
    const planWithWindow: QueryPlan = {
      ...basePlan,
      time_window: { start: '2026-01-01', end: '2028-12-31' },
    }

    await tool.retrieve(planWithWindow)

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('abhisek_mohanty_primary')
    expect(sqlParams[1]).toBe('lahiri')
    expect(sqlParams[2]).toBe(2026)
    expect(sqlParams[3]).toBe(2028)
  })

  it('returns empty results without error when no row matches', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, { year: 1899 })

    expect(bundle.results).toHaveLength(0)
    expect(bundle.tool_name).toBe('query_varshaphala')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('returns valid ToolBundle shape', async () => {
    mockQuery.mockResolvedValue({ rows: [yearRow], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, { year_start: 2026, year_end: 2027 })

    expect(bundle.tool_name).toBe('query_varshaphala')
    expect(bundle.tool_version).toBe('1.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('VARSHAPHALA_RAW')
    expect(bundle.results[0].confidence).toBe(0.9)
    expect(bundle.results[0].significance).toBe(0.75)
    expect(bundle.invocation_params).toMatchObject({
      chart_id: 'abhisek_mohanty_primary',
      ayanamsha: 'lahiri',
      year_start: 2026,
      year_end: 2027,
    })
  })

  it('logs error path on DB failure and rethrows', async () => {
    mockQuery.mockRejectedValueOnce(new Error('vp_fail'))
    await expect(tool.retrieve(basePlan, { year: 2026 })).rejects.toThrow('vp_fail')
    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({
        tool_name: 'query_varshaphala',
        status: 'error',
        error_code: 'vp_fail',
      }),
    )
  })
})
