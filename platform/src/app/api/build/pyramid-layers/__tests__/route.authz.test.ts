/**
 * Regression test for V3-E-011 finding 4 — cross-tenant read disclosure on
 * GET /api/build/pyramid-layers.
 *
 * Before the fix this route checked only `getServerUser() !== null` and then
 * queried `pyramid_layers` for a caller-supplied `chart_id` with no ownership
 * check, returning that chart's per-layer build status to ANY authenticated
 * user. Fix adds `requireChartPermission({ access: 'read' })` immediately
 * after the existing user check — preserving the route's existing order
 * (chart_id presence is validated BEFORE getServerUser() runs; that order is
 * untouched) — before the `pyramid_layers` query.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextRequest } from 'next/server'

const { mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))

import { GET } from '../route'

const VICTIM_CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const VICTIM_UID = 'victim-uid'
const ATTACKER_UID = 'attacker-uid'
const ADMIN_UID = 'admin-uid'

let issued: string[] = []

function makeReq(chartId: string): NextRequest {
  return new NextRequest(`http://localhost/api/build/pyramid-layers?chart_id=${chartId}`)
}

function setupMocks(opts: { uid: string; role?: string; ownerId?: string | null; grantPermission?: string | null }) {
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
      return Promise.resolve({ rows: ownerId ? [{ owner_id: ownerId }] : [], rowCount: ownerId ? 1 : 0 })
    }
    if (/FROM pyramid_layers/.test(sql)) {
      return Promise.resolve({
        rows: [{ layer: 'L1', sublayer: 'ga_chart_facts', status: 'complete' }],
        rowCount: 1,
      })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const layerQueries = () => issued.filter(q => /FROM pyramid_layers/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/build/pyramid-layers — V3-E-011 finding 4 cross-tenant read disclosure', () => {
  it('DENIES a non-owner guest — and never discloses per-layer build status', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(layerQueries()).toHaveLength(0)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(layerQueries()).toHaveLength(0)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    issued = []
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(401)
    expect(layerQueries()).toHaveLength(0)
  })

  it('returns 400 for a missing chart_id before ever calling getServerUser (existing order preserved)', async () => {
    mockGetServerUser.mockResolvedValue({ uid: ATTACKER_UID })
    const res = await GET(new NextRequest('http://localhost/api/build/pyramid-layers'))
    expect(res.status).toBe(400)
    expect(mockGetServerUser).not.toHaveBeenCalled()
  })

  it('ALLOWS the owner — the legitimate layer-status path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.chart_id).toBe(VICTIM_CHART)
    expect(layerQueries().length).toBeGreaterThan(0)
  })

  it('ALLOWS a chart_grants view-grantee — read disclosure is exactly what a view grant is for', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: 'view' })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })

  it('ALLOWS super_admin on a chart they do not own', async () => {
    setupMocks({ uid: ADMIN_UID, role: 'super_admin', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
  })
})
