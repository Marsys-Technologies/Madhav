/**
 * Regression test for P2 blocker B-008 — `GET /api/cockpit/registry`.
 *
 * Verified claim: this route called `getServerUser()` ZERO times.
 *
 * Unlike the rest of the sweep, nothing it returns is chart-scoped: it is the
 * global `asset_registry` catalog. So no ownership gate applies, and the sweep
 * brief's "don't over-fix things legitimately meant to be broadly readable"
 * caveat is genuinely in play. It still gets authentication, for one concrete
 * reason rather than a general tidiness instinct: the rows include `count_sql`,
 * `size_sql`, and `target_table` — the internal table names and SQL of every
 * asset in the system. That is precisely the reconnaissance an attacker needs to
 * drive the `atlas/sample` dump this same sweep closes, served anonymously.
 *
 * Authentication only — any logged-in user may read the catalog, exactly as
 * before. The response is identical for every caller.
 *
 * The `Cache-Control: public` header is also corrected to `private`: `public`
 * permits a shared/CDN cache to store and re-serve what is now an authenticated
 * response. The 60s freshness window is preserved.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../route'

let issued: string[] = []

function setupMocks(uid: string | null) {
  mockGetServerUser.mockResolvedValue(uid ? { uid } : null)
  issued = []
  mockQuery.mockImplementation((sql: string) => {
    issued.push(sql)
    return Promise.resolve({
      rows: [{ asset_id: 'ka_kshetra', layer: 'kala', target_table: 'kala_kshetra', count_sql: 'SELECT count(*) FROM kala_kshetra WHERE chart_id=$1' }],
      rowCount: 1,
    })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/cockpit/registry — P2-B-008 unauthenticated schema/SQL disclosure', () => {
  it('DENIES an anonymous caller — and never queries the registry', async () => {
    setupMocks(null)
    const res = await GET()
    expect(res.status).toBe(401)
    // The internal SQL/table names must not leak in the denial body.
    expect(JSON.stringify(await res.json())).not.toContain('kala_kshetra')
    expect(issued).toHaveLength(0)
  })

  it('ALLOWS any authenticated caller — the catalog is not chart-scoped', async () => {
    setupMocks('any-uid')
    const res = await GET()
    expect(res.status).toBe(200)
    expect((await res.json()).data.assets).toHaveLength(1)
  })

  it('does not permit a shared cache to store the authenticated response', async () => {
    setupMocks('any-uid')
    const res = await GET()
    const cc = res.headers.get('Cache-Control') ?? ''
    expect(cc).toContain('private')
    expect(cc).not.toContain('public')
  })
})
