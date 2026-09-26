/**
 * Packet B2 ("the DAG-derived downstream count").
 *
 * THE FEATURE: vw_asset_downstream_dependents (migration 1096) — a DAG-derived
 * count of transitive downstream dependents, surfaced as
 * AssetStats.downstream_dependent_count. Mirrors the C-1 graceful-degradation
 * precedent (blocked_by_asset_id_degradation.test.ts): the view may not exist yet
 * in every environment (migration 1096 pending), so the route probes
 * information_schema.views once per process (downstreamDependentsViewPresent,
 * @/lib/db/viewPresence) and degrades to `null` — never a crash, and never a
 * fabricated `0` standing in for "not computed".
 *
 * §N.8: this suite proves THREE distinct signals never collapse into one another —
 * absent (view missing / query failed) → null; a genuine leaf → real 0; a real hub
 * → the real count — because a defect that returns 0 for "not computed" would be
 * indistinguishable, on screen, from an honest "no downstream impact".
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

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
  viewPresent: boolean
  downstreamRows?: { asset_id: string; downstream_dependent_count: number }[]
  downstreamQueryThrows?: boolean
}) {
  const { viewPresent, downstreamRows = [], downstreamQueryThrows = false } = opts

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
    if (/information_schema\.views/.test(s)) {
      return Promise.resolve({ rows: viewPresent ? [{ present: 1 }] : [], rowCount: viewPresent ? 1 : 0 })
    }
    if (/FROM vw_asset_downstream_dependents/.test(s)) {
      if (downstreamQueryThrows) return Promise.reject(new Error('relation "vw_asset_downstream_dependents" does not exist'))
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
  it('view PRESENT: a real hub asset gets its real, non-zero count', async () => {
    setupMocks({
      viewPresent: true,
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

  it('view PRESENT: a genuine leaf reads a real, present 0 — never null, never omitted', async () => {
    setupMocks({
      viewPresent: true,
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

  it('view ABSENT (migration 1096 not yet applied): degrades to null, never a fabricated 0, and the route still returns assets', async () => {
    setupMocks({ viewPresent: false })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body.data.assets)).toBe(true)
    expect(body.data.assets.length).toBe(2)
    for (const a of body.data.assets) {
      expect(a.downstream_dependent_count ?? null).toBeNull()
    }
  })

  it('view PRESENT but the query itself throws: degrades to null for every asset, never crashes the route', async () => {
    setupMocks({ viewPresent: true, downstreamQueryThrows: true })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.data.assets.length).toBe(2)
    for (const a of body.data.assets) {
      expect(a.downstream_dependent_count ?? null).toBeNull()
    }
  })

  it('probes information_schema.views only ONCE across multiple requests in the same process (cached, never per-request)', async () => {
    setupMocks({ viewPresent: true, downstreamRows: [] })
    const { GET } = await import('../route')
    await GET(makeReq())
    await GET(makeReq())
    await GET(makeReq())
    const probeCalls = mockQuery.mock.calls.filter(([sql]) => /information_schema\.views/.test(String(sql)))
    expect(probeCalls.length).toBe(1)
  })

  it('queries vw_asset_downstream_dependents ONCE per request, registry-wide (not per-asset, not per-chart)', async () => {
    setupMocks({
      viewPresent: true,
      downstreamRows: [
        { asset_id: 'ga_hub', downstream_dependent_count: 42 },
        { asset_id: 'ga_leaf', downstream_dependent_count: 0 },
      ],
    })
    const { GET } = await import('../route')
    await GET(makeReq())
    const downstreamCalls = mockQuery.mock.calls.filter(([sql]) => /FROM vw_asset_downstream_dependents/.test(String(sql).replace(/\s+/g, ' ')))
    expect(downstreamCalls.length).toBe(1)
    // Registry-wide: no chart_id param bound (the DAG is chart-independent).
    expect(downstreamCalls[0][1] ?? []).toEqual([])
  })
})
