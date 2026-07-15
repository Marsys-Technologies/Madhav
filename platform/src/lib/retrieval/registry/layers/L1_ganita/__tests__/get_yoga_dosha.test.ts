/**
 * get_yoga_dosha.test.ts — D-1.5b Lane B-6 (item 5, B9 dosha gate) unit tests.
 * No live DB required — `query` is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getYogaDoshaCapability } from '../get_yoga_dosha'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getYogaDoshaCapability (backs ganita_yogas_get) — B9 dosha gate', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('excludes catalog-only dosha_label (fire_reason=requires_pass) rows from SQL by default', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })   // countResult
    mockQuery.mockResolvedValueOnce({ rows: [] })                  // result (paged rows)
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })    // firingsCountResult
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })    // doshaGatedCountResult

    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)

    // Both the count query and the paged SELECT must carry the gate clause when all is not set.
    const countSql = mockQuery.mock.calls[0][0] as string
    const rowsSql = mockQuery.mock.calls[1][0] as string
    expect(countSql).toMatch(/NOT \(fact_category = 'dosha_label'/)
    expect(rowsSql).toMatch(/NOT \(fact_category = 'dosha_label'/)

    const content = result.content as Record<string, unknown>
    const gate = content['dosha_label_gate'] as Record<string, unknown>
    expect(gate['applied']).toBe(true)
    expect(gate['all']).toBe(false)
    expect(gate['excluded_total']).toBe(2)
  })

  it('all=true lifts the gate — no gate clause in SQL, excluded_total reported as 0', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '7' }] })   // countResult
    mockQuery.mockResolvedValueOnce({ rows: [] })                  // result
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '5' }] })    // firingsCountResult
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '2' }] })    // doshaGatedCountResult (unused when all=true)

    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID, all: true }, undefined)
    const countSql = mockQuery.mock.calls[0][0] as string
    expect(countSql).not.toMatch(/requires_pass/)

    const content = result.content as Record<string, unknown>
    const gate = content['dosha_label_gate'] as Record<string, unknown>
    expect(gate['applied']).toBe(false)
    expect(gate['all']).toBe(true)
    expect(gate['excluded_total']).toBe(0)
  })

  it('requires chart_id-shaped input to run without throwing (defensive smoke)', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const result = await getYogaDoshaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
  })
})
