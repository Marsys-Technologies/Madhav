import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { queryRemediesCapability } from '../query_remedies'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const SATURN_ROW = {
  resonance_id: 'r-sat-1', graha: 'Saturn', resonance_score: 0.094,
  weakness_score: 0.3, contradiction_factor: 0, domain_burden: null, motif_burden: null,
  remedy_priority_class: 'low', is_yoga_karaka_flag: false, weakest_rank_in_chart: 8,
  associated_doshas_array: null, associated_motifs_array: null, associated_cdlm_cells_array: [],
  citation_ref: null, citation_human: null, computed_at: '2025-01-01T00:00:00Z',
}
const VENUS_ROW = { ...SATURN_ROW, resonance_id: 'r-ven-1', graha: 'Venus', resonance_score: 0.173, remedy_priority_class: 'critical', weakest_rank_in_chart: 1 }

function withResonances(rows: object[]) {
  return (sql: string) => {
    if (String(sql).includes('FROM bodha_rm_resonances')) return Promise.resolve({ rows })
    return Promise.resolve({ rows: [] })
  }
}

describe('F-50 graha-filtered remedy lead honesty', () => {
  beforeEach(() => queryMock.mockReset())
  afterEach(() => vi.restoreAllMocks())

  it('does not present one graha-filtered row as the chart-wide #1 remedy target', async () => {
    queryMock.mockImplementation(withResonances([SATURN_ROW]))
    const result = await queryRemediesCapability.handler({ chart_id: CHART_ID, graha: 'Saturn' }, undefined) as { content: { narration: { lead: string } }; is_error: boolean }

    expect(result.is_error).toBe(false)
    expect(result.content.narration.lead).not.toMatch(/#1 remedy-priority target/i)
    expect(result.content.narration.lead).toMatch(/low/i)
    expect(result.content.narration.lead).toMatch(/8.*chart-wide|rank.*8/i)
  })

  it('keeps chart-wide #1 framing for an unfiltered ranked result', async () => {
    queryMock.mockImplementation(withResonances([VENUS_ROW, SATURN_ROW]))
    const result = await queryRemediesCapability.handler({ chart_id: CHART_ID }, undefined) as { content: { narration: { lead: string } }; is_error: boolean }

    expect(result.is_error).toBe(false)
    expect(result.content.narration.lead).toMatch(/Venus.*#1 remedy-priority target/i)
  })
})
