import { describe, it, expect } from 'vitest'
import { fetchAllLelEvents, classifyScorability, partitionScorable, type LelEvent } from '../lel'
import type { McpClient } from '../../../doctrine_harness/lib/mcp_client'

function ev(overrides: Partial<LelEvent>): LelEvent {
  return {
    event_id: 'id-' + Math.random(),
    event_date: '2020-01-01',
    category: 'other',
    domain: 'other/misc',
    description: 'A precise event.',
    event_type: 'other',
    ...overrides,
  }
}

describe('classifyScorability', () => {
  it('excludes the birth anchor', () => {
    const v = classifyScorability(ev({ domain: 'other/birth' }))
    expect(v.scorable).toBe(false)
    expect(v.reasons).toContain('birth_anchor_not_an_outcome')
  })

  it('scores a discrete, precisely-dated event as scorable', () => {
    const v = classifyScorability(ev({ description: 'Joined Cognizant — first corporate IT job. Tenure exactly one year.' }))
    expect(v.scorable).toBe(true)
    expect(v.reasons).toEqual([])
  })

  it('excludes a multi-phase arc description', () => {
    const v = classifyScorability(
      ev({ description: 'Stammering onset in childhood (~1995). Three-phase arc: Phase 1 (childhood ~1995-2006): significant stammering.' })
    )
    expect(v.scorable).toBe(false)
    expect(v.reasons.length).toBeGreaterThan(0)
  })

  it('excludes a bare "around YYYY" (no month) description', () => {
    const v = classifyScorability(ev({ description: 'Father received a large sum from selling real estate (around 2010).' }))
    expect(v.scorable).toBe(false)
    expect(v.reasons).toContain('bare_around_year')
  })

  it('does NOT exclude "around" when a month qualifies the date', () => {
    const v = classifyScorability(ev({ description: 'Began IIT preparation around March 2001, continued through 2003.' }))
    // "around March 2001" has a month between "around" and the year, so bare_around_year must not fire.
    expect(v.reasons).not.toContain('bare_around_year')
  })

  it('excludes a month-or-month ambiguous date', () => {
    const v = classifyScorability(ev({ description: 'Paternal grandfather passed away (June or July 2009).' }))
    expect(v.scorable).toBe(false)
    expect(v.reasons).toContain('month_or_month')
  })

  it('excludes an explicit year-span duration', () => {
    const v = classifyScorability(ev({ description: 'Native read Shani Shtotram every night for approximately 7-10 years.' }))
    expect(v.scorable).toBe(false)
  })
})

describe('partitionScorable', () => {
  it('splits into scorable and excluded with reasons attached', () => {
    const events = [
      ev({ event_id: 'a', description: 'Married on a specific date.' }),
      ev({ event_id: 'b', description: 'Vague onset (~1999).', domain: 'other/x' }),
      ev({ event_id: 'birth', domain: 'other/birth' }),
    ]
    const { scorable, excluded } = partitionScorable(events)
    expect(scorable.map((e) => e.event_id)).toEqual(['a'])
    expect(excluded.map((e) => e.event_id).sort()).toEqual(['b', 'birth'])
  })
})

describe('fetchAllLelEvents', () => {
  function mockClient(pages: LelEvent[][]): McpClient {
    let call = 0
    return {
      callTool: async (name: string) => {
        expect(name).toBe('lel_query')
        const page = pages[Math.min(call, pages.length - 1)]
        call++
        return {
          raw: { ok: true, status: 200, body: '' },
          content: { ok: true, events: page, total_count: call === 1 ? 57 : page.length },
          isToolError: false,
        }
      },
    } as unknown as McpClient
  }

  it('pages via a date_from cursor until no new events are added, deduping by event_id', async () => {
    // Page 1: 3 events, last dated 2025-07-01 (simulates the 50-row server cap landing mid-day).
    // Page 2 (date_from=2025-07-01, catching the same-day duplicate): 1 new event on 2025-07-01 + 1 more later.
    // Page 3 (date_from=2025-07-15): no new events -> stop.
    const p1 = [ev({ event_id: '1', event_date: '2020-01-01' }), ev({ event_id: '2', event_date: '2024-01-01' }), ev({ event_id: '3', event_date: '2025-07-01' })]
    const p2 = [ev({ event_id: '3', event_date: '2025-07-01' }), ev({ event_id: '4', event_date: '2025-07-01' }), ev({ event_id: '5', event_date: '2025-07-15' })]
    const p3 = [ev({ event_id: '5', event_date: '2025-07-15' })]
    const client = mockClient([p1, p2, p3])
    const { events, pagesFetched } = await fetchAllLelEvents(client, 'chart-id')
    expect(events.map((e) => e.event_id).sort()).toEqual(['1', '2', '3', '4', '5'])
    expect(pagesFetched).toBe(3)
  })

  it('stops immediately when the first page is empty', async () => {
    const client = mockClient([[]])
    const { events } = await fetchAllLelEvents(client, 'chart-id')
    expect(events).toEqual([])
  })
})
