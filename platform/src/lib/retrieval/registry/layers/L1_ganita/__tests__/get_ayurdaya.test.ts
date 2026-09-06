/**
 * get_ayurdaya.test.ts — F-E2/F-E3 (L1_W1_ANALYSIS_BATCH_E.md, NOW) unit tests. No live DB
 * required — `query` is mocked.
 *
 * F-E2: the SELECT omitted fact_value_jsonb, making maraka_grahas, per_graha contributions,
 * lagna_years, and harana_status unreachable at 0 hops despite the writer already storing
 * them. F-E3: harana_status is a real incompleteness disclosure that lived only inside the
 * (previously-omitted) jsonb — no consumer could see it without already knowing to look.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getAyurdayaCapability } from '../get_ayurdaya'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getAyurdayaCapability (ganita_ayurdaya_get)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('selects fact_value_jsonb (F-E2) and promotes harana_status to a top-level field (F-E3)', async () => {
    const rows = [
      {
        fact_id: 'f1', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_num: 98.75, fact_value_text: 'purnayu',
        fact_value_jsonb: { per_graha: { SU: 10.5 }, lagna_years: 4.2, classification: 'purnayu', method: 'pindayu', harana_status: 'base_only_haranas_deferred_to_w3' },
      },
      {
        fact_id: 'f2', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_num: null, fact_value_text: 'SAT,MAR',
        fact_value_jsonb: { maraka_grahas: ['SAT', 'MAR'] },
      },
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })

    const result = await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)

    const selectSql = mockQuery.mock.calls[0][0] as string
    expect(selectSql).toMatch(/fact_value_jsonb/)

    const content = result.content as Record<string, unknown>
    expect(content['harana_status']).toBe('base_only_haranas_deferred_to_w3')
    const returnedRows = content['rows'] as Array<Record<string, unknown>>
    expect(returnedRows[1]['fact_value_jsonb']).toEqual({ maraka_grahas: ['SAT', 'MAR'] })
  })

  it('does not fabricate harana_status when no total_years row is on the page', async () => {
    const rows = [
      { fact_id: 'f2', fact_subject: 'CHART', fact_key: 'maraka_grahas', fact_value_num: null, fact_value_text: 'SAT,MAR', fact_value_jsonb: { maraka_grahas: ['SAT', 'MAR'] } },
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })

    const result = await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['harana_status']).toBeUndefined()
  })

  it('reports harana_status as an array if the served page ever carries divergent values (honest, not silently collapsed)', async () => {
    const rows = [
      { fact_id: 'f1', fact_subject: 'PINDAYU', fact_key: 'total_years', fact_value_jsonb: { harana_status: 'status_a' } },
      { fact_id: 'f3', fact_subject: 'AMSAYU', fact_key: 'total_years', fact_value_jsonb: { harana_status: 'status_b' } },
    ]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })

    const result = await getAyurdayaCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['harana_status']).toEqual(['status_a', 'status_b'])
  })
})
