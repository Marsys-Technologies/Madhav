/**
 * query_rm_chart_summary — unit tests
 * ======================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryRmChartSummaryCapability } from '../query_rm_chart_summary'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_rm_chart_summary — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryRmChartSummaryCapability.uri).toBe('marsys://tool/L2/query_rm_chart_summary')
    expect(queryRmChartSummaryCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryRmChartSummaryCapability.required_inputs).toContain('chart_id')
    const schema = queryRmChartSummaryCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryRmChartSummaryCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_rm_chart_summary — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryRmChartSummaryCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries bodha_rm_chart_summary, scoped by chart_id', async () => {
    await queryRmChartSummaryCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_rm_chart_summary')
    expect(String(calls[0]?.[0])).toContain('chart_id = $1')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies snapshot_type filter when provided', async () => {
    await queryRmChartSummaryCapability.handler(
      { chart_id: CHART_A, snapshot_type: 'annual' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('snapshot_type = $')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryRmChartSummaryCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['count']).toBe(0)
    expect(content['empty_reason']).toBeDefined()
  })

  it('respects the MAX_LIMIT bound and reports total_matching/more_available', async () => {
    vi.mocked(mockQuery)
      .mockResolvedValueOnce({ rows: [{ summary_id: 1 }] } as never)
      .mockResolvedValueOnce({ rows: [{ total: '5' }] } as never)
    const result = await queryRmChartSummaryCapability.handler(
      { chart_id: CHART_A, limit: 999 },
      undefined
    )
    const content = result.content as Record<string, unknown>
    expect(content['total_matching']).toBe(5)
    expect(content['more_available']).toBe(true)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('LIMIT $')
    expect(calls[0]?.[1]).toContain(10)
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryRmChartSummaryCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('provenance.tables reflects the queried table', async () => {
    const result = await queryRmChartSummaryCapability.handler({ chart_id: CHART_A }, undefined)
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['bodha_rm_chart_summary'])
  })
})
