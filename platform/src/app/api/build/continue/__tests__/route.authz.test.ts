/**
 * Regression test for V3-E-011 (Paripraśna Assurance systemic authorization
 * sweep, Session S5): cross-tenant build-resume WRITE on POST
 * /api/build/continue.
 *
 * Same root-cause family as B-001/B-007/B-008 and the two cockpit siblings
 * fixed alongside this route: the handler checked only
 * `getServerUser() !== null` and then trusted the caller-supplied
 * `chart_id` (here, from the JSON body) with no ownership/grant check — any
 * authenticated user could resume/continue another tenant's build
 * (`SELECT ... FROM builds WHERE chart_id=$1`) and INSERT a `build_events`
 * row against it: a genuine cross-tenant write, not merely a read
 * disclosure.
 *
 * Fix: gate the route through `requireChartPermission` at 'write' access
 * (owner or super_admin only — resuming a build is state-changing, so a
 * chart_grants 'view' grantee must not pass, matching the B-008 precedent
 * that a mere view-grantee cannot trigger builds), placed right after
 * chart_id is extracted from the body, before the SELECT.
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

function makeReq(chartId: string): NextRequest {
  return new NextRequest('http://localhost/api/build/continue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_id: chartId }),
  })
}

/** SQL-shape-dispatching mock, mirroring the runs/route.authz.test.ts precedent. */
function setupMocks(opts: {
  uid: string
  role?: string
  ownerId?: string | null
  grantPermission?: string | null
  buildId?: string | null
}) {
  const { uid, role = 'guest', ownerId = VICTIM_UID, grantPermission = null, buildId = 'build-1' } = opts
  mockGetServerUser.mockResolvedValue({ uid })

  mockQuery.mockImplementation((sql: string) => {
    if (/FROM profiles/.test(sql)) return Promise.resolve({ rows: [{ role }], rowCount: 1 })
    if (/FROM chart_grants/.test(sql)) {
      return Promise.resolve({
        rows: grantPermission ? [{ permission: grantPermission }] : [],
        rowCount: grantPermission ? 1 : 0,
      })
    }
    if (/owner_id[\s\S]*FROM charts/.test(sql)) {
      return Promise.resolve({
        rows: ownerId !== null ? [{ owner_id: ownerId }] : [],
        rowCount: ownerId !== null ? 1 : 0,
      })
    }
    if (/INSERT INTO build_events/.test(sql)) return Promise.resolve({ rows: [], rowCount: 1 })
    if (/FROM builds\b/.test(sql)) {
      return Promise.resolve({ rows: buildId ? [{ build_id: buildId }] : [], rowCount: buildId ? 1 : 0 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const insertCalls = () => mockQuery.mock.calls.filter(([sql]) => /INSERT INTO build_events/.test(sql as string))
const selectCalls = () => mockQuery.mock.calls.filter(([sql]) => /FROM builds\b/.test(sql as string))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('POST /api/build/continue — V3-E-011 cross-tenant build-resume write', () => {
  it('DENIES a non-owner guest resuming another chart\'s build — zero DB writes', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(insertCalls()).toHaveLength(0)
    expect(selectCalls()).toHaveLength(0)
  })

  it('DENIES a chart_grants view-grantee — a read grant is not a build-resume grant', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await POST(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(insertCalls()).toHaveLength(0)
  })

  it('DENIES a caller when the chart does not exist at all', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await POST(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(insertCalls()).toHaveLength(0)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    const res = await POST(makeReq(VICTIM_CHART))
    expect(res.status).toBe(401)
    expect(insertCalls()).toHaveLength(0)
  })

  it('ALLOWS the legitimate owner to resume their own build', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await POST(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.ok).toBe(true)
    expect(body.build_id).toBe('build-1')
    expect(insertCalls()).toHaveLength(1)
  })

  it('ALLOWS super_admin to resume a build on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await POST(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    expect(insertCalls()).toHaveLength(1)
  })
})
