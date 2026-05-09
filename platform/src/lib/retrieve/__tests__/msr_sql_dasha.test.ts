import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/storage', () => ({
  getStorageClient: vi.fn(),
}))
vi.mock('@/lib/telemetry', () => ({
  telemetry: { recordLatency: vi.fn() },
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn(),
}))

import { getStorageClient } from '@/lib/storage'
import { tool } from '../msr_sql'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000001',
  query_text: 'Ketu MD moksha activation',
  query_class: 'predictive',
  domains: ['spiritual'],
  forward_looking: true,
  audience_tier: 'client',
  tools_authorized: ['msr_sql'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'time_indexed_prediction',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })
  vi.mocked(getStorageClient).mockReturnValue({
    query: mockQuery,
    transaction: vi.fn(),
    readObject: vi.fn(),
    writeObject: vi.fn(),
    objectExists: vi.fn(),
    readFile: vi.fn(),
    fileExists: vi.fn(),
    listFiles: vi.fn(),
  } as unknown as ReturnType<typeof getStorageClient>)
})

describe('msr_sql dasha_activation mapping', () => {
  it('maps dasha_activation lord names to DSH.MD.* entity filter at param index 8', async () => {
    await tool.retrieve(basePlan, { dasha_activation: ['Ketu'] })

    expect(mockQuery).toHaveBeenCalledTimes(1)
    const params = mockQuery.mock.calls[0][1]
    expect(params[8]).toEqual(['DSH.MD.KETU'])
  })

  it('uppercases lord names and supports multi-lord arrays', async () => {
    await tool.retrieve(basePlan, { dasha_activation: ['ketu', 'mercury'] })
    const params = mockQuery.mock.calls[0][1]
    expect(params[8]).toEqual(['DSH.MD.KETU', 'DSH.MD.MERCURY'])
  })

  it('merges dasha_activation with explicit entities_involved_any', async () => {
    await tool.retrieve(basePlan, {
      dasha_activation: ['Ketu'],
      entities_involved_any: ['HSE.12'],
    })
    const params = mockQuery.mock.calls[0][1]
    expect(params[8]).toEqual(['HSE.12', 'DSH.MD.KETU'])
  })

  it('passes null entitiesFilter when neither field is provided', async () => {
    await tool.retrieve(basePlan)
    const params = mockQuery.mock.calls[0][1]
    expect(params[8]).toBeNull()
  })
})
