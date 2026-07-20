/**
 * query_rm_dasha_windowed_prescriptions — unit tests
 * ======================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md). This table is 0 rows
 * on the live chart at wiring time (B.10 honesty note in the source file) — tests verify
 * the empty-state discipline explicitly, not just descriptor shape.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryRmDashaWindowedPrescriptionsCapability } from '../query_rm_dasha_windowed_prescriptions'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_rm_dasha_windowed_prescriptions — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryRmDashaWindowedPrescriptionsCapability.uri).toBe(
      'marsys://tool/L2/query_rm_dasha_windowed_prescriptions'
    )
    expect(queryRmDashaWindowedPrescriptionsCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryRmDashaWindowedPrescriptionsCapability.required_inputs).toContain('chart_id')
    const schema = queryRmDashaWindowedPrescriptionsCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryRmDashaWindowedPrescriptionsCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_rm_dasha_windowed_prescriptions — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryRmDashaWindowedPrescriptionsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries bodha_rm_dasha_windowed_prescriptions, scoped by chart_id', async () => {
    await queryRmDashaWindowedPrescriptionsCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM bodha_rm_dasha_windowed_prescriptions')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('applies dasha_system / dasha_lord filters when provided', async () => {
    await queryRmDashaWindowedPrescriptionsCapability.handler(
      { chart_id: CHART_A, dasha_system: 'vimshottari', dasha_lord: 'Jupiter' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('dasha_system = $')
    expect(String(calls[0]?.[0])).toContain('dasha_lord = $')
  })

  it('applies active_on_date window filter when provided', async () => {
    await queryRmDashaWindowedPrescriptionsCapability.handler(
      { chart_id: CHART_A, active_on_date: '2026-07-20' },
      undefined
    )
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('window_start_iso <=')
    expect(String(calls[0]?.[0])).toContain('window_end_iso >=')
  })

  it('B.10 honesty: currently-0-row table reports a real, non-fabricated empty_reason, not an error', async () => {
    const result = await queryRmDashaWindowedPrescriptionsCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toMatch(/not yet be populated/i)
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryRmDashaWindowedPrescriptionsCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })

  it('provenance.tables reflects the queried table', async () => {
    const result = await queryRmDashaWindowedPrescriptionsCapability.handler({ chart_id: CHART_A }, undefined)
    const content = result.content as Record<string, unknown>
    const prov = content['provenance'] as Record<string, unknown>
    expect(prov['tables']).toEqual(['bodha_rm_dasha_windowed_prescriptions'])
  })
})
