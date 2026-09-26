import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

/**
 * Packet B2 — C-4, surface 2/3 (review B1_rereview2_20260926T193112Z.md, "BLOCKS
 * B2"): "`/api/cockpit/runs/[id]/assets` — returns raw `bra.state`, no
 * `disposition`, no in-repo consumer but a live endpoint. Deferred and recorded."
 *
 * THE FIX: mirrors runs/active/route.ts's C-2b precedent exactly — `disposition`
 * selected unconditionally (it predates blocked_by_asset_id), `blocked_by_asset_id`
 * (migration 1095) gated by the same process-cached columnPresence probe every
 * other B1/B2 surface uses, so a caller of this endpoint can finally distinguish a
 * cascade victim (`disposition==='blocked_dependency'`) from a genuine root
 * failure — the same distinction runs/active/route.ts and stats/route.ts already
 * carry.
 */
const mockQuery = vi.fn()
const mockGetServerUser = vi.fn()

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

const request = new NextRequest('http://localhost/api/cockpit/runs/run-1/assets')
const context = { params: Promise.resolve({ id: 'run-1' }) }

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
  mockGetServerUser.mockResolvedValue({ uid: 'admin-1' })
})

function mockRoleThenColumnProbe(columnPresent: boolean) {
  mockQuery.mockImplementation((sql: string) => {
    const s = String(sql).replace(/\s+/g, ' ')
    if (/FROM profiles/.test(s)) return Promise.resolve({ rows: [{ role: 'super_admin' }] })
    if (/information_schema\.columns/.test(s)) {
      return Promise.resolve({ rows: columnPresent ? [{ present: 1 }] : [], rowCount: columnPresent ? 1 : 0 })
    }
    if (/FROM build_run_assets bra/.test(s)) {
      // R-1 precedent (blocked_by_asset_id_degradation.test.ts): Postgres throws
      // when a SELECT names a column that does not exist. Reproduce that here so
      // this test would catch a regression to an unconditional select.
      if (!columnPresent && /bra\.blocked_by_asset_id\b/.test(s)) {
        return Promise.reject(new Error('column "blocked_by_asset_id" does not exist'))
      }
      return Promise.resolve({
        rows: [{
          asset_id: 'bg_dependent', position: 1, state: 'error',
          started_at: '2026-01-01T00:00:00Z', ended_at: '2026-01-01T00:00:05Z',
          error: 'BLOCKED: upstream dependency(ies) bg_root did not complete in this run',
          disposition: 'blocked_dependency',
          blocked_by_asset_id: columnPresent ? 'bg_root' : null,
          sanskrit_name: 'test', english_name: 'Test', layer: 'brahmagyan', target_floor: null,
          rows_written: null,
        }],
      })
    }
    return Promise.resolve({ rows: [] })
  })
}

describe('GET /api/cockpit/runs/[id]/assets — disposition + blocked_by_asset_id (Packet B2, C-4)', () => {
  it('column PRESENT: the SQL actually SELECTs disposition and the real column, and the response carries them', async () => {
    mockRoleThenColumnProbe(true)
    const { GET } = await import('../route')
    const res = await GET(request, context)
    expect(res.status).toBe(200)
    const body = await res.json()
    const row = body.data.run_assets[0]
    expect(row.disposition).toBe('blocked_dependency')
    expect(row.blocked_by_asset_id).toBe('bg_root')

    // Non-vacuous: prove the SQL text itself requests these columns, so a mutation
    // that drops them from the SELECT (leaving the mock's fixed row shape
    // unchanged) cannot pass silently — the mock's "if the SQL still names the
    // real column, throw when absent" branch alone is not enough, because a SELECT
    // with the columns REMOVED never trips that branch either.
    const mainQuery = mockQuery.mock.calls.find(([sql]) => /FROM build_run_assets bra/.test(String(sql)))
    expect(mainQuery, 'main build_run_assets query was never issued').toBeTruthy()
    const sqlText = String(mainQuery![0])
    expect(sqlText).toMatch(/bra\.disposition/)
    expect(sqlText).toMatch(/bra\.blocked_by_asset_id/)
  })

  it('column ABSENT (migration 1095 not yet applied): the SQL aliases a NULL literal (never the real column), disposition still selected, route does not crash', async () => {
    mockRoleThenColumnProbe(false)
    const { GET } = await import('../route')
    const res = await GET(request, context)
    expect(res.status).toBe(200)
    const body = await res.json()
    const row = body.data.run_assets[0]
    expect(row.disposition).toBe('blocked_dependency')
    expect(row.blocked_by_asset_id).toBeNull()

    const mainQuery = mockQuery.mock.calls.find(([sql]) => /FROM build_run_assets bra/.test(String(sql)))
    const sqlText = String(mainQuery![0])
    expect(sqlText).toMatch(/bra\.disposition/)
    expect(sqlText).not.toMatch(/bra\.blocked_by_asset_id/)
    expect(sqlText).toMatch(/NULL::text AS blocked_by_asset_id/)
  })

  it('non-super_admin caller is forbidden (pre-existing gate, unaffected by this fix)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    const { GET } = await import('../route')
    const res = await GET(request, context)
    expect(res.status).toBe(403)
  })
})
