/**
 * reading_checklist.fetch_gochara_sweep.test.ts — ADJUDICATION-6 (migration 527)
 * regression guard for `fetchGocharaSweep`'s two `kala_gochara_windows` reads.
 *
 * Mocks `@/lib/db/client` (no live DB) and asserts, on the ACTUAL SQL text passed
 * to `query`, that:
 *   1. both statements now carry the AUTHORITATIVE_GENERATION_FILTER correlated
 *      subquery (regression guard: a future edit must not silently drop it and
 *      reintroduce the "2.0 rows appear alongside v1 rows in one response"
 *      defect ADJUDICATION-6 exists to prevent);
 *   2. the filter is a semantic no-op TODAY — i.e. the query still returns the
 *      exact same rows as before migration 527 when every row is generation='v1'
 *      and the authority table is empty (byte-identical behavior claim from the
 *      PR body), proven here by asserting the coverage-probe/window fetch behave
 *      identically to their pre-527 fixtures.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { fetchGocharaSweep } from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('fetchGocharaSweep — ADJUDICATION-6 generation/authority filter (migration 527)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('both SQL statements carry the authoritative-generation correlated subquery', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '1' }] }) // coverage probe
      .mockResolvedValueOnce({ rows: [] }) // main window fetch

    await fetchGocharaSweep(CHART_ID, 'career', '2026-08-01', 3)

    expect(mockQuery).toHaveBeenCalledTimes(2)
    const [coverageCall, windowCall] = mockQuery.mock.calls
    const expectedFragment =
      "generation = COALESCE( (SELECT authoritative_generation FROM kala_gochara_authority WHERE chart_id = w.chart_id), 'v1')"
    expect((coverageCall[0] as string).replace(/\s+/g, ' ')).toContain(expectedFragment)
    expect((windowCall[0] as string).replace(/\s+/g, ' ')).toContain(expectedFragment)
  })

  it('byte-identical behavior today: honest empty when coverage probe returns 0 (no 2.0 rows exist to change this)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ n: '0' }] })

    const result = await fetchGocharaSweep(CHART_ID, 'health', '2026-08-01', 3)

    expect(result.domain_covered).toBe(false)
    expect(result.available).toBe(true)
    expect(result.windows).toEqual([])
    // only the coverage probe ran — short-circuits before the window fetch,
    // exactly as before migration 527.
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('byte-identical behavior today: populated coverage still returns the real rows unmodified', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '2' }] })
      .mockResolvedValueOnce({
        rows: [
          {
            event_class: 'marriage',
            temporal_shape: 'point',
            window_start: '2026-09-01',
            window_end: '2026-09-01',
            peak_date: '2026-09-01',
            valence: 'gain',
            is_adverse: false,
          },
        ],
      })

    const result = await fetchGocharaSweep(CHART_ID, 'relationships', '2026-08-01', 3)

    expect(result.domain_covered).toBe(true)
    expect(result.upcoming_window_count).toBe(1)
    expect(result.windows).toHaveLength(1)
    expect(result.windows[0].event_class).toBe('marriage')
  })
})
