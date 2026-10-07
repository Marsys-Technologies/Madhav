/**
 * Samīkṣā review-tab server actions — chart-context staleness and the
 * chart_id binding on every ledger mutation (Jātaka Phase-A3, independent-
 * review findings).
 *
 * editCandidateAction's UPDATE excludes a chart-context-stale row and is
 * bound to the caller's own authorized chart_id. Every other mutation
 * (dismiss/confirm/resolve) that reaches the shared DAL by rowId alone first
 * asserts the row actually belongs to that chart — a write-access grant on
 * chart A must not let a caller mutate chart B's ledger rows by guessing or
 * reusing a UUID (pre-existing gap, found during this review's read of
 * actions.ts, fixed alongside the staleness work since it is the same file
 * and the same class of "never trust an id alone" discipline).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('next/cache', () => ({ revalidatePath: vi.fn() }))

const { mockResolveAccess, mockQuery, mockTransitionLifecycle, mockConfirmDetectedCandidate, mockRecordConversationalOutcome } = vi.hoisted(() => ({
  mockResolveAccess: vi.fn(),
  mockQuery: vi.fn(),
  mockTransitionLifecycle: vi.fn(),
  mockConfirmDetectedCandidate: vi.fn(),
  mockRecordConversationalOutcome: vi.fn(),
}))

vi.mock('@/lib/auth/chart-page-guard', () => ({ resolveChartPageAccess: mockResolveAccess }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/pariprashna/samiksha/writer', () => ({ transitionLifecycle: mockTransitionLifecycle }))
vi.mock('@/lib/pariprashna/samiksha/reviewConfirm', () => ({ confirmDetectedCandidate: mockConfirmDetectedCandidate }))
vi.mock('@/lib/pariprashna/samiksha/outcome_recorder', () => ({ recordConversationalOutcome: mockRecordConversationalOutcome }))

import { editCandidateAction, dismissCandidateAction, resolvePredictionAction } from '../../../../app/clients/[id]/samiksha/actions'

const CHART = 'c-1'
const OTHER_CHART = 'c-2'
const ROW = 'r-1'

beforeEach(() => {
  vi.clearAllMocks()
  mockResolveAccess.mockResolvedValue({ permission: 'all' })
  mockQuery.mockImplementation(async (sql: string) => {
    if (/SELECT chart_id/i.test(sql)) return { rows: [{ chart_id: CHART }] }
    return { rows: [] }
  })
  mockTransitionLifecycle.mockResolvedValue({ id: ROW })
  mockConfirmDetectedCandidate.mockResolvedValue({ id: ROW })
})

describe('editCandidateAction — excludes a chart-context-stale row, bound to the caller\'s chart', () => {
  it('the UPDATE is scoped to chart_id = $n AND chart_context_stale_at IS NULL', async () => {
    await editCandidateAction({ chartId: CHART, rowId: ROW, claimText: 'edited' })
    const update = mockQuery.mock.calls.find(([sql]) => /^\s*UPDATE/i.test(sql as string))
    expect(update, 'expected the edit UPDATE').toBeDefined()
    const [sql, params] = update!
    expect(sql as string).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
    expect(sql as string).toMatch(/chart_id\s*=\s*\$\d/)
    expect(params).toContain(CHART)
  })
})

describe('every mutation refuses a row that does not belong to the caller\'s authorized chart (IDOR)', () => {
  it('dismissCandidateAction refuses a row belonging to a different chart, without calling transitionLifecycle', async () => {
    mockQuery.mockImplementation(async (sql: string) =>
      /SELECT chart_id/i.test(sql) ? { rows: [{ chart_id: OTHER_CHART }] } : { rows: [] },
    )
    await expect(dismissCandidateAction({ chartId: CHART, rowId: ROW, reason: 'x' })).rejects.toThrow()
    expect(mockTransitionLifecycle).not.toHaveBeenCalled()
  })

  it('resolvePredictionAction refuses a row belonging to a different chart, without calling recordConversationalOutcome', async () => {
    mockQuery.mockImplementation(async (sql: string) =>
      /SELECT chart_id/i.test(sql) ? { rows: [{ chart_id: OTHER_CHART }] } : { rows: [] },
    )
    await expect(resolvePredictionAction({ chartId: CHART, rowId: ROW, outcome: 'happened' })).rejects.toThrow()
    expect(mockRecordConversationalOutcome).not.toHaveBeenCalled()
  })

  it('a row that does belong to the chart proceeds normally (regression)', async () => {
    await dismissCandidateAction({ chartId: CHART, rowId: ROW, reason: 'x' })
    expect(mockTransitionLifecycle).toHaveBeenCalledWith(ROW, 'dismissed', { dismissed_reason: 'x' })
  })

  it('a row with no chart_id match at all (unknown id) is refused the same way', async () => {
    mockQuery.mockImplementation(async (sql: string) => (/SELECT chart_id/i.test(sql) ? { rows: [] } : { rows: [] }))
    await expect(dismissCandidateAction({ chartId: CHART, rowId: 'unknown', reason: 'x' })).rejects.toThrow()
  })
})
