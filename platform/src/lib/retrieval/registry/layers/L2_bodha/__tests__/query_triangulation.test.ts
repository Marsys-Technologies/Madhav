/**
 * query_triangulation — unit tests
 * ====================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryTriangulationCapability } from '../query_triangulation'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_triangulation — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryTriangulationCapability.uri).toBe('marsys://tool/L2/query_triangulation')
    expect(queryTriangulationCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryTriangulationCapability.required_inputs).toContain('chart_id')
    const schema = queryTriangulationCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('exposes a tradition enum with all 4 traditions', () => {
    const schema = queryTriangulationCapability.input_schema?.['tradition'] as unknown as Record<string, unknown>
    expect(schema['enum']).toEqual(['parashari', 'jaimini', 'kp', 'tajika'])
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryTriangulationCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_triangulation — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryTriangulationCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries bodha_triangulation, scoped by chart_id', async () => {
    await queryTriangulationCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_triangulation')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies question_class and tradition filters when provided', async () => {
    await queryTriangulationCapability.handler(
      { chart_id: CHART_A, question_class: 'marriage_timing', tradition: 'jaimini' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('question_class = $')
    expect(String(calls[0]?.[0])).toContain('tradition = $')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryTriangulationCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['empty_reason']).toBeDefined()
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryTriangulationCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('provenance.tables reflects the queried table', async () => {
    const result = await queryTriangulationCapability.handler({ chart_id: CHART_A }, undefined)
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['bodha_triangulation'])
  })
})
