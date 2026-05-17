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
import { tool } from '../query_signal_state'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000011',
  query_text: 'signal state test',
  query_class: 'holistic',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['query_signal_state'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const litSignal = {
  signal_id: 'SIG.MSR.142',
  query_date: '2026-05-17',
  state: 'lit' as const,
  confidence: 0.82,
  dasha_system: 'vimshottari',
  computed_by: 'signal_activator_v1',
  ayanamsha: 'lahiri',
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

describe('query_signal_state tool', () => {
  it('returns lit signal row with default chart_id + CURRENT_DATE when no params', async () => {
    mockQuery.mockResolvedValue({ rows: [litSignal], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.signal_id).toBe('SIG.MSR.142')
    expect(content.state).toBe('lit')

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('CURRENT_DATE')
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('abhisek_mohanty_primary')
  })

  it('filters by signal_ids + states with ANY($N::text[])', async () => {
    mockQuery.mockResolvedValue({ rows: [litSignal], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      signal_ids: ['SIG.MSR.142', 'SIG.MSR.001'],
      states: ['lit', 'ripening'],
      query_date: '2026-05-17',
    })

    expect(bundle.results).toHaveLength(1)
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('signal_id = ANY')
    expect(sql).toContain('state = ANY')
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams[0]).toBe('abhisek_mohanty_primary')
    expect(sqlParams).toContainEqual(['SIG.MSR.142', 'SIG.MSR.001'])
    expect(sqlParams).toContainEqual(['lit', 'ripening'])
  })

  it('treats query_date as range start when end_date supplied', async () => {
    mockQuery.mockResolvedValue({ rows: [litSignal], rowCount: 1 })

    await tool.retrieve(basePlan, { query_date: '2026-01-01', end_date: '2026-12-31' })

    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('query_date >= $')
    expect(sql).toContain('query_date <= $')
    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams).toContain('2026-01-01')
    expect(sqlParams).toContain('2026-12-31')
  })

  it('returns diagnostic row (not empty results) when no signal rows match', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, { query_date: '1900-01-01' })

    // tool injects a degraded/empty diagnostic content row
    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.note).toContain('signal_states empty')
    expect(bundle.results[0].confidence).toBe(0)
    expect(bundle.results[0].significance).toBe(0)
  })

  it('returns valid ToolBundle shape + logs error on DB throw', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [litSignal], rowCount: 1 })
    const ok = await tool.retrieve(basePlan)
    expect(ok.tool_name).toBe('query_signal_state')
    expect(ok.tool_version).toBe('1.0.0')
    expect(ok.schema_version).toBe('1.0')
    expect(ok.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(ok.results[0].source_canonical_id).toBe('SIGNAL_STATES')

    // Tool degrades gracefully (does NOT throw) when DB query fails — injects diagnostic
    mockQuery.mockRejectedValueOnce(new Error('db_down'))
    const degraded = await tool.retrieve(basePlan)
    expect(degraded.results).toHaveLength(1)
    const content = JSON.parse(degraded.results[0].content)
    expect(content.note).toContain('signal_states query failed')
    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({ tool_name: 'query_signal_state' }),
    )
  })
})
