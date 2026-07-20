/**
 * query_rm_pattern_remedies — unit tests
 * ==========================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryRmPatternRemediesCapability } from '../query_rm_pattern_remedies'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_rm_pattern_remedies — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryRmPatternRemediesCapability.uri).toBe('marsys://tool/L2/query_rm_pattern_remedies')
    expect(queryRmPatternRemediesCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryRmPatternRemediesCapability.required_inputs).toContain('chart_id')
    const schema = queryRmPatternRemediesCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryRmPatternRemediesCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_rm_pattern_remedies — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryRmPatternRemediesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries bodha_rm_pattern_remedies, scoped by chart_id, ordered by theme_strength DESC', async () => {
    await queryRmPatternRemediesCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_rm_pattern_remedies')
    expect(String(calls[0]?.[0])).toContain('ORDER BY theme_strength DESC')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies source_kind filter when provided', async () => {
    await queryRmPatternRemediesCapability.handler(
      { chart_id: CHART_A, source_kind: 'cdlm_pattern_cluster' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('source_kind = $')
    expect(calls[0]?.[1]).toContain('cdlm_pattern_cluster')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryRmPatternRemediesCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['empty_reason']).toBeDefined()
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryRmPatternRemediesCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('provenance.tables reflects the queried table', async () => {
    const result = await queryRmPatternRemediesCapability.handler({ chart_id: CHART_A }, undefined)
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['bodha_rm_pattern_remedies'])
  })
})
