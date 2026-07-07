/**
 * lel_event_writer.test.ts — Unit tests for recordLelEvent().
 *
 * DB client is mocked — no real Postgres. Coverage:
 *   1. Inserts the full 14-column NOT-NULL superset with recorded_at = now().
 *   2. ON CONFLICT (chart_id, event_id) DO UPDATE never touches recorded_at.
 *   3. Rejects an unknown event class (not in brahma_event_ontology).
 *   4. Uses a provided event_id; derives a deterministic uuid5 otherwise.
 */

import { describe, it, expect, vi, beforeEach, type MockInstance } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { recordLelEvent, deriveLelEventId } from '@/lib/mcp/lel_event_writer'

const mockQuery = query as unknown as MockInstance

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function makeEvent(overrides: Record<string, unknown> = {}) {
  return {
    event_class: 'career_entry',
    event_date: '2015-06-01',
    description: 'Joined first firm',
    domain: 'career',
    ...overrides,
  }
}

/** Seed: ontology validation passes, then INSERT returns a row. */
function seedValid(created = true) {
  mockQuery
    .mockResolvedValueOnce({ rows: [{ event_class_id: 'career_entry' }], rowCount: 1 }) // ontology check
    .mockResolvedValueOnce({
      rows: [{ event_id: 'evt-uuid', recorded_at: '2026-07-08T00:00:00Z', created }],
      rowCount: 1,
    }) // INSERT
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('recordLelEvent', () => {
  it('inserts the full NOT-NULL superset with recorded_at = now()', async () => {
    seedValid()
    await recordLelEvent({ chartId: CHART, event: makeEvent(), provenance: { key_id: 'k1', trace_id: 't1' } })

    // 2nd call is the INSERT (1st is the ontology validation).
    const [sql, params] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(sql).toContain('INSERT INTO life_events')
    // The 14 NOT-NULL superset columns must all be present.
    for (const col of [
      'chart_id', 'event_id', 'event_date', 'event_type', 'description',
      'domain', 'outcome_observed', 'source_citation', 'recorded_at',
      'category', 'source_section', 'build_id', 'chart_state', 'provenance',
    ]) {
      expect(sql).toContain(col)
    }
    // recorded_at is stamped with now() — a real event, not the sentinel.
    expect(sql).toContain('now()')
    // ON CONFLICT upserts but does NOT clobber recorded_at.
    expect(sql).toContain('ON CONFLICT (chart_id, event_id) DO UPDATE')
    expect(sql).not.toMatch(/recorded_at\s*=\s*EXCLUDED/)

    // params: chart_id, event_id, event_date, event_type, description, domain,
    //         outcome_observed, source_citation, category, source_section,
    //         build_id, chart_state, provenance
    expect(params[0]).toBe(CHART)
    expect(params[2]).toBe('2015-06-01')
    expect(params[3]).toBe('career_entry')          // event_type defaults to event_class
    expect(params[5]).toBe('career')                 // domain
    expect(params[6]).toBe(false)                    // outcome_observed default
    expect(params[8]).toBe('career_entry')           // category = event_type
    expect(params[10]).toBe('lel_intake-api')        // build_id
  })

  it('defaults outcome_observed to false for a not-yet-observed event', async () => {
    seedValid()
    await recordLelEvent({ chartId: CHART, event: makeEvent() })
    const [, params] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(params[6]).toBe(false)
  })

  it('honours an explicit outcome_observed = true', async () => {
    seedValid()
    await recordLelEvent({ chartId: CHART, event: makeEvent({ outcome_observed: true }) })
    const [, params] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(params[6]).toBe(true)
  })

  it('rejects an unknown event class (not in brahma_event_ontology)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [], rowCount: 0 }) // ontology check → empty
    await expect(
      recordLelEvent({ chartId: CHART, event: makeEvent({ event_class: 'not_a_real_class' }) })
    ).rejects.toThrow(/Unknown event class/)
    // Must NOT reach the INSERT.
    expect(mockQuery).toHaveBeenCalledOnce()
  })

  it('uses a provided event_id when supplied', async () => {
    seedValid()
    const provided = '11111111-2222-3333-4444-555555555555'
    await recordLelEvent({ chartId: CHART, event: makeEvent({ event_id: provided }) })
    const [, params] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(params[1]).toBe(provided)
  })

  it('deriveLelEventId is deterministic for identical inputs', () => {
    const a = deriveLelEventId(CHART, makeEvent())
    const b = deriveLelEventId(CHART, makeEvent())
    expect(a).toBe(b)
    expect(a).toMatch(/^[0-9a-f-]{36}$/)
  })
})
