/**
 * Packet B1 — C-1 (review B1_review_20260926T182200Z.md, BLOCKS THE DEPLOY).
 *
 * THE DEFECT: route.ts unconditionally selected build_run_assets.blocked_by_asset_id
 * (migration 1095). That column does not exist in every environment yet — if the
 * CODE deploys before the MIGRATION applies (a real, observed condition: production
 * was confirmed on migration 1079, with 1095 not yet in _migrations_applied), the
 * SELECT throws. The route's OUTER catch swallows the exception and returns
 * `data: { assets: [] }` with HTTP 200 — the entire cockpit reads as empty, for
 * every chart, while reporting success. Not a degraded surface; a blank one that
 * looks successful.
 *
 * THE FIX: a module-level cache (`blockedByAssetIdColumnPresent`), probed once via
 * information_schema.columns and mirroring asset_runner.py's own
 * `_duration_columns_present` graceful-degradation precedent (migration 1094). When
 * absent, the disposition queries alias `NULL::text AS blocked_by_asset_id` instead
 * of selecting the real column, so the route degrades to "no drill-down field" —
 * never to "no assets at all".
 *
 * Each test resets the module registry and re-imports route.ts fresh, because the
 * whole POINT of the cache is that it persists across requests within one process —
 * testing that requires starting from an unprobed module each time.
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

/** Builds a mockQuery implementation. `columnPresent` controls whether the
 * information_schema probe reports blocked_by_asset_id as existing. */
function setupMocks(opts: { columnPresent: boolean; blockedAssetError?: string | null }) {
  const { columnPresent, blockedAssetError = null } = opts
  const probeCalls: string[] = []
  const dispositionQueryCalls: string[] = []

  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockQuery.mockImplementation((sql: string) => {
    const s = sql.replace(/\s+/g, ' ')
    if (/FROM profiles/.test(s)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/FROM chart_grants/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/owner_id[\s\S]*FROM charts/.test(s)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/information_schema\.columns/.test(s)) {
      probeCalls.push(s)
      return Promise.resolve({ rows: columnPresent ? [{ present: 1 }] : [], rowCount: columnPresent ? 1 : 0 })
    }
    if (/FROM asset_registry/.test(s)) {
      return Promise.resolve({
        rows: [{
          // count_sql: null forces fetchAllCounts' 'missing_table' path (a truthy
          // `base.error`, deterministically, without depending on the rows_written
          // shortcut's pre-existing 'error: null unconditionally' behaviour — a
          // property of fetchAllCounts this test does not touch and is not about).
          asset_id: 'bg_blocked_probe', count_sql: null,
          size_sql: null, scope: 'per_chart', is_active: true, target_floor: null,
          asset_type: 'data', asset_kind: 'data', health_probe: null,
          service_health: null, last_invoked_at: null, last_selftest_at: null, has_substeps: false,
        }],
        rowCount: 1,
      })
    }
    if (/FROM asset_throughput/.test(s)) {
      return Promise.resolve({
        rows: [{
          asset_id: 'bg_blocked_probe', state: 'error', last_built_at: '2026-09-26 18:00:00+00',
          rows_written: null,
        }],
        rowCount: 1,
      })
    }
    if (/FROM build_substep_progress/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_run_assets bra[\s\S]*JOIN build_runs/.test(s)) {
      dispositionQueryCalls.push(s)
      // R-1 (review B1_rereview_20260926T190244Z.md): faithful to production.
      // Postgres throws when a SELECT names a column that does not exist. If the
      // emitted SQL references the REAL column (bra.blocked_by_asset_id) while the
      // fixture says the column is absent, THROW — reproducing exactly what
      // production would do. This is the mechanism the whole file exists to
      // prove: with the C-1 guard deleted (blockedByCol hard-coded to
      // 'bra.blocked_by_asset_id' regardless of columnPresent), this branch fires
      // and every test below goes red — verified by the same mutation the
      // reviewer ran (N1b), reproduced in this session before restoring the fix.
      if (!columnPresent && /bra\.blocked_by_asset_id\b/.test(s)) {
        return Promise.reject(new Error('column "blocked_by_asset_id" does not exist'))
      }
      // WHERE bra.asset_id = ANY (the global-scope query) — no global assets here.
      if (/asset_id = ANY/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
      return Promise.resolve({
        rows: [{
          asset_id: 'bg_blocked_probe',
          disposition: 'blocked_dependency',
          blocked_by_asset_id: columnPresent ? 'bg_upstream_root' : null,
          ended_at: '2026-09-26 18:00:00+00',
        }],
        rowCount: 1,
      })
    }
    if (/count\(\*\)/.test(s)) return Promise.resolve({ rows: [{ count: '0' }], rowCount: 1 })
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
  return { probeCalls, dispositionQueryCalls }
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
})

describe('cockpit stats route — blocked_by_asset_id graceful degradation (Packet B1 C-1)', () => {
  it('with the column ABSENT, the route still returns assets — never a blank success', async () => {
    setupMocks({ columnPresent: false })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    expect(res.status).toBe(200)
    const body = await res.json()
    // THE decisive assertion: this must NOT be the blanked-cockpit failure mode
    // (data: { assets: [] }) that an unguarded throw + outer catch would produce.
    expect(Array.isArray(body.data.assets)).toBe(true)
    expect(body.data.assets.length).toBeGreaterThan(0)
    expect(body.data.assets[0].asset_id).toBe('bg_blocked_probe')
  })

  it('with the column ABSENT, state is still correctly derived as blocked (disposition survives; only the drill-down field is omitted)', async () => {
    setupMocks({ columnPresent: false })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const asset = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'bg_blocked_probe')
    expect(asset.state).toBe('blocked')
    expect(asset.blocked_by_asset_id ?? null).toBeNull()
  })

  it('with the column PRESENT, blocked_by_asset_id is populated from the real column', async () => {
    setupMocks({ columnPresent: true })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const asset = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'bg_blocked_probe')
    expect(asset.state).toBe('blocked')
    expect(asset.blocked_by_asset_id).toBe('bg_upstream_root')
  })

  it('probes information_schema.columns only ONCE across multiple requests in the same process (cached, never per-request)', async () => {
    const { probeCalls } = setupMocks({ columnPresent: false })
    const { GET } = await import('../route')
    await GET(makeReq())
    await GET(makeReq())
    await GET(makeReq())
    expect(probeCalls.length).toBe(1)
  })
})
