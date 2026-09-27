/**
 * query_calibration — chart-context staleness (Jātaka Phase-A2, item 2).
 *
 * The domain-scoped verdict query's JOIN to mimamsa_predictions (used to
 * narrow by `p.domain`) must exclude a prediction a correction has marked
 * chart_context_stale_at (migration 1122). In practice mimamsa_calibration is
 * fully rebuilt on every correction (mi_pramana), so it can only ever match a
 * current prediction unless a prediction_id happens to collide across
 * corrections — this is defense-in-depth for that edge case, matching every
 * other current-query consumer of mimamsa_predictions.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { queryCalibrationCapability } from '../query_calibration'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

beforeEach(() => {
  vi.mocked(mockQuery).mockReset()
  vi.mocked(mockQuery).mockResolvedValue({ rows: [] } as never)
})

describe('query_calibration — domain join excludes context-stale predictions', () => {
  it('the verdict query\'s JOIN mimamsa_predictions carries the staleness exclusion', async () => {
    await queryCalibrationCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)
    const call = vi.mocked(mockQuery).mock.calls.find(
      (c) => (c[0] as string).includes('FROM mimamsa_calibration') && (c[0] as string).includes('JOIN mimamsa_predictions'),
    )
    expect(call).toBeDefined()
    expect(call![0] as string).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })

  it('never touches lifecycle_status or outcome to express the staleness filter', async () => {
    await queryCalibrationCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)
    const call = vi.mocked(mockQuery).mock.calls.find((c) => (c[0] as string).includes('JOIN mimamsa_predictions'))!
    expect(call[0] as string).not.toMatch(/SET\s+/i)
  })
})
