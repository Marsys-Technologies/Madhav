/**
 * query_life_events (lel_query) — WP-1.3(d) / F-L10-021
 * ======================================================
 * The `lel_query` MCP primitive must serve the native's user-authored life events
 * from the chart-scoped `life_events` table (57 rows for the canonical chart), NOT
 * the Bodha MSR signals surface it was mis-pointed at (lel_origin filter → 0 rows).
 *
 * DB is mocked — no live connection required.
 */

import { describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

const FAKE_EVENTS = [
  {
    event_id: 'LEL-001', event_date: '2010-06-15', category: 'career',
    domain: 'career', description: 'Joined first company', significance: 'major',
    event_type: 'milestone', source_citation: 'LEL_v1_2 §3', source_section: '§3',
    outcome_observed: true,
  },
  {
    event_id: 'LEL-002', event_date: '2014-02-01', category: 'relationship',
    domain: 'relationship', description: 'Marriage', significance: 'major',
    event_type: 'milestone', source_citation: 'LEL_v1_2 §4', source_section: '§4',
    outcome_observed: true,
  },
]

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('COUNT(*)')) return { rows: [{ total: '57' }] }
    if (sql.includes('FROM life_events')) return { rows: FAKE_EVENTS }
    return { rows: [] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'
import { queryLifeEventsCapability } from '../query_life_events'

describe('query_life_events (lel_query) — WP-1.3(d)', () => {
  it('is per_chart and requires chart_id', () => {
    expect(queryLifeEventsCapability.scope).toBe('per_chart')
    expect(queryLifeEventsCapability.required_inputs).toContain('chart_id')
    expect(queryLifeEventsCapability.name).toBe('lel_query')
  })

  it('errors (no DB) when chart_id is absent', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await queryLifeEventsCapability.handler({}, {})
    expect(result.is_error).toBe(true)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it('queries the life_events table scoped to chart_id and serves usable fields', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await queryLifeEventsCapability.handler({ chart_id: CHART_A }, {})
    expect(result.is_error).toBe(false)
    const calls = vi.mocked(mockQuery).mock.calls
    const mainCall = calls.find(c => String(c[0]).includes('ORDER BY event_date'))!
    expect(String(mainCall[0])).toContain('chart_id = $1')
    expect((mainCall[1] as unknown[])[0]).toBe(CHART_A)
    // NOT the bodha signals table — the whole point of the fix.
    expect(String(mainCall[0])).not.toContain('bodha_msr_signals')

    const content = result.content as Record<string, unknown>
    const events = content.events as Record<string, unknown>[]
    expect(events.length).toBe(2)
    for (const field of ['event_id', 'event_date', 'description', 'domain', 'category', 'significance']) {
      expect(events[0]).toHaveProperty(field)
    }
    expect(content.count).toBe(2)
  })

  it('LIMIT is capped at 50 (bounded serving)', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryLifeEventsCapability.handler({ chart_id: CHART_A, limit: 9999 }, {})
    const mainCall = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('ORDER BY event_date'))!
    const limitParam = (mainCall[1] as unknown[]).at(-1)
    expect(Number(limitParam)).toBeLessThanOrEqual(50)
  })

  it('optional filters (category, domain, significance, date range) narrow the SQL', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, category: 'career', domain: 'career', significance: 'major', start_date: '2000-01-01', end_date: '2020-01-01' },
      {},
    )
    const mainCall = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('ORDER BY event_date'))!
    const sql = String(mainCall[0])
    expect(sql).toContain('category = $')
    expect(sql).toContain('domain = $')
    expect(sql).toContain('significance = $')
    expect(sql).toContain('event_date >= $')
    expect(sql).toContain('event_date <= $')
    const params = mainCall[1] as unknown[]
    expect(params).toContain('career')
    expect(params).toContain('major')
  })

  it('reports total_matching for the family (D5 coverage receipt)', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await queryLifeEventsCapability.handler({ chart_id: CHART_A }, {})
    const content = result.content as Record<string, unknown>
    expect(content.total_matching).toBe(57)
  })
})
