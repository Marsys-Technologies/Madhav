import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { fetchGocharaSweep } from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('fetchGocharaSweep — F-134 past-peak disclosure', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('flags an already-peaked window with is_past_peak=true and counts it, ' +
     'while a genuinely future window gets is_past_peak=false', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '3' }] }) // coverage probe
      .mockResolvedValueOnce({
        rows: [
          { // reproduces F-134's live top_windows[0]: peaked over a year before as_of_date
            event_class: 'major_gain', temporal_shape: 'interval',
            window_start: '2024-02-05', window_end: '2034-01-30',
            peak_date: '2025-04-27', valence: 'gain', is_adverse: false,
          },
          { // genuinely future peak — must NOT be flagged
            event_class: 'major_loss', temporal_shape: 'interval',
            window_start: '2024-02-05', window_end: '2034-01-30',
            peak_date: '2030-08-14', valence: 'loss', is_adverse: true,
          },
          { // null peak_date — must be null (honest "can't tell"), not true/false
            event_class: 'financial_deception', temporal_shape: 'interval',
            window_start: '2024-02-05', window_end: '2034-01-30',
            peak_date: null, valence: 'loss', is_adverse: true,
          },
        ],
      })

    const result = await fetchGocharaSweep(CHART_ID, 'wealth', '2026-08-16', 3)

    expect(result.windows[0].is_past_peak).toBe(true)
    expect(result.windows[1].is_past_peak).toBe(false)
    expect(result.windows[2].is_past_peak).toBeNull()
    expect(result.past_peak_window_count).toBe(1)
    // upcoming_window_count is unchanged in meaning — still the raw overlap-matched count
    expect(result.upcoming_window_count).toBe(3)
  })
})
