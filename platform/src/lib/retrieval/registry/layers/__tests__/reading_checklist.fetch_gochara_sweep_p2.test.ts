/**
 * reading_checklist.fetch_gochara_sweep_p2.test.ts — WP7 P-2 acceptance.
 *
 * Mocks `@/lib/db/client` (no live DB) and asserts the '4.x' provenance and
 * qualification columns survive the 200-row SQL cap / 5-window display trim:
 *   (a) a confirmed '4.0' row (active_sentences ids, argmax peak_basis,
 *       completeness_state='confirmed') serves contact_ids and is_confirmed;
 *   (b) an unqualified row counts as context-only, never as a confirmed
 *       timing window (§N.6: no false density claim);
 *   (c) v1-generation rows with NULL new columns degrade to nulls/[] without
 *       error (the interface's existing honest-null convention);
 *   and the trim stays first-N in stored order — never a re-rank (H-5).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { fetchGocharaSweep } from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const ROW_40_CONFIRMED = {
  event_class: 'marriage',
  temporal_shape: 'span',
  window_start: '2026-09-01',
  window_end: '2026-10-15',
  peak_date: '2026-09-20',
  valence: 'gain',
  is_adverse: false,
  peak_basis: 'gochara_lambda_v3_argmax',
  generation: '4.0',
  active_sentences: ['sha256:9f2c…', 'sha256:71ab…'],
  completeness_state: 'confirmed',
}

const ROW_40_UNQUALIFIED = {
  event_class: 'career_shift',
  temporal_shape: 'span',
  window_start: '2026-11-01',
  window_end: '2027-02-01',
  peak_date: '2026-12-10',
  valence: 'mixed',
  is_adverse: null,
  peak_basis: 'point_class_context_envelope',
  generation: '4.0',
  active_sentences: [],
  completeness_state: 'unqualified',
}

const ROW_V1_NULLS = {
  event_class: 'marriage',
  temporal_shape: 'point',
  window_start: '2026-09-01',
  window_end: '2026-09-01',
  peak_date: '2026-09-01',
  valence: 'gain',
  is_adverse: false,
  peak_basis: null,
  generation: null,
  active_sentences: null,
  completeness_state: null,
}

describe('fetchGocharaSweep — P-2: contact_ids / completeness_state / peak_basis through the cap', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it("serves contact_ids and is_confirmed on a confirmed '4.0' row; unqualified row counts context-only", async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '2' }] }) // coverage probe
      .mockResolvedValueOnce({ rows: [ROW_40_CONFIRMED, ROW_40_UNQUALIFIED] })

    const result = await fetchGocharaSweep(CHART_ID, 'relationships', '2026-08-01', 3)

    expect(result.windows).toHaveLength(2)
    const [confirmed, unqualified] = result.windows

    // (a) confirmed row: ids + qualification carried through the trim
    expect(confirmed.contact_ids).toEqual(['sha256:9f2c…', 'sha256:71ab…'])
    expect(confirmed.completeness_state).toBe('confirmed')
    expect(confirmed.peak_basis).toBe('gochara_lambda_v3_argmax')
    expect(confirmed.generation).toBe('4.0')
    expect(confirmed.is_confirmed).toBe(true)

    // (b) unqualified / non-argmax row: present but never a confirmed timing window
    expect(unqualified.is_confirmed).toBe(false)
    expect(unqualified.contact_ids).toEqual([])

    // §N.6 counts: the page of 2 must not read as 2 confirmed timing windows
    expect(result.confirmed_rows_in_page).toBe(1)
    expect(result.context_only_rows_in_page).toBe(1)
    expect(result.catalog_only_note).toContain('context-only')
    expect(result.note).toContain('context-only')

    // provenance read off the rows; manifest_id is P-4's capability, null here
    expect(result.provenance).toEqual({ generation: '4.0', manifest_id: null })
  })

  it('v1-generation rows with NULL new columns degrade to nulls and empty arrays without error', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '1' }] })
      .mockResolvedValueOnce({ rows: [ROW_V1_NULLS] })

    const result = await fetchGocharaSweep(CHART_ID, 'relationships', '2026-08-01', 3)

    expect(result.windows).toHaveLength(1)
    const w = result.windows[0]
    expect(w.peak_basis).toBeNull()
    expect(w.generation).toBeNull()
    expect(w.completeness_state).toBeNull()
    expect(w.contact_ids).toEqual([])
    expect(w.is_confirmed).toBe(false)
    // a null-qualification row is context, not a confirmed timing window
    expect(result.confirmed_rows_in_page).toBe(0)
    expect(result.context_only_rows_in_page).toBe(1)
    expect(result.provenance).toEqual({ generation: null, manifest_id: null })
  })

  it('the SQL projection carries the P-2 columns and the trim stays first-N stored order', async () => {
    const manyRows = [0, 1, 2, 3, 4, 5, 6].map((i) => ({
      ...ROW_40_CONFIRMED,
      event_class: `class_${i}`,
    }))
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '7' }] })
      .mockResolvedValueOnce({ rows: manyRows })

    const result = await fetchGocharaSweep(CHART_ID, 'career', '2026-08-01', 3)

    const windowSql = (mockQuery.mock.calls[1][0] as string).replace(/\s+/g, ' ')
    expect(windowSql).toContain('w.peak_basis')
    expect(windowSql).toContain('w.generation')
    expect(windowSql).toContain('w.active_sentences')
    expect(windowSql).toContain('w.completeness_state')

    // display trim = first 5 rows in stored order, never re-ranked
    expect(result.windows.map((w) => w.event_class)).toEqual([
      'class_0', 'class_1', 'class_2', 'class_3', 'class_4',
    ])
    expect(result.upcoming_window_count).toBe(7)
  })

  it('empty page keeps zero counts and null note (no false context claim)', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ n: '1' }] })
      .mockResolvedValueOnce({ rows: [] })

    const result = await fetchGocharaSweep(CHART_ID, 'career', '2026-08-01', 3)

    expect(result.confirmed_rows_in_page).toBe(0)
    expect(result.context_only_rows_in_page).toBe(0)
    expect(result.catalog_only_note).toBeNull()
  })
})
