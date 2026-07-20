/**
 * query_journal — unit tests
 * =============================
 * W2b Batch 4 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryJournalCapability } from '../query_journal'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_A = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

describe('query_journal — descriptor shape', () => {
  it('has the correct URI and is per_chart scope', () => {
    expect(queryJournalCapability.uri).toBe('marsys://tool/L5/query_journal')
    expect(queryJournalCapability.scope).toBe('per_chart')
  })

  it('chart_id is required with no default (Rule-4)', () => {
    expect(queryJournalCapability.required_inputs).toContain('chart_id')
    const schema = queryJournalCapability.input_schema?.['chart_id'] as unknown as Record<string, unknown>
    expect(schema?.['default']).toBeUndefined()
  })

  it('passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryJournalCapability as CapabilityDescriptor)
    expect(violations).toHaveLength(0)
  })
})

describe('query_journal — handler contract', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
    vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
  })

  it('error-if-missing: chart_id absent -> is_error true', async () => {
    const result = await queryJournalCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('queries mimamsa_journal, scoped by chart_id', async () => {
    await queryJournalCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('FROM mimamsa_journal')
    expect(calls[0]?.[1]).toContain(CHART_A)
  })

  it('answered_only=true adds the native_answer IS NOT NULL filter', async () => {
    await queryJournalCapability.handler({ chart_id: CHART_A, answered_only: true }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(String(calls[0]?.[0])).toContain('native_answer IS NOT NULL')
  })

  it('0 rows is a valid, honestly-flagged empty result, not an error', async () => {
    const result = await queryJournalCapability.handler({ chart_id: CHART_A }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(content['empty_reason']).toBeDefined()
  })

  it('native chart UUID never appears in any query param', async () => {
    await queryJournalCapability.handler({ chart_id: CHART_A }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    for (const [sql, params] of calls) {
      expect(String(sql)).not.toContain(NATIVE_CHART_ID)
      for (const p of (params as unknown[]) ?? []) {
        expect(String(p)).not.toContain(NATIVE_CHART_ID)
      }
    }
  })
})
