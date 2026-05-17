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
import { tool } from '../lel_query'
import type { QueryPlan } from '../types'

const mockQuery = vi.fn()

const basePlan: QueryPlan = {
  query_plan_id: '00000000-0000-0000-0000-000000000010',
  query_text: 'lel query test',
  query_class: 'factual',
  domains: [],
  forward_looking: false,
  audience_tier: 'super_admin',
  tools_authorized: ['lel_query'],
  history_mode: 'synthesized',
  panel_mode: false,
  expected_output_shape: 'single_answer',
  manifest_fingerprint: 'abc123',
  schema_version: '1.0',
}

const careerEvent = {
  event_id: 'EVT.2008.06.09.01',
  event_date: '2008-06-09',
  category: 'career',
  description: 'Job change to new firm',
  significance: 'major',
  chart_state: { dasha: 'Saturn-Saturn' },
  source_section: 'LEL §3',
}

function makeLelRows(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    event_id: `EVT.200${i % 9}.0${(i % 9) + 1}.01`,
    event_date: `200${i % 9}-0${(i % 9) + 1}-01`,
    category: 'career',
    description: `Event ${i + 1}`,
    significance: 'major',
    chart_state: { dasha: 'Saturn-Mercury' },
    source_section: 'LEL §3',
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

describe('lel_query tool', () => {
  it('returns life-event rows when no params supplied', async () => {
    const rows = makeLelRows(12)
    mockQuery.mockResolvedValue({ rows, rowCount: 12 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.results).toHaveLength(12)
    expect(bundle.tool_name).toBe('lel_query')
  })

  it('filters by date range + category and returns matching row', async () => {
    mockQuery.mockResolvedValue({ rows: [careerEvent], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan, {
      start_date: '2008-01-01',
      end_date: '2008-12-31',
      category: 'career',
      significance: 'major',
    })

    expect(bundle.results).toHaveLength(1)
    const content = JSON.parse(bundle.results[0].content)
    expect(content.event_id).toBe('EVT.2008.06.09.01')

    const sqlParams: unknown[] = mockQuery.mock.calls[0][1]
    expect(sqlParams).toEqual(['2008-01-01', '2008-12-31', 'career', 'major'])
  })

  it('returns empty results without error when no rows match', async () => {
    mockQuery.mockResolvedValue({ rows: [], rowCount: 0 })

    const bundle = await tool.retrieve(basePlan, { category: 'spiritual' })

    expect(bundle.results).toHaveLength(0)
    expect(bundle.tool_name).toBe('lel_query')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('returns valid ToolBundle shape', async () => {
    mockQuery.mockResolvedValue({ rows: [careerEvent], rowCount: 1 })

    const bundle = await tool.retrieve(basePlan)

    expect(bundle.tool_name).toBe('lel_query')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.served_from_cache).toBe(false)
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(bundle.results[0].source_canonical_id).toBe('LEL')
    expect(bundle.results[0].confidence).toBe(1.0)
    expect(bundle.results[0].significance).toBe(1.0)
  })

  it('clamps limit to 50 and logs error path on DB failure', async () => {
    // first call: limit clamp check
    mockQuery.mockResolvedValueOnce({ rows: [careerEvent], rowCount: 1 })
    await tool.retrieve(basePlan, { limit: 9999 })
    const sql: string = mockQuery.mock.calls[0][0]
    expect(sql).toContain('LIMIT 50')

    // second call: error path
    mockQuery.mockRejectedValueOnce(new Error('boom'))
    await expect(tool.retrieve(basePlan)).rejects.toThrow('boom')
    expect(writeToolExecutionLog).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'error', tool_name: 'lel_query', error_code: 'boom' }),
    )
  })
})
