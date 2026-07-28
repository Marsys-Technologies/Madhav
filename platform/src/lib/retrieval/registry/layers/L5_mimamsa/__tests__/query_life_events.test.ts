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

// WP-B1 F-LEL-NOOP regression fixture: a richer pool, distinct from FAKE_EVENTS above,
// used only when the handler's SQL carries an ILIKE `%word%` param (i.e. `query` was
// actually wired through). Lets the mock honestly filter/paginate instead of returning
// the same fixed rows regardless of input — the exact failure mode being regressed.
const SEARCH_POOL = [
  {
    event_id: 'LEL-101', event_date: '2005-01-01', category: 'career',
    domain: 'career/promotion', description: 'Received first major promotion milestone',
    significance: 'major', event_type: 'milestone', source_citation: 'LEL_v1_2 §10',
    source_section: '§10', outcome_observed: true,
  },
  {
    event_id: 'LEL-102', event_date: '2010-06-01', category: 'relationship',
    domain: 'relationship/marriage', description: 'Marriage ceremony milestone celebrated',
    significance: 'major', event_type: 'milestone', source_citation: 'LEL_v1_2 §11',
    source_section: '§11', outcome_observed: true,
  },
  {
    event_id: 'LEL-103', event_date: '2016-03-01', category: 'health',
    domain: 'health/chronic', description: 'Severe headaches onset milestone',
    significance: 'moderate', event_type: 'milestone', source_citation: 'LEL_v1_2 §12',
    source_section: '§12', outcome_observed: true,
  },
  {
    event_id: 'LEL-104', event_date: '2020-04-01', category: 'creative',
    domain: 'creative/award', description: 'Painting award milestone win',
    significance: 'minor', event_type: 'milestone', source_citation: 'LEL_v1_2 §13',
    source_section: '§13', outcome_observed: true,
  },
]

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params: unknown[] = []) => {
    const searchWords = params
      .filter((v): v is string => typeof v === 'string' && v.startsWith('%') && v.endsWith('%'))
      .map(v => v.slice(1, -1).toLowerCase())

    if (searchWords.length === 0) {
      // Legacy fixture path — untouched by the query/offset regression tests below.
      if (sql.includes('COUNT(*)')) return { rows: [{ total: '57' }] }
      if (sql.includes('FROM life_events')) return { rows: FAKE_EVENTS }
      return { rows: [] }
    }

    // Query-aware path: AND-of-words substring match across the same columns the
    // real ILIKE predicate covers, so distinct `query` strings genuinely diverge.
    const matches = SEARCH_POOL.filter(ev =>
      searchWords.every(w =>
        [ev.description, ev.domain, ev.category, ev.event_type, ev.source_citation]
          .some(field => field.toLowerCase().includes(w)),
      ),
    )

    if (sql.includes('COUNT(*)')) return { rows: [{ total: String(matches.length) }] }
    if (sql.includes('FROM life_events')) {
      // Handler appends [...filterParams, limit, offset] as the final two SQL params.
      const limit  = Number(params[params.length - 2])
      const offset = Number(params[params.length - 1])
      return { rows: matches.slice(offset, offset + limit) }
    }
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
    // Params are [...filters, limit, offset] — limit is second-to-last since the
    // WP-B1 fix appends offset as the final param.
    const limitParam = (mainCall[1] as unknown[]).at(-2)
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

// ── WP-B1 F-LEL-NOOP regression suite ──────────────────────────────────────────
// PARISHODHANA_RECONCILIATION_v1_0.md disposed `mimamsa_lel_query`'s `query`/`offset`
// params as LIVE-OPEN for 4 consecutive campaigns: distinct query strings and distinct
// offsets against the canonical chart all returned the byte-identical `result_hash`.
// Root cause: register_p1_aliases.ts forwarded both params verbatim, but this handler
// never read args['query'] or args['offset'] — only the SQL params below prove that.
describe('query_life_events — query/offset wiring (WP-B1 F-LEL-NOOP fix)', () => {
  it('two different `query` values produce genuinely different result sets', async () => {
    vi.mocked(mockQuery).mockClear()
    const promotion = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'promotion', limit: 10, offset: 0 }, {},
    )
    const headaches = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'headaches', limit: 10, offset: 0 }, {},
    )
    expect(promotion.is_error).toBe(false)
    expect(headaches.is_error).toBe(false)

    const promotionIds = (promotion.content as { events: { event_id: string }[] }).events.map(e => e.event_id)
    const headachesIds = (headaches.content as { events: { event_id: string }[] }).events.map(e => e.event_id)

    expect(promotionIds).toEqual(['LEL-101'])
    expect(headachesIds).toEqual(['LEL-103'])
    // The exact defect being regressed: two distinct queries must not collapse to the
    // same page (previously: byte-identical result_hash regardless of `query`).
    expect(JSON.stringify(promotion.content)).not.toBe(JSON.stringify(headaches.content))
  })

  it('a `query` matching nothing returns an honest empty result, not a silent fallback', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'zzz_nonexistent_xyzzy_no_match' }, {},
    )
    const content = result.content as Record<string, unknown>
    expect(result.is_error).toBe(false)
    expect(content.events).toEqual([])
    expect(content.count).toBe(0)
    expect(content.total_matching).toBe(0)
    expect(content.has_more).toBe(false)
  })

  it('`query` reaches the SQL as an ILIKE predicate, not just the echoed filters object', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryLifeEventsCapability.handler({ chart_id: CHART_A, query: 'milestone' }, {})
    const mainCall = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('ORDER BY event_date'))!
    expect(String(mainCall[0])).toContain('ILIKE')
    expect(mainCall[1] as unknown[]).toContain('%milestone%')
  })

  it('two different `offset` values on the same query page through distinct rows', async () => {
    vi.mocked(mockQuery).mockClear()
    const page0 = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'milestone', limit: 1, offset: 0 }, {},
    )
    const page1 = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'milestone', limit: 1, offset: 1 }, {},
    )
    const id0 = (page0.content as { events: { event_id: string }[] }).events[0]?.event_id
    const id1 = (page1.content as { events: { event_id: string }[] }).events[0]?.event_id

    expect(id0).toBe('LEL-101')
    expect(id1).toBe('LEL-102')
    // The exact defect being regressed: two distinct offsets must not collapse to the
    // same page (previously: byte-identical result_hash regardless of `offset`).
    expect(id0).not.toBe(id1)
  })

  it('offset reports an honest end-of-results indicator once the last page is reached', async () => {
    vi.mocked(mockQuery).mockClear()
    const lastPage = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'milestone', limit: 1, offset: 3 }, {},
    )
    const pastEnd = await queryLifeEventsCapability.handler(
      { chart_id: CHART_A, query: 'milestone', limit: 1, offset: 4 }, {},
    )
    expect((lastPage.content as Record<string, unknown>).has_more).toBe(false)
    expect((lastPage.content as { events: unknown[] }).events.length).toBe(1)
    expect((pastEnd.content as Record<string, unknown>).has_more).toBe(false)
    expect((pastEnd.content as { events: unknown[] }).events).toEqual([])
  })

  it('the OFFSET clause reaches the SQL, not just the params echo', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryLifeEventsCapability.handler({ chart_id: CHART_A, query: 'milestone', offset: 2 }, {})
    const mainCall = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('ORDER BY event_date'))!
    expect(String(mainCall[0])).toContain('OFFSET $')
    expect(mainCall[1] as unknown[]).toContain(2)
  })

  it('input_schema declares `query` and `offset` (previously accepted silently, undocumented)', () => {
    expect(queryLifeEventsCapability.input_schema).toHaveProperty('query')
    expect(queryLifeEventsCapability.input_schema).toHaveProperty('offset')
  })
})
