/**
 * query_predictions — chart-context staleness (Jātaka Phase-A2, item 2).
 *
 * A prediction row a chart correction has marked chart_context_stale_at
 * (migration 1122 — a real, native-verified outcome mi_bhavisya's rebuild
 * never touches) is historical evidence computed under former birth details.
 * By default the current-chart serving read excludes it, same as every other
 * current-chart consumer of this table. An explicit `include_stale` request
 * may still see it — but only with explicit historical-context metadata
 * (never silently indistinguishable from a current row), matching the
 * historical/audit carve-out this session's own governing instructions state.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { queryPredictionsCapability } from '../query_predictions'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

const CHART = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

beforeEach(() => {
  vi.mocked(mockQuery).mockReset()
  vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
})

describe('query_predictions — default (current-chart) view excludes context-stale rows', () => {
  it('scopes both the page query and the total_matching count to chart_context_stale_at IS NULL', async () => {
    await queryPredictionsCapability.handler({ chart_id: CHART }, undefined)
    const calls = vi.mocked(mockQuery).mock.calls
    expect(calls.length).toBeGreaterThanOrEqual(2)
    for (const [sql] of calls) {
      expect(sql as string).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
    }
  })

  it('never touches lifecycle_status or outcome to express the staleness filter', async () => {
    await queryPredictionsCapability.handler({ chart_id: CHART, lifecycle_status: 'confirmed' }, undefined)
    const [sql] = vi.mocked(mockQuery).mock.calls[0]
    // The caller's own lifecycle_status filter (unrelated) is fine; the staleness
    // condition itself must be a separate, explicit clause, not a lifecycle rewrite.
    expect((sql as string).match(/chart_context_stale_at/g)?.length).toBeGreaterThan(0)
  })
})

describe('query_predictions — include_stale opts into historical rows with explicit metadata', () => {
  it('drops the staleness filter and stamps each row with its historical-context metadata', async () => {
    vi.mocked(mockQuery).mockImplementation(async (sql: string) => {
      if (/COUNT/i.test(sql)) return { rows: [{ total: '1' }] } as never
      return {
        rows: [
          {
            prediction_id: 'pred_1',
            lifecycle_status: 'expired',
            chart_context_stale_at: '2026-09-27T00:00:00Z',
            chart_context_stale_reason: 'chart_details_changed',
            chart_context_superseded_by_run_id: 'run-1',
          },
        ],
      } as never
    })
    const result = await queryPredictionsCapability.handler({ chart_id: CHART, include_stale: true }, undefined)
    const [pageSql] = vi.mocked(mockQuery).mock.calls[0]
    expect(pageSql as string).not.toMatch(/chart_context_stale_at\s+IS\s+NULL/)
    const content = (result as { content: { predictions: Array<Record<string, unknown>> } }).content
    expect(content.predictions[0]).toMatchObject({
      chart_context: {
        current: false,
        stale_reason: 'chart_details_changed',
        superseded_by_run_id: 'run-1',
      },
    })
  })

  it('a current row (not stale) is stamped current:true, never silently indistinguishable from a historical one', async () => {
    vi.mocked(mockQuery).mockImplementation(async (sql: string) => {
      if (/COUNT/i.test(sql)) return { rows: [{ total: '1' }] } as never
      return { rows: [{ prediction_id: 'pred_2', chart_context_stale_at: null, chart_context_stale_reason: null, chart_context_superseded_by_run_id: null }] } as never
    })
    const result = await queryPredictionsCapability.handler({ chart_id: CHART, include_stale: true }, undefined)
    const content = (result as { content: { predictions: Array<Record<string, unknown>> } }).content
    expect(content.predictions[0]).toMatchObject({ chart_context: { current: true } })
  })
})
