/**
 * Packet B1 — R-3 (review B1_rereview_20260926T190244Z.md).
 *
 * THE DEFECT: C-5(b) (route.ts's `eventMatchedDisposition` gate — a disposition is
 * only trusted when its build_run_assets.ended_at equals the SAME NOW() as
 * asset_throughput.last_built_at, since _mark_asset_error_terminal writes both
 * inside one transaction) had NO test. The reviewer deleted the guard entirely
 * (N4) and nothing went red.
 *
 * THE FIX (this file): a disposition whose `ended_at` does NOT match
 * `last_built_at` must degrade to plain 'error' (never trust a disposition from a
 * different attempt than the one that produced the CURRENT error); the same
 * tuple with a matching `ended_at` must yield 'blocked'.
 *
 * Mutation-checked in this session: with the gate deleted (dispEntry.disposition
 * passed straight through, unconditionally), the mismatched-timestamp test goes
 * red — verified below before restoring.
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

function setupMocks(opts: { dispositionEndedAt: string; throughputLastBuiltAt: string }) {
  mockGetServerUser.mockResolvedValue({ uid: UID })
  mockQuery.mockImplementation((sql: string) => {
    const s = sql.replace(/\s+/g, ' ')
    if (/FROM profiles/.test(s)) return Promise.resolve({ rows: [{ role: 'guest' }], rowCount: 1 })
    if (/FROM chart_grants/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/owner_id[\s\S]*FROM charts/.test(s)) return Promise.resolve({ rows: [{ owner_id: UID }], rowCount: 1 })
    if (/information_schema\.columns/.test(s)) return Promise.resolve({ rows: [{ present: 1 }], rowCount: 1 })
    if (/FROM asset_registry/.test(s)) {
      return Promise.resolve({
        rows: [{
          // count_sql: null -> deterministic truthy 'missing_table' base.error,
          // independent of the R-2 last_error wiring: this file is testing the
          // C-5(b) ended_at gate specifically, not R-2's separate fix.
          asset_id: 'bg_ended_at_probe', count_sql: null,
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
          asset_id: 'bg_ended_at_probe', state: 'error',
          last_built_at: opts.throughputLastBuiltAt, rows_written: null, last_error: 'irrelevant here',
        }],
        rowCount: 1,
      })
    }
    if (/FROM build_substep_progress/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
    if (/FROM build_run_assets bra[\s\S]*JOIN build_runs/.test(s)) {
      if (/asset_id = ANY/.test(s)) return Promise.resolve({ rows: [], rowCount: 0 })
      return Promise.resolve({
        rows: [{
          asset_id: 'bg_ended_at_probe', disposition: 'blocked_dependency',
          blocked_by_asset_id: 'bg_upstream_root', ended_at: opts.dispositionEndedAt,
        }],
        rowCount: 1,
      })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
})

describe('cockpit stats route — the ended_at/last_built_at event binding (Packet B1, R-3 / C-5b)', () => {
  it('MATCHING ended_at: the disposition is trusted — renders blocked', async () => {
    setupMocks({ dispositionEndedAt: '2026-09-26 18:00:00.123456+00', throughputLastBuiltAt: '2026-09-26 18:00:00.123456+00' })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const asset = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'bg_ended_at_probe')
    expect(asset.state).toBe('blocked')
  })

  it('MISMATCHED ended_at (a different attempt than the one that produced the current error): the disposition is NOT trusted — degrades to plain error', async () => {
    setupMocks({ dispositionEndedAt: '2026-09-20 10:00:00.000000+00', throughputLastBuiltAt: '2026-09-26 18:00:00.123456+00' })
    const { GET } = await import('../route')
    const res = await GET(makeReq())
    const body = await res.json()
    const asset = body.data.assets.find((a: { asset_id: string }) => a.asset_id === 'bg_ended_at_probe')
    expect(asset.state).toBe('error')
  })
})
