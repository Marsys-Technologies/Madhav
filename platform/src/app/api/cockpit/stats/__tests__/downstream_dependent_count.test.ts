/**
 * Packet B2 ("the DAG-derived downstream count").
 *
 * THE FEATURE: a DAG-derived count of transitive downstream dependents (a
 * recursive CTE over asset_registry, DOWNSTREAM_DEPENDENTS_SQL in
 * @/lib/cockpit/downstreamDependents — no database view, no migration, no
 * presence probe), surfaced as AssetStats.downstream_dependent_count. If the
 * query fails, the route degrades to `null` — never a crash, and never a
 * fabricated `0` standing in for "not computed". The SQL itself is proven
 * against real Postgres in tests/integration/downstream_dependents.db.test.ts;
 * this suite mocks the query and proves the route contract.
 *
 * §N.8: this suite proves THREE distinct signals never collapse into one another —
 * absent (query failed) → null; a genuine leaf → real 0; a real hub
 * → the real count — because a defect that returns 0 for "not computed" would be
 * indistinguishable, on screen, from an honest "no downstream impact".
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'
import { DOWNSTREAM_DEPENDENTS_SQL } from '@/lib/cockpit/downstreamDependents'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const UID = 'owner-uid'

function makeReq(): NextRequest {
  return new NextRequest(`http://localhost/api/cockpit/stats?chart_id=${CHART_ID}`)
}

function setupMocks(opts: {
  downstreamRows?: { asset_id: string; downstream_dependent_count: number }[]
  downstreamQueryThrows?: boolean
}) {
  const { downstreamRows = [], downstreamQueryThrows = false } = opts

  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockQuery.mockImplementation((sql: string) => {
    const s = sql.replace(/\s+/g, ' ')
    if (/FROM profiles/.test(s)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/FROM chart_grants/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/owner_id[\s\S]*FROM charts/.test(s)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/information_schema\.columns/.test(s)) {
      // blocked_by_asset_id probe — irrelevant to this suite, report absent so
      // that code path stays inert and doesn't interfere with these assertions.
      return Promise.resolve({ rows: [], rowCount: 0 })
    }
    if (/WITH RECURSIVE edges/.test(s)) {
      if (downstreamQueryThrows) return Promise.reject(new Error('canceling statement due to statement timeout'))
      return Promise.resolve({ rows: downstreamRows, rowCount: downstreamRows.length })
    }
    if (/FROM asset_registry/.test(s)) {
      return Promise.resolve({
        rows: [
          { asset_id: 'ga_hub', count_sql: null, size_sql: null, scope: 'per_chart', is_active: true, target_floor: null, asset_type: 'data', asset_kind: 'data', health_probe: null, service_health: null, last_invoked_at: null, last_selftest_at: null, has_substeps: false },
          { asset_id: 'ga_leaf', count_sql: null, size_sql: null, scope: 'per_chart', is_active: true, target_floor: null, asset_type: 'data', asset_kind: 'data', health_probe: null, service_health: null, last_invoked_at: null, last_selftest_at: null, has_substeps: false },
        ],
        rowCount: 2,
      })
    }
    if (/FROM asset_throughput/.test(s)) {
      return Promise.resolve({
        rows: [
          { asset_id: 'ga_hub', state: 'error', last_built_at: '2026-09-26 18:00:00+00', rows_written: null, last_error: 'boom' },
          { asset_id: 'ga_leaf', state: 'error', last_built_at: '2026-09-26 18:00:00+00', rows_written: null, last_error: 'boom' },
        ],
        rowCount: 2,
      })
    }
    if (/FROM build_substep_progress/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_run_assets bra[\s\S]*JOIN build_runs/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/count\(\*\)/.test(s)) return Promise.resolve({ rows: [{ count: '0' }], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
})

describe('cockpit stats route — downstream_dependent_count (Packet B2)', () => {
  it('query OK: a real hub asset gets its real, non-zero count', async () => {
    setupMocks({
      downstreamRows: [
        { asset_id: 'ga_hub', downstream_dependent_count: 42 },
        { asset_id: 'ga_leaf', downstream_dependent_count: 0 },
      ],
    })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const hub = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'ga_hub')
    expect(hub.downstream_dependent_count).toBe(42)
  })

  it('query OK: a genuine leaf reads a real, present 0 — never null, never omitted', async () => {
    setupMocks({
      downstreamRows: [
        { asset_id: 'ga_hub', downstream_dependent_count: 42 },
        { asset_id: 'ga_leaf', downstream_dependent_count: 0 },
      ],
    })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const leaf = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'ga_leaf')
    expect(leaf.downstream_dependent_count).not.toBeNull()
    expect(leaf.downstream_dependent_count).toBe(0)
  })

  it('the query itself throws: degrades to null for every asset, never crashes the route', async () => {
    setupMocks({ downstreamQueryThrows: true })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.assets.length).toBe(2)
    for (const a of body.data.assets) {
      expect(a.downstream_dependent_count ?? null).toBeNull()
    }
  })

  it('runs the shared DOWNSTREAM_DEPENDENTS_SQL exactly ONCE per request, registry-wide (not per-asset, not per-chart), with no view/probe query', async () => {
    setupMocks({
      downstreamRows: [
        { asset_id: 'ga_hub', downstream_dependent_count: 42 },
        { asset_id: 'ga_leaf', downstream_dependent_count: 0 },
      ],
    })
    const { GET } = await import('../route')
    await GET(makeReq())
    const downstreamCalls = mockQuery.mock.calls.filter(([sql]) => /WITH RECURSIVE edges/.test(String(sql)))
    expect(downstreamCalls.length).toBe(1)
    expect(downstreamCalls[0][0]).toBe(DOWNSTREAM_DEPENDENTS_SQL)
    // Registry-wide: no chart_id param bound (the DAG is chart-independent).
    expect(downstreamCalls[0][1] ?? []).toEqual([])
    // No database object is involved: nothing probes information_schema.views and
    // nothing selects from a vw_asset_downstream_dependents relation.
    const all = mockQuery.mock.calls.map(([sql]) => String(sql))
    expect(all.some(sql => /information_schema\.views/.test(sql))).toBe(false)
    expect(all.some(sql => /vw_asset_downstream_dependents/.test(sql))).toBe(false)
  })

  it('counts arrive from pg as bigint strings and are coerced to numbers on the wire', async () => {
    setupMocks({
      downstreamRows: [
        { asset_id: 'ga_hub', downstream_dependent_count: '79' as unknown as number },
        { asset_id: 'ga_leaf', downstream_dependent_count: '0' as unknown as number },
      ],
    })
    const { GET } = await import('../route')
    const body = await (await GET(makeReq())).json()
    const hub = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'ga_hub')
    expect(hub.downstream_dependent_count).toBe(79)
    expect(typeof hub.downstream_dependent_count).toBe('number')
  })

  it('a query that returns no rows degrades every asset to null, not 0', async () => {
    setupMocks({ downstreamRows: [] })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    for (const a of body.data.assets) expect(a.downstream_dependent_count ?? null).toBeNull()
  })
})
