/**
 * query_load_bearing — unit tests
 * ===================================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md). Confirms this is
 * deliberately distinct from the GATED mi_adhilepa calibration-overlay siblings.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryLoadBearingCapability } from '../query_load_bearing'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_load_bearing — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryLoadBearingCapability.uri).toBe('marsys://tool/L5/query_load_bearing')
    expect(queryLoadBearingCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryLoadBearingCapability.required_inputs).toContain('chart_id')
    const schema = queryLoadBearingCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryLoadBearingCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_load_bearing — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryLoadBearingCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries mimamsa_load_bearing (not the GATED overlay tables), scoped by chart_id', async () => {
    await queryLoadBearingCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    const sql = String(calls[0]?.[0])
    expect(sql).toContain('FROM mimamsa_load_bearing')
    expect(sql).not.toContain('mimamsa_fact_adjustment')
    expect(sql).not.toContain('mimamsa_signal_adjustment')
    expect(sql).not.toContain('leakage_status')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies role filter when provided', async () => {
    await queryLoadBearingCapability.handler({ chart_id: CHART_A, role: 'load_bearing' }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('role = $')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryLoadBearingCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['empty_reason']).toBeDefined()
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryLoadBearingCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })
})
