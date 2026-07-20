/**
 * query_cdlm_summary — unit tests
 * =================================
 * Covers the pre-existing chart_summary tier (unchanged, backward-compat check) plus
 * the W2 dark-set `tier` facet extension (domain_rollups / pattern_clusters /
 * evolution_gradients) — RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0,
 * DARK_SET_WIRING_PLAN_v1_0 "CDLM rollup tiers".
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryCdlmSummaryCapability } from '../query_cdlm_summary'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_cdlm_summary — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryCdlmSummaryCapability.uri).toBe('marsys://tool/L2/query_cdlm_summary')
    expect(queryCdlmSummaryCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryCdlmSummaryCapability.required_inputs).toContain('chart_id')
    const schema = queryCdlmSummaryCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('exposes the tier facet with all 4 tiers, default chart_summary', () => {
    const tierSchema = queryCdlmSummaryCapability.input_schema?.['tier'] as unknown as Record<string, unknown>
    expect(tierSchema).toBeDefined()
    expect(tierSchema['enum']).toEqual([
      'chart_summary', 'domain_rollups', 'pattern_clusters', 'evolution_gradients',
    ])
    expect(tierSchema['default']).toBe('chart_summary')
  })

  it('exposes a domain filter for the domain_rollups tier', () => {
    expect(queryCdlmSummaryCapability.input_schema?.['domain']).toBeDefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryCdlmSummaryCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_cdlm_summary — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryCdlmSummaryCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('default tier is chart_summary, queries bodha_cdlm_chart_summary (backward compat)', async () => {
    await queryCdlmSummaryCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_cdlm_chart_summary')
  })

  it('tier=domain_rollups queries bodha_cdlm_domain_rollups and applies domain filter', async () => {
    const result = await queryCdlmSummaryCapability.handler(
      { chart_id: CHART_A, tier: 'domain_rollups', domain: 'career' },
      undefined
    )
    expect(result.is_error).toBe(false)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_cdlm_domain_rollups')
    expect(String(calls[0]?.[0])).toContain('domain = $')
    expect(calls[0]?.[1]).toContain('career')
    const content = result.content as Record<string, unknown>
    expect(content['tier']).toBe('domain_rollups')
  })

  it('tier=pattern_clusters queries bodha_cdlm_pattern_clusters', async () => {
    await queryCdlmSummaryCapability.handler({ chart_id: CHART_A, tier: 'pattern_clusters' }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_cdlm_pattern_clusters')
  })

  it('tier=evolution_gradients queries bodha_cdlm_evolution_gradients (0 rows is a valid empty result, not an error)', async () => {
    const result = await queryCdlmSummaryCapability.handler(
      { chart_id: CHART_A, tier: 'evolution_gradients' },
      undefined
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['count']).toBe(0)
  })

  it('domain filter is ignored (not an error) for non-domain_rollups tiers', async () => {
    const result = await queryCdlmSummaryCapability.handler(
      { chart_id: CHART_A, tier: 'chart_summary', domain: 'career' },
      undefined
    )
    expect(result.is_error).toBe(false)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).not.toContain('domain = $')
  })

  it('unknown tier -> is_error true with a clear message', async () => {
    const result = await queryCdlmSummaryCapability.handler(
      { chart_id: CHART_A, tier: 'not_a_real_tier' },
      undefined
    )
    expect(result.is_error).toBe(true)
    expect((result.content as Record<string, unknown>)['error']).toMatch(/Unknown tier/)
  })

  it('native chart UUID never appears in any query param across all tiers', async () => {
    for (const tier of ['chart_summary', 'domain_rollups', 'pattern_clusters', 'evolution_gradients']) {
      await queryCdlmSummaryCapability.handler({ chart_id: CHART_A, tier }, undefined)
    }
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('provenance.tables reflects the queried tier table', async () => {
    const result = await queryCdlmSummaryCapability.handler(
      { chart_id: CHART_A, tier: 'pattern_clusters' },
      undefined
    )
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['bodha_cdlm_pattern_clusters'])
  })
})
