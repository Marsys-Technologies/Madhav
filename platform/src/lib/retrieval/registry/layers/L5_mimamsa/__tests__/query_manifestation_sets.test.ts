/**
 * query_manifestation_sets — unit tests
 * =========================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md). Confirms this is
 * distinct from mimamsa_manifestation_grammar (a different, already-served table).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryManifestationSetsCapability } from '../query_manifestation_sets'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_manifestation_sets — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryManifestationSetsCapability.uri).toBe('marsys://tool/L5/query_manifestation_sets')
    expect(queryManifestationSetsCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryManifestationSetsCapability.required_inputs).toContain('chart_id')
    const schema = queryManifestationSetsCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryManifestationSetsCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_manifestation_sets — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryManifestationSetsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries mimamsa_manifestation_sets (not mimamsa_manifestation_grammar), scoped by chart_id', async () => {
    await queryManifestationSetsCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    const sql = String(calls[0]?.[0])
    expect(sql).toContain('FROM mimamsa_manifestation_sets')
    expect(sql).not.toContain('mimamsa_manifestation_grammar')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies domain and channel_id filters when provided', async () => {
    await queryManifestationSetsCapability.handler(
      { chart_id: CHART_A, domain: 'career', channel_id: 'ch-1' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('domain = $')
    expect(String(calls[0]?.[0])).toContain('channel_id = $')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryManifestationSetsCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['empty_reason']).toBeDefined()
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryManifestationSetsCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })
})
