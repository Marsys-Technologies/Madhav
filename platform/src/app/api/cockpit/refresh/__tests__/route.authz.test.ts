/**
 * Regression test for P2 blocker B-008 — cross-tenant write on
 * POST /api/cockpit/refresh.
 *
 * Before the fix this route checked only `getServerUser() !== null` and then
 * INSERTed/UPDATEd `asset_throughput` rows for the caller-supplied `chart_id`:
 *
 *     INSERT INTO asset_throughput (chart_id, asset_id, state)
 *     SELECT $1, unnest($2::text[]), 'dormant'
 *     ON CONFLICT (chart_id, asset_id) DO UPDATE SET updated_at = now()
 *
 * With `scope: 'global'` that is one row per active registry asset, materialized
 * against a chart the caller has no relationship to. Non-destructive (it does not
 * delete data), but it is still a cross-tenant WRITE: it creates 'dormant'
 * throughput rows that did not previously exist for that chart, which the cockpit
 * stats surface and the build planner both read.
 *
 * Gate level is 'write' (permission === 'all'), consistent with the Clear routes
 * and POST /api/cockpit/runs: a `chart_grants` 'view' grantee may read a chart,
 * not write build-state rows into it.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { POST } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

/** Every SQL statement the route issued, so we can assert on the write itself. */
let issued: string[] = []

function makeReq(body: object): NextRequest {
  return new NextRequest('http://localhost/api/cockpit/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function setupMocks(opts: {
  uid: string
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null } = opts
  mockGetServerUser.mockResolvedValue({ uid })
  issued = []

  mockQuery.mockImplementation((sql: string) => {
    issued.push(sql)
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({ rows: [{ owner_id: ownerId }], rowCount: 1 })
    }
    if (/FROM asset_registry/.test(sql)) {
      return Promise.resolve({ rows: [{ asset_id: 'ka_kshetra' }, { asset_id: 'ka_avadhi' }], rowCount: 2 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const throughputWrites = () => issued.filter(q => /INSERT INTO asset_throughput/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/cockpit/refresh — P2-B-008 cross-tenant asset_throughput write', () => {
  it('DENIES a non-owner guest — and writes NO asset_throughput row', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({ chart_id: VICTIM_CHART, scope: 'global' }))
    expect(res.status).toBe(403)
    expect((await res.json()).code).toBe('FORBIDDEN_CHART')
    expect(throughputWrites()).toHaveLength(0)
  })

  it('DENIES a chart_grants view-grantee — a read grant is not a write grant', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await POST(makeReq({ chart_id: VICTIM_CHART, scope: 'layer', scope_target: 'kala' }))
    expect(res.status).toBe(403)
    expect(throughputWrites()).toHaveLength(0)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await POST(makeReq({ chart_id: VICTIM_CHART, scope: 'global' }))
    expect(res.status).toBe(403)
    expect(throughputWrites()).toHaveLength(0)
  })

  it('ALLOWS the owner — the legitimate refresh path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq({ chart_id: VICTIM_CHART, scope: 'global' }))
    expect(res.status).toBe(200)
    expect((await res.json()).refreshed.asset_count).toBe(2)
    expect(throughputWrites().length).toBeGreaterThan(0)
  })

  it('ALLOWS super_admin on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await POST(makeReq({ chart_id: VICTIM_CHART, scope: 'global' }))
    expect(res.status).toBe(200)
  })
})
