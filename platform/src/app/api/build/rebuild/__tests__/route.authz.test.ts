/**
 * Regression test for V3-E-010 (EDIR_V3_REGISTER) — cross-tenant write on
 * POST /api/build/rebuild.
 *
 * Same root-cause family as B-001/B-007/B-008: a caller-supplied `chart_id`
 * was trusted after only "is anyone logged in" — never checked against actual
 * chart ownership/grants. Before the fix this route checked only
 * `getServerUser() !== null` and then INSERTed a `build_events` row for the
 * caller-supplied `chart_id`:
 *
 *     INSERT INTO build_events (build_id, chart_id, event_type, payload, created_at)
 *     VALUES ($1, $2, 'rebuild_requested', $3::jsonb, NOW())
 *
 * That is a cross-tenant WRITE: any authenticated user (default role `guest`)
 * could enqueue a single-asset rebuild event against ANY chart_id, regardless
 * of ownership. Gate level is 'write' (permission === 'all'), matching the
 * sibling rebuild-all fix and the B-008 precedents (POST /api/cockpit/runs,
 * /api/cockpit/refresh): a `chart_grants` 'view' grantee may read a chart, not
 * trigger a rebuild against it.
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
  return new NextRequest('http://localhost/api/build/rebuild', {
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
    if (/INSERT INTO build_events/.test(sql)) {
      return Promise.resolve({ rows: [], rowCount: 1 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const buildEventWrites = () => issued.filter(q => /INSERT INTO build_events/i.test(q))

const REQ_BODY = { asset_id: 'ka_kshetra', build_id: 'some-build-id', chart_id: VICTIM_CHART }

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/build/rebuild — V3-E-010 cross-tenant build_events write', () => {
  it('DENIES a non-owner guest — and writes NO build_events row', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq(REQ_BODY))
    expect(res.status).toBe(403)
    expect(buildEventWrites()).toHaveLength(0)
  })

  it('DENIES a chart_grants view-grantee — a read grant is not a rebuild grant', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await POST(makeReq(REQ_BODY))
    expect(res.status).toBe(403)
    expect(buildEventWrites()).toHaveLength(0)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await POST(makeReq(REQ_BODY))
    expect(res.status).toBe(403)
    expect(buildEventWrites()).toHaveLength(0)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    issued = []
    const res = await POST(makeReq(REQ_BODY))
    expect(res.status).toBe(401)
    expect(buildEventWrites()).toHaveLength(0)
  })

  it('ALLOWS the owner — the legitimate single-asset rebuild path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq(REQ_BODY))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(buildEventWrites().length).toBeGreaterThan(0)
  })

  it('ALLOWS super_admin on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await POST(makeReq(REQ_BODY))
    expect(res.status).toBe(200)
    expect(buildEventWrites().length).toBeGreaterThan(0)
  })
})
