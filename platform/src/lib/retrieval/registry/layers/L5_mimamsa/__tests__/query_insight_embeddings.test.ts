/**
 * query_insight_embeddings — unit tests
 * =========================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md). Verifies the two
 * honest, non-fabricated modes (lookup, nearest) and that the raw vector is never
 * returned in either mode.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryInsightEmbeddingsCapability } from '../query_insight_embeddings'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_insight_embeddings — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryInsightEmbeddingsCapability.uri).toBe('marsys://tool/L5/query_insight_embeddings')
    expect(queryInsightEmbeddingsCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryInsightEmbeddingsCapability.required_inputs).toContain('chart_id')
    const schema = queryInsightEmbeddingsCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryInsightEmbeddingsCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_insight_embeddings — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryInsightEmbeddingsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('mode=lookup requires insight_id -> is_error true if absent', async () => {
    const result = await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'lookup' }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('mode=lookup queries mimamsa_insight_embeddings by insight_id, never selects the raw vector column', async () => {
    await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'lookup', insight_id: 'ins-1' }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    const sql = String(calls[0]?.[0])
    expect(sql).toContain('FROM mimamsa_insight_embeddings')
    expect(sql).not.toMatch(/\bembedding\b/)
    expect(sql).toContain('embed_model_version')
  })

  it('mode=nearest requires seed_insight_id -> is_error true if absent', async () => {
    const result = await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'nearest' }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('mode=nearest uses pgvector cosine distance <=> between two already-computed embeddings, never returns raw vectors', async () => {
    await queryInsightEmbeddingsCapability.handler(
      { chart_id: CHART_A, mode: 'nearest', seed_insight_id: 'ins-seed' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    const sql = String(calls[0]?.[0])
    expect(sql).toContain('<=>')
    expect(sql).toContain('cosine_distance')
    // The raw vector is never selected as its own output column — every "embedding"
    // occurrence in the query must be inside the <=> distance expression, not a bare
    // "n.embedding," or "s.embedding," selected column.
    expect(sql).not.toMatch(/,\s*n\.embedding\s*,/)
    expect(sql).not.toMatch(/,\s*s\.embedding\s*,/)
  })

  it('unknown mode -> is_error true', async () => {
    const result = await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'bogus' }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('B.10 honesty: 0-row table reports empty_reason, not an error, for both modes', async () => {
    const lookup = await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'lookup', insight_id: 'x' }, undefined)
    expect(lookup.is_error).toBe(false)
    expect((lookup.content as Record<string, unknown>)['empty_reason']).toBeDefined()

    const nearest = await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'nearest', seed_insight_id: 'x' }, undefined)
    expect(nearest.is_error).toBe(false)
    expect((nearest.content as Record<string, unknown>)['empty_reason']).toBeDefined()
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryInsightEmbeddingsCapability.handler({ chart_id: CHART_A, mode: 'lookup', insight_id: 'x' }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })
})
