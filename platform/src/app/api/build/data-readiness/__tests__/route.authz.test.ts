/**
 * Regression test for V3-E-011 finding 3 — cross-tenant read disclosure on
 * GET /api/build/data-readiness.
 *
 * Before the fix this route checked only `getServerUser() !== null` and then
 * queried `build_events`/`build_checkpoints` for a caller-supplied `chart_id`
 * with no ownership check, returning that chart's build_status, ready/missing
 * asset lists to ANY authenticated user. Fix adds
 * `requireChartPermission({ access: 'read' })` right after `chart_id` is read,
 * before the first DB query — same brain/pattern as the sibling
 * V3-E-010 rebuild fixes (`POST /api/build/rebuild`).
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
  return new NextRequest(`http://localhost/api/build/data-readiness?chart_id=${chartId}`)
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
    if (/FROM asset_registry/.test(sql)) {
      return Promise.resolve({ rows: [{ asset_id: 'ga_chart_facts' }], rowCount: 1 })
    }
    if (/FROM build_events/.test(sql)) {
      return Promise.resolve({ rows: [{ build_id: 'build-1' }], rowCount: 1 })
    }
    if (/FROM build_checkpoints/.test(sql)) {
      return Promise.resolve({ rows: [{ asset_id: 'ga_chart_facts', status: 'success' }], rowCount: 1 })
    }
    return Promise.resolve({ rows: [], rowCount: 0 })
  })
}

const dataQueries = () => issued.filter(q => /FROM build_events|FROM build_checkpoints|FROM asset_registry/i.test(q))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('GET /api/build/data-readiness — V3-E-011 finding 3 cross-tenant read disclosure', () => {
  it('DENIES a non-owner guest — and never discloses build readiness data', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(dataQueries()).toHaveLength(0)
  })

  it('DENIES a chart_grants view-grantee only if not granted — sanity: no grant at all', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: VICTIM_UID, grantPermission: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
  })

  it('DENIES when the chart does not exist', async () => {
    setupMocks({ uid: ATTACKER_UID, role: 'guest', ownerId: null })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(403)
    expect(dataQueries()).toHaveLength(0)
  })

  it('DENIES an unauthenticated caller', async () => {
    mockGetServerUser.mockResolvedValue(null)
    issued = []
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(401)
    expect(dataQueries()).toHaveLength(0)
  })

  it('ALLOWS the owner — the legitimate readiness-check path must keep working', async () => {
    setupMocks({ uid: VICTIM_UID, role: 'guest', ownerId: VICTIM_UID })
    const res = await GET(makeReq(VICTIM_CHART))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.chart_id).toBe(VICTIM_CHART)
    expect(dataQueries().length).toBeGreaterThan(0)
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
