/**
 * query_mimamsa_discoveries — unit tests
 * ==========================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md). Verifies the
 * L5/L2 discoveries distinction (URI + table are both L5-specific, never bodha_discoveries).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryMimamsaDiscoveriesCapability } from '../query_mimamsa_discoveries'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_mimamsa_discoveries — descriptor shape', () => {
  it('has an L5 URI distinct from L2 bodha_discoveries', () => {
    expect(queryMimamsaDiscoveriesCapability.uri).toBe('marsys://tool/L5/query_mimamsa_discoveries')
    expect(queryMimamsaDiscoveriesCapability.uri).not.toContain('bodha_discoveries')
    expect(queryMimamsaDiscoveriesCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryMimamsaDiscoveriesCapability.required_inputs).toContain('chart_id')
    const schema = queryMimamsaDiscoveriesCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryMimamsaDiscoveriesCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_mimamsa_discoveries — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryMimamsaDiscoveriesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries mimamsa_discoveries (not bodha_discoveries), scoped by chart_id', async () => {
    await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM mimamsa_discoveries')
    expect(String(calls[0]?.[0])).not.toContain('bodha_discoveries')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies discovery_class filter when provided', async () => {
    await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART_A, discovery_class: 'emergent_law' }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('discovery_class = $')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['empty_reason']).toBeDefined()
  })

  it('provenance.tables reflects mimamsa_discoveries only', async () => {
    const result = await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART_A }, undefined)
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['mimamsa_discoveries'])
  })

  it('F-143: provenance discloses that n_support is not a scored-outcome count', async () => {
    const result = await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART_A }, undefined)
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    const semantics = prov['n_support_semantics'] as Record<string, string>
    // This capability serves n_support raw, and its meaning differs per discovery_class —
    // assignments for emergent_law, LIMIT-3-capped anchor matches for retrodiction.
    expect(semantics['emergent_law']).toMatch(/assignments/i)
    expect(semantics['emergent_law']).toMatch(/n_scored_matches/)
    expect(semantics['retrodiction']).toMatch(/not an adjudicated hit/)
  })

  it('F-143: retrodiction is a filterable discovery_class (51 such rows exist on the canonical chart)', () => {
    const schema = queryMimamsaDiscoveriesCapability.input_schema?.['discovery_class'] as unknown as Record<string, unknown>
    expect(schema?.['enum']).toContain('retrodiction')
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })
})
