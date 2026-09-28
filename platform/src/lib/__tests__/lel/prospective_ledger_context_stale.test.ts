/**
 * brahma_prospective_ledger — chart-context staleness (Jātaka Phase-A3, item 2).
 *
 * "Old-context ledger rows cannot seed a current reading." A row a correction
 * has marked chart_context_stale_at (migration 1123) must not be matched
 * against a new LEL event as though it were still a live standing prediction,
 * and the general-purpose list should exclude it by default while still
 * disclosing it on explicit request.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { listProspectivePredictions, matchOpenPredictionsForLelEvent } from '../../lel/prospective_ledger'

const mockQuery = vi.mocked(query)

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [] } as never)
})

describe('listProspectivePredictions — excludes stale rows by default', () => {
  it('scopes the query to chart_context_stale_at IS NULL', async () => {
    await listProspectivePredictions('c1', {})
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })

  it('includeStale drops the exclusion', async () => {
    await listProspectivePredictions('c1', { includeStale: true } as never)
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).not.toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})

describe('matchOpenPredictionsForLelEvent — never matches a stale row to a real-world event', () => {
  it('scopes the open-prediction match query to chart_context_stale_at IS NULL', async () => {
    await matchOpenPredictionsForLelEvent({
      chart_id: 'c1',
      life_event_id: 'ev-1',
      event_class: 'career_change',
      event_date: '2026-09-27',
      date_confidence: 'exact',
    })
    const [sql] = mockQuery.mock.calls[0]!
    expect(sql as string).toMatch(/lifecycle_status = 'open'/)
    expect(sql as string).toMatch(/chart_context_stale_at\s+IS\s+NULL/)
  })
})
